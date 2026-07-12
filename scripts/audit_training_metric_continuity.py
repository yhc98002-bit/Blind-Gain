#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            raise ValueError(f"blank metric row at {path}:{line_number}")
        row = json.loads(line)
        if not isinstance(row, dict) or not isinstance(row.get("step"), int):
            raise ValueError(f"invalid metric row at {path}:{line_number}")
        rows.append(row)
    return rows


def audit_metric_continuity(
    segment_paths: list[Path],
    *,
    expected_steps: int,
    validation_cadence: int,
) -> dict[str, Any]:
    if not segment_paths:
        raise ValueError("at least one metric segment is required")
    if expected_steps < 1 or validation_cadence < 1:
        raise ValueError("expected steps and validation cadence must be positive")

    training_counts: Counter[int] = Counter()
    validation_counts: Counter[int] = Counter()
    malformed_training_steps: set[int] = set()
    segment_records: list[dict[str, Any]] = []
    for path in segment_paths:
        rows = _read_rows(path)
        for row in rows:
            step = int(row["step"])
            if "reward" in row or "actor" in row or "perf" in row:
                training_counts[step] += 1
                required = ("reward", "actor", "perf", "response_length")
                if any(not isinstance(row.get(field), dict) for field in required):
                    malformed_training_steps.add(step)
                elif not all(
                    key in row["reward"] for key in ("overall", "format", "accuracy")
                ) or not all(key in row["actor"] for key in ("kl_loss", "ppo_kl")):
                    malformed_training_steps.add(step)
            if isinstance(row.get("val"), dict):
                validation_counts[step] += 1
        segment_records.append(
            {
                "path": str(path),
                "sha256": _sha256(path),
                "row_count": len(rows),
                "min_step": min((int(row["step"]) for row in rows), default=None),
                "max_step": max((int(row["step"]) for row in rows), default=None),
            }
        )

    expected_training = set(range(1, expected_steps + 1))
    expected_validation = set(range(0, expected_steps + 1, validation_cadence))
    observed_training = set(training_counts)
    observed_validation = set(validation_counts)
    missing_training = sorted(expected_training - observed_training)
    extra_training = sorted(observed_training - expected_training)
    duplicate_training = sorted(step for step, count in training_counts.items() if count != 1)
    missing_validation = sorted(expected_validation - observed_validation)
    extra_validation = sorted(observed_validation - expected_validation)
    duplicate_validation = sorted(step for step, count in validation_counts.items() if count != 1)
    checks = {
        "all_training_steps_present_once": not missing_training
        and not extra_training
        and not duplicate_training,
        "all_training_rows_have_reward_kl_perf": not malformed_training_steps,
        "all_validation_steps_present_once": not missing_validation
        and not extra_validation
        and not duplicate_validation,
        "segment_hashes_recorded": all(
            len(record["sha256"]) == 64 for record in segment_records
        ),
    }
    return {
        "schema_version": "blind-gains.training-metric-continuity-audit.v1",
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "expected_steps": expected_steps,
        "validation_cadence": validation_cadence,
        "segments": segment_records,
        "observed_training_steps": sorted(observed_training),
        "observed_validation_steps": sorted(observed_validation),
        "missing_training_steps": missing_training,
        "extra_training_steps": extra_training,
        "duplicate_training_steps": duplicate_training,
        "malformed_training_steps": sorted(malformed_training_steps),
        "missing_validation_steps": missing_validation,
        "extra_validation_steps": extra_validation,
        "duplicate_validation_steps": duplicate_validation,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--segment", type=Path, action="append", required=True)
    parser.add_argument("--expected-steps", type=int, required=True)
    parser.add_argument("--validation-cadence", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite continuity audit: {args.output}")
    payload = audit_metric_continuity(
        args.segment,
        expected_steps=args.expected_steps,
        validation_cadence=args.validation_cadence,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(f".{args.output.name}.partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, args.output)
    print(json.dumps(payload, sort_keys=True))
    raise SystemExit(0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
