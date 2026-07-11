from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.freeze_geo3k_pilot_subset import freeze_subset


def _jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _fixture(tmp_path: Path) -> dict[str, Path]:
    source = tmp_path / "source.jsonl"
    rows = []
    difficulty = []
    for index in range(3):
        image = tmp_path / f"{index}.png"
        image.write_bytes(b"image")
        rows.append(
            {
                "split": "train",
                "row_index": index,
                "images": [{"path": str(image), "sha256": "0" * 64}],
                "problem": "<image>Find x" if index == 0 else "<image>Find the triangle angle",
                "answer": str(index + 1),
            }
        )
        difficulty.append(
            {
                "split": "train",
                "row_index": index,
                "p_sample": index / 2,
                "greedy_correct": index == 2,
            }
        )
    rows.append(
        {
            "split": "test",
            "row_index": 0,
            "images": [],
            "problem": "test",
            "answer": "0",
        }
    )
    _jsonl(source, rows)
    base = tmp_path / "base.jsonl"
    _jsonl(base, difficulty)
    layer1 = tmp_path / "layer1.json"
    layer1.write_text(
        json.dumps({"remove_train_record_ids": ["geometry3k:train:0:image0"]}),
        encoding="utf-8",
    )
    train_test = tmp_path / "train_test.json"
    train_test.write_text(
        json.dumps(
            {
                "complete": True,
                "remove_train_record_ids": ["geometry3k:train:1:image0"],
            }
        ),
        encoding="utf-8",
    )
    return {
        "source_manifest": source,
        "layer1_filter": layer1,
        "train_test_filter": train_test,
        "base_difficulty_rows": base,
        "ids_output": tmp_path / "ids.json",
        "dataset_output": tmp_path / "dataset.jsonl",
        "summary_output": tmp_path / "summary.json",
    }


def test_freeze_subset_applies_union_and_preserves_local_image_paths(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)

    result = freeze_subset(**paths)

    assert json.loads(paths["ids_output"].read_text()) == [2]
    dataset = json.loads(paths["dataset_output"].read_text())
    assert dataset["row_index"] == 2
    assert dataset["images"] == [str(tmp_path / "2.png")]
    assert result["n_remove_union"] == 2
    assert result["n_retained"] == 1
    assert result["distribution"]["filtered"]["base_model_difficulty"]["mean_p_sample"] == 1


def test_freeze_subset_rejects_unknown_filter_ids(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    paths["layer1_filter"].write_text(
        json.dumps({"remove_train_record_ids": ["geometry3k:train:999:image0"]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unknown source IDs"):
        freeze_subset(**paths)
