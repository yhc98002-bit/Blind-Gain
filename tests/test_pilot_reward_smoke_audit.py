from __future__ import annotations

import math
from pathlib import Path

import yaml

from scripts.audit_pilot_reward_smoke import (
    audit_runtime_placement,
    audit_shadow_partitions,
    audit_shadow_rows,
    audit_training_contract,
)


def _row(training: float, accuracy: float, contract: bool, reason: str = "none") -> dict:
    return {
        "training_reward": training,
        "native_r1v_shadow_reward": 0.5,
        "canonical_eval_reward": accuracy,
        "reward_disagreement_reason": reason,
        "mathruler_accuracy_reward": accuracy,
        "contract_valid": contract,
        "parser_version": "canonical-v2",
        "pilot_reward_version": "pilot-reward-v1",
        "symbolic_grader_guard_version": "posix-itimer-v1",
        "symbolic_grader_timeout_seconds": 5.0,
        "mathruler_error": None,
        "native_r1v_shadow_error": None,
        "native_r1v_shadow_valid": True,
    }


def test_shadow_audit_accepts_complete_nondegenerate_rows() -> None:
    payload = audit_shadow_rows(
        [_row(1.0, 1.0, True), _row(0.5, 0.0, True)], expected_minimum_rows=2
    )
    assert payload["status"] == "pass"
    assert all(payload["checks"].values())


def test_shadow_audit_rejects_missing_field_nan_and_bad_identity() -> None:
    missing = _row(1.0, 1.0, True)
    missing.pop("native_r1v_shadow_reward")
    malformed = _row(0.25, 0.0, True)
    malformed["canonical_eval_reward"] = math.nan

    payload = audit_shadow_rows([missing, malformed], expected_minimum_rows=2)

    assert payload["status"] == "fail"
    assert payload["checks"]["all_required_fields_present"] is False
    assert payload["checks"]["all_numeric_shadows_finite"] is False
    assert payload["checks"]["training_reward_identity_exact"] is False


def test_shadow_audit_rejects_extra_rows_and_version_drift_under_exact_contract() -> None:
    rows = [_row(1.0, 1.0, True), _row(0.5, 0.0, True), _row(1.0, 1.0, True)]
    rows[0]["parser_version"] = None

    payload = audit_shadow_rows(
        rows,
        expected_minimum_rows=2,
        require_exact_row_count=True,
    )

    assert payload["status"] == "fail"
    assert payload["checks"]["row_count_matches_contract"] is False
    assert payload["checks"]["parser_and_reward_versions_exact"] is False


def test_shadow_audit_rejects_missing_guard_and_invalid_native_shadow() -> None:
    missing_guard = _row(1.0, 1.0, True)
    missing_guard.pop("symbolic_grader_guard_version")
    invalid_native = _row(0.5, 0.0, True)
    invalid_native["native_r1v_shadow_valid"] = False
    invalid_native["native_r1v_shadow_error"] = "SymbolicGraderTimeout"

    payload = audit_shadow_rows(
        [missing_guard, invalid_native],
        expected_minimum_rows=2,
    )

    assert payload["status"] == "fail"
    assert payload["checks"]["all_required_fields_present"] is False
    assert payload["checks"]["symbolic_grader_guard_exact"] is False
    assert payload["checks"]["native_shadows_valid"] is False
    assert payload["symbolic_timeout_counts"] == {"native_r1v_shadow": 1}


def test_training_contract_requires_five_step_marker_and_clean_log() -> None:
    manifest = {
        "job_type": "l3_pilot_reward_plumbing_smoke",
        "status": "complete",
        "exit_code": 0,
        "command": "trainer.max_steps=5",
    }
    checks = audit_training_contract(
        manifest,
        "Running step 0: 100%| 5.00/5.00",
        expected_steps=5,
    )
    assert all(checks.values())

    failed = audit_training_contract(
        manifest,
        "Running step 0: 20%| 1.00/5.00\nTraceback (most recent call last)",
        expected_steps=5,
    )
    assert failed["training_progress_reaches_expected_steps"] is False
    assert failed["training_log_has_no_traceback"] is False


def test_partition_audit_requires_exact_validation_suffix_identity() -> None:
    rows = [
        {**_row(1.0, 1.0, True), "ground_truth": "train-a"},
        {**_row(0.5, 0.0, True), "ground_truth": "train-b"},
        {**_row(1.0, 1.0, True), "ground_truth": "test-a"},
        {**_row(0.5, 0.0, True), "ground_truth": "test-b"},
    ]
    accepted = audit_shadow_partitions(
        rows,
        expected_training_rows=2,
        validation_ground_truths=["test-a", "test-b"],
    )
    rejected = audit_shadow_partitions(
        rows,
        expected_training_rows=2,
        validation_ground_truths=["test-b", "test-a"],
    )

    assert accepted["status"] == "pass"
    assert accepted["training_audit"]["status"] == "pass"
    assert accepted["validation_audit"]["status"] == "pass"
    assert rejected["status"] == "fail"
    assert rejected["checks"]["validation_ground_truth_sequence_exact"] is False


def _placement_fixture(tmp_path: Path, *, tensor_parallel_width: int) -> tuple[dict, Path, str]:
    run_dir = tmp_path / "experiments" / "runs" / "smoke"
    run_dir.mkdir(parents=True)
    config_path = run_dir / "effective_config.yaml"
    config = {
        "worker": {"rollout": {"tensor_parallel_size": tensor_parallel_width}},
        "trainer": {"nnodes": 1, "n_gpus_per_node": 4},
    }
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    import hashlib

    config_hash = hashlib.sha256(config_path.read_bytes()).hexdigest()
    patch_path = run_dir / "easyr1_worktree.patch"
    patch_path.write_text("patched EasyR1 worktree\n", encoding="utf-8")
    logger_path = run_dir / "easyr1_logger.py"
    logger_path.write_text(
        "existing and not resume_requested\n"
        "Preserving existing EasyR1 file logger artifact during resume\n",
        encoding="utf-8",
    )
    checkpoint_path = str(tmp_path / "checkpoints" / "smoke" / "smoke")
    manifest = {
        "config_path": str(config_path),
        "base_config_hash": config_hash,
        "gpu_ids": [1, 5, 6, 7],
        "tensor_parallel_width": tensor_parallel_width,
        "replica_count": 4 // tensor_parallel_width,
        "placement_policy_version": "pi-2026-07-11",
        "easyr1_revision": "dd71bbd252694f5f850213eec15795b6b88d9fea",
        "easyr1_worktree_patch": str(patch_path),
        "easyr1_worktree_patch_sha256": hashlib.sha256(
            patch_path.read_bytes()
        ).hexdigest(),
        "easyr1_logger_snapshot": str(logger_path),
        "easyr1_logger_sha256": hashlib.sha256(logger_path.read_bytes()).hexdigest(),
        "checkpoint_path": checkpoint_path,
        "command": (
            f"python -m verl.trainer.main config={config_path} "
            f"trainer.save_checkpoint_path={checkpoint_path}"
        ),
    }
    manifest_path = run_dir / "run_manifest.json"
    return manifest, manifest_path, f'config: {{"tensor_parallel_size": {tensor_parallel_width}}}'


def test_runtime_placement_audit_accepts_derived_tp1_snapshot(tmp_path: Path) -> None:
    manifest, manifest_path, training_log = _placement_fixture(
        tmp_path, tensor_parallel_width=1
    )

    result = audit_runtime_placement(
        manifest,
        training_log,
        run_manifest_path=manifest_path,
    )

    assert result["status"] == "pass"
    assert result["expected_rollout_replica_count"] == 4
    assert all(result["checks"].values())


def test_runtime_placement_audit_rejects_historical_tp2_manifest_pattern(
    tmp_path: Path,
) -> None:
    manifest, manifest_path, training_log = _placement_fixture(
        tmp_path, tensor_parallel_width=2
    )
    manifest["tensor_parallel_width"] = 1
    manifest["replica_count"] = 1

    result = audit_runtime_placement(
        manifest,
        training_log,
        run_manifest_path=manifest_path,
    )

    assert result["status"] == "fail"
    assert result["checks"]["effective_config_requires_tp1"] is False
    assert result["checks"]["manifest_tp_matches_effective_config"] is False
    assert result["checks"]["manifest_replica_count_derived"] is False
    assert result["checks"]["runtime_log_tp_matches_effective_config"] is False


def test_runtime_placement_audit_rejects_mutated_easyr1_snapshot(tmp_path: Path) -> None:
    manifest, manifest_path, training_log = _placement_fixture(
        tmp_path, tensor_parallel_width=1
    )
    Path(manifest["easyr1_logger_snapshot"]).write_text(
        "mutated after manifest creation\n", encoding="utf-8"
    )

    result = audit_runtime_placement(
        manifest,
        training_log,
        run_manifest_path=manifest_path,
    )

    assert result["status"] == "fail"
    assert result["checks"]["easyr1_logger_hash_matches_manifest"] is False
    assert result["checks"]["easyr1_resume_safe_logger_present"] is False
