from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from src.train.m5_resume_integrity import (
    continuity_checks,
    raw_hash_continuity,
    validate_config_derivation,
)


def test_config_audit_rejects_hidden_reward_change(tmp_path: Path) -> None:
    base = {
        "data": {"seed": 1},
        "worker": {
            "actor": {"model": {"freeze_vision_tower": False}},
            "rollout": {"tensor_parallel_size": 2},
            "reward": {
                "reward_function": "/x/examples/reward_function/r1v.py:compute_score"
            },
        },
        "trainer": {
            "max_steps": 100,
            "experiment_name": "anchor_a0_recipe_3b_geo3k",
            "save_freq": 20,
            "save_checkpoint_path": "/old",
            "load_checkpoint_path": None,
        },
    }
    derived = copy.deepcopy(base)
    for key, value in {
        "max_steps": 101,
        "experiment_name": "m5_anchor_resume_integrity_step101",
        "save_freq": 101,
        "save_checkpoint_path": (
            "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
            "checkpoints/m5_anchor_resume_integrity_step101"
        ),
        "load_checkpoint_path": (
            "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
            "checkpoints/anchor_a0_recipe_3b_geo3k/"
            "anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_100"
        ),
    }.items():
        derived["trainer"][key] = value
    derived["worker"]["reward"]["reward_function"] = "/tmp/shaped.py:score"
    base_path = tmp_path / "base.yaml"
    derived_path = tmp_path / "derived.yaml"
    base_path.write_text(yaml.safe_dump(base), encoding="utf-8")
    derived_path.write_text(yaml.safe_dump(derived), encoding="utf-8")

    result = validate_config_derivation(base_path, derived_path, mode="integrity")

    assert result["status"] == "fail"
    assert result["checks"]["exact_allowed_diff_keys"] is False
    assert result["checks"]["native_reward_unchanged"] is False


def _metric(step: int, *, pg_loss: float = 0.02) -> dict:
    return {
        "step": step,
        "reward": {"overall": 0.7},
        "actor": {
            "pg_loss": pg_loss,
            "kl_loss": 0.05,
            "grad_norm": 0.3,
            "lr": 1e-6,
            "kl_coef": 0.01,
        },
        "perf": {"total_num_tokens": 1_900_000, "time_per_step": 1500.0},
    }


def test_continuity_rejects_exploded_policy_loss() -> None:
    source = {step: _metric(step) for step in range(91, 101)}
    integrity = {101: _metric(101, pg_loss=4.0)}

    result = continuity_checks(source, integrity)

    assert result["status"] == "fail"
    assert result["checks"]["policy_loss_bounded"] is False


def test_continuity_accepts_exact_one_step_with_finite_metrics() -> None:
    source = {step: _metric(step) for step in range(91, 101)}
    integrity = {101: _metric(101)}

    result = continuity_checks(source, integrity)

    assert result["status"] == "pass"
    assert all(result["checks"].values())


def test_raw_hash_continuity_rejects_one_changed_shard() -> None:
    relocation = {
        "status": "raw_training_state_relocated_due_to_shared_quota",
        "files": [
            {"file": f"model_world_size_4_rank_{rank}.pt", "sha256": f"m{rank}"}
            for rank in range(4)
        ]
        + [
            {"file": f"optim_world_size_4_rank_{rank}.pt", "sha256": f"o{rank}"}
            for rank in range(4)
        ],
    }
    restored = {
        "status": "pass",
        "files_stable_during_hash": True,
        "files": [
            {"path": row["file"], "sha256": row["sha256"]}
            for row in relocation["files"]
        ],
    }
    restored["files"][3]["sha256"] = "changed"

    result = raw_hash_continuity(relocation, restored)

    assert result["status"] == "fail"
    assert result["checks"]["raw_shard_names_and_hashes_exact"] is False
