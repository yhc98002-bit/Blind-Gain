from __future__ import annotations

import copy
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIGS = {
    "real": ROOT / "configs/train/mech_a1_real_3b_geo3k.yaml",
    "gray": ROOT / "configs/train/mech_a2_gray_3b_geo3k.yaml",
    "none": ROOT / "configs/train/mech_a2b_noimage_3b_geo3k.yaml",
    "caption": ROOT / "configs/train/mech_a3_caption_3b_geo3k.yaml",
}


def _normalized(config: dict) -> dict:
    normalized = copy.deepcopy(config)
    normalized["data"].pop("image_condition")
    normalized["trainer"].pop("experiment_name")
    normalized["trainer"].pop("save_checkpoint_path")
    return normalized


def test_mechanical_pilot_configs_are_matched_except_arm_identity() -> None:
    loaded = {condition: yaml.safe_load(path.read_text(encoding="utf-8")) for condition, path in CONFIGS.items()}
    reference = _normalized(loaded["real"])
    assert _normalized(loaded["gray"]) == reference
    assert _normalized(loaded["none"]) == reference
    assert _normalized(loaded["caption"]) == reference

    for condition, config in loaded.items():
        assert config["data"]["image_condition"] == condition
        assert config["data"]["image_condition_seed"] == 20260710
        assert config["worker"]["actor"]["model"]["freeze_vision_tower"] is True
        assert config["worker"]["rollout"]["tensor_parallel_size"] == 1
        assert config["trainer"]["n_gpus_per_node"] == 4
        assert config["worker"]["rollout"]["n"] == 5
        assert config["worker"]["reward"]["reward_function_kwargs"][
            "symbolic_grader_timeout_seconds"
        ] == 5.0
        assert config["trainer"]["max_steps"] == 100
        assert "/checkpoints/pilot/" in config["trainer"]["save_checkpoint_path"]
        assert len(config["data"]["caption_store_paths"]) == 3
        assert config["trainer"]["val_before_train"] is True
        assert config["trainer"]["val_freq"] == 10
        assert config["worker"]["rollout"]["val_override_config"] == {
            "temperature": 0.0,
            "top_p": 1.0,
            "n": 1,
        }
        assert config["data"]["val_files"] == "hiyouga/geometry3k@test"
