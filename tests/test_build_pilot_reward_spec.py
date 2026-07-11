from __future__ import annotations

import pytest

from scripts.build_pilot_reward_spec import PRECEDENCE_RULE, build_report


def _audit(status: str = "pass") -> dict:
    return {
        "status": status,
        "n_rows": 12800,
        "expected_steps": 5,
        "checks": {"shadow": True},
        "training_contract_checks": {"training": True},
        "training_reward_counts": {"0.0": 10, "0.5": 20, "1.0": 30},
        "reward_disagreement_reason_counts": {"none": 60},
    }


def _manifest() -> dict:
    return {
        "run_id": "smoke",
        "node": "an29",
        "gpu_allocation": "1,5,6,7",
        "git_hash": "git",
        "config_hash": "config",
        "data_manifest_hash": "data",
        "status": "complete",
        "exit_code": 0,
    }


def test_pilot_reward_report_contains_exact_precedence_and_evidence(tmp_path) -> None:
    report = build_report(_audit(), _manifest(), tmp_path / "audit.json")
    assert PRECEDENCE_RULE in report
    assert "12,800-row" not in report
    assert "`12800`" in report
    assert "Machine status JSON" in report


def test_pilot_reward_report_rejects_nonpass_audit(tmp_path) -> None:
    with pytest.raises(ValueError, match="non-pass"):
        build_report(_audit("fail"), _manifest(), tmp_path / "audit.json")
