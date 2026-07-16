from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from PIL import Image

from scripts.freeze_virl39k_training_subset import freeze_subset


def _fixture(tmp_path: Path) -> dict[str, Path | int]:
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    for name, color in (("a.png", "red"), ("b.png", "green"), ("c.png", "blue")):
        Image.new("RGB", (16, 12), color).save(image_dir / name)
    table = pa.Table.from_pylist(
        [
            {
                "question": "<image><image> compare",
                "answer": "\\boxed{A}",
                "PassRate_32BTrained": 0.5,
                "PassRate_7BBase": 0.25,
                "category": "chart",
                "source": "source-a",
                "qid": "multi",
                "image": ["images/a.png", "images/b.png"],
            },
            {
                "question": "read the value",
                "answer": "\\boxed{5}",
                "PassRate_32BTrained": 1.0,
                "PassRate_7BBase": 0.75,
                "category": "document",
                "source": "source-b",
                "qid": "keep",
                "image": ["images/c.png"],
            },
        ]
    )
    parquet = tmp_path / "source.parquet"
    pq.write_table(table, parquet)
    filtering = tmp_path / "filter.json"
    filtering.write_text(
        json.dumps(
            {
                "complete": True,
                "pending_layers": [],
                "n_train_records": 3,
                "remove_train_record_ids": ["virl39k:train:multi:image1"],
                "inspect_only_train_record_ids": ["virl39k:train:keep:image0"],
            }
        ),
        encoding="utf-8",
    )
    return {
        "source_parquet": parquet,
        "image_root": tmp_path,
        "filter_manifest": filtering,
        "ids_output": tmp_path / "ids.json",
        "dataset_output": tmp_path / "dataset.jsonl",
        "summary_output": tmp_path / "summary.json",
        "expected_items": 2,
        "expected_records": 3,
    }


def test_freezer_drops_whole_multi_image_item_and_retains_inspect_only(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)

    summary = freeze_subset(**paths)

    assert json.loads(Path(paths["ids_output"]).read_text()) == ["keep"]
    frozen = json.loads(Path(paths["dataset_output"]).read_text())
    assert frozen["qid"] == "keep"
    assert frozen["images"] == [str(tmp_path / "images" / "c.png")]
    assert frozen["problem"].startswith("<image>\n")
    assert summary["n_remove_records"] == 1
    assert summary["n_remove_items"] == 1
    assert summary["n_inspect_only_items_retained"] == 1
    assert summary["candidate_language"] == "conservative contamination candidates"


def test_freezer_rejects_incomplete_decontamination(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    Path(paths["filter_manifest"]).write_text(
        json.dumps({"complete": False, "pending_layers": ["ocr_text_overlap"]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="manifest is incomplete"):
        freeze_subset(**paths)


def test_freezer_rejects_unknown_record_ids(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    Path(paths["filter_manifest"]).write_text(
        json.dumps(
            {
                "complete": True,
                "pending_layers": [],
                "n_train_records": 3,
                "remove_train_record_ids": ["virl39k:train:unknown:image0"],
                "inspect_only_train_record_ids": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unknown record IDs"):
        freeze_subset(**paths)
