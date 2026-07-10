from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
from PIL import Image

from src.eval.fliptrack_metrics import match_tier
from src.fliptrack.build_v02 import (
    build,
    generate_coordinate_point_pairs,
    generate_coordinate_register_eight_point_pairs,
    generate_coordinate_register_legible_pairs,
    generate_coordinate_register_pairs,
    generate_header_table_pairs,
    generate_parallel_pairs,
    write_contact_sheets,
)


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


def test_experimental_coordinate_and_document_pairs_are_truthful(tmp_path: Path) -> None:
    rows = generate_coordinate_point_pairs(tmp_path / "points", n=2, seed=59)
    rows += generate_header_table_pairs(tmp_path / "docs", n=2, seed=61)
    assert {row["template_id"] for row in rows} == {"coordinate_point_read_v02", "header_cued_table_code_v02"}
    for row in rows:
        with Image.open(row["image_a_path"]) as image_a, Image.open(row["image_b_path"]) as image_b:
            changed = np.any(np.asarray(image_a.convert("RGB")) != np.asarray(image_b.convert("RGB")), axis=2)
        with Image.open(row["changed_region_mask_a"]) as mask:
            allowed = np.asarray(mask.convert("L")) > 0
        assert np.any(changed)
        assert not np.any(changed & ~allowed)


def test_build_can_select_experimental_families_without_changing_defaults(tmp_path: Path) -> None:
    rows = build(
        tmp_path / "selected",
        n_per_template=2,
        seed=67,
        families={"coordinate_point", "header_table"},
    )

    assert len(rows) == 4
    assert {row["template_id"] for row in rows} == {
        "coordinate_point_read_v02",
        "header_cued_table_code_v02",
    }


def test_random_target_coordinate_register_is_truthful_and_varies_query_label(tmp_path: Path) -> None:
    rows = generate_coordinate_register_pairs(tmp_path / "register", n=8, seed=71)
    labels = {row["verifier_results"]["target_label"] for row in rows}
    assert len(labels) >= 5
    for row in rows:
        assert row["verifier_results"]["point_count"] == 12
        assert row["verifier_results"]["target_label"] in row["question"]
        with Image.open(row["image_a_path"]) as image_a, Image.open(row["image_b_path"]) as image_b:
            changed = np.any(np.asarray(image_a.convert("RGB")) != np.asarray(image_b.convert("RGB")), axis=2)
        with Image.open(row["changed_region_mask_a"]) as mask:
            allowed = np.asarray(mask.convert("L")) > 0
        assert np.any(changed)
        assert not np.any(changed & ~allowed)


def test_r6_coordinate_register_changes_only_declared_legibility(tmp_path: Path) -> None:
    rows = generate_coordinate_register_legible_pairs(tmp_path / "register-r6", n=2, seed=73)
    assert {row["template_id"] for row in rows} == {"coordinate_register_random_target_v02"}
    for row in rows:
        assert row["provenance"]["render_variant"] == "legibility_r6_scale70_radius10_label18"
        assert row["verifier_results"]["point_count"] == 12
        assert row["verifier_results"]["render_scale"] == 70
        assert row["verifier_results"]["point_radius"] == 10
        assert row["verifier_results"]["label_size"] == 18


def test_r7_eight_point_register_is_a_distinct_geometry_template(tmp_path: Path) -> None:
    rows = generate_coordinate_register_eight_point_pairs(tmp_path / "register-r7", n=3, seed=79)
    assert {row["template_id"] for row in rows} == {"coordinate_register_eight_point_v02"}
    for row in rows:
        assert row["verifier_results"]["point_count"] == 8
        assert row["provenance"]["render_variant"] == "eight_point_r7_scale72_radius11_label19"
        assert row["verifier_results"]["target_label"] in row["question"]


def test_contact_sheet_contains_twenty_pairs_when_available(tmp_path: Path) -> None:
    rows = build(tmp_path / "source", n_per_template=20, seed=47)
    outputs = write_contact_sheets(rows, tmp_path / "sheets", n_per_template=20)

    assert len(outputs) == 6
    for output in outputs:
        assert output.is_file()
        with Image.open(output) as sheet:
            assert sheet.size == (1880, 1250)
