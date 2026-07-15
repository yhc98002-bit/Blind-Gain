from __future__ import annotations

import json
from pathlib import Path

from scripts.run_m11_generalization_queue import (
    expand_cells,
    initial_state,
    pilot_release_status,
    record_capacity_poll,
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


def test_capacity_poll_heartbeat_persists_without_event_growth() -> None:
    state = initial_state(_config())
    event_count = len(state["events"])

    record_capacity_poll(state, [1, 3], [1])
    first_time = state["last_capacity_poll_utc"]
    record_capacity_poll(state, [], [])

    assert state["capacity_poll_count"] == 2
    assert first_time is not None
    assert state["last_capacity_poll_utc"] is not None
    assert state["last_observed_free_gpus"] == []
    assert state["last_stable_free_gpus"] == []
    assert len(state["events"]) == event_count


def test_m11_requires_blind_arm_completion_and_stable_capacity() -> None:
    config = _config()

    assert config["pilot_release_gate"]["mode"] == "all_complete"
    assert {item["arm"] for item in config["pilot_release_gate"]["required_arms"]} == {
        "a2b_noimage",
        "a3_caption",
    }
    assert config["gpu_free_stability_polls"] == 2
    assert {model["python"] for model in config["models"].values()} == {
        ".venv-m11/bin/python"
    }


def test_failed_pilot_vacancy_does_not_open_m11_release_gate(tmp_path: Path) -> None:
    config = _config()
    config["pilot_release_gate"] = {
        "mode": "all_complete",
        "required_arms": [
            {
                "arm": "a2b_noimage",
                "node": "an29",
                "manifest_glob": "runs/a2b/*.json",
            },
            {
                "arm": "a3_caption",
                "node": "an29",
                "manifest_glob": "runs/a3/*.json",
            },
        ],
    }
    for directory, arm, status, exit_code in (
        ("a2b", "a2b_noimage", "fail", 1),
        ("a3", "a3_caption", "complete", 0),
    ):
        path = tmp_path / "runs" / directory / "run_manifest.json"
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps(
                {
                    "job_type": "l13_mechanical_pilot_arm",
                    "arm": arm,
                    "node": "an29",
                    "status": status,
                    "exit_code": exit_code,
                }
            ),
            encoding="utf-8",
        )

    ready, evidence = pilot_release_status(config, tmp_path)

    assert ready is False
    assert evidence["a2b_noimage"]["complete"] is False
    assert evidence["a3_caption"]["complete"] is True


def test_all_completed_blind_arms_open_m11_release_gate(tmp_path: Path) -> None:
    config = _config()
    config["pilot_release_gate"] = {
        "mode": "all_complete",
        "required_arms": [
            {
                "arm": arm,
                "node": "an29",
                "manifest_glob": f"runs/{arm}/*.json",
            }
            for arm in ("a2b_noimage", "a3_caption")
        ],
    }
    for arm in ("a2b_noimage", "a3_caption"):
        path = tmp_path / "runs" / arm / "run_manifest.json"
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps(
                {
                    "job_type": "l13_mechanical_pilot_arm",
                    "arm": arm,
                    "node": "an29",
                    "status": "complete",
                    "exit_code": 0,
                }
            ),
            encoding="utf-8",
        )

    ready, evidence = pilot_release_status(config, tmp_path)

    assert ready is True
    assert all(item["complete"] for item in evidence.values())


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
    assert 'M11 isolated runtime audit is absent or non-pass' in launcher
    assert 'runtime_audit_sha256: $runtime_audit_hash' in launcher
    assert 'runtime_freeze_sha256: $runtime_freeze_hash' in launcher
    assert 'critical M11 queue code or config differs from HEAD' in launcher
    assert 'both registered an29 blind arms complete' in launcher
    assert 'm11_runtime_audit_v2.json' in launcher
    assert 'm11_runtime_freeze_v2.txt' in launcher
