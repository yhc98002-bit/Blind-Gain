"""Fixtures for the standing generator census (08-12 dispatch P0.4).

The pre-existing state fails these by construction: the 08-11 census was a
hand-built artifact with no producing script, so a new generator family could
be silently absent from review. The standing exporter is inventory-driven —
these tests plant manifests in a synthetic data root and assert that every
template-carrying variant appears automatically, that sampling stays within
variants, and that unmapped capability stages surface loudly instead of being
guessed.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.build_generator_census import (
    UNMAPPED_STAGE,
    build_census,
    render_markdown,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def _plant(data_root: Path) -> None:
    _write_jsonl(
        data_root / "fam_a" / "manifest.jsonl",
        [
            {"template_id": "coordinate_register_x", "pair_id": f"a{i}",
             "question": "q", "category": "geo", "image_a_path": "x.png",
             "image_b_path": "y.png"}
            for i in range(5)
        ]
        + [
            {"template_id": "coordinate_register_x", "intervention_type": "fact_read",
             "pair_id": f"b{i}", "question": "q2", "category": "geo",
             "image_a_path": "x.png", "image_b_path": "y.png"}
            for i in range(3)
        ],
    )
    _write_jsonl(
        data_root / "fam_b" / "manifest_causal.jsonl",
        [
            {"template_id": "mystery_new_family_v1", "pair_id": f"c{i}",
             "question": "q3", "category": "novel", "image_a_path": "z.png",
             "image_b_path": "w.png"}
            for i in range(4)
        ],
    )
    # Not a census manifest: rows carry no template_id — must be skipped.
    _write_jsonl(
        data_root / "captions.jsonl",
        [{"image_sha256": "ff", "caption": "words"} for _ in range(3)],
    )


def test_every_template_carrying_variant_appears_automatically(tmp_path: Path) -> None:
    _plant(tmp_path)
    census = build_census(tmp_path, examples_per_variant=2)

    assert census["n_families"] == 2
    assert census["n_variants"] == 3  # fam_a base + fam_a fact_read + fam_b
    assert census["manifests_without_template_id"] == 1
    variants = {row["variant"] for row in census["inventory"]}
    assert "coordinate_register_x" in variants
    assert "coordinate_register_x|fact_read" in variants
    assert "mystery_new_family_v1" in variants


def test_new_family_appears_without_any_code_change(tmp_path: Path) -> None:
    _plant(tmp_path)
    before = build_census(tmp_path, examples_per_variant=2)
    _write_jsonl(
        tmp_path / "fam_c_new" / "manifest.jsonl",
        [{"template_id": "hier_coord_v1_l3", "pair_id": "n0", "question": "q",
          "category": "hier", "image_a_path": "a.png", "image_b_path": "b.png"}],
    )
    after = build_census(tmp_path, examples_per_variant=2)

    assert after["n_families"] == before["n_families"] + 1
    added = [r for r in after["inventory"] if r["family"] == "fam_c_new"]
    assert len(added) == 1 and added[0]["template_id"] == "hier_coord_v1_l3"


def test_sampling_is_within_variant_first_n_in_manifest_order(tmp_path: Path) -> None:
    _plant(tmp_path)
    census = build_census(tmp_path, examples_per_variant=2)
    base = next(r for r in census["inventory"] if r["variant"] == "coordinate_register_x")

    assert base["n_in_benchmark"] == 5
    assert base["n_in_package"] == 2
    assert [e["pair_id"] for e in base["examples"]] == ["a0", "a1"]


def test_unmapped_capability_stage_surfaces_loudly(tmp_path: Path) -> None:
    _plant(tmp_path)
    census = build_census(tmp_path, examples_per_variant=1)
    novel = next(r for r in census["inventory"] if r["family"] == "fam_b")

    assert novel["capability_stage"] == UNMAPPED_STAGE
    assert "needs PI/doc mapping" in novel["stage_source"]
    assert census["n_unmapped_stage"] >= 1
    markdown = render_markdown(census)
    assert "variants with unmapped capability stage" in markdown
    assert "mystery_new_family_v1" in markdown
