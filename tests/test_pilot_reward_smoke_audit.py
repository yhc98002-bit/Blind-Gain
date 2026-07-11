from __future__ import annotations

import math

from scripts.audit_pilot_reward_smoke import audit_shadow_rows


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
