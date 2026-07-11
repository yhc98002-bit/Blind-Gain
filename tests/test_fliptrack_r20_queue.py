from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.run_fliptrack_r20_queue import build_launch_command, validate_config


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/eval/fliptrack_r20_queue_v1.json"


def _config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_r20_queue_registers_exact_full_cell_matrix() -> None:
    validate_config(_config(), ROOT)


def test_r20_queue_rejects_one_omitted_hardness_cell() -> None:
    config = copy.deepcopy(_config())
    config["cells"] = [cell for cell in config["cells"] if cell["id"] != "qwen25vl7b_noise"]
    with pytest.raises(ValueError, match="matrix mismatch"):
        validate_config(config, ROOT)


def test_r20_queue_builds_complete_image_and_caption_commands() -> None:
    config = _config()
    image_cell = next(cell for cell in config["cells"] if cell["id"] == "qwen25vl3b_medium")
    caption_cell = next(cell for cell in config["cells"] if cell["id"] == "qwen25vl7b_caption")
    image = build_launch_command(config, image_cell, "experiments/runs/image")
    caption = build_launch_command(config, caption_cell, "experiments/runs/caption")
    assert image[-3:] == ["32", "4 5 6 7", "medium"]
    assert caption[-2:] == ["4 5 6 7", "32"]
    assert config["caption_inputs"]["7b"] in caption


def test_r20_queue_uses_nonblocking_aggregation() -> None:
    queue_source = (ROOT / "scripts/run_fliptrack_r20_queue.py").read_text(encoding="utf-8")
    aggregate_source = (ROOT / "scripts/launch_fliptrack_aggregate.sh").read_text(encoding="utf-8")
    assert 'str(cell["id"]), "async"' in queue_source
    assert "_wait_for_aggregates" in queue_source
    assert 'LAUNCH_MODE="${3:-sync}"' in aggregate_source
    assert "nohup setsid --wait" in aggregate_source
