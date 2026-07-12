#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import os
from pathlib import Path
import re
from typing import Any

import yaml


REQUIRED_FIELDS = {
    "training_reward",
    "native_r1v_shadow_reward",
    "canonical_eval_reward",
    "reward_disagreement_reason",
    "mathruler_accuracy_reward",
    "contract_valid",
    "parser_version",
    "pilot_reward_version",
    "symbolic_grader_guard_version",
    "symbolic_grader_timeout_seconds",
    "mathruler_error",
    "native_r1v_shadow_error",
    "native_r1v_shadow_valid",
}
VALID_REASONS = {
    "none",
    "canonical_correct_mathruler_incorrect",
    "mathruler_correct_canonical_incorrect",
    "mathruler_error_canonical_incorrect",
    "mathruler_error_canonical_correct",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_runtime_placement(
    manifest: dict[str, Any],
    training_log: str,
    *,
    run_manifest_path: Path,
) -> dict[str, Any]:
    errors: list[str] = []
    config_value = manifest.get("config_path")
    config_path = Path(str(config_value)) if config_value else Path()
    config: dict[str, Any] = {}
    if not config_value or not config_path.is_file():
        errors.append(f"effective config is absent: {config_value!r}")
    else:
        try:
            loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                config = loaded
            else:
                errors.append("effective config is not a mapping")
        except Exception as error:
            errors.append(f"effective config could not be parsed: {error}")

    trainer = config.get("trainer", {}) if isinstance(config, dict) else {}
    rollout = config.get("worker", {}).get("rollout", {}) if isinstance(config, dict) else {}
    configured_gpus = trainer.get("n_gpus_per_node")
    configured_tp = rollout.get("tensor_parallel_size")
    gpu_ids = manifest.get("gpu_ids")
    expected_replicas = (
        configured_gpus // configured_tp
        if isinstance(configured_gpus, int)
        and isinstance(configured_tp, int)
        and configured_tp > 0
        and configured_gpus % configured_tp == 0
        else None
    )
    runtime_tp_values = sorted(
        {int(value) for value in re.findall(r'"tensor_parallel_size":\s*(\d+)', training_log)}
    )
    checkpoint_path = str(manifest.get("checkpoint_path", ""))
    command = str(manifest.get("command", ""))
    run_dir = run_manifest_path.resolve().parent
    config_resolved = config_path.resolve() if config_value and config_path.exists() else None

    checks = {
        "effective_config_exists_and_parses": bool(config),
        "effective_config_is_immutable_run_snapshot": bool(
            config_resolved
            and config_resolved.parent == run_dir
            and config_resolved.name == "effective_config.yaml"
        ),
        "effective_config_hash_matches_manifest": bool(
            config_resolved
            and manifest.get("base_config_hash") == _sha256(config_resolved)
        ),
        "single_node_four_gpu_config": trainer.get("nnodes") == 1
        and configured_gpus == 4,
        "effective_config_requires_tp1": configured_tp == 1,
        "manifest_gpu_ids_exact": isinstance(gpu_ids, list)
        and len(gpu_ids) == 4
        and len(set(gpu_ids)) == 4
        and all(isinstance(gpu, int) and 0 <= gpu <= 7 for gpu in gpu_ids),
        "manifest_tp_matches_effective_config": manifest.get("tensor_parallel_width")
        == configured_tp
        == 1,
        "manifest_replica_count_derived": manifest.get("replica_count")
        == expected_replicas
        == 4,
        "runtime_log_tp_matches_effective_config": runtime_tp_values == [configured_tp]
        and configured_tp == 1,
        "placement_policy_pinned": manifest.get("placement_policy_version")
        == "pi-2026-07-11",
        "command_uses_effective_config_snapshot": bool(
            config_value and f"config={config_value}" in command
        ),
        "checkpoint_namespace_isolated": bool(
            checkpoint_path
            and "/checkpoints/smoke/" in checkpoint_path
            and f"trainer.save_checkpoint_path={checkpoint_path}" in command
        ),
    }
    if not all(checks.values()):
        errors.extend(name for name, passed in checks.items() if not passed)
    return {
        "schema_version": "blind-gains.pilot-reward-smoke-placement-audit.v1",
        "status": "pass" if all(checks.values()) and not errors else "fail",
        "checks": checks,
        "effective_config_path": str(config_path) if config_value else None,
        "effective_config_sha256": _sha256(config_path)
        if config_value and config_path.is_file()
        else None,
        "configured_tensor_parallel_width": configured_tp,
        "configured_gpu_count": configured_gpus,
        "expected_rollout_replica_count": expected_replicas,
        "runtime_log_tensor_parallel_values": runtime_tp_values,
        "errors": errors,
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
    guard_mismatches = 0
    invalid_native_shadows = 0
    symbolic_timeout_counts: collections.Counter[str] = collections.Counter()
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
        try:
            guard_matches = (
                row.get("symbolic_grader_guard_version") == "posix-itimer-v1"
                and math.isclose(
                    float(row.get("symbolic_grader_timeout_seconds")),
                    5.0,
                    abs_tol=1e-12,
                )
            )
        except (TypeError, ValueError):
            guard_matches = False
        if not guard_matches:
            guard_mismatches += 1
        if row.get("native_r1v_shadow_valid") is not True or row.get(
            "native_r1v_shadow_error"
        ) is not None:
            invalid_native_shadows += 1
        if row.get("mathruler_error") == "SymbolicGraderTimeout":
            symbolic_timeout_counts["mathruler"] += 1
        if row.get("native_r1v_shadow_error") == "SymbolicGraderTimeout":
            symbolic_timeout_counts["native_r1v_shadow"] += 1

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
        "symbolic_grader_guard_exact": guard_mismatches == 0,
        "native_shadows_valid": invalid_native_shadows == 0,
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
    if guard_mismatches:
        errors.append(f"symbolic grader guard mismatches: {guard_mismatches}")
    if invalid_native_shadows:
        errors.append(f"invalid native-r1v shadows: {invalid_native_shadows}")
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
        "symbolic_grader_guard_mismatches": guard_mismatches,
        "invalid_native_shadow_rows": invalid_native_shadows,
        "symbolic_timeout_counts": dict(sorted(symbolic_timeout_counts.items())),
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


def audit_shadow_partitions(
    rows: list[dict[str, Any]],
    *,
    expected_training_rows: int,
    validation_ground_truths: list[str],
) -> dict[str, Any]:
    expected_validation_rows = len(validation_ground_truths)
    training_rows = rows[:expected_training_rows]
    validation_rows = rows[expected_training_rows:]
    observed_validation_ground_truths = [
        str(row.get("ground_truth", "")).strip() for row in validation_rows
    ]
    expected_validation_ground_truths = [
        str(value).strip() for value in validation_ground_truths
    ]
    checks = {
        "total_count_matches_training_plus_validation": len(rows)
        == expected_training_rows + expected_validation_rows,
        "training_partition_count_exact": len(training_rows) == expected_training_rows,
        "validation_partition_count_exact": len(validation_rows)
        == expected_validation_rows,
        "validation_ground_truth_sequence_exact": observed_validation_ground_truths
        == expected_validation_ground_truths,
    }
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "n_training_rows": len(training_rows),
        "expected_training_rows": expected_training_rows,
        "n_validation_rows": len(validation_rows),
        "expected_validation_rows": expected_validation_rows,
        "training_audit": audit_shadow_rows(
            training_rows,
            expected_minimum_rows=expected_training_rows,
            require_exact_row_count=True,
        ),
        "validation_audit": audit_shadow_rows(
            validation_rows,
            expected_minimum_rows=expected_validation_rows,
            require_exact_row_count=True,
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--shadow-jsonl", type=Path, required=True)
    parser.add_argument("--training-log", type=Path)
    parser.add_argument(
        "--validation-manifest",
        type=Path,
        default=Path("data/geometry3k_caption_images_manifest.jsonl"),
    )
    parser.add_argument("--validation-split", default="test")
    parser.add_argument("--validation-answer-key", default="answer")
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
    validation_source_rows = [
        json.loads(line)
        for line in args.validation_manifest.read_text(encoding="utf-8").splitlines()
        if line
    ]
    validation_ground_truths = [
        str(row[args.validation_answer_key])
        for row in validation_source_rows
        if str(row.get("split")) == args.validation_split
    ]
    if not validation_ground_truths:
        raise ValueError("validation manifest produced no registered ground truths")
    expected_training = args.expected_steps * args.rollout_batch_size * args.group_size
    expected_total = expected_training + len(validation_ground_truths)
    payload = audit_shadow_rows(
        rows,
        expected_minimum_rows=expected_total,
        require_exact_row_count=True,
    )
    partitions = audit_shadow_partitions(
        rows,
        expected_training_rows=expected_training,
        validation_ground_truths=validation_ground_truths,
    )
    training_checks = audit_training_contract(
        manifest, training_log, expected_steps=args.expected_steps
    )
    training_checks["final_validation_marker_present"] = "Start validation..." in training_log
    training_checks["final_validation_finish_marker_present"] = "Finish validation." in training_log
    placement_audit = audit_runtime_placement(
        manifest,
        training_log,
        run_manifest_path=args.run_manifest,
    )
    payload["training_contract_checks"] = training_checks
    payload["partition_audit"] = partitions
    payload["placement_audit"] = placement_audit
    payload["status"] = (
        "pass"
        if payload["status"] == "pass"
        and partitions["status"] == "pass"
        and partitions["training_audit"]["status"] == "pass"
        and partitions["validation_audit"]["status"] == "pass"
        and all(training_checks.values())
        and placement_audit["status"] == "pass"
        else "fail"
    )
    payload.update(
        {
            "schema_version": "blind-gains.pilot-reward-smoke-audit.v5",
            "run_manifest": str(args.run_manifest),
            "shadow_jsonl": str(args.shadow_jsonl),
            "training_log": str(training_log_path),
            "expected_steps": args.expected_steps,
            "rollout_batch_size": args.rollout_batch_size,
            "group_size": args.group_size,
            "n_training_shadow_rows": partitions["n_training_rows"],
            "n_validation_shadow_rows": partitions["n_validation_rows"],
            "validation_manifest": str(args.validation_manifest),
            "validation_split": args.validation_split,
            "validation_answer_key": args.validation_answer_key,
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
