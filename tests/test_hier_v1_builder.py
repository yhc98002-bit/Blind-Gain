"""I10 fixtures for the hier_v1 mother-item builders (P1.1; registration §2 +
Amendments A1/A2). Each registered verifier obligation has a fixture the
violating behavior fails: the cue ink rule (a), per-layer gold recompute and
question naming (b), L2/L3 byte-identity (c), cross-layer matching (d), and
the A2 layer × role matrix. The pre-P1.1 state fails all of these trivially
(no implementation existed); the corruption cases below protect against the
cue-ladder failure class going forward.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import pytest
from PIL import ImageDraw

import scripts.build_hier_dev_batch as builder
from scripts.hier_v1_lib import (
    COORD_ALLOWED,
    CHART_ALLOWED,
    EXTREMUM_KINDS,
    build_chart_geometry,
    build_coord_geometry,
    coord_extremum,
    cue_ink_disjoint,
    crossing_fraction,
    hier_palette_report,
    render_coord_layers,
    render_chart_layers,
)


def _rng(seed: int = 7) -> random.Random:
    return random.Random(seed)


def _coord_geometry(role: str, kind: str = "largest_y", n: int = 8,
                    max_tries: int = 500):
    for seed in range(max_tries):
        geometry = build_coord_geometry(role, kind, n, _rng(seed))
        if geometry is not None:
            return geometry
    raise AssertionError(f"no {role} geometry found in {max_tries} tries")


def test_coord_switch_changes_target_and_answer() -> None:
    geometry = _coord_geometry("target_switch")
    assert geometry["target_a"] != geometry["target_b"]
    assert geometry["answer_a"] != geometry["answer_b"]
    # side B's recorded target really is side B's extremum
    target_b, gap_b = coord_extremum(geometry["points_b"], geometry["extremum_kind"])
    assert target_b == geometry["target_b"] and gap_b >= 1


def test_coord_stable_keeps_target_moves_answer() -> None:
    geometry = _coord_geometry("target_stable")
    assert geometry["target_a"] == geometry["target_b"]
    assert geometry["answer_a"] != geometry["answer_b"]
    target_b, gap_b = coord_extremum(geometry["points_b"], geometry["extremum_kind"])
    assert target_b == geometry["target_a"] and gap_b >= 1


def test_coord_invariance_preserves_answer_and_target() -> None:
    geometry = _coord_geometry("invariance")
    assert geometry["target_a"] == geometry["target_b"]
    assert geometry["answer_a"] == geometry["answer_b"]
    assert geometry["moved_label"] != geometry["target_a"]
    assert geometry["points_a"] != geometry["points_b"]


def test_coord_gold_recomputes_from_scene_per_layer() -> None:
    """Obligation (b): the recorded answer equals the read-axis coordinate of
    the extremum recomputed from the serialized scene — per side."""
    geometry = _coord_geometry("target_stable")
    kind = geometry["extremum_kind"]
    read = EXTREMUM_KINDS[kind]["read"]
    for side in ("a", "b"):
        points = geometry[f"points_{side}"]
        target, _ = coord_extremum(points, kind)
        assert str(points[target][read]) == geometry[f"answer_{side}"]
    # L2 question names the target entity
    assert f"point {geometry['target_a']}" in geometry["questions"]["l2"]


def test_cue_ink_rule_holds_and_detects_violation() -> None:
    """Obligation (a): the shipped cue passes the allowed-color rule; a cue
    drawn over existing ink (the cue-ladder occlusion mistake) is detected."""
    geometry = _coord_geometry("target_stable")
    layers = None
    for seed in range(200):
        candidate = build_coord_geometry("target_stable", geometry["extremum_kind"],
                                         8, _rng(seed))
        if candidate is None:
            continue
        layers = render_coord_layers(candidate["points_a"], candidate["target_a"])
        if layers is not None:
            geometry = candidate
            break
    assert layers is not None, "no legal cue placement found in 200 scenes"
    base, l1, record = layers
    assert record["cue_ink_disjoint"] and record["cue_pixel_count"] > 0
    assert cue_ink_disjoint(base, l1, COORD_ALLOWED)

    # adversarial: paint a "cue" straight across the target point (occluding)
    from scripts.hier_v1_lib import coord_target_px
    bad = base.copy()
    tx, ty = coord_target_px(geometry["points_a"], geometry["target_a"])
    ImageDraw.Draw(bad).line((tx - 30, ty, tx + 30, ty), fill=(196, 30, 58), width=3)
    assert not cue_ink_disjoint(base, bad, COORD_ALLOWED)

    # an "L1" identical to L2 (unrendered variant, the cue-ladder v07 bug)
    assert not cue_ink_disjoint(base, base.copy(), COORD_ALLOWED)


def test_chart_roles_and_crossing_bands() -> None:
    for role in ("target_switch", "target_stable", "invariance"):
        geometry = None
        for seed in range(2000):
            geometry = build_chart_geometry(role, 5, "low", _rng(seed))
            if geometry is not None:
                break
        assert geometry is not None, f"no chart {role} geometry found"
        xa, xr = geometry["xa"] - 1, geometry["xr"] - 1
        assert xa != xr
        if role == "target_switch":
            assert geometry["target_a"] != geometry["target_b"]
            assert geometry["answer_a"] != geometry["answer_b"]
        elif role == "target_stable":
            assert geometry["target_a"] == geometry["target_b"]
            assert geometry["answer_a"] != geometry["answer_b"]
        else:
            assert geometry["answer_a"] == geometry["answer_b"]
        # gold recompute from serialized values, both sides
        for side in ("a", "b"):
            values = geometry[f"values_{side}"]
            target = geometry[f"target_{side}"]
            assert str(values[target][xr]) == geometry[f"answer_{side}"]
        assert 0.0 <= geometry["crossing_fraction_a"] <= 0.25


def test_nine_series_palette_is_recorded_and_separated() -> None:
    report = hier_palette_report()
    assert set(report) == {"normal", "protanopia", "deuteranopia", "tritanopia"}
    assert report["normal"] > 10, report  # dual coding carries the rest


def test_smoke_build_respects_a2_matrix_and_c_d(tmp_path, monkeypatch) -> None:
    """End-to-end smoke cell: A2 layer × role matrix; (c) L2/L3 byte-identity;
    (d) answers/negatives identical across a mother's layers."""
    monkeypatch.setattr(builder, "PER_ROLE", 2)
    result = builder.build_family_cell(
        "hier_coord_v1", "n8", {"n_points": 8}, tmp_path)
    rows = result["rows_by_layer"]
    assert len(rows["l3"]) == 6 and len(rows["probe"]) == 6
    assert len(rows["l2"]) == 4 and len(rows["l1"]) == 4  # stable+invariance only
    switch_mothers = {r["mother_item_id"] for r in rows["l3"]
                      if r["role"] == "target_switch"}
    assert all(r["mother_item_id"] not in switch_mothers
               for layer in ("l2", "l1") for r in rows[layer])
    by_mother: dict[str, list[dict]] = {}
    for layer in ("l3", "l2", "l1"):
        for row in rows[layer]:
            by_mother.setdefault(row["mother_item_id"], []).append(row)
    for mother_rows in by_mother.values():
        answers = {(r["answer_a"], r["answer_b"]) for r in mother_rows}
        negatives = {json.dumps(r["hard_negatives"], sort_keys=True)
                     for r in mother_rows}
        scenes = {json.dumps([r["scene_a"], r["scene_b"]], sort_keys=True, default=str)
                  for r in mother_rows}
        assert len(answers) == 1 and len(negatives) == 1 and len(scenes) == 1
        by_layer = {r["layer"]: r for r in mother_rows}
        if "l2" in by_layer:
            assert by_layer["l2"]["image_a_sha256"] == by_layer["l3"]["image_a_sha256"]
            assert by_layer["l2"]["image_b_sha256"] == by_layer["l3"]["image_b_sha256"]
            assert by_layer["l1"]["image_a_sha256"] != by_layer["l3"]["image_a_sha256"]
    for row in rows["probe"]:
        if row["role"] == "target_switch":
            assert row["answer_a"] != row["answer_b"]
        else:
            assert row["answer_a"] == row["answer_b"]
