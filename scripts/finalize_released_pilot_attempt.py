#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RELEASE_EXIT_CODE = 75


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _resolve(project_root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_root / path


def _logged_steps(experiment_log: Path) -> list[int]:
    if not experiment_log.is_file():
        raise ValueError(f"experiment log absent: {experiment_log}")
    steps: list[int] = []
    for line_number, line in enumerate(experiment_log.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        payload = json.loads(line)
        step = payload.get("step")
        if not isinstance(step, int):
            raise ValueError(f"non-integer step at {experiment_log}:{line_number}")
        steps.append(step)
    return sorted(set(steps))


def finalize_released_attempt(
    manifest_path: Path,
    evidence_path: Path,
    release_confirmation: str,
    *,
    project_root: Path = ROOT,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    if evidence_path.exists():
        raise ValueError(f"evidence output already exists: {evidence_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = {
        "status": "running",
        "job_type": "l13_mechanical_pilot_arm",
        "arm": "a2_gray",
        "node": "an21",
        "resumed_from_global_step": 60,
    }
    for key, expected in required.items():
        if payload.get(key) != expected:
            raise ValueError(f"unexpected {key}: {payload.get(key)!r}; expected {expected!r}")
    if not release_confirmation.strip():
        raise ValueError("release confirmation must be non-empty")

    checkpoint_root = _resolve(project_root, str(payload["checkpoint_path"]))
    durable_checkpoints = sorted(path.name for path in checkpoint_root.glob("global_step_*") if path.is_dir())
    tracker = checkpoint_root / "checkpoint_tracker.json"
    if durable_checkpoints or tracker.exists():
        raise ValueError(
            "released attempt has durable resume state; refuse discard finalization: "
            f"checkpoints={durable_checkpoints}, tracker={tracker.exists()}"
        )

    steps = _logged_steps(checkpoint_root / "experiment_log.jsonl")
    if 60 not in steps:
        raise ValueError("released attempt log does not contain the registered resume step 60")
    discarded_steps = [step for step in steps if step > 60]
    if not discarded_steps or max(discarded_steps) >= 80:
        raise ValueError(f"unexpected uncheckpointed step range: {discarded_steps}")

    before_hash = _sha256(manifest_path)
    ended = (now or dt.datetime.now(dt.timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    deviation = {
        "code": "compute_allocation_released_before_checkpoint",
        "scientific_config_change": False,
        "release_confirmation": release_confirmation,
        "last_logged_step": max(steps),
        "discarded_uncheckpointed_steps": discarded_steps,
        "durable_checkpoint_written": False,
    }
    payload.setdefault("deviations", []).append(deviation)
    payload.update(
        {
            "end_time_utc": ended,
            "exit_code": RELEASE_EXIT_CODE,
            "artifacts_exist": False,
            "status": "fail",
            "termination_reason": deviation,
        }
    )
    _atomic_json(manifest_path, payload)
    after_hash = _sha256(manifest_path)
    evidence = {
        "schema_version": "blind-gains.released-pilot-attempt.v1",
        "status": "pass",
        "run_id": payload["run_id"],
        "node": payload["node"],
        "release_confirmation": release_confirmation,
        "checkpoint_root": str(checkpoint_root),
        "durable_checkpoints": durable_checkpoints,
        "checkpoint_tracker_exists": tracker.exists(),
        "logged_steps": steps,
        "discarded_uncheckpointed_steps": discarded_steps,
        "manifest_sha256_before": before_hash,
        "manifest_sha256_after": after_hash,
        "finalized_at_utc": ended,
    }
    _atomic_json(evidence_path, evidence)
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--release-confirmation", required=True)
    args = parser.parse_args()
    finalize_released_attempt(args.manifest, args.evidence, args.release_confirmation)


if __name__ == "__main__":
    main()
