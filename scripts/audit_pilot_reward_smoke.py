#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import json
import math
import os
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "training_reward",
    "native_r1v_shadow_reward",
    "canonical_eval_reward",
    "reward_disagreement_reason",
    "mathruler_accuracy_reward",
    "contract_valid",
    "parser_version",
    "pilot_reward_version",
}
VALID_REASONS = {
    "none",
    "canonical_correct_mathruler_incorrect",
    "mathruler_correct_canonical_incorrect",
    "mathruler_error_canonical_incorrect",
    "mathruler_error_canonical_correct",
}


def audit_shadow_rows(
    rows: list[dict[str, Any]],
    *,
    expected_minimum_rows: int,
    format_weight: float = 0.5,
) -> dict[str, Any]:
    errors: list[str] = []
    missing_counts: collections.Counter[str] = collections.Counter()
    reward_counts: collections.Counter[float] = collections.Counter()
    reason_counts: collections.Counter[str] = collections.Counter()
    identity_mismatches = 0
    nonfinite_values = 0
    for row in rows:
        for field in REQUIRED_FIELDS - row.keys():
            missing_counts[field] += 1
        try:
            numeric = {
                key: float(row[key])
                for key in (
                    "training_reward",
                    "native_r1v_shadow_reward",
                    "canonical_eval_reward",
                    "mathruler_accuracy_reward",
                )
            }
            if not all(math.isfinite(value) for value in numeric.values()):
                nonfinite_values += 1
            expected = (
                (1.0 - format_weight) * numeric["mathruler_accuracy_reward"]
                + format_weight * float(bool(row["contract_valid"]))
            )
            if not math.isclose(numeric["training_reward"], expected, abs_tol=1e-12):
                identity_mismatches += 1
            reward_counts[numeric["training_reward"]] += 1
        except (KeyError, TypeError, ValueError):
            nonfinite_values += 1
        reason = str(row.get("reward_disagreement_reason", "missing"))
        reason_counts[reason] += 1
        if reason not in VALID_REASONS:
            errors.append(f"invalid reward disagreement reason: {reason}")
        if row.get("parser_version") not in {None, "canonical-v2"}:
            errors.append(f"unexpected parser version: {row.get('parser_version')}")

    checks = {
        "row_count_at_least_expected": len(rows) >= expected_minimum_rows,
        "all_required_fields_present": not missing_counts,
        "all_numeric_shadows_finite": nonfinite_values == 0,
        "training_reward_identity_exact": identity_mismatches == 0,
        "training_reward_non_degenerate": len(reward_counts) >= 2,
        "reason_codes_valid": not errors,
    }
    if len(rows) < expected_minimum_rows:
        errors.append(
            f"shadow row count {len(rows)} is below expected minimum {expected_minimum_rows}"
        )
    if missing_counts:
        errors.append(f"missing shadow fields: {dict(sorted(missing_counts.items()))}")
    if nonfinite_values:
        errors.append(f"nonfinite or malformed shadow rows: {nonfinite_values}")
    if identity_mismatches:
        errors.append(f"training reward identity mismatches: {identity_mismatches}")
    if len(reward_counts) < 2:
        errors.append("training reward is degenerate")
    return {
        "schema_version": "blind-gains.pilot-reward-smoke-audit.v1",
        "status": "pass" if all(checks.values()) and not errors else "fail",
        "checks": checks,
        "n_rows": len(rows),
        "expected_minimum_rows": expected_minimum_rows,
        "training_reward_counts": {
            str(key): value for key, value in sorted(reward_counts.items())
        },
        "reward_disagreement_reason_counts": dict(sorted(reason_counts.items())),
        "missing_field_counts": dict(sorted(missing_counts.items())),
        "identity_mismatches": identity_mismatches,
        "nonfinite_rows": nonfinite_values,
        "errors": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--shadow-jsonl", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-steps", type=int, default=5)
    parser.add_argument("--rollout-batch-size", type=int, default=512)
    parser.add_argument("--group-size", type=int, default=5)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite pilot reward audit: {args.output}")
    manifest = json.loads(args.run_manifest.read_text(encoding="utf-8"))
    if manifest.get("status") != "complete" or manifest.get("exit_code") != 0:
        raise ValueError("pilot reward smoke run is not complete with exit code zero")
    rows = [
        json.loads(line)
        for line in args.shadow_jsonl.read_text(encoding="utf-8").splitlines()
        if line
    ]
    expected = args.expected_steps * args.rollout_batch_size * args.group_size
    payload = audit_shadow_rows(rows, expected_minimum_rows=expected)
    payload.update(
        {
            "run_manifest": str(args.run_manifest),
            "shadow_jsonl": str(args.shadow_jsonl),
            "expected_steps": args.expected_steps,
            "rollout_batch_size": args.rollout_batch_size,
            "group_size": args.group_size,
        }
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(f".{args.output.name}.partial.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, args.output)
    print(json.dumps(payload, sort_keys=True))
    raise SystemExit(0 if payload["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
