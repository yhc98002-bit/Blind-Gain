#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from scripts.finalize_pilot_step_evaluation import R19_MANIFEST_SHA256
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT


ROOT = Path(__file__).resolve().parents[1]
AGGREGATE_TAG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite pipeline state: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def validate_evaluation(
    evaluation: dict[str, Any],
    *,
    evaluation_run: Path,
    training_run: Path,
    checkpoint_path: Path,
    global_step: int,
) -> None:
    expected = {
        "job_type": "fliptrack_v02_image_evaluation",
        "global_step": global_step,
        "image_mode": "real",
        "max_new_tokens": 32,
        "decoding": {"temperature": 0.0, "top_p": 1.0, "n": 1},
        "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
        "data_manifest_hash": R19_MANIFEST_SHA256,
    }
    mismatches = {
        key: {"expected": value, "observed": evaluation.get(key)}
        for key, value in expected.items()
        if evaluation.get(key) != value
    }
    path_expectations = {
        "source_training_run": training_run,
        "model_revision": checkpoint_path,
    }
    for key, expected_path in path_expectations.items():
        observed = Path(str(evaluation.get(key, "")))
        if observed.resolve() != expected_path.resolve():
            mismatches[key] = {
                "expected": str(expected_path.resolve()),
                "observed": str(observed.resolve()),
            }
    if mismatches:
        raise ValueError(f"evaluation contract mismatch for {evaluation_run}: {mismatches}")


def find_existing_aggregate(tag: str, source_run: Path, root: Path = ROOT) -> Path | None:
    matches = sorted((root / "experiments/runs").glob(f"fliptrack_aggregate_{tag}_*"))
    valid: list[Path] = []
    for path in matches:
        manifest_path = path / "run_manifest.json"
        if not manifest_path.is_file():
            continue
        payload = _read(manifest_path)
        if Path(str(payload.get("source_run", ""))).resolve() == source_run.resolve():
            valid.append(path)
    if len(valid) > 1:
        raise ValueError(f"multiple aggregate runs found for immutable tag {tag}: {valid}")
    return valid[0] if valid else None


def launch_aggregate(source_run: Path, tag: str, root: Path = ROOT) -> Path:
    result = subprocess.run(
        ["bash", "scripts/launch_fliptrack_aggregate.sh", str(source_run), tag, "sync"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"aggregate launch failed ({result.returncode}): {result.stderr.strip()}")
    candidates = [line.strip() for line in result.stdout.splitlines() if line.strip().startswith("experiments/runs/")]
    if len(candidates) != 1:
        raise RuntimeError(f"aggregate launcher returned an ambiguous run path: {result.stdout!r}")
    return root / candidates[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation-run", type=Path, required=True)
    parser.add_argument("--training-run", type=Path, required=True)
    parser.add_argument("--checkpoint-path", type=Path, required=True)
    parser.add_argument("--global-step", type=int, choices=(60, 100), required=True)
    parser.add_argument("--aggregate-tag", required=True)
    parser.add_argument("--marker", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--poll-seconds", type=int, default=60)
    args = parser.parse_args()
    if not AGGREGATE_TAG_PATTERN.fullmatch(args.aggregate_tag):
        raise ValueError("invalid aggregate tag")
    if args.poll_seconds < 10:
        raise ValueError("poll interval must be at least 10 seconds")
    if args.marker.exists() or args.state.exists():
        raise FileExistsError("pilot evaluation marker/state already exists")

    evaluation_manifest = args.evaluation_run / "run_manifest.json"
    training_manifest = args.training_run / "run_manifest.json"
    if not evaluation_manifest.is_file() or not training_manifest.is_file():
        raise FileNotFoundError("evaluation or training manifest absent")
    training = _read(training_manifest)
    if training.get("job_type") != "l13_mechanical_pilot_arm" or training.get("status") != "complete":
        raise ValueError("training source must be a complete L13 pilot arm")
    expected_checkpoint = Path(str(training["checkpoint_path"])) / f"global_step_{args.global_step}/actor/huggingface"
    if expected_checkpoint.resolve() != args.checkpoint_path.resolve():
        raise ValueError("checkpoint path does not match training run and global step")

    while True:
        evaluation = _read(evaluation_manifest)
        validate_evaluation(
            evaluation,
            evaluation_run=args.evaluation_run,
            training_run=args.training_run,
            checkpoint_path=args.checkpoint_path,
            global_step=args.global_step,
        )
        status = evaluation.get("status")
        if status == "complete":
            if evaluation.get("artifacts_exist") is not True:
                raise ValueError("complete evaluation has unverified artifacts")
            break
        if status != "running":
            raise RuntimeError(f"evaluation reached terminal non-complete status: {status!r}")
        print(json.dumps({"time_utc": _now(), "evaluation_status": status}), flush=True)
        time.sleep(args.poll_seconds)

    aggregate_run = find_existing_aggregate(args.aggregate_tag, args.evaluation_run)
    if aggregate_run is None:
        aggregate_run = launch_aggregate(args.evaluation_run, args.aggregate_tag)
    aggregate = _read(aggregate_run / "run_manifest.json")
    if aggregate.get("status") != "complete":
        raise RuntimeError(f"aggregate run is not complete: {aggregate_run}")

    subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            "scripts/finalize_pilot_step_evaluation.py",
            "--evaluation-run",
            str(args.evaluation_run),
            "--aggregate-run",
            str(aggregate_run),
            "--checkpoint-path",
            str(args.checkpoint_path),
            "--global-step",
            str(args.global_step),
            "--output",
            str(args.marker),
        ],
        cwd=ROOT,
        check=True,
    )
    _atomic_json(
        args.state,
        {
            "schema_version": "blind-gains.pilot-step-evaluation-watch.v1",
            "status": "complete",
            "scientific_gate_decision": None,
            "evaluation_run": str(args.evaluation_run),
            "aggregate_run": str(aggregate_run.relative_to(ROOT)),
            "training_run": str(args.training_run),
            "checkpoint_path": str(args.checkpoint_path),
            "global_step": args.global_step,
            "marker": str(args.marker),
            "completed_at_utc": _now(),
        },
    )


if __name__ == "__main__":
    main()
