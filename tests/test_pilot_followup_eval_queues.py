from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from scripts import run_pilot_geo3k_step100_queue as geo_queue
from scripts import run_pilot_step100_eval_queue as r19_queue
from scripts.audit_pilot_geo3k_step100_eval import audit_run
from scripts.run_pilot_geo3k_step100_eval import FOLLOWUP_ROW_SCHEMA_VERSION
from scripts.watch_pilot_step_evaluation import validate_training_source
from scripts.watch_pilot_followup_eval_lifecycle import validate_children


ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _followup_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict, dict]:
    training_run = tmp_path / "experiments/runs/train"
    checkpoint_root = tmp_path / "checkpoints/pilot/a1"
    checkpoint = checkpoint_root / "global_step_60/actor/huggingface"
    checkpoint.mkdir(parents=True)
    _write_json(
        checkpoint / "model.safetensors.index.json",
        {"weight_map": {"model.layer": "model-00001-of-00001.safetensors"}},
    )
    (checkpoint / "model-00001-of-00001.safetensors").write_bytes(b"weights")
    _write_json(
        training_run / "run_manifest.json",
        {
            "job_type": "m3_mechanical_pilot_arm",
            "status": "complete",
            "exit_code": 0,
            "artifacts_exist": True,
            "arm": "a1_real",
            "seed": 2,
            "image_condition": "real",
            "node": "an12",
            "checkpoint_path": str(checkpoint_root),
        },
    )
    release_run = tmp_path / "experiments/runs/a3_release"
    _write_json(
        release_run / "run_manifest.json",
        {
            "job_type": "m3_mechanical_pilot_arm",
            "status": "complete",
            "exit_code": 0,
            "artifacts_exist": True,
            "arm": "a3_caption",
            "seed": 2,
        },
    )
    r19_manifest = tmp_path / "data/r19.jsonl"
    r19_manifest.parent.mkdir(parents=True)
    r19_manifest.write_text('{"pair_id":"fixture"}\n', encoding="utf-8")
    r19_hash = hashlib.sha256(r19_manifest.read_bytes()).hexdigest()
    monkeypatch.setattr(r19_queue, "R19_MANIFEST_SHA256", r19_hash)
    monkeypatch.setattr(geo_queue, "R19_MANIFEST_SHA256", r19_hash)
    marker = training_run / "step60_fliptrack_complete.json"
    r19 = {
        "schema_version": r19_queue.FOLLOWUP_CONFIG_SCHEMA,
        "arm": "a1_real",
        "seed": 2,
        "node": "an29",
        "gpu_ids": [0, 1, 2, 3],
        "global_step": 60,
        "num_shards": 4,
        "image_mode": "real",
        "max_new_tokens": 32,
        "cohort_release_training_run": str(release_run.relative_to(tmp_path)),
        "training_run": str(training_run.relative_to(tmp_path)),
        "checkpoint_path": str(checkpoint.relative_to(tmp_path)),
        "r19_manifest": str(r19_manifest.relative_to(tmp_path)),
        "r19_manifest_sha256": r19_hash,
        "marker": str(marker.relative_to(tmp_path)),
        "evaluation_run": "experiments/runs/eval",
        "aggregate_tag": "m3_fixture_step60",
        "state_path": "experiments/runs/r19_queue/state.json",
        "poll_seconds": 10,
        "stable_free_polls": 2,
    }
    geo = {
        "schema_version": geo_queue.FOLLOWUP_CONFIG_SCHEMA,
        "arm": "a1_real",
        "condition": "real",
        "seed": 2,
        "node": "an29",
        "gpu_id": 4,
        "global_step": 60,
        "expected_row_count": 601,
        "training_run": str(training_run.relative_to(tmp_path)),
        "r19_queue_run": "experiments/runs/r19_queue",
        "r19_marker": str(marker.relative_to(tmp_path)),
        "checkpoint_path": str(checkpoint.relative_to(tmp_path)),
        "caption_run": "-",
        "state_path": "experiments/runs/geo_queue/state.json",
        "poll_seconds": 10,
        "stable_free_polls": 2,
    }
    return r19, geo


def test_followup_queues_allow_evaluation_node_to_differ_from_training_node(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    r19, geo = _followup_fixture(tmp_path, monkeypatch)

    r19_queue.validate_config(r19, tmp_path)
    assert r19_queue.inspect_dependencies(r19, tmp_path)["status"] == "ready"
    geo_queue.validate_config(geo, tmp_path)


def test_followup_queue_rejects_unregistered_seed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    r19, geo = _followup_fixture(tmp_path, monkeypatch)
    r19["seed"] = 1
    geo["seed"] = 1

    with pytest.raises(ValueError, match="seed must be 2 or 3"):
        r19_queue.validate_config(r19, tmp_path)
    with pytest.raises(ValueError, match="seed must be 2 or 3"):
        geo_queue.validate_config(geo, tmp_path)


def test_followup_queue_waits_for_full_cohort_release(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, _ = _followup_fixture(tmp_path, monkeypatch)
    release_run = tmp_path / "experiments/runs/release"
    _write_json(
        release_run / "run_manifest.json",
        {
            "job_type": "m3_mechanical_pilot_arm",
            "arm": "a3_caption",
            "seed": 2,
            "status": "running",
        },
    )
    config["cohort_release_training_run"] = str(release_run.relative_to(tmp_path))

    observed = r19_queue.inspect_dependencies(config, tmp_path)

    assert observed == {"status": "waiting_cohort_release", "reason": "running"}


def test_followup_r19_launcher_passes_exact_step_to_low_level_launcher(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, _ = _followup_fixture(tmp_path, monkeypatch)
    observed: dict = {}

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed["command"] = command
        observed["env"] = kwargs["env"]
        return subprocess.CompletedProcess(command, 75, "", "occupied")

    monkeypatch.setattr(r19_queue.subprocess, "run", fake_run)
    result = r19_queue._launch_evaluation(config, tmp_path)

    assert result.returncode == 75
    assert observed["env"]["BLIND_GAINS_PILOT_GLOBAL_STEP"] == "60"
    assert observed["env"]["BLIND_GAINS_PILOT_SOURCE_RUN"] == config["training_run"]


def test_watcher_accepts_registered_m3_source_and_rejects_wrong_seed() -> None:
    source = {
        "job_type": "m3_mechanical_pilot_arm",
        "status": "complete",
        "seed": 2,
    }
    validate_training_source(source)
    source["seed"] = 1
    with pytest.raises(ValueError, match="seed must be 2 or 3"):
        validate_training_source(source)


def test_followup_audit_selects_distinct_schema_before_input_checks(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "experiments/runs/eval"
    _write_json(
        run_dir / "run_manifest.json",
        {
            "job_type": "m3_pilot_geo3k_checkpoint_eval",
            "global_step": 60,
            "pilot_seed": 2,
            "expected_artifacts": [],
        },
    )

    result = audit_run(run_dir, root=tmp_path)

    assert result["schema_version"] == "blind-gains.pilot-followup-geo3k-audit.v1"
    assert result["checks"]["job_type"] is True
    assert result["checks"]["global_step"] is True


def test_followup_schema_is_distinct_and_launchers_are_syntax_valid() -> None:
    assert FOLLOWUP_ROW_SCHEMA_VERSION != "blind-gains.pilot-geo3k-step100-eval.v1"
    for launcher in (
        "scripts/launch_pilot_followup_r19_queue.sh",
        "scripts/launch_pilot_followup_geo3k_queue.sh",
        "scripts/launch_pilot_geo3k_step100_eval.sh",
        "scripts/launch_pilot_geo3k_step100_audit.sh",
        "scripts/launch_pilot_seed2_eval_lifecycle.sh",
    ):
        subprocess.run(["bash", "-n", str(ROOT / launcher)], check=True)


def test_lifecycle_rejects_incomplete_arm_checkpoint_matrix(tmp_path: Path) -> None:
    queue_run = tmp_path / "experiments/runs/queue"
    _write_json(queue_run / "run_manifest.json", {"status": "running"})
    payload = {
        "schema_version": "blind-gains.pilot-followup-eval-children.v1",
        "seed": 2,
        "endpoints": [
            {
                "arm": "a1_real",
                "global_step": 60,
                "r19_queue_run": str(queue_run.relative_to(tmp_path)),
                "geo3k_queue_run": str(queue_run.relative_to(tmp_path)),
            }
        ],
    }

    with pytest.raises(ValueError, match="exactly eight"):
        validate_children(payload, tmp_path)
