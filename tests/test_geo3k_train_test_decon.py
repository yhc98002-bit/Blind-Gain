from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from scripts.build_geo3k_train_test_decon import build_records


def test_train_test_builder_preserves_split_identity_and_refuses_overwrite(tmp_path: Path) -> None:
    rows = []
    for split, index, color in (("train", 0, "red"), ("test", 0, "blue")):
        image = tmp_path / f"{split}.png"
        Image.new("RGB", (12, 8), color).save(image)
        import hashlib

        rows.append(
            {
                "split": split,
                "row_index": index,
                "problem": "<image>Find x.",
                "answer": "1",
                "images": [
                    {"path": str(image), "sha256": hashlib.sha256(image.read_bytes()).hexdigest()}
                ],
            }
        )
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    train = tmp_path / "train.jsonl"
    test = tmp_path / "test.jsonl"
    summary = tmp_path / "summary.json"

    payload = build_records(manifest, train, test, summary)

    assert payload["record_ids_disjoint"] is True
    assert payload["n_train_records"] == payload["n_test_records"] == 1
    assert json.loads(train.read_text(encoding="utf-8"))["record_id"] == "geometry3k:train:0:image0"
    assert json.loads(test.read_text(encoding="utf-8"))["record_id"] == "geometry3k:test:0:image0"
    try:
        build_records(manifest, train, test, summary)
    except FileExistsError:
        pass
    else:
        raise AssertionError("builder overwrote a frozen record artifact")
