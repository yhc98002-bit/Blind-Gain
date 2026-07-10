from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from PIL import Image

from src.data.virl39k_loader import answer_type, dataset_stats, load_rows, write_contact_sheet


def test_manual_virl39k_loader_resolves_images_and_reports_missing(tmp_path: Path) -> None:
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    Image.new("RGB", (12, 8), "red").save(image_dir / "present.png")
    table = pa.Table.from_pylist(
        [
            {
                "question": "<image> choose",
                "answer": "\\boxed{A}",
                "PassRate_32BTrained": 1.0,
                "PassRate_7BBase": 0.5,
                "category": "geometry",
                "source": "fixture",
                "qid": "q1",
                "image": ["images/present.png"],
            },
            {
                "question": "<image> calculate",
                "answer": "\\boxed{12}",
                "PassRate_32BTrained": 0.5,
                "PassRate_7BBase": -1.0,
                "category": "math",
                "source": "fixture",
                "qid": "q2",
                "image": ["images/missing.png"],
            },
        ]
    )
    parquet = tmp_path / "rows.parquet"
    pq.write_table(table, parquet)
    rows = load_rows(parquet, tmp_path)
    stats = dataset_stats(rows)
    assert len(rows) == 2
    assert stats["n_image_references"] == 2
    assert stats["missing_image_rate"] == 0.5
    assert stats["answer_type_counts"] == {"multiple_choice": 1, "numeric": 1}
    output = tmp_path / "sheet.png"
    write_contact_sheet(rows, output)
    assert output.is_file()


def test_answer_type_preserves_nontrivial_expressions() -> None:
    assert answer_type("\\boxed{A}") == "multiple_choice"
    assert answer_type("\\boxed{-3/4}") == "numeric"
    assert answer_type("\\boxed{x=2}") == "text_or_expression"
