from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
from PIL import Image

from src.eval.fliptrack_metrics import match_tier
from src.fliptrack.build_v02 import build, generate_parallel_pairs, write_contact_sheets


def test_v02_generators_emit_truthful_non_degenerate_pairs(tmp_path: Path) -> None:
    rows = build(tmp_path / "source", n_per_template=2, seed=41)

    assert len(rows) == 12
    assert len({row["template_id"] for row in rows}) == 6
    assert any(row["provenance"]["training_domain_alignment"] == "high" for row in rows)
    for row in rows:
        assert match_tier(row["answer_a"], row["answer_b"]) == 0
        assert match_tier(row["answer_b"], row["answer_a"]) == 0
        with Image.open(row["image_a_path"]) as image_a, Image.open(row["image_b_path"]) as image_b:
            pixels_a = np.asarray(image_a.convert("RGB"))
            pixels_b = np.asarray(image_b.convert("RGB"))
        with Image.open(row["changed_region_mask_a"]) as mask_a, Image.open(row["changed_region_mask_b"]) as mask_b:
            allowed = (np.asarray(mask_a.convert("L")) > 0) | (np.asarray(mask_b.convert("L")) > 0)
        changed = np.any(pixels_a != pixels_b, axis=2)
        assert np.any(changed)
        assert not np.any(changed & ~allowed)


def test_v02_questions_remove_known_caption_leaks(tmp_path: Path) -> None:
    rows = build(tmp_path / "source", n_per_template=1, seed=43)
    by_template = {row["template_id"]: row for row in rows}

    chart = by_template["starred_series_value_v02"]
    assert "starred series" in chart["question"].lower()
    question_words = set(re.findall(r"[a-z]+", chart["question"].lower()))
    assert question_words.isdisjoint({"blue", "red", "green", "purple"})
    grid = by_template["indexed_symbol_grid_v02"]
    assert "highlight" not in grid["question"].lower()
    assert ":" not in grid["question"]


def test_semantic_side_assignment_is_randomized(tmp_path: Path) -> None:
    rows = generate_parallel_pairs(tmp_path / "parallel", n=40, seed=53)
    swapped = sum(bool(row["provenance"]["semantic_side_assignment_swapped"]) for row in rows)
    assert 10 <= swapped <= 30


def test_contact_sheet_contains_twenty_pairs_when_available(tmp_path: Path) -> None:
    rows = build(tmp_path / "source", n_per_template=20, seed=47)
    outputs = write_contact_sheets(rows, tmp_path / "sheets", n_per_template=20)

    assert len(outputs) == 6
    for output in outputs:
        assert output.is_file()
        with Image.open(output) as sheet:
            assert sheet.size == (1880, 1250)
