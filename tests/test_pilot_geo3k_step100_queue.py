from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import run_pilot_geo3k_step100_queue as queue


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[dict, Path]:
    training = tmp_path / "experiments/runs/training"
    checkpoint = tmp_path / "checkpoints/pilot/a2/global_step_100/actor/huggingface"
    _write_json(
        training / "run_manifest.json",
        {
            "job_type": "l13_mechanical_pilot_arm",
            "arm": "a2_gray",
            "node": "an12",
            "image_condition": "gray",
            "status": "running",
            "exit_code": None,
            "artifacts_exist": None,
            "checkpoint_path": str(tmp_path / "checkpoints/pilot/a2"),
        },
    )
    upstream = tmp_path / "experiments/runs/r19-queue"
    _write_json(upstream / "run_manifest.json", {"status": "running"})
    config = {
        "schema_version": "blind-gains.pilot-geo3k-step100-queue.v1",
        "arm": "a2_gray",
        "condition": "gray",
        "node": "an12",
        "gpu_id": 4,
        "global_step": 100,
        "expected_row_count": 601,
        "training_run": str(training.relative_to(tmp_path)),
        "r19_queue_run": str(upstream.relative_to(tmp_path)),
        "r19_marker": str(
            (training / "step100_fliptrack_complete.json").relative_to(tmp_path)
        ),
        "checkpoint_path": str(checkpoint.relative_to(tmp_path)),
        "caption_run": "-",
        "state_path": "experiments/runs/geo3k-queue/state.json",
        "poll_seconds": 10,
        "stable_free_polls": 2,
    }
    config_path = tmp_path / "config.json"
    _write_json(config_path, config)
    monkeypatch.setattr(queue, "R19_MANIFEST_SHA256", "r19-hash")
    return config, config_path


def _complete_marker(tmp_path: Path, config: dict) -> None:
    training_manifest = tmp_path / config["training_run"] / "run_manifest.json"
    training = json.loads(training_manifest.read_text(encoding="utf-8"))
    training.update(status="complete", exit_code=0, artifacts_exist=True)
    _write_json(training_manifest, training)
    checkpoint = tmp_path / config["checkpoint_path"]
    checkpoint.mkdir(parents=True)
    (checkpoint / "model.safetensors.index.json").write_text("{}\n", encoding="utf-8")
    _write_json(
        tmp_path / config["r19_marker"],
        {
            "schema_version": queue.MARKER_SCHEMA_VERSION,
            "status": "complete",
            "global_step": 100,
            "r19_manifest_sha256": queue.R19_MANIFEST_SHA256,
            "checkpoint_path": str(checkpoint.resolve()),
            "evaluation_run": "experiments/runs/r19-eval",
            "checks": {"evaluation": True, "aggregate": True},
        },
    )


def test_waiting_marker_never_queries_gpu_or_launches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, config_path = _fixture(tmp_path, monkeypatch)

    result = queue.run_queue(
        config_path,
        root=tmp_path,
        once=True,
        capacity_query=lambda *_args: pytest.fail("capacity queried before marker"),
        evaluation_launcher=lambda *_args: pytest.fail("evaluation launched before marker"),
        audit_launcher=lambda *_args: pytest.fail("audit launched before marker"),
    )

    state = json.loads((tmp_path / config["state_path"]).read_text(encoding="utf-8"))
    assert result == 3
    assert state["status"] == "waiting_r19_marker"


def test_marker_with_one_false_check_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, _ = _fixture(tmp_path, monkeypatch)
    _complete_marker(tmp_path, config)
    marker_path = tmp_path / config["r19_marker"]
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    marker["checks"]["aggregate"] = False
    _write_json(marker_path, marker)

    with pytest.raises(ValueError, match="marker validation failed"):
        queue.validate_r19_marker(config, tmp_path)


def test_marker_validation_is_independent_of_relocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, _ = _fixture(tmp_path, monkeypatch)
    _complete_marker(tmp_path, config)
    retention_marker = (
        tmp_path / config["checkpoint_path"]
    ).parent / "RAW_STATE_RELOCATED.json"

    assert not retention_marker.exists()
    marker = queue.validate_r19_marker(config, tmp_path)
    assert marker["status"] == "complete"


def test_two_clean_polls_launch_exact_evaluation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, config_path = _fixture(tmp_path, monkeypatch)
    _complete_marker(tmp_path, config)
    state_path = tmp_path / config["state_path"]
    _write_json(
        state_path,
        {
            "schema_version": "blind-gains.pilot-geo3k-step100-queue-state.v1",
            "status": "confirming_free_capacity",
            "poll_count": 1,
            "stable_free_poll_count": 1,
        },
    )
    evaluation = tmp_path / "experiments/runs/evaluation"
    launched: list[str] = []

    result = queue.run_queue(
        config_path,
        root=tmp_path,
        once=True,
        capacity_query=lambda _node, _gpus: {4: []},
        evaluation_launcher=lambda observed, _root: (
            launched.append(observed["arm"]) or evaluation
        ),
        audit_launcher=lambda *_args: pytest.fail("audit launched before evaluation"),
    )

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert result == 3
    assert launched == ["a2_gray"]
    assert state["status"] == "evaluation_running"
    assert state["evaluation_run"] == "experiments/runs/evaluation"


def test_complete_audit_closes_queue_without_performance_readout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, config_path = _fixture(tmp_path, monkeypatch)
    evaluation_run = tmp_path / "experiments/runs/evaluation"
    evaluation_manifest = evaluation_run / "run_manifest.json"
    _write_json(
        evaluation_manifest,
        {
            "run_id": "evaluation",
            "job_type": "m2_pilot_geo3k_step100_eval",
            "arm": "a2_gray",
            "condition": "gray",
            "node": "an12",
            "gpu_ids": [4],
            "global_step": 100,
            "expected_row_count": 601,
        },
    )
    audit_run = tmp_path / "experiments/runs/audit"
    _write_json(
        audit_run / "run_manifest.json",
        {
            "job_type": "m2_pilot_geo3k_step100_audit",
            "status": "complete",
            "exit_code": 0,
            "artifacts_exist": True,
            "source_evaluation_run": str(evaluation_run.relative_to(tmp_path)),
            "source_evaluation_manifest_sha256": queue._sha256(evaluation_manifest),
        },
    )
    _write_json(
        audit_run / "audit.json",
        {
            "status": "pass",
            "row_count": 601,
            "checks": {"rows": True, "scores": True},
            "static_mismatch_count": 0,
            "score_recomputation_mismatch_count": 0,
            "strict_identity_mismatch_count": 0,
            "output_sha256": "output-hash",
            "run_id": "evaluation",
            "run_manifest": str(evaluation_manifest),
            "run_manifest_sha256": queue._sha256(evaluation_manifest),
            "performance_values_reported": False,
        },
    )
    _write_json(
        tmp_path / config["state_path"],
        {
            "schema_version": "blind-gains.pilot-geo3k-step100-queue-state.v1",
            "status": "audit_running",
            "poll_count": 4,
            "stable_free_poll_count": 2,
            "evaluation_run": str(evaluation_run.relative_to(tmp_path)),
            "audit_run": str(audit_run.relative_to(tmp_path)),
            "performance_values_inspected": False,
        },
    )

    result = queue.run_queue(config_path, root=tmp_path, once=True)

    state = json.loads(
        (tmp_path / config["state_path"]).read_text(encoding="utf-8")
    )
    assert result == 0
    assert state["status"] == "complete"
    assert state["output_sha256"] == "output-hash"
    assert state["performance_values_inspected"] is False


def test_audit_from_another_evaluation_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, config_path = _fixture(tmp_path, monkeypatch)
    expected = tmp_path / "experiments/runs/expected-evaluation"
    foreign = tmp_path / "experiments/runs/foreign-evaluation"
    _write_json(expected / "run_manifest.json", {"run_id": "expected"})
    _write_json(foreign / "run_manifest.json", {"run_id": "foreign"})
    audit_run = tmp_path / "experiments/runs/audit"
    _write_json(
        audit_run / "run_manifest.json",
        {
            "job_type": "m2_pilot_geo3k_step100_audit",
            "status": "complete",
            "exit_code": 0,
            "artifacts_exist": True,
            "source_evaluation_run": str(foreign.relative_to(tmp_path)),
            "source_evaluation_manifest_sha256": queue._sha256(
                foreign / "run_manifest.json"
            ),
        },
    )
    _write_json(audit_run / "audit.json", {})
    _write_json(
        tmp_path / config["state_path"],
        {
            "schema_version": "blind-gains.pilot-geo3k-step100-queue-state.v1",
            "status": "audit_running",
            "poll_count": 4,
            "stable_free_poll_count": 2,
            "evaluation_run": str(expected.relative_to(tmp_path)),
            "audit_run": str(audit_run.relative_to(tmp_path)),
            "performance_values_inspected": False,
        },
    )

    with pytest.raises(ValueError, match="not bound"):
        queue.run_queue(config_path, root=tmp_path, once=True)


def test_released_node_is_rejected() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "scripts/run_pilot_geo3k_step100_queue.py"
    ).read_text(encoding="utf-8")
    assert '{"an12", "an29"}' in source
    assert "an21" not in source
    assert "os.kill" not in source


def test_a2_recovery_config_binds_fresh_r19_queue() -> None:
    root = Path(__file__).resolve().parents[1]
    config = json.loads(
        (root / "configs/eval/m2_a2_geo3k_step100_queue_v2.json").read_text(
            encoding="utf-8"
        )
    )

    assert config["training_run"].endswith(
        "mech_a2_gray_resume60_retry2_an12_20260715T165701Z"
    )
    assert config["r19_queue_run"].endswith(
        "pilot_step100_eval_queue_a2_gray_login_20260716T152519Z"
    )
    assert config["checkpoint_path"].endswith(
        "mech_a2_gray_resume60_retry2/global_step_100/actor/huggingface"
    )
