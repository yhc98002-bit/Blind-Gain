from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import run_m8_virl39k_7b_summary_queue as queue
from src.eval.blind_solvability import CONDITIONS


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _fixture(tmp_path: Path) -> tuple[dict, Path]:
    model = f"Qwen/Qwen2.5-VL-7B-Instruct@{'a' * 40}"
    runs = {}
    for condition in CONDITIONS:
        run = tmp_path / f"experiments/runs/{condition}"
        output = run / "per_item.jsonl"
        _write_json(
            run / "run_manifest.json",
            {
                "job_type": "m8_virl39k_7b_blind_solvability_v1",
                "condition": condition,
                "node": "an29",
                "gpu_ids": [queue.EXPECTED_GPU[condition]],
                "tensor_parallel_width": 1,
                "replica_count": 1,
                "model_revision": model,
                "sample_size": 4096,
                "sample_count": 16,
                "max_tokens": 2048,
                "seed": 20260710,
                "status": "running",
                "exit_code": None,
                "artifacts_exist": None,
                "expected_artifacts": [str(output.relative_to(tmp_path))],
            },
        )
        runs[condition] = str(run.relative_to(tmp_path))
    config = {
        "schema_version": "blind-gains.m8-summary-queue.v1",
        "expected_job_type": "m8_virl39k_7b_blind_solvability_v1",
        "expected_model_revision": model,
        "expected_row_count": 4096,
        "runs": runs,
        "outputs": {
            "summary_json": "reports/summary.json",
            "summary_markdown": "reports/summary.md",
            "audit_json": "reports/audit.json",
            "audit_markdown": "reports/audit.md",
        },
        "state_path": "experiments/runs/queue/state.json",
        "poll_seconds": 30,
    }
    config_path = tmp_path / "config.json"
    _write_json(config_path, config)
    return config, config_path


def _complete_sources(tmp_path: Path, config: dict) -> None:
    for condition in CONDITIONS:
        run = tmp_path / config["runs"][condition]
        manifest_path = run / "run_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest.update(status="complete", exit_code=0, artifacts_exist=True)
        _write_json(manifest_path, manifest)
        (run / "per_item.jsonl").write_text("{}\n" * 4096, encoding="utf-8")


def test_running_sources_never_launch_summary(tmp_path: Path) -> None:
    config, config_path = _fixture(tmp_path)

    result = queue.run_queue(
        config_path,
        root=tmp_path,
        once=True,
        summary_launcher=lambda *_args: pytest.fail("summary launched early"),
    )

    state = json.loads((tmp_path / config["state_path"]).read_text(encoding="utf-8"))
    assert result == 3
    assert state["status"] == "waiting_source_runs"
    assert state["performance_values_inspected"] is False


def test_wrong_model_is_rejected_before_completion(tmp_path: Path) -> None:
    config, config_path = _fixture(tmp_path)
    manifest_path = tmp_path / config["runs"]["gray"] / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["model_revision"] = "wrong-model"
    _write_json(manifest_path, manifest)

    with pytest.raises(ValueError, match="identity mismatch"):
        queue.run_queue(config_path, root=tmp_path, once=True)


def test_unpinned_model_revision_is_rejected(tmp_path: Path) -> None:
    config, _ = _fixture(tmp_path)
    config["expected_model_revision"] = "Qwen/Qwen2.5-VL-7B-Instruct@main"

    with pytest.raises(ValueError, match="pin an exact"):
        queue.validate_config(config, tmp_path)


def test_all_exact_sources_launch_one_summary(tmp_path: Path) -> None:
    config, config_path = _fixture(tmp_path)
    _complete_sources(tmp_path, config)
    launched: list[str] = []
    summary_run = tmp_path / "experiments/runs/summary"

    result = queue.run_queue(
        config_path,
        root=tmp_path,
        once=True,
        summary_launcher=lambda path, _root: (
            launched.append(str(path)) or summary_run
        ),
    )

    state = json.loads((tmp_path / config["state_path"]).read_text(encoding="utf-8"))
    assert result == 3
    assert len(launched) == 1
    assert state["status"] == "summary_running"
    assert state["summary_run"] == "experiments/runs/summary"


def test_complete_summary_requires_all_audit_checks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, config_path = _fixture(tmp_path)
    summary_run = tmp_path / "experiments/runs/summary"
    expected_artifacts = [config["outputs"][name] for name in (
        "summary_json", "summary_markdown", "audit_json", "audit_markdown"
    )]
    _write_json(
        summary_run / "run_manifest.json",
        {
            "job_type": "m8_virl39k_7b_summary_audit",
            "node": "login",
            "gpu_ids": [],
            "expected_artifacts": expected_artifacts,
            "queue_config": str(config_path.relative_to(tmp_path)),
            "queue_config_sha256": queue._sha256(config_path),
            "status": "complete",
            "exit_code": 0,
            "artifacts_exist": True,
        },
    )
    audit = {
        "status": "pass",
        "expected_job_type": config["expected_job_type"],
        "expected_model_revision": config["expected_model_revision"],
        "row_counts": {condition: 4096 for condition in CONDITIONS},
        "recomputed_score_mismatch_count": 0,
        "checks": {"rows": True, "scores": True},
        "runs": config["runs"],
    }
    summary = {
        "status": "pass",
        "n_items": 4096,
        "evaluation_contract": {"model_revision": config["expected_model_revision"]},
    }
    _write_json(tmp_path / config["outputs"]["audit_json"], audit)
    _write_json(tmp_path / config["outputs"]["summary_json"], summary)
    (tmp_path / config["outputs"]["audit_markdown"]).write_text("audit\n")
    (tmp_path / config["outputs"]["summary_markdown"]).write_text("summary\n")
    _write_json(
        tmp_path / config["state_path"],
        {
            "schema_version": "blind-gains.m8-summary-queue-state.v1",
            "status": "summary_running",
            "summary_run": str(summary_run.relative_to(tmp_path)),
            "poll_count": 1,
            "performance_values_inspected": False,
        },
    )

    monkeypatch.chdir(tmp_path)
    assert queue.run_queue(Path("config.json"), root=tmp_path, once=True) == 0
    state = json.loads((tmp_path / config["state_path"]).read_text(encoding="utf-8"))
    assert state["status"] == "complete"
    assert state["performance_values_inspected"] is False

    audit["checks"]["scores"] = False
    _write_json(tmp_path / config["outputs"]["audit_json"], audit)
    with pytest.raises(ValueError, match="structural check"):
        queue.validate_summary_run(summary_run, config, config_path, tmp_path)


def test_summary_from_foreign_queue_config_is_rejected(tmp_path: Path) -> None:
    config, config_path = _fixture(tmp_path)
    summary_run = tmp_path / "experiments/runs/foreign-summary"
    _write_json(
        summary_run / "run_manifest.json",
        {
            "job_type": "m8_virl39k_7b_summary_audit",
            "node": "login",
            "gpu_ids": [],
            "expected_artifacts": [config["outputs"][name] for name in (
                "summary_json", "summary_markdown", "audit_json", "audit_markdown"
            )],
            "queue_config": str(config_path.relative_to(tmp_path)),
            "queue_config_sha256": "foreign-config-hash",
            "status": "running",
        },
    )

    with pytest.raises(ValueError, match="identity mismatch"):
        queue.validate_summary_run(summary_run, config, config_path, tmp_path)
