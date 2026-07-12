from __future__ import annotations

import json
from pathlib import Path

from scripts.finalize_pilot_step_evaluation import (
    R19_MANIFEST_SHA256,
    build_marker,
)
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    (checkpoint / "model.safetensors.index.json").write_text(
        '{"weight_map":{"x":"model.safetensors"}}\n', encoding="utf-8"
    )
    evaluation = tmp_path / "evaluation"
    evaluation.mkdir()
    (evaluation / "run_manifest.json").write_text(
        json.dumps(
            {
                "status": "complete",
                "exit_code": 0,
                "artifacts_exist": True,
                "job_type": "pilot_fliptrack_checkpoint_eval",
                "model_revision": str(checkpoint),
                "global_step": 60,
                "image_mode": "real",
                "decoding": {"temperature": 0.0, "top_p": 1.0, "n": 1},
                "max_new_tokens": 32,
                "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
                "data_manifest_hash": R19_MANIFEST_SHA256,
            }
        ),
        encoding="utf-8",
    )
    aggregate = tmp_path / "aggregate"
    aggregate.mkdir()
    (aggregate / "run_manifest.json").write_text(
        json.dumps(
            {
                "status": "complete",
                "exit_code": 0,
                "artifacts_exist": True,
                "source_run": str(evaluation),
            }
        ),
        encoding="utf-8",
    )
    (aggregate / "metrics.json").write_text('{"n_pairs":1200}\n', encoding="utf-8")
    return evaluation, aggregate, checkpoint


def test_marker_binds_exact_evaluation_aggregate_and_checkpoint(tmp_path: Path) -> None:
    evaluation, aggregate, checkpoint = _fixture(tmp_path)

    marker = build_marker(
        evaluation_run=evaluation,
        aggregate_run=aggregate,
        checkpoint_path=checkpoint,
        global_step=60,
    )

    assert marker["status"] == "complete"
    assert all(marker["checks"].values())
    assert len(marker["checkpoint_index_sha256"]) == 64
    assert len(marker["evaluation_output_sha256"]) == 64


def test_marker_rejects_aggregate_from_another_eval(tmp_path: Path) -> None:
    evaluation, aggregate, checkpoint = _fixture(tmp_path)
    aggregate_manifest = aggregate / "run_manifest.json"
    payload = json.loads(aggregate_manifest.read_text(encoding="utf-8"))
    payload["source_run"] = str(tmp_path / "different-evaluation")
    aggregate_manifest.write_text(json.dumps(payload), encoding="utf-8")

    marker = build_marker(
        evaluation_run=evaluation,
        aggregate_run=aggregate,
        checkpoint_path=checkpoint,
        global_step=60,
    )

    assert marker["status"] == "fail"
    assert not marker["checks"]["aggregate_source_run_exact"]


def test_marker_rejects_unregistered_prompt_contract(tmp_path: Path) -> None:
    evaluation, aggregate, checkpoint = _fixture(tmp_path)
    manifest = evaluation / "run_manifest.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["prompt_contract_sha256"] = "wrong"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    marker = build_marker(
        evaluation_run=evaluation,
        aggregate_run=aggregate,
        checkpoint_path=checkpoint,
        global_step=60,
    )

    assert marker["status"] == "fail"
    assert not marker["checks"]["evaluation_prompt_contract_locked"]
