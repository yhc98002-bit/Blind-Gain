from __future__ import annotations

import math

from scripts.audit_pilot_reward_smoke import audit_shadow_rows, audit_training_contract


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
