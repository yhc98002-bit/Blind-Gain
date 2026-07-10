from __future__ import annotations

import io
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from PIL import Image

from src.data.mmk12_loader import discover_parquet, iter_examples, scan_dataset, write_contact_sheet


def _image_bytes(color: str) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (12, 8), color).save(buffer, format="PNG")
    return buffer.getvalue()


def test_mmk12_streaming_loader_scans_embedded_images(tmp_path: Path) -> None:
    parquet_dir = tmp_path / "data"
    parquet_dir.mkdir()
    table = pa.Table.from_pylist(
        [
            {
                "id": "train-1",
                "question": "<image> value?",
                "answer": "12",
                "subject": "math",
                "image": {"bytes": _image_bytes("red"), "path": None},
            },
            {
                "id": "train-2",
                "question": "<image> option?",
                "answer": "B",
                "subject": "physics",
                "image": {"bytes": _image_bytes("blue"), "path": None},
            },
        ]
    )
    pq.write_table(table, parquet_dir / "train-00000-of-00001.parquet")
    paths = discover_parquet(parquet_dir)
    examples = list(iter_examples(paths, batch_size=1))
    stats, selected = scan_dataset(examples, sample_size=2)
    assert len(examples) == 2
    assert stats["missing_image_rate"] == 0.0
    assert stats["answer_type_counts"] == {"multiple_choice": 1, "numeric": 1}
    assert stats["subject_counts"] == {"math": 1, "physics": 1}
    output = tmp_path / "sheet.png"
    write_contact_sheet(selected, output)
    assert output.is_file()


def test_mmk12_loader_rejects_duplicate_ids(tmp_path: Path) -> None:
    example = {
        "id": "duplicate",
        "question": "q",
        "answer": "1",
        "subject": "math",
        "split": "train",
        "image_bytes": _image_bytes("white"),
        "image_path": None,
    }
    try:
        scan_dataset([example, dict(example)])
    except ValueError as error:
        assert "duplicate MMK12 id" in str(error)
    else:
        raise AssertionError("duplicate ID was accepted")
