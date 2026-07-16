from __future__ import annotations

from copy import deepcopy

import torch

from scripts.audit_mini_a5_advantages import (
    ALLOWED_ARM_DIFFS,
    build_advantage_checks,
    config_differences,
    independent_grpo,
)


def test_advantage_fixtures_all_pass_and_detect_old_shared_uid_control() -> None:
    checks, evidence = build_advantage_checks()
    assert all(checks.values())
    assert evidence["max_abs_cp_vs_independent_reference"] == 0.0
    assert evidence["max_abs_cp_vs_member_when_rewards_equal"] == 0.0
    assert evidence["max_abs_standard_member_vs_old_shared_2g_bug"] > 1e-3


def test_config_diff_rejects_nonregistered_optimizer_drift() -> None:
    cp = {
        "algorithm": {"pair_group_mode": "joint"},
        "worker": {
            "reward": {"reward_function": "cp"},
            "actor": {"optim": {"lr": 1e-6}},
        },
        "trainer": {"experiment_name": "cp", "save_checkpoint_path": "cp"},
    }
    member = deepcopy(cp)
    member["algorithm"]["pair_group_mode"] = "member"
    member["worker"]["reward"]["reward_function"] = "member"
    member["trainer"]["experiment_name"] = "member"
    member["trainer"]["save_checkpoint_path"] = "member"
    assert set(config_differences(cp, member)) == ALLOWED_ARM_DIFFS

    member["worker"]["actor"]["optim"]["lr"] = 2e-6
    assert "worker.actor.optim.lr" in config_differences(cp, member)


def test_independent_grpo_rejects_singleton_group() -> None:
    try:
        independent_grpo(torch.tensor([1.0]), ["only"])
    except ValueError as error:
        assert "fewer than two" in str(error)
    else:
        raise AssertionError("singleton GRPO group was accepted")
