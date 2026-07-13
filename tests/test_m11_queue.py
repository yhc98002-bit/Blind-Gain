from __future__ import annotations

import json
from pathlib import Path

from scripts.run_m11_generalization_queue import expand_cells, initial_state


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

    assert state["status"] == "waiting_prerequisites"
    assert all(cell["status"] == "pending" for cell in state["cells"].values())
    assert all(cell["run_dir"] is None for cell in state["cells"].values())


def test_queue_launcher_is_login_only_and_fail_closed() -> None:
    root = Path(__file__).resolve().parents[1]
    launcher = (root / "scripts/launch_m11_generalization_queue.sh").read_text(
        encoding="utf-8"
    )

    assert 'node: "login"' in launcher
    assert 'gpu_allocation: []' in launcher
    assert 'refusing M11 queue because final outputs already exist' in launcher
    assert 'nohup setsid' in launcher
