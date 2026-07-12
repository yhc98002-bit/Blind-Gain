from __future__ import annotations

import pytest

from scripts.build_pilot_reward_spec import PRECEDENCE_RULE, build_report


def _audit(status: str = "pass") -> dict:
    partition = {
        "status": "pass",
        "training_reward_counts": {"0.0": 10, "0.5": 20, "1.0": 30},
        "reward_disagreement_reason_counts": {"none": 60},
    }
    return {
        "schema_version": "blind-gains.pilot-reward-smoke-audit.v6",
        "status": status,
        "n_rows": 13401,
        "n_training_shadow_rows": 12800,
        "n_validation_shadow_rows": 601,
        "expected_steps": 5,
        "checks": {"shadow": True},
        "training_contract_checks": {"training": True},
        "partition_audit": {
            "status": "pass",
            "checks": {"partition": True},
            "training_audit": partition,
            "validation_audit": partition,
        },
        "placement_audit": {
            "status": "pass",
            "checks": {"tp1": True},
            "runtime_log_tensor_parallel_values": [1],
        },
    }


def _manifest() -> dict:
    return {
        "run_id": "smoke",
        "node": "an29",
        "gpu_allocation": "1,5,6,7",
        "git_hash": "git",
        "config_hash": "config",
        "data_manifest_hash": "data",
        "tensor_parallel_width": 1,
        "replica_count": 4,
        "easyr1_revision": "revision",
        "easyr1_worktree_patch_sha256": "patch",
        "easyr1_logger_sha256": "logger",
        "status": "complete",
        "exit_code": 0,
    }


def test_pilot_reward_report_contains_exact_precedence_and_evidence(tmp_path) -> None:
    report = build_report(_audit(), _manifest(), tmp_path / "audit.json")
    assert PRECEDENCE_RULE in report
    assert "12,800-row" not in report
    assert "`12800`" in report
    assert "`601`" in report
    assert "Machine status JSON" in report
    assert "TP`1` with `4` rollout replicas" in report
    assert "worktree patch SHA256" in report


def test_pilot_reward_report_rejects_nonpass_audit(tmp_path) -> None:
    with pytest.raises(ValueError, match="non-pass"):
        build_report(_audit("fail"), _manifest(), tmp_path / "audit.json")


def test_pilot_reward_report_rejects_false_placement_subcheck(tmp_path) -> None:
    audit = _audit()
    audit["placement_audit"]["checks"]["tp1"] = False

    with pytest.raises(ValueError, match="false sub-check"):
        build_report(audit, _manifest(), tmp_path / "audit.json")
