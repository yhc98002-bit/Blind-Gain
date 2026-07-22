from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts import run_pilot_seed3_queue_v2 as queue


ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _dependencies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    seed2_status: str = "complete",
    m6_status: str = "complete",
) -> tuple[Path, Path, Path]:
    monkeypatch.setattr(queue, "ROOT", tmp_path)
    seed2 = tmp_path / "experiments/runs/seed2/run_manifest.json"
    seed2_output = tmp_path / "experiments/runs/seed2/lifecycle_complete.json"
    m6 = tmp_path / "experiments/runs/m6/run_manifest.json"
    m6_state = tmp_path / "experiments/runs/m6/queue_state.json"
    m6_audit = tmp_path / "reports/mini_a5_plumbing_smoke_audit_v1.json"
    m5 = tmp_path / "experiments/runs/m5/run_manifest.json"
    _write(
        seed2,
        {
            "status": seed2_status,
            "expected_artifacts": [
                "experiments/runs/seed2/children.json",
                "experiments/runs/seed2/lifecycle_complete.json",
            ],
        },
    )
    _write(
        seed2_output,
        {
            "status": "complete",
            "performance_values_opened": False,
            "checks": {"matrix": True},
        },
    )
    _write(
        m6,
        {
            "status": m6_status,
            "expected_artifacts": [
                "experiments/runs/m6/queue_state.json",
                "reports/mini_a5_plumbing_smoke_audit_v1.json",
                "reports/mini_a5_plumbing_smoke_audit_v1.md",
            ],
        },
    )
    _write(m6_state, {"status": "complete", "main_optimizer_steps_authorized": 0})
    _write(m6_audit, {"status": "pass", "checks": {"cp": True, "member": True}})
    _write(m5, {"status": "running"})
    return seed2, m6, m5


def test_dependency_requires_sealed_seed2_and_completed_m6_smoke(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed2, m6, m5 = _dependencies(tmp_path, monkeypatch, m6_status="running")

    status, observed = queue.dependency_state(seed2, m6, m5)

    assert status == "waiting"
    assert observed["m6_smoke"] == "running"


def test_dependency_accepts_structurally_verified_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed2, m6, m5 = _dependencies(tmp_path, monkeypatch)

    status, _ = queue.dependency_state(seed2, m6, m5)

    assert status == "ready"


def test_dependency_rejects_m6_main_step_authorization(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed2, m6, m5 = _dependencies(tmp_path, monkeypatch)
    state = tmp_path / "experiments/runs/m6/queue_state.json"
    _write(state, {"status": "complete", "main_optimizer_steps_authorized": 1})

    status, observed = queue.dependency_state(seed2, m6, m5)

    assert status == "fail"
    assert observed["m6_artifact"] == "invalid"


def test_arm_release_waits_for_step100_merge_and_retention(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(queue, "ROOT", tmp_path)
    training_run = tmp_path / "experiments/runs/train"
    watcher_run = tmp_path / "experiments/runs/watch"
    checkpoint = tmp_path / "checkpoints/pilot/arm"
    _write(
        training_run / "run_manifest.json",
        {
            "status": "complete",
            "exit_code": 0,
            "artifacts_exist": True,
            "checkpoint_path": str(checkpoint),
        },
    )
    _write(watcher_run / "run_manifest.json", {"status": "running"})
    record = {
        "training_run": str(training_run.relative_to(tmp_path)),
        "watcher_run": str(watcher_run.relative_to(tmp_path)),
    }

    assert queue.arm_checkpoint_ready(record) == (
        False,
        "waiting_step100_merge_and_retention",
    )
    _write(
        checkpoint / "global_step_100/actor/huggingface/model.safetensors.index.json",
        {"weight_map": {"x": "model.safetensors"}},
    )
    _write(
        checkpoint / "global_step_100/actor/RAW_STATE_RELOCATED.json",
        {"status": "raw_training_state_relocated_due_to_shared_quota"},
    )
    assert queue.arm_checkpoint_ready(record) == (
        True,
        "training_and_step100_retention_complete",
    )


def test_attached_watcher_is_adopted_without_second_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(queue, "ROOT", tmp_path)
    training = "experiments/runs/mech_a1_real_seed3_fixture"
    watcher = "experiments/runs/pilot_checkpoint_watch_fixture"
    training_path = tmp_path / training
    training_path.mkdir(parents=True)
    (training_path / "checkpoint_watcher_run.txt").write_text(
        watcher + "\n", encoding="utf-8"
    )
    _write(
        tmp_path / watcher / "run_manifest.json",
        {
            "job_type": "pilot_checkpoint_retention_watch",
            "parent_training_run": training,
            "compute_node": "an29",
            "status": "running",
        },
    )
    assert queue.attached_watcher_run(training, "an29") == watcher


def test_adversarial_attached_watcher_parent_mismatch_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(queue, "ROOT", tmp_path)
    training = "experiments/runs/mech_a1_real_seed3_fixture"
    watcher = "experiments/runs/pilot_checkpoint_watch_fixture"
    training_path = tmp_path / training
    training_path.mkdir(parents=True)
    (training_path / "checkpoint_watcher_run.txt").write_text(watcher, encoding="utf-8")
    _write(
        tmp_path / watcher / "run_manifest.json",
        {
            "job_type": "pilot_checkpoint_retention_watch",
            "parent_training_run": "experiments/runs/different-parent",
            "compute_node": "an29",
            "status": "running",
        },
    )
    with pytest.raises(RuntimeError, match="identity mismatch"):
        queue.attached_watcher_run(training, "an29")


def test_adversarial_watcher_path_traversal_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(queue, "ROOT", tmp_path)
    training = "experiments/runs/mech_a1_real_seed3_fixture"
    training_path = tmp_path / training
    training_path.mkdir(parents=True)
    (training_path / "checkpoint_watcher_run.txt").write_text(
        "experiments/runs/pilot_checkpoint_watch_../../outside", encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="outside the immutable run namespace"):
        queue.attached_watcher_run(training, "an29")


def test_seed3_launcher_is_registered_gpu_inert_and_syntax_valid() -> None:
    launcher = ROOT / "scripts/launch_pilot_seed3_queue_v2.sh"
    source = launcher.read_text(encoding="utf-8")

    subprocess.run(["bash", "-n", str(launcher)], check=True)
    assert "registered_pilot_seed23_v1.md" in source
    assert "sealed-seed2-lifecycle-manifest" in source
    assert "m6-smoke-queue-manifest" in source
    assert "pilot_followup_evaluation_recovery_lifecycle" in source
    assert 'job_type: "m3_seed3_training_capacity_queue_v4"' in source
    assert '(.job_type == "m6_registered_smoke_member_recovery_v1")' in source
    assert "performance_values_opened: false" in source


def test_seed3_recovery_launcher_is_fail_closed_and_syntax_valid() -> None:
    launcher = ROOT / "scripts/launch_pilot_seed3_queue_recovery.sh"
    source = launcher.read_text(encoding="utf-8")

    subprocess.run(["bash", "-n", str(launcher)], check=True)
    assert "checkpoint watcher failed to launch (73)" in source
    assert 'job_type:"m3_seed3_training_capacity_queue_v5"' in source
    assert "--adopted-arm a1_real" in source
    assert "no optimizer trajectory is restarted or reconstructed" in source


def test_seed3_scheduler_never_launches_a_second_watcher() -> None:
    source = (ROOT / "scripts/run_pilot_seed3_queue_v2.py").read_text(
        encoding="utf-8"
    )
    assert '"scripts/launch_pilot_checkpoint_watch.sh"' not in source
    assert "attached_watcher_run(training_run, node)" in source
