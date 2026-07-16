from __future__ import annotations

import json
from pathlib import Path

import yaml

from scripts.audit_mini_a5_advantages import ALLOWED_ARM_DIFFS, config_differences


ROOT = Path(__file__).resolve().parents[1]
CP_CONFIG = ROOT / "configs/train/mini_a5_cp_plumbing_smoke_v1.yaml"
MEMBER_CONFIG = ROOT / "configs/train/mini_a5_member_plumbing_smoke_v1.yaml"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_smoke_configs_are_one_step_eight_gpu_tp1_and_matched() -> None:
    cp = _load(CP_CONFIG)
    member = _load(MEMBER_CONFIG)
    assert set(config_differences(cp, member)) == ALLOWED_ARM_DIFFS
    for config in (cp, member):
        assert config["trainer"]["max_steps"] == 1
        assert config["trainer"]["nnodes"] == 1
        assert config["trainer"]["n_gpus_per_node"] == 8
        assert config["worker"]["rollout"]["tensor_parallel_size"] == 1
        assert config["worker"]["rollout"]["n"] == 5
        assert config["data"]["rollout_batch_size"] == 16
        assert config["data"]["max_response_length"] == 2048
        assert config["data"]["shuffle"] is False
        assert config["trainer"]["save_model_only"] is True
        assert config["worker"]["actor"]["model"]["freeze_vision_tower"] is True


def test_smoke_batch_is_exactly_eight_adjacent_pairs() -> None:
    rows = [
        json.loads(line)
        for line in (ROOT / "data/mini_a5_plumbing_val_v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ][:16]
    assert len(rows) == 16
    assert len({row["pair_group_uid"] for row in rows}) == 8
    assert all(
        rows[index]["pair_group_uid"] == rows[index + 1]["pair_group_uid"]
        and rows[index]["pair_member"] == "a"
        and rows[index + 1]["pair_member"] == "b"
        for index in range(0, 16, 2)
    )


def test_adversarial_smoke_optimizer_drift_is_detected() -> None:
    cp = _load(CP_CONFIG)
    member = _load(MEMBER_CONFIG)
    member["worker"]["actor"]["optim"]["lr"] = 2.0e-6
    assert "worker.actor.optim.lr" in config_differences(cp, member)
