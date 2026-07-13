from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.watch_m2_pilot_completion import (
    EXPECTED_ARMS,
    _update_state,
    observe,
    validate_config,
    write_terminal_notification,
)


NODES = {
    "a1_real": "an12",
    "a2_gray": "an12",
    "a2b_noimage": "an29",
    "a3_caption": "an29",
}


def _write_parent(
    root: Path,
    arm: str,
    *,
    status: str,
    exit_code: int | None,
    artifacts_exist: bool | None,
    end_time_utc: str | None,
) -> dict[str, str]:
    run_id = f"mech_{arm}_fixture"
    manifest = root / "experiments" / "runs" / run_id / "run_manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps(
            {
                "job_type": "l13_mechanical_pilot_arm",
                "run_id": run_id,
                "arm": arm,
                "node": NODES[arm],
                "gpu_ids": [0, 1, 2, 3],
                "status": status,
                "exit_code": exit_code,
                "artifacts_exist": artifacts_exist,
                "start_time_utc": "2026-07-13T00:00:00Z",
                "end_time_utc": end_time_utc,
                "checkpoint_path": f"checkpoints/pilot/{run_id}",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "arm": arm,
        "node": NODES[arm],
        "run_id": run_id,
        "manifest": str(manifest.relative_to(root)),
    }


def _config(root: Path, overrides: dict[str, dict] | None = None) -> dict:
    overrides = overrides or {}
    arms = []
    for arm in EXPECTED_ARMS:
        values = {
            "status": "complete",
            "exit_code": 0,
            "artifacts_exist": True,
            "end_time_utc": "2026-07-13T01:00:00Z",
        }
        values.update(overrides.get(arm, {}))
        arms.append(_write_parent(root, arm, **values))
    return {
        "schema_version": "blind-gains.m2-completion-watchdog-config.v1",
        "poll_interval_seconds": 10,
        "arms": arms,
        "state_path": "watchdog/state.json",
        "terminal_json": "watchdog/terminal.json",
        "terminal_markdown": "watchdog/terminal.md",
    }


def test_all_four_verified_parent_runs_produce_complete_observation(tmp_path: Path) -> None:
    observation = observe(_config(tmp_path), tmp_path)

    assert observation["status"] == "complete"
    assert observation["complete_arm_count"] == 4
    assert {item["outcome"] for item in observation["arms"]} == {"complete"}
    assert observation["scientific_gate_decision"] is None


def test_running_parent_keeps_watchdog_open(tmp_path: Path) -> None:
    config = _config(
        tmp_path,
        {
            "a3_caption": {
                "status": "running",
                "exit_code": None,
                "artifacts_exist": None,
                "end_time_utc": None,
            }
        },
    )

    observation = observe(config, tmp_path)

    assert observation["status"] == "watching"
    assert observation["complete_arm_count"] == 3
    assert next(item for item in observation["arms"] if item["arm"] == "a3_caption")[
        "outcome"
    ] == "running"


@pytest.mark.parametrize(
    "override,expected_error",
    [
        ({"exit_code": 1}, "nonzero_or_missing_exit_code"),
        ({"artifacts_exist": False}, "expected_artifacts_not_verified"),
        ({"end_time_utc": None}, "missing_end_time_utc"),
    ],
)
def test_complete_label_cannot_mask_incomplete_or_failed_parent(
    tmp_path: Path, override: dict, expected_error: str
) -> None:
    config = _config(tmp_path, {"a2_gray": override})

    observation = observe(config, tmp_path)
    gray = next(item for item in observation["arms"] if item["arm"] == "a2_gray")

    assert observation["status"] == "failed"
    assert gray["outcome"] == "invalid"
    assert any(expected_error in error for error in gray["errors"])


def test_parent_identity_mismatch_fails_closed(tmp_path: Path) -> None:
    config = _config(tmp_path)
    config["arms"][0]["run_id"] = "stale_or_unrelated_run"

    observation = observe(config, tmp_path)

    assert observation["status"] == "failed"
    assert observation["arms"][0]["outcome"] == "invalid"
    assert "run_id_mismatch" in observation["arms"][0]["errors"][0]


def test_config_rejects_duplicate_arm_that_would_hide_missing_arm(tmp_path: Path) -> None:
    config = _config(tmp_path)
    config["arms"][3] = dict(config["arms"][2])

    with pytest.raises(ValueError, match="incomplete or duplicated"):
        validate_config(config, tmp_path)


def test_runtime_has_no_process_control_or_gpu_launch_path() -> None:
    root = Path(__file__).resolve().parents[1]
    source = (root / "scripts/watch_m2_pilot_completion.py").read_text(
        encoding="utf-8"
    )

    assert "subprocess" not in source
    assert "os.kill" not in source
    assert "nvidia-smi" not in source
    assert "ssh " not in source


def test_terminal_notification_is_immutable_and_restart_idempotent(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    observation = observe(config, tmp_path)
    state = _update_state(None, observation, "a" * 64)

    write_terminal_notification(config, state, tmp_path)
    original_json = (tmp_path / "watchdog" / "terminal.json").read_bytes()
    original_markdown = (tmp_path / "watchdog" / "terminal.md").read_bytes()
    write_terminal_notification(config, state, tmp_path)

    assert (tmp_path / "watchdog" / "terminal.json").read_bytes() == original_json
    assert (tmp_path / "watchdog" / "terminal.md").read_bytes() == original_markdown
