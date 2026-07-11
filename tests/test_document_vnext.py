from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.fliptrack.build_document_vnext import (
    TEMPLATE_ID,
    build_declared_batch,
    generate_document_vnext_pairs,
)


def test_document_vnext_pair_is_dense_exact_and_single_character(tmp_path: Path) -> None:
    rows = generate_document_vnext_pairs(tmp_path / "source", 2, seed=101)

    assert len(rows) == 2
    assert {row["template_id"] for row in rows} == {TEMPLATE_ID}
    for row in rows:
        assert Path(row["image_a_path"]).is_file()
        assert Path(row["image_b_path"]).is_file()
        assert Path(row["changed_region_mask_a"]).is_file()
        assert row["answer_a"] != row["answer_b"]
        assert len(row["answer_a"]) == len(row["answer_b"]) == 5
        assert sum(a != b for a, b in zip(row["answer_a"], row["answer_b"])) == 1
        verifier = row["verifier_results"]
        assert verifier["row_count"] == 18
        assert verifier["target_row_highlighted"] is False
        assert verifier["target_cell_highlighted"] is False


def test_declared_batch_refuses_non_100_pair_or_overwrite(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "schema_version": "blind-gains.document-vnext-calibration.v1",
                "n_pairs": 2,
                "seed": 1,
                "template_id": TEMPLATE_ID,
                "iteration_policy": "one shot",
                "target_7b_real_pair_accuracy": [0.5, 0.9],
                "evaluation_cells": [],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="exactly one declared 100-pair batch"):
        build_declared_batch(
            config_path=config,
            out_dir=tmp_path / "source",
            manifest_path=tmp_path / "manifest.jsonl",
            contact_sheet_dir=tmp_path / "contacts",
            metadata_path=tmp_path / "metadata.json",
        )
