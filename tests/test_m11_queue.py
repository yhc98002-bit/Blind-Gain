from __future__ import annotations

import json
from pathlib import Path

from scripts.run_m11_generalization_queue import (
    expand_cells,
    initial_state,
    update_free_gpu_streaks,
)


def _config() -> dict:
    root = Path(__file__).resolve().parents[1]
    return json.loads(
        (root / "configs/eval/m11_generalization_v1.json").read_text(encoding="utf-8")
    )


def test_m11_queue_expands_exact_smoke_and_full_matrices() -> None:
    config = _config()

    smoke = expand_cells(config, "smoke")
    full = expand_cells(config, "full")

    assert len(smoke) == 6
    assert len(full) == 18
    assert sum(cell["kind"] == "fliptrack" for cell in full) == 12
    assert sum(cell["kind"] == "blind" for cell in full) == 6
    assert len({cell["id"] for cell in smoke + full}) == 24


def test_full_cells_cannot_start_as_running() -> None:
    state = initial_state(_config())

    assert state["status"] == "waiting_capacity"
    assert all(cell["status"] == "pending" for cell in state["cells"].values())
    assert all(cell["run_dir"] is None for cell in state["cells"].values())


def test_free_gpu_requires_two_consecutive_capacity_polls() -> None:
    config = _config()
    state = initial_state(config)

    assert update_free_gpu_streaks(config, state, [2]) == []
    assert update_free_gpu_streaks(config, state, [2]) == [2]
    assert update_free_gpu_streaks(config, state, []) == []
    assert state["gpu_free_streaks"]["2"] == 0


def test_m11_is_capacity_gated_not_training_completion_gated() -> None:
    config = _config()

    assert "prerequisite_run_manifests" not in config
    assert len(config["neighbor_run_manifests"]) == 4
    assert config["gpu_free_stability_polls"] == 2


def test_queue_launcher_is_login_only_and_fail_closed() -> None:
    root = Path(__file__).resolve().parents[1]
    launcher = (root / "scripts/launch_m11_generalization_queue.sh").read_text(
        encoding="utf-8"
    )

    assert 'node: "login"' in launcher
    assert 'gpu_allocation: []' in launcher
    assert 'refusing M11 queue because final outputs already exist' in launcher
    assert 'active M11 queue already exists' in launcher
    assert 'nohup setsid' in launcher
