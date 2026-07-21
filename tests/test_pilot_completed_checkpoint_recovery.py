from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.run_a1_seed2_checkpoint_recovery_queue import a3_ready
from scripts.watch_pilot_completed_parent_checkpoints import (
    execution_plan,
    validate_recovery_inputs,
)


ROOT = Path(__file__).resolve().parents[1]


def _parent() -> dict:
    return {
        "run_id": "mech_a1_real_seed2_an29_x",
        "job_type": "m3_mechanical_pilot_arm",
        "status": "complete",
        "exit_code": 0,
        "artifacts_exist": True,
    }


def _watcher() -> dict:
    return {
        "job_type": "pilot_checkpoint_retention_watch",
        "status": "fail",
        "exit_code": 1,
        "parent_training_run": "experiments/runs/mech_a1_real_seed2_an29_x",
    }


def test_completed_parent_recovery_accepts_only_exact_failed_lineage() -> None:
    assert validate_recovery_inputs(_parent(), _watcher()) == []
    watcher = _watcher()
    watcher["parent_training_run"] = "experiments/runs/other"
    assert validate_recovery_inputs(_parent(), watcher) == ["watcher_parent_mismatch"]


def test_old_running_parent_assumption_is_rejected() -> None:
    parent = _parent()
    parent["status"] = "running"
    parent["exit_code"] = None
    assert "parent_not_complete" in validate_recovery_inputs(parent, _watcher())


def test_recovery_starts_at_40_and_defers_only_step60_merged_relocation() -> None:
    assert execution_plan() == (
        (40, "relocate_after_merge"),
        (60, "retain_for_registered_evaluation"),
        (80, "relocate_after_merge"),
        (100, "retain_final_on_shared"),
        (60, "relocate_after_registered_evaluation"),
    )


def test_a3_readiness_requires_complete_merge_and_raw_marker(tmp_path: Path) -> None:
    manifest = {"status": "complete", "exit_code": 0, "artifacts_exist": True}
    root = tmp_path / "a3"
    merged = root / "global_step_100/actor/huggingface/model.safetensors.index.json"
    raw = root / "global_step_100/actor/RAW_STATE_RELOCATED.json"
    merged.parent.mkdir(parents=True)
    merged.write_text("{}\n", encoding="utf-8")
    assert a3_ready(manifest, root) is False
    raw.write_text("{}\n", encoding="utf-8")
    assert a3_ready(manifest, root) is True


def test_recovery_launchers_parse() -> None:
    for name in (
        "launch_pilot_completed_checkpoint_recovery.sh",
        "launch_a1_seed2_checkpoint_recovery_queue.sh",
    ):
        subprocess.run(["bash", "-n", str(ROOT / "scripts" / name)], check=True)
