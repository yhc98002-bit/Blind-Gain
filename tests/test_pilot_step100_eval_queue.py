from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from scripts import run_pilot_step100_eval_queue as queue


ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    retention_status: str = "complete",
    retention_job_type: str = "pilot_checkpoint_retention_recovery",
    training_status: str = "complete",
) -> tuple[dict, Path]:
    training_run = tmp_path / "experiments/runs/train"
    retention_run = tmp_path / "experiments/runs/retention"
    checkpoint = tmp_path / "checkpoints/pilot/a3/global_step_100/actor/huggingface"
    checkpoint.mkdir(parents=True)
    _write_json(
        checkpoint / "model.safetensors.index.json",
        {"weight_map": {"model.layer": "model-00001-of-00001.safetensors"}},
    )
    (checkpoint / "model-00001-of-00001.safetensors").write_bytes(b"weights")
    (checkpoint.parent / "RAW_STATE_RELOCATED.json").write_text("{}\n", encoding="utf-8")
    _write_json(
        training_run / "run_manifest.json",
        {
            "job_type": "l13_mechanical_pilot_arm",
            "arm": "a3_caption",
            "node": "an29",
            "status": training_status,
            "exit_code": 0 if training_status == "complete" else None,
            "artifacts_exist": True if training_status == "complete" else None,
            "end_time_utc": "2026-07-15T00:00:00Z"
            if training_status == "complete"
            else None,
            "checkpoint_path": str(tmp_path / "checkpoints/pilot/a3"),
        },
    )
    retention = {
        "job_type": retention_job_type,
        "parent_training_run": str(training_run.relative_to(tmp_path)),
        "compute_node": "an29",
        "status": retention_status,
        "exit_code": 0 if retention_status == "complete" else None,
        "artifacts_exist": True if retention_status == "complete" else None,
        "expected_artifacts": [
            str(checkpoint / "model.safetensors.index.json"),
            str(checkpoint.parent / "RAW_STATE_RELOCATED.json"),
        ],
    }
    if retention_job_type == "pilot_resume60_checkpoint_retention_watch":
        retention.update(
            {
                "run_root": str(tmp_path / "checkpoints/pilot/a3"),
                "resume_schedule": [80, 100],
            }
        )
    _write_json(retention_run / "run_manifest.json", retention)
    r19 = tmp_path / "data/r19.jsonl"
    r19.parent.mkdir(parents=True)
    r19.write_text('{"pair_id":"fixture"}\n', encoding="utf-8")
    r19_hash = hashlib.sha256(r19.read_bytes()).hexdigest()
    monkeypatch.setattr(queue, "R19_MANIFEST_SHA256", r19_hash)
    config = {
        "schema_version": "blind-gains.pilot-step100-eval-queue.v1",
        "arm": "a3_caption",
        "node": "an29",
        "gpu_ids": [4, 5, 6, 7],
        "global_step": 100,
        "num_shards": 4,
        "image_mode": "real",
        "max_new_tokens": 32,
        "training_run": str(training_run.relative_to(tmp_path)),
        "retention_run": str(retention_run.relative_to(tmp_path)),
        "checkpoint_path": str(checkpoint.relative_to(tmp_path)),
        "r19_manifest": str(r19.relative_to(tmp_path)),
        "r19_manifest_sha256": r19_hash,
        "marker": str(
            (training_run / "step100_fliptrack_complete.json").relative_to(tmp_path)
        ),
        "evaluation_run": "experiments/runs/evaluation",
        "aggregate_tag": "fixture_step100",
        "state_path": "experiments/runs/queue/state.json",
        "poll_seconds": 10,
        "stable_free_polls": 2,
    }
    config_path = tmp_path / "config.json"
    _write_json(config_path, config)
    return config, config_path


def test_config_rejects_released_node_before_any_remote_query(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, _ = _fixture(tmp_path, monkeypatch)
    config["node"] = "an21"

    with pytest.raises(ValueError, match="permanent nodes"):
        queue.validate_config(config, tmp_path)


def test_failed_storage_relocation_does_not_block_complete_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, _ = _fixture(tmp_path, monkeypatch, retention_status="failed")

    observed = queue.inspect_dependencies(config, tmp_path)

    assert observed["status"] == "ready"
    assert observed["archive_relocation"]["status"] == "failed"


def test_dependency_waits_for_identity_correct_running_training(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, _ = _fixture(tmp_path, monkeypatch, training_status="running")

    observed = queue.inspect_dependencies(config, tmp_path)

    assert observed == {"status": "waiting_training", "reason": "running"}


def test_dependency_accepts_complete_checkpoint_while_archive_is_running(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, _ = _fixture(
        tmp_path,
        monkeypatch,
        retention_job_type="pilot_resume60_checkpoint_retention_watch",
        retention_status="running",
    )

    observed = queue.inspect_dependencies(config, tmp_path)

    assert observed["status"] == "ready"
    assert observed["archive_relocation"]["status"] == "running"


def test_dependency_ignores_archive_schedule_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, _ = _fixture(
        tmp_path,
        monkeypatch,
        retention_job_type="pilot_resume60_checkpoint_retention_watch",
    )
    retention_manifest = tmp_path / config["retention_run"] / "run_manifest.json"
    retention = json.loads(retention_manifest.read_text(encoding="utf-8"))
    retention["resume_schedule"] = [100]
    _write_json(retention_manifest, retention)

    observed = queue.inspect_dependencies(config, tmp_path)

    assert observed["status"] == "ready"


def test_dependency_requires_hash_verified_final_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, _ = _fixture(tmp_path, monkeypatch)
    checkpoint = tmp_path / config["checkpoint_path"]
    (checkpoint / "model.safetensors.index.json").unlink()

    observed = queue.inspect_dependencies(config, tmp_path)

    assert observed["status"] == "waiting_checkpoint"
    assert observed["reason"] == "merged_index_absent"


def test_occupied_neighbor_keeps_queue_gpu_inert(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, config_path = _fixture(tmp_path, monkeypatch)

    result = queue.run_queue(
        config_path,
        root=tmp_path,
        once=True,
        capacity_query=lambda _node, _gpus: {4: [991], 5: [], 6: [], 7: []},
    )

    state = json.loads((tmp_path / config["state_path"]).read_text(encoding="utf-8"))
    assert result == 3
    assert state["status"] == "waiting_capacity"
    assert state["stable_free_poll_count"] == 0
    assert not (tmp_path / config["evaluation_run"]).exists()


def test_marker_validation_rejects_one_false_lifecycle_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, _ = _fixture(tmp_path, monkeypatch)
    marker = tmp_path / config["marker"]
    _write_json(
        marker,
        {
            "schema_version": queue.MARKER_SCHEMA_VERSION,
            "status": "complete",
            "global_step": 100,
            "r19_manifest_sha256": queue.R19_MANIFEST_SHA256,
            "checkpoint_path": str((tmp_path / config["checkpoint_path"]).resolve()),
            "checks": {"evaluation_complete": True, "aggregate_complete": False},
        },
    )

    with pytest.raises(ValueError, match="marker validation failed"):
        queue.validate_marker(config, tmp_path)


def test_queue_launcher_is_syntax_valid_and_never_accepts_an21() -> None:
    launcher = ROOT / "scripts/launch_pilot_step100_eval_queue.sh"
    subprocess.run(["bash", "-n", str(launcher)], check=True)
    source = (ROOT / "scripts/run_pilot_step100_eval_queue.py").read_text(
        encoding="utf-8"
    )
    assert '{"an12", "an29"}' in source
    assert "os.kill" not in source


def test_a1_base_config_is_bound_to_the_exact_recovery_lifecycle() -> None:
    config = json.loads(
        (ROOT / "configs/eval/m2_a1_step100_eval_queue_v1.json").read_text(
            encoding="utf-8"
        )
    )

    assert config["arm"] == "a1_real"
    assert config["node"] == "an12"
    assert config["gpu_ids"] == [4, 5, 6, 7]
    assert config["training_run"].endswith(
        "mech_a1_real_resume60_an12_20260714T080855Z"
    )
    assert config["retention_run"].endswith(
        "pilot_retention_recovery_mech_a1_real_resume60_login_20260715T195146Z"
    )
    assert config["checkpoint_path"].endswith(
        "mech_a1_real_resume60/global_step_100/actor/huggingface"
    )
    assert config["marker"] == f'{config["training_run"]}/step100_fliptrack_complete.json'


def test_a2_base_config_is_bound_to_the_active_primary_watcher() -> None:
    config = json.loads(
        (ROOT / "configs/eval/m2_a2_step100_eval_queue_v1.json").read_text(
            encoding="utf-8"
        )
    )

    assert config["arm"] == "a2_gray"
    assert config["node"] == "an12"
    assert config["gpu_ids"] == [4, 5, 6, 7]
    assert config["training_run"].endswith(
        "mech_a2_gray_resume60_retry2_an12_20260715T165701Z"
    )
    assert config["retention_run"].endswith(
        "pilot_resume60_checkpoint_watch_mech_a2_gray_resume60_retry2_login_20260715T170029Z"
    )
    assert config["checkpoint_path"].endswith(
        "mech_a2_gray_resume60_retry2/global_step_100/actor/huggingface"
    )
