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
    require_exact_row_count: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    missing_counts: collections.Counter[str] = collections.Counter()
    reward_counts: collections.Counter[float] = collections.Counter()
    reason_counts: collections.Counter[str] = collections.Counter()
    identity_mismatches = 0
    nonfinite_values = 0
    version_mismatches = 0
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
        if row.get("parser_version") != "canonical-v2" or row.get("pilot_reward_version") != "pilot-reward-v1":
            version_mismatches += 1

    checks = {
        "row_count_matches_contract": (
            len(rows) == expected_minimum_rows
            if require_exact_row_count
            else len(rows) >= expected_minimum_rows
        ),
        "all_required_fields_present": not missing_counts,
        "all_numeric_shadows_finite": nonfinite_values == 0,
        "training_reward_identity_exact": identity_mismatches == 0,
        "training_reward_non_degenerate": len(reward_counts) >= 2,
        "reason_codes_valid": not errors,
        "parser_and_reward_versions_exact": version_mismatches == 0,
    }
    if require_exact_row_count and len(rows) != expected_minimum_rows:
        errors.append(
            f"shadow row count {len(rows)} does not equal expected contract {expected_minimum_rows}"
        )
    elif len(rows) < expected_minimum_rows:
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
    if version_mismatches:
        errors.append(f"parser/reward version mismatches: {version_mismatches}")
    return {
        "schema_version": "blind-gains.pilot-reward-smoke-audit.v2",
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
        "version_mismatches": version_mismatches,
        "errors": errors,
    }


def audit_training_contract(
    manifest: dict[str, Any], training_log: str, *, expected_steps: int
) -> dict[str, bool]:
    return {
        "manifest_job_type_exact": manifest.get("job_type") == "l3_pilot_reward_plumbing_smoke",
        "manifest_exit_zero": manifest.get("status") == "complete" and manifest.get("exit_code") == 0,
        "command_registers_expected_steps": f"trainer.max_steps={expected_steps}" in str(manifest.get("command", "")),
        "training_progress_reaches_expected_steps": f"{expected_steps:.2f}/{expected_steps:.2f}" in training_log,
        "training_log_has_no_traceback": "Traceback (most recent call last)" not in training_log,
        "training_log_has_no_image_grid_mismatch": "Image features and image tokens do not match" not in training_log,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--shadow-jsonl", type=Path, required=True)
    parser.add_argument("--training-log", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-steps", type=int, default=5)
    parser.add_argument("--rollout-batch-size", type=int, default=512)
    parser.add_argument("--group-size", type=int, default=5)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite pilot reward audit: {args.output}")
    manifest = json.loads(args.run_manifest.read_text(encoding="utf-8"))
    training_log_path = args.training_log or Path(str(manifest.get("stdout_stderr_log", "")))
    if not training_log_path.is_file():
        raise FileNotFoundError(f"pilot reward smoke training log is absent: {training_log_path}")
    training_log = training_log_path.read_text(encoding="utf-8", errors="replace")
    rows = [
        json.loads(line)
        for line in args.shadow_jsonl.read_text(encoding="utf-8").splitlines()
        if line
    ]
    expected = args.expected_steps * args.rollout_batch_size * args.group_size
    payload = audit_shadow_rows(
        rows,
        expected_minimum_rows=expected,
        require_exact_row_count=True,
    )
    training_checks = audit_training_contract(
        manifest, training_log, expected_steps=args.expected_steps
    )
    payload["training_contract_checks"] = training_checks
    payload["status"] = (
        "pass" if payload["status"] == "pass" and all(training_checks.values()) else "fail"
    )
    payload.update(
        {
            "run_manifest": str(args.run_manifest),
            "shadow_jsonl": str(args.shadow_jsonl),
            "training_log": str(training_log_path),
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
