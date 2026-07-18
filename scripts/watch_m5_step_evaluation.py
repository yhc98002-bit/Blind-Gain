#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from scripts.watch_pilot_step_evaluation import find_existing_aggregate, launch_aggregate


ROOT = Path(__file__).resolve().parents[1]
REGISTERED_STEPS = frozenset({150, 200, 300, 400})


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite M5 evaluation state: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f".{path.name}.{os.getpid()}.partial")
    partial.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(partial, path)


def validate_source(source_run: Path, checkpoint_path: Path, global_step: int) -> None:
    if global_step not in REGISTERED_STEPS:
        raise ValueError("M5 global step is not registered")
    manifest = _read(source_run / "run_manifest.json")
    if manifest.get("job_type") != "m5_anchor_longhorizon_400":
        raise ValueError("M5 evaluation source has the wrong job type")
    if manifest.get("target_global_step") != 400 or manifest.get("terminal_no_extension") is not True:
        raise ValueError("M5 source lacks the fixed terminal contract")
    if global_step == 150:
        incident = _read(ROOT / "reports/m5_host_memory_incident_v1.json")
        if Path(str(incident.get("failed_run", ""))).resolve() != source_run.resolve():
            raise ValueError("M5 step-150 source is not bound by the incident record")
        if manifest.get("status") != "fail" or incident.get("last_verified_checkpoint", {}).get("step") != 150:
            raise ValueError("M5 step-150 failed-parent provenance is invalid")
    elif manifest.get("status") not in {"running", "complete"}:
        raise ValueError("M5 source is not running or complete")
    expected = (
        Path(str(manifest["checkpoint_path"]))
        / f"global_step_{global_step}/actor/huggingface"
    )
    if checkpoint_path.resolve() != expected.resolve():
        raise ValueError("M5 checkpoint does not match the source run and global step")


def wait_for_complete(run: Path, *, expected_job_type: str, poll_seconds: int) -> None:
    manifest_path = run / "run_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"evaluation manifest absent: {manifest_path}")
    while True:
        manifest = _read(manifest_path)
        if manifest.get("job_type") != expected_job_type:
            raise ValueError(f"unexpected evaluation job type: {manifest.get('job_type')!r}")
        status = manifest.get("status")
        if status == "complete":
            if manifest.get("artifacts_exist") is not True:
                raise ValueError("complete evaluation has unverified artifacts")
            return
        if status != "running":
            raise RuntimeError(f"evaluation reached terminal non-complete status: {status!r}")
        print(json.dumps({"time_utc": _now(), "run": str(run), "status": status}), flush=True)
        time.sleep(poll_seconds)


def aggregate(run: Path, tag: str) -> Path:
    existing = find_existing_aggregate(tag, run)
    result = existing if existing is not None else launch_aggregate(run, tag)
    manifest = _read(result / "run_manifest.json")
    if manifest.get("status") != "complete":
        raise RuntimeError(f"aggregate run is not complete: {result}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geo3k-run", type=Path, required=True)
    parser.add_argument("--r19-evaluation-run", type=Path, required=True)
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--checkpoint-path", type=Path, required=True)
    parser.add_argument("--global-step", type=int, required=True)
    parser.add_argument("--aggregate-tag", required=True)
    parser.add_argument("--gray-evaluation-run", type=Path)
    parser.add_argument("--gray-aggregate-tag")
    parser.add_argument("--noise-evaluation-run", type=Path)
    parser.add_argument("--noise-aggregate-tag")
    parser.add_argument("--marker", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--poll-seconds", type=int, default=60)
    args = parser.parse_args()
    if args.poll_seconds < 10:
        raise ValueError("poll interval must be at least 10 seconds")
    if args.marker.exists() or args.state.exists():
        raise FileExistsError("M5 evaluation marker/state already exists")
    blind_args = (
        args.gray_evaluation_run,
        args.gray_aggregate_tag,
        args.noise_evaluation_run,
        args.noise_aggregate_tag,
    )
    if args.global_step == 400 and any(value is None for value in blind_args):
        raise ValueError("M5 step 400 requires gray and noise evaluation runs/tags")
    if args.global_step != 400 and any(value is not None for value in blind_args):
        raise ValueError("M5 blind-floor evaluations are registered only at step 400")
    validate_source(args.source_run, args.checkpoint_path, args.global_step)

    wait_for_complete(args.geo3k_run, expected_job_type="m5_geo3k_checkpoint_eval", poll_seconds=args.poll_seconds)
    wait_for_complete(args.r19_evaluation_run, expected_job_type="fliptrack_v02_image_evaluation", poll_seconds=args.poll_seconds)
    r19_aggregate = aggregate(args.r19_evaluation_run, args.aggregate_tag)
    gray_aggregate: Path | None = None
    noise_aggregate: Path | None = None
    if args.global_step == 400:
        assert args.gray_evaluation_run is not None and args.gray_aggregate_tag is not None
        assert args.noise_evaluation_run is not None and args.noise_aggregate_tag is not None
        wait_for_complete(args.gray_evaluation_run, expected_job_type="fliptrack_v02_image_evaluation", poll_seconds=args.poll_seconds)
        wait_for_complete(args.noise_evaluation_run, expected_job_type="fliptrack_v02_image_evaluation", poll_seconds=args.poll_seconds)
        gray_aggregate = aggregate(args.gray_evaluation_run, args.gray_aggregate_tag)
        noise_aggregate = aggregate(args.noise_evaluation_run, args.noise_aggregate_tag)

    command = [
        str(ROOT / ".venv/bin/python"),
        "scripts/finalize_m5_step_evaluation.py",
        "--geo3k-run", str(args.geo3k_run),
        "--r19-evaluation-run", str(args.r19_evaluation_run),
        "--r19-aggregate-run", str(r19_aggregate),
        "--source-run", str(args.source_run),
        "--checkpoint-path", str(args.checkpoint_path),
        "--global-step", str(args.global_step),
        "--output", str(args.marker),
    ]
    if args.global_step == 400:
        assert gray_aggregate is not None and noise_aggregate is not None
        command.extend(
            [
                "--gray-evaluation-run", str(args.gray_evaluation_run),
                "--gray-aggregate-run", str(gray_aggregate),
                "--noise-evaluation-run", str(args.noise_evaluation_run),
                "--noise-aggregate-run", str(noise_aggregate),
            ]
        )
    subprocess.run(command, cwd=ROOT, check=True)
    _atomic_json(
        args.state,
        {
            "schema_version": "blind-gains.m5-step-evaluation-watch.v1",
            "status": "complete",
            "source_training_run": str(args.source_run),
            "checkpoint_path": str(args.checkpoint_path),
            "global_step": args.global_step,
            "geo3k_run": str(args.geo3k_run),
            "r19_evaluation_run": str(args.r19_evaluation_run),
            "r19_aggregate_run": str(r19_aggregate.relative_to(ROOT)),
            "gray_evaluation_run": str(args.gray_evaluation_run) if args.gray_evaluation_run else None,
            "gray_aggregate_run": str(gray_aggregate.relative_to(ROOT)) if gray_aggregate else None,
            "noise_evaluation_run": str(args.noise_evaluation_run) if args.noise_evaluation_run else None,
            "noise_aggregate_run": str(noise_aggregate.relative_to(ROOT)) if noise_aggregate else None,
            "marker": str(args.marker),
            "completed_at_utc": _now(),
            "performance_values_opened": False,
            "scientific_gate_decision": None,
        },
    )


if __name__ == "__main__":
    main()
