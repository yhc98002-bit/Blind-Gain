"""Adversarial fixtures (I10) for the Gate-1 matched-difference audit.

A naive matched-difference check (for example one that only counts the number
of changed fields, only inspects a fixed whitelist of paths, or compares the
raw text line count) passes at least one of the planted configs below. The
registered audit (scripts/check_mini_a5_matched_diff.py, acceptance condition
8 of docs/registered_mini_a5_gate1_completion_v1.md) must reject every one of
them and accept the positive control.
"""
from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from scripts.check_mini_a5_matched_diff import ALLOWED_CHANGED_KEYS, check

TEMPLATE = {
    "data": {
        "train_files": "data/mini_a5_train_v1/train.parquet",
        "val_files": "data/mini_a5_plumbing_val_v1.jsonl",
        "rollout_batch_size": 400,
        "seed": 20260716,
    },
    "algorithm": {"pair_group_mode": "member", "kl_coef": 0.01},
    "worker": {
        "actor": {"optim": {"lr": 1.0e-6}},
        "reward": {
            "reward_function": "src/rewards/cp_grpo_reward.py:compute_member_score"
        },
    },
    "trainer": {
        "max_steps": 120,
        "experiment_name": "mini_a5_same_data_seed1",
        "save_checkpoint_path": "/ckpt/mini_a5/mini_a5_same_data_seed1",
    },
}


def _registered_candidate() -> dict:
    candidate = copy.deepcopy(TEMPLATE)
    candidate["data"]["train_files"] = "data/mini_a5_std_train_v1/train.parquet"
    candidate["trainer"]["experiment_name"] = "mini_a5_std_seed1"
    candidate["trainer"]["save_checkpoint_path"] = "/ckpt/mini_a5/mini_a5_std_seed1"
    return candidate


def _write(tmp_path: Path, name: str, payload: dict) -> Path:
    path = tmp_path / name
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def _check(tmp_path: Path, candidate: dict) -> list[str]:
    return check(
        _write(tmp_path, "candidate.yaml", candidate),
        _write(tmp_path, "template.yaml", TEMPLATE),
    )


def test_registered_three_field_change_passes(tmp_path: Path) -> None:
    assert _check(tmp_path, _registered_candidate()) == []


def test_extra_hyperparameter_drift_fails(tmp_path: Path) -> None:
    """Naive '3 fields changed? fine' passes this: it changes lr too but hides
    it by reverting experiment_name, keeping the changed-field count at 3."""
    candidate = _registered_candidate()
    candidate["worker"]["actor"]["optim"]["lr"] = 2.0e-6
    candidate["trainer"]["experiment_name"] = TEMPLATE["trainer"]["experiment_name"]
    violations = _check(tmp_path, candidate)
    assert any("disallowed change: worker.actor.optim.lr" in v for v in violations)
    assert any("required change absent" in v for v in violations)


def test_seed_drift_alongside_allowed_changes_fails(tmp_path: Path) -> None:
    candidate = _registered_candidate()
    candidate["data"]["seed"] = 1
    violations = _check(tmp_path, candidate)
    assert violations == ["disallowed change: data.seed"]


def test_grouping_mode_drift_fails(tmp_path: Path) -> None:
    candidate = _registered_candidate()
    candidate["algorithm"]["pair_group_mode"] = "none"
    assert _check(tmp_path, candidate) == [
        "disallowed change: algorithm.pair_group_mode"
    ]


def test_added_key_fails(tmp_path: Path) -> None:
    """A whitelist-only checker never notices a brand-new key."""
    candidate = _registered_candidate()
    candidate["algorithm"]["delta_q_weighting"] = True
    assert _check(tmp_path, candidate) == [
        "disallowed change: algorithm.delta_q_weighting"
    ]


def test_removed_key_fails(tmp_path: Path) -> None:
    candidate = _registered_candidate()
    del candidate["algorithm"]["kl_coef"]
    assert _check(tmp_path, candidate) == ["disallowed change: algorithm.kl_coef"]


def test_unchanged_template_fails(tmp_path: Path) -> None:
    """The template itself is NOT a valid per-mode config: the three allowed
    changes are mandatory, not optional."""
    violations = _check(tmp_path, copy.deepcopy(TEMPLATE))
    assert len(violations) == len(ALLOWED_CHANGED_KEYS)
    assert all("required change absent" in v for v in violations)


def test_reward_function_drift_fails(tmp_path: Path) -> None:
    candidate = _registered_candidate()
    candidate["worker"]["reward"]["reward_function"] = (
        "src/rewards/cp_grpo_reward.py:compute_score"
    )
    assert _check(tmp_path, candidate) == [
        "disallowed change: worker.reward.reward_function"
    ]


@pytest.mark.parametrize("mode", ["std", "necessity"])
def test_real_repo_configs_pass_when_present(mode: str) -> None:
    """Positive control against the actual registered configs (skipped when
    the repo layout is absent, e.g. in an isolated checkout)."""
    root = Path(__file__).resolve().parents[1]
    candidate = root / f"configs/train/mini_a5_{mode}_3b_v1.yaml"
    template = root / "configs/train/mini_a5_same_data_3b_v1.yaml"
    if not (candidate.is_file() and template.is_file()):
        pytest.skip("registered configs not present in this checkout")
    assert check(candidate, template) == []
