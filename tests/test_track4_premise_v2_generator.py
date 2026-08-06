"""Planted fixtures for the Track-4 premise-construct v2 generator (I10).

Registered in docs/registered_track4_premise_v2_design_v1.md. Every gold is
verified by RECOMPUTATION from the stored scene program, never by trusting a
builder field. Four load-bearing properties:

  * a planted premise_transition pair whose premise golds differ and are both
    recoverable from the scene points, on both semantic and physical sides;
  * the constraint INVERSION versus frozen B1: the transition pair violates
    B1's stay-nearest filter (dist(T, N') < d2 - 0.5), so the frozen builder
    could never emit it -- and P0.1's invariance-measuring "transition" metric
    credits a premise-frozen prediction that the redefined metric rejects
    (the adversarial fixture the old code/metric fails, I10);
  * a planted easy-variant scene proving the difficulty lever (n_points) is
    what actually changed: 8 points in the dict, and the frozen renderer's
    output depends on exactly the points passed, everything else held fixed;
  * cross-version refusal on a REAL generated group, not only synthetic ones.
"""
from __future__ import annotations

import math
import random

import numpy as np
import pytest

from scripts.build_track4_premise_v2_dev_batch import (
    MARGIN_A,
    MARGIN_B,
    MARGIN_D3,
    attempt_seed,
    build_group_geometry,
    build_invariance_geometry,
    materialize_group,
    split_of,
)
from src.fliptrack.build_v02 import (
    _answers_distinguishable,
    _exact_change_mask,
    _render_high_entropy_coordinate_register,
)
from src.train.intervention_group_schema import (
    InterventionGroupSchemaError,
    validate_group,
    validate_group_v2,
)


def first_geometry(intervention: str, limit: int = 60000):
    """Deterministically find the first accepted geometry for a type, using the
    builder's own attempt-indexed seeding (so the fixture is stable)."""
    for attempt in range(1, limit):
        rng = random.Random(attempt_seed(intervention, attempt))
        geometry = build_group_geometry(intervention, rng)
        if geometry is not None:
            return geometry
    raise AssertionError(f"no {intervention} geometry accepted in {limit} attempts")


def ranked(points: dict[str, tuple[int, int]], target: str):
    """Independent nearest-neighbour recomputation (not the builder's helper)."""
    tx, ty = points[target]
    return sorted(
        (math.hypot(px - tx, py - ty), label)
        for label, (px, py) in points.items()
        if label != target
    )


# ------------------------------------------------- planted premise-transition


def test_planted_transition_premise_golds_differ_and_recompute():
    g = first_geometry("premise_transition")
    p = g["premise"]
    assert p["transition"] is True
    assert p["answer_a"] != p["answer_b"]

    ra = ranked(g["points_a"], g["target"])
    rb = ranked(g["points_b"], g["target"])
    # premise golds recomputed from the scene programs alone
    assert ra[0][1] == p["answer_a"]
    assert rb[0][1] == p["answer_b"]
    # A-side premise is the runner-up on the B side: the runner-up became nearest
    assert ra[1][1] == p["answer_b"]
    # decidability margins on both sides, mirroring each other
    assert ra[1][0] - ra[0][0] >= MARGIN_A - 1e-9
    assert rb[1][0] - rb[0][0] >= MARGIN_B - 1e-9
    # the pre-move runner-up gap that guarantees the B-side margin
    assert ra[2][0] - ra[1][0] >= MARGIN_D3 - 1e-9
    # final golds are the x-coordinates of the respective nearest points
    assert g["gold_a"] == str(g["points_a"][p["answer_a"]][0])
    assert g["gold_b"] == str(g["points_b"][p["answer_b"]][0])
    # the new nearest point (runner-up) did NOT move: the answer change is
    # carried entirely by the premise change
    assert g["points_a"][p["answer_b"]] == g["points_b"][p["answer_b"]]
    # distinguishability guards under the frozen lenient matcher
    assert _answers_distinguishable(g["gold_a"], g["gold_b"])
    assert _answers_distinguishable(p["answer_a"], p["answer_b"])


def test_transition_violates_frozen_b1_invariance_filter():
    """The constraint inversion is geometric: the moved point lands on the far
    side of the d2 boundary with margin, where B1's chained_premise candidate
    filter (dist < d2 - 0.5) could never have produced it."""
    g = first_geometry("premise_transition")
    tx, ty = g["points_a"][g["target"]]
    moved = g["moved_label"]
    assert moved == g["premise"]["answer_a"]  # the old nearest point is what moved
    d2 = ranked(g["points_a"], g["target"])[1][0]
    nx, ny = g["points_b"][moved]
    d_new = math.hypot(nx - tx, ny - ty)
    assert d_new >= d2 + MARGIN_B - 1e-9      # v2 transition constraint
    assert not (d_new < d2 - 0.5)             # B1's invariance constraint fails


def test_old_transition_metric_misreads_transitions():
    """P0.1's premise_transition_accuracy credits producing the SAME premise on
    both members against a single shared gold. On a genuine transition item that
    is exactly backwards. The redefined metric requires each member's premise to
    match ITS OWN gold, with the golds differing by construction."""

    def old_credit(pred_a: str, pred_b: str, shared_gold: str) -> int:
        same = pred_a.strip().lower() == pred_b.strip().lower()
        both = (pred_a.strip().lower() == shared_gold.strip().lower()
                and pred_b.strip().lower() == shared_gold.strip().lower())
        return int(same and both)

    def new_credit(pred_a: str, pred_b: str, gold_a: str, gold_b: str) -> int:
        return int(pred_a.strip().lower() == gold_a.strip().lower()
                   and pred_b.strip().lower() == gold_b.strip().lower()
                   and gold_a.strip().lower() != gold_b.strip().lower())

    g = first_geometry("premise_transition")
    ga, gb = g["premise"]["answer_a"], g["premise"]["answer_b"]

    # premise-frozen policy: repeats the A-side premise on both members
    assert old_credit(ga, ga, ga) == 1        # old metric rewards it
    assert new_credit(ga, ga, ga, gb) == 0    # redefined metric rejects it

    # genuinely tracking policy: premise changes as constructed
    assert old_credit(ga, gb, ga) == 0        # old metric scores it zero
    assert new_credit(ga, gb, ga, gb) == 1    # redefined metric rewards it


# ---------------------------------------------- materialized group round-trip


def test_materialized_transition_group_verifiable_and_v1_refused(tmp_path):
    g = first_geometry("premise_transition")
    invariance = build_invariance_geometry(g, random.Random(7), prefer_style_twin=True)
    result = materialize_group(out_dir=tmp_path, geometry=g,
                               invariance=invariance, rng=random.Random(11))

    row = result["causal_row"]
    assert row["premise_transition"] is True
    assert row["premise_answer_a"] != row["premise_answer_b"]
    # physical sides: recompute each premise gold from the serialized scene
    for side in ("a", "b"):
        points = {label: (x, y) for label, x, y in row[f"scene_points_{side}"]}
        r = ranked(points, g["target"])
        assert r[0][1] == row[f"premise_answer_{side}"]
        assert row[f"answer_{side}"] == str(points[r[0][1]][0])

    group = result["group"]
    assert group["original"]["premise_answer"] == g["premise"]["answer_a"]
    causal = [m for m in group["members"] if m["kind"] == "causal"][0]
    assert causal["premise_transition"] is True
    assert causal["premise_answer"] == g["premise"]["answer_b"]

    # the mismatched control receives its donor image in the cross-group pass;
    # stand one in so the structural rules can be exercised here
    for m in group["members"]:
        if m.get("condition") == "mismatched_real":
            m["image_path"] = "donor.png"
            m["image_sha256"] = "d0"
        if m.get("condition") == "gray":
            m["image_path"] = "gray.png"
            m["image_sha256"] = "g0"
    assert validate_group_v2(group)["intervention_type"] == "premise_transition"
    with pytest.raises(InterventionGroupSchemaError,
                       match="refuses groups of an unknown version"):
        validate_group(group)  # the frozen v1 loader refuses real v2 output


# --------------------------------------------------- planted easier variant


def test_planted_easy_variant_lever_is_point_count():
    g8 = first_geometry("chained_premise_easy")
    assert g8["n_points"] == 8
    assert len(g8["points_a"]) == len(g8["labels"]) == 8
    assert len(g8["points_b"]) == 8
    g20 = first_geometry("chained_premise")
    assert g20["n_points"] == len(g20["points_a"]) == 20

    # the chained (stay-nearest) construction is preserved at n=8
    p = g8["premise"]
    assert p["transition"] is False and p["answer_a"] == p["answer_b"]
    assert ranked(g8["points_a"], g8["target"])[0][1] == p["answer_a"]
    assert ranked(g8["points_b"], g8["target"])[0][1] == p["answer_a"]

    # the frozen renderer draws exactly the points it is given, on the same
    # canvas with the same fonts -- so point count is a real render-level lever
    img8 = _render_high_entropy_coordinate_register(g8["points_a"])
    dropped = {l: pt for l, pt in g8["points_a"].items()
               if l != next(l for l in g8["labels"] if l != g8["target"])}
    img7 = _render_high_entropy_coordinate_register(dropped)
    assert img8.size == img7.size == (1400, 1240)
    assert np.any(np.asarray(_exact_change_mask(img8, img7)))


# --------------------------------------------------------- split enforcement


def test_accepted_geometries_are_development_bucket_only():
    for intervention in ("premise_transition", "chained_premise_easy"):
        g = first_geometry(intervention)
        assert split_of(g["scene_program_id"]) == "development"


def test_split_rule_is_deterministic_and_proportioned():
    ids = [f"t4v2_{i:016x}" for i in range(3000)]
    buckets = [split_of(s) for s in ids]
    assert buckets == [split_of(s) for s in ids]  # deterministic
    frac = {b: buckets.count(b) / len(buckets)
            for b in ("training", "development", "confirmatory")}
    assert 0.55 <= frac["training"] <= 0.65
    assert 0.15 <= frac["development"] <= 0.25
    assert 0.15 <= frac["confirmatory"] <= 0.25
