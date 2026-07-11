from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.validate_vlmeval_run import validate_outputs


def _write_config(path: Path) -> None:
    path.write_text(json.dumps({"model": {"model-a": {}}, "data": {"bench-a": {}}}), encoding="utf-8")


def test_validate_outputs_requires_every_model_dataset_artifact(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    _write_config(config)
    with pytest.raises(FileNotFoundError, match="model-a_bench-a"):
        validate_outputs(config, tmp_path / "work")


def test_validate_outputs_hashes_nonempty_inference_workbook(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    _write_config(config)
    workbook = tmp_path / "work" / "model-a" / "model-a_bench-a.xlsx"
    workbook.parent.mkdir(parents=True)
    workbook.write_bytes(b"workbook fixture")
    score = workbook.with_name("model-a_bench-a_acc.csv")
    score.write_text("split,Overall\nnone,0.5\n", encoding="utf-8")
    payload = validate_outputs(config, tmp_path / "work")
    assert payload["status"] == "pass"
    assert payload["artifacts"][0]["bytes"] == len(b"workbook fixture")
    assert len(payload["artifacts"][0]["sha256"]) == 64
    assert payload["score_artifacts"][0]["path"].endswith("_acc.csv")


def test_validate_outputs_accepts_mathvista_score_artifact(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    _write_config(config)
    workbook = tmp_path / "work" / "model-a" / "model-a_bench-a.xlsx"
    workbook.parent.mkdir(parents=True)
    workbook.write_bytes(b"mathvista workbook fixture")
    score = workbook.with_name("model-a_bench-a_local-judge_score.csv")
    score.write_text("Task&Skill,acc\nOverall,0.5\n", encoding="utf-8")
    payload = validate_outputs(config, tmp_path / "work")
    assert payload["status"] == "pass"
    assert payload["score_artifacts"][0]["path"].endswith("_score.csv")


def test_validate_outputs_inference_only_still_requires_workbook(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    _write_config(config)
    workbook = tmp_path / "work" / "model-a" / "model-a_bench-a.xlsx"
    workbook.parent.mkdir(parents=True)
    workbook.write_bytes(b"inference-only workbook")
    payload = validate_outputs(config, tmp_path / "work", require_scores=False)
    assert payload["status"] == "pass"
    assert payload["require_scores"] is False
    assert payload["score_artifacts"] == []

    workbook.unlink()
    with pytest.raises(FileNotFoundError, match="model-a_bench-a"):
        validate_outputs(config, tmp_path / "work", require_scores=False)
