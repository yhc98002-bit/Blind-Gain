from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts import run_m5_after_seed3_a2_queue as queue


ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _a2_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[str, str, Path]:
    monkeypatch.setattr(queue, "ROOT", tmp_path)
    training = "experiments/runs/mech_a2_gray_seed3_fixture"
    watcher = "experiments/runs/pilot_checkpoint_watch_a2_gray_seed3_fixture"
    checkpoint = tmp_path / "checkpoints/pilot/mech_a2_gray_seed3"
    _write(
        tmp_path / training / "run_manifest.json",
        {
            "job_type": "m3_mechanical_pilot_arm",
            "seed": 3,
            "arm": "a2_gray",
            "image_condition": "gray",
            "node": "an12",
            "gpu_ids": [0, 1, 2, 3],
            "tensor_parallel_width": 1,
            "replica_count": 4,
            "status": "complete",
            "exit_code": 0,
            "artifacts_exist": True,
            "checkpoint_path": str(checkpoint),
        },
    )
    (tmp_path / training / "checkpoint_watcher_run.txt").write_text(
        watcher + "\n", encoding="utf-8"
    )
    _write(
        tmp_path / watcher / "run_manifest.json",
        {
            "job_type": "pilot_checkpoint_retention_watch",
            "parent_training_run": training,
            "compute_node": "an12",
            "status": "running",
        },
    )
    _write(
        checkpoint / "global_step_100/actor/huggingface/model.safetensors.index.json",
        {"weight_map": {"x": "model.safetensors"}},
    )
    _write(
        checkpoint / "global_step_100/actor/RAW_STATE_RELOCATED.json",
        {
            "status": "raw_training_state_relocated_due_to_shared_quota",
            "files": [{"file": f"rank-{index}"} for index in range(8)],
        },
    )
    _write(checkpoint / "checkpoint_tracker.json", {"last_global_step": 100})
    return training, watcher, checkpoint


def test_adversarial_a2_release_waits_for_watcher_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A final marker alone must not release an12 while its watcher is still active."""
    training, watcher, _ = _a2_fixture(tmp_path, monkeypatch)

    status, evidence = queue.a2_release_state(training, watcher)

    assert status == "waiting"
    assert evidence["training_status"] == "complete"
    assert evidence["watcher_status"] == "running"


def test_a2_release_requires_verified_training_and_watcher(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    training, watcher, _ = _a2_fixture(tmp_path, monkeypatch)
    watcher_manifest = tmp_path / watcher / "run_manifest.json"
    payload = json.loads(watcher_manifest.read_text(encoding="utf-8"))
    payload.update({"status": "complete", "exit_code": 0, "artifacts_exist": True})
    _write(watcher_manifest, payload)

    status, evidence = queue.a2_release_state(training, watcher)

    assert status == "ready"
    assert all(evidence["completion_checks"].values())


def test_adversarial_a2_identity_rejects_wrong_arm(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    training, watcher, _ = _a2_fixture(tmp_path, monkeypatch)
    manifest = tmp_path / training / "run_manifest.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["arm"] = "a2b_noimage"
    _write(manifest, payload)

    with pytest.raises(ValueError, match="identity mismatch"):
        queue.validate_a2_identity(training, watcher)


def test_segment_launcher_is_exactly_single_node_m5() -> None:
    arguments = queue._segment_launch_args(
        node="an12",
        gpu_ids=(0, 1, 2, 3),
        start_step=200,
        restore_run="experiments/runs/m5_step200_restore",
        preflight_run="experiments/runs/m5_ray_startup_preflight",
        prior_run="experiments/runs/m5_anchor_source",
        handoff_run="experiments/runs/m5_step200_handoff",
    )

    assert arguments == [
        "bash",
        "scripts/launch_m5_anchor_segment.sh",
        "an12",
        "0,1,2,3",
        "200",
        "experiments/runs/m5_step200_restore",
        "experiments/runs/m5_ray_startup_preflight",
        "experiments/runs/m5_anchor_source",
        "experiments/runs/m5_step200_handoff",
    ]


def test_adversarial_evaluation_pointer_uses_source_parent_field(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(queue, "ROOT", tmp_path)
    segment = "experiments/runs/m5_anchor_longhorizon_segment250_300_fixture"
    evaluation = "experiments/runs/m5_checkpoint_evaluation_queue_fixture"
    _write(tmp_path / segment / "run_manifest.json", {"status": "running"})
    (tmp_path / segment / "evaluation_queue_run.txt").write_text(
        evaluation + "\n", encoding="utf-8"
    )
    _write(
        tmp_path / evaluation / "run_manifest.json",
        {"source_training_run": segment, "status": "running"},
    )

    observed = queue._child_pointer(
        segment,
        "evaluation_queue_run.txt",
        "experiments/runs/m5_checkpoint_evaluation_queue_",
        parent_field="source_training_run",
    )

    assert observed == evaluation


def test_queue_has_no_process_signal_or_pilot_arm_launch_path() -> None:
    source = (ROOT / "scripts/run_m5_after_seed3_a2_queue.py").read_text(
        encoding="utf-8"
    )
    assert "os.kill(" not in source
    assert "terminate(" not in source
    assert "pkill" not in source
    assert "launch_mech_pilot_followup_arm" not in source
    assert "a2b_noimage" not in source
    assert "a3_caption" not in source


def test_storage_heartbeat_refreshes_before_six_hour_guard_expiry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ticks = iter((0.0, 7201.0, 7202.0))
    monkeypatch.setattr(queue.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(
        queue,
        "_refresh_storage_snapshot",
        lambda _run_dir, label: {"path": label, "free_bytes": 100 * 1024**3},
    )
    state = {"segments": {"200-250": {}}}
    state_path = tmp_path / "queue_state.json"
    heartbeat = queue._storage_heartbeat(
        state,
        state_path,
        tmp_path,
        segment_label="200-250",
    )

    heartbeat({"status": "running"})

    snapshots = state["segments"]["200-250"]["storage_heartbeat_snapshots"]
    assert snapshots == [
        {"path": "heartbeat_200_250", "free_bytes": 100 * 1024**3}
    ]
    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    assert persisted["segments"]["200-250"]["storage_heartbeat_snapshots"] == snapshots


def test_adversarial_queue_failure_reconciles_mutable_state(tmp_path: Path) -> None:
    state = tmp_path / "queue_state.json"
    _write(state, {"status": "training_segment_200-250"})

    queue._record_queue_failure(tmp_path, RuntimeError("fixture failure"))

    payload = json.loads(state.read_text(encoding="utf-8"))
    assert payload["status"] == "failed_closed"
    assert payload["failure"]["error_type"] == "RuntimeError"
    assert payload["failure"]["message"] == "fixture failure"


def test_adversarial_running_child_without_wrapper_fails_after_three_polls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(queue, "ROOT", tmp_path)
    run = "experiments/runs/m5_step250_restore_fixture"
    _write(
        tmp_path / run / "run_manifest.json",
        {"run_id": "m5_step250_restore_fixture", "node": "login", "status": "running"},
    )
    monkeypatch.setattr(
        queue,
        "_run_liveness",
        lambda _run_path, _manifest: (False, "fixture_wrapper_absent"),
    )
    monkeypatch.setattr(queue.time, "sleep", lambda _seconds: None)

    with pytest.raises(RuntimeError, match="three polls"):
        queue._wait_complete(run, poll_seconds=60)


def test_login_liveness_accepts_relative_manifest_argument(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(queue, "ROOT", tmp_path)
    run = tmp_path / "experiments/runs/m5_eval_fixture"
    _write(
        run / "run_manifest.json",
        {"run_id": "m5_eval_fixture", "node": "login", "status": "running"},
    )
    (run / "pids").mkdir()
    (run / "pids/login.pid").write_text("123\n", encoding="ascii")
    monkeypatch.setattr(
        queue.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=(
                "python scripts/run_manifest_job.py "
                "experiments/runs/m5_eval_fixture/run_manifest.json"
            ),
            stderr="",
        ),
    )

    alive, reason = queue._run_liveness(
        run, json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
    )

    assert alive is True
    assert reason == "login_wrapper_identity_match"


def test_launcher_is_gpu_inert_registered_and_syntax_valid() -> None:
    launcher = ROOT / "scripts/launch_m5_after_seed3_a2_queue.sh"
    source = launcher.read_text(encoding="utf-8")

    subprocess.run(["bash", "-n", str(launcher)], check=True)
    assert 'job_type:"m5_after_seed3_a2_lifecycle_queue"' in source
    assert "child_node:\"an12\"" in source
    assert "child_gpu_ids:[0,1,2,3]" in source
    assert "performance_values_opened:false" in source
    assert "run_m5_after_seed3_a2_queue.py" in source
