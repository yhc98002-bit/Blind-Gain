from __future__ import annotations

from pathlib import Path

from PIL import Image

from src.data.geometry3k_export import export_rows


def test_export_rows_keeps_manifest_outside_image_tree_and_hashes_content(tmp_path: Path) -> None:
    image = Image.new("RGB", (16, 12), "red")
    rows = [
        {"images": [image], "problem": "<image>Find x.", "answer": "3"},
        {"images": [image.copy()], "problem": "<image>Find y.", "answer": "4"},
    ]
    output_dir = tmp_path / "images"
    output_dir.mkdir()
    records = export_rows(rows, "train", output_dir)
    assert len(records) == 2
    assert records[0]["images"][0]["sha256"] == records[1]["images"][0]["sha256"]
    assert all(Path(record["images"][0]["path"]).is_file() for record in records)
    assert not any(path.suffix == ".jsonl" for path in output_dir.rglob("*"))
