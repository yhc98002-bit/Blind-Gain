#!/usr/bin/env python3
"""Track-4 premise-construct v2 — development batch builder (Paper 2, branch-2
response). Registered in docs/registered_track4_premise_v2_design_v1.md.

Successor to scripts/build_b1_geometry_track_prototype.py. The B1 builder and
its 100-pair corpus are FROZEN (declared batch); this script never touches
them. It imports B1's helpers read-only and adds:

  premise_transition        the genuinely premise-changing item type. B1's
                            chained_premise bakes premise INVARIANCE into its
                            candidate filter (moved nearest neighbour stays
                            nearest: dist(T, N') < d2 - 0.5). The transition
                            type inverts the constraint: the nearest neighbour
                            N is pushed BEYOND the runner-up M with margin
                            (dist(T, N') >= d2 + 1.0), and the runner-up gap
                            d3 - d2 >= 1.0 gives the B-side premise the same
                            ambiguity margin the A-side has (d2 - d1 >= 1.0).
  *_easy variants           n_points 8 instead of 20 — the one difficulty
                            lever the frozen renderer already parameterizes
                            (it draws whatever point dict it is given; font
                            and spacing are hardcoded).
  intervention groups (v2)  one group per scene program: original + causal +
                            invariance + no_image/gray/mismatched_real
                            controls, per-member premise golds, pending
                            blind-solvability, schema
                            blind-gains.intervention-group.v2.

Development-split enforcement: every scene program is hashed into a split
bucket (training [0,60) / development [60,80) / confirmatory [80,100)); this
builder REJECTS any scene outside the development bucket, so no program
generated here can ever collide with a training or confirmatory program.

One-shot declared batch: 160 groups, no acceptance iteration. CPU only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image

from scripts.build_b1_geometry_track_prototype import (
    _save_b1_pair,
    base_scene,
    flip_targets,
    hard_negatives,
    render_style_variant,
    spacing_ok,
)
from src.fliptrack.build_v02 import (
    _answers_distinguishable,
    _render_high_entropy_coordinate_register,
)
from src.train.intervention_group_schema import SCHEMA_VERSION_V2, validate_batch_v2

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
BATCH_SEED = 20260806

TEMPLATE_FAMILY = "t4v2_coordinate_register"
TEMPLATES = {20: "t4v2_coordinate_register_n20_v1", 8: "t4v2_coordinate_register_n8_v1"}

COUNTS = {
    "premise_transition": 40,
    "premise_transition_easy": 40,
    "chained_premise_easy": 40,
    "chained_premise": 20,
    "fact_read": 20,
}
N_POINTS = {
    "premise_transition": 20,
    "premise_transition_easy": 8,
    "chained_premise_easy": 8,
    "chained_premise": 20,
    "fact_read": 20,
}

MARGIN_A = 1.0            # A-side premise decidability: d2 - d1 >= 1.0 (B1's value)
MARGIN_B = 1.0            # transition push-beyond margin AND B-side decidability
MARGIN_D3 = 1.0           # transition: d3 - d2 >= 1.0 so the new runner-up is far
CHAINED_STAY_MARGIN = 0.5  # frozen from B1: moved N stays nearest by dist < d2 - 0.5

SPLIT_BUCKETS = {"training": (0, 60), "development": (60, 80), "confirmatory": (80, 100)}


def scene_program_id(points: dict[str, tuple[int, int]]) -> str:
    payload = json.dumps(sorted(points.items()), sort_keys=True, default=str)
    return "t4v2_" + hashlib.sha256(("t4v2|" + payload).encode()).hexdigest()[:16]


def split_of(spid: str) -> str:
    bucket = int(hashlib.sha256((spid + "|split-v1").encode()).hexdigest()[:8], 16) % 100
    for name, (lo, hi) in SPLIT_BUCKETS.items():
        if lo <= bucket < hi:
            return name
    raise AssertionError(bucket)


def attempt_seed(intervention: str, attempt: int) -> int:
    return int(hashlib.sha256(f"{BATCH_SEED}|{intervention}|{attempt}".encode()).hexdigest()[:12], 16)


def ranked_neighbors(points: dict[str, tuple[int, int]], target: str) -> list[tuple[float, str]]:
    tp = points[target]
    return sorted(
        (math.hypot(p[0] - tp[0], p[1] - tp[1]), label)
        for label, p in points.items()
        if label != target
    )


def serialize_points(points: dict[str, tuple[int, int]]) -> list[list[Any]]:
    return [[label, p[0], p[1]] for label, p in sorted(points.items())]


def build_group_geometry(intervention: str, rng: random.Random) -> dict[str, Any] | None:
    """Pure geometry for one group. Returns None on any constraint rejection.

    All premise/answer golds returned here are verifiable by recomputing
    nearest-neighbour structure from points_a / points_b alone — the fixtures
    in tests/test_track4_premise_v2_generator.py do exactly that.
    """
    n = N_POINTS[intervention]
    labels, points_a = base_scene(rng, n)
    spid = scene_program_id(points_a)
    if split_of(spid) != "development":
        return None  # dev-batch builder accepts only development-bucket programs
    core = intervention[:-5] if intervention.endswith("_easy") else intervention

    geometry: dict[str, Any] = {
        "intervention": intervention,
        "core": core,
        "n_points": n,
        "scene_program_id": spid,
        "labels": labels,
        "points_a": points_a,
    }

    if core == "fact_read":
        flip = flip_targets(points_a, rng)
        if flip is None:
            return None
        target, new_point = flip
        points_b = dict(points_a)
        points_b[target] = new_point
        geometry.update(
            target=target,
            points_b=points_b,
            question=f"What is the x-coordinate of point {target}?",
            gold_a=str(points_a[target][0]),
            gold_b=str(new_point[0]),
            premise=None,
        )
        return geometry

    target = rng.choice(labels)
    ranked = ranked_neighbors(points_a, target)
    (d1, nn_label), (d2, runner_up) = ranked[0], ranked[1]
    if d2 - d1 < MARGIN_A:
        return None
    nn_point = points_a[nn_label]
    tp = points_a[target]
    others = {p for l, p in points_a.items() if l != nn_label}
    question = (
        f"Consider the point nearest to point {target}. "
        "What is the x-coordinate of that nearest point?"
    )
    premise_question = f"Which labeled point is nearest to point {target}?"

    if core == "chained_premise":
        # B1's frozen construction: the moved nearest neighbour STAYS nearest.
        candidates = [
            (x, nn_point[1])
            for x in range(-7, 8)
            if x != 0
            and abs(x - nn_point[0]) >= 3
            and _answers_distinguishable(str(nn_point[0]), str(x))
            and spacing_ok((x, nn_point[1]), others)
            and math.hypot(x - tp[0], nn_point[1] - tp[1]) < d2 - CHAINED_STAY_MARGIN
        ]
        if not candidates:
            return None
        new_nn = candidates[rng.randrange(len(candidates))]
        points_b = dict(points_a)
        points_b[nn_label] = new_nn
        rb = ranked_neighbors(points_b, target)
        if rb[0][1] != nn_label:  # belt-and-braces (redundant by construction)
            return None
        gold_a, gold_b = str(nn_point[0]), str(new_nn[0])
        if not _answers_distinguishable(gold_a, gold_b):
            return None
        geometry.update(
            target=target,
            points_b=points_b,
            question=question,
            gold_a=gold_a,
            gold_b=gold_b,
            premise={
                "question": premise_question,
                "answer_a": nn_label,
                "answer_b": nn_label,
                "transition": False,
                "margin_a": d2 - d1,
                "margin_b": rb[1][0] - rb[0][0],
                "hard_negative_labels": sorted({runner_up, ranked[2][1]} - {nn_label}) if len(ranked) > 2 else [runner_up],
            },
            moved_label=nn_label,
        )
        return geometry

    if core != "premise_transition":
        raise AssertionError(f"unknown intervention {intervention}")

    # premise_transition: INVERTED constraint — push N beyond the runner-up M.
    if len(ranked) < 3:
        return None
    d3 = ranked[2][0]
    if d3 - d2 < MARGIN_D3:
        return None  # B-side premise would be ambiguous between M and the third point
    ru_point = points_a[runner_up]
    gold_a, gold_b = str(nn_point[0]), str(ru_point[0])
    if not _answers_distinguishable(gold_a, gold_b):
        return None  # final-answer distinguishability guard (answers come from two
        # DIFFERENT points here, so B1's moved-point delta guard does not apply)
    if not _answers_distinguishable(nn_label, runner_up):
        return None  # premise golds must be distinguishable as answers
    candidates = [
        (x, nn_point[1])
        for x in range(-7, 8)
        if x != 0
        and abs(x - nn_point[0]) >= 3
        and spacing_ok((x, nn_point[1]), others)
        and math.hypot(x - tp[0], nn_point[1] - tp[1]) >= d2 + MARGIN_B
    ]
    if not candidates:
        return None
    new_nn = candidates[rng.randrange(len(candidates))]
    points_b = dict(points_a)
    points_b[nn_label] = new_nn
    rb = ranked_neighbors(points_b, target)
    (b1, nb_label), (b2, _) = rb[0], rb[1]
    if nb_label != runner_up:  # belt-and-braces (redundant by construction)
        return None
    if b2 - b1 < MARGIN_B - 1e-9:  # B-side ambiguity margin, mirroring A's
        return None
    geometry.update(
        target=target,
        points_b=points_b,
        question=question,
        gold_a=gold_a,
        gold_b=gold_b,
        premise={
            "question": premise_question,
            "answer_a": nn_label,
            "answer_b": runner_up,
            "transition": True,
            "margin_a": d2 - d1,
            "margin_b": b2 - b1,
            "hard_negative_labels": [ranked[2][1]],
        },
        moved_label=nn_label,
    )
    return geometry


def build_invariance_geometry(geometry: dict[str, Any], rng: random.Random, prefer_style_twin: bool) -> dict[str, Any]:
    """Invariance member for a group: style twin (same facts, variant rendering)
    or distractor move constrained to preserve the answer AND the premise."""
    points_a = geometry["points_a"]
    if prefer_style_twin:
        return {"invariance_kind": "style_twin", "points_inv": dict(points_a)}
    target = geometry["target"]
    protected = {target}
    d_floor = None
    if geometry["premise"] is not None:
        ranked = ranked_neighbors(points_a, target)
        protected |= {ranked[0][1], ranked[1][1]}  # N and M stay put
        d_floor = ranked[1][0]  # moved distractor must stay at distance >= d2
    else:
        protected |= {geometry.get("moved_label") or target}
    tp = points_a[target]
    pool = [l for l in geometry["labels"] if l not in protected]
    for moved in rng.sample(pool, len(pool)):
        pt = points_a[moved]
        others = {p for l, p in points_a.items() if l != moved}
        candidates = [
            (x, pt[1])
            for x in range(-7, 8)
            if x != 0
            and abs(x - pt[0]) >= 3
            and spacing_ok((x, pt[1]), others)
            and (d_floor is None or math.hypot(x - tp[0], pt[1] - tp[1]) >= d_floor)
        ]
        if candidates:
            new_pt = candidates[rng.randrange(len(candidates))]
            points_inv = dict(points_a)
            points_inv[moved] = new_pt
            return {"invariance_kind": "distractor_move", "moved_distractor": moved,
                    "points_inv": points_inv}
    return {"invariance_kind": "style_twin", "points_inv": dict(points_a)}


def materialize_group(
    *,
    out_dir: Path,
    geometry: dict[str, Any],
    invariance: dict[str, Any],
    rng: random.Random,
) -> dict[str, Any]:
    """Render and save one group: a causal pair row, an invariance pair row and
    a v2 group record (blind_solvability pending, mismatched control unset)."""
    intervention = geometry["intervention"]
    spid = geometry["scene_program_id"]
    n = geometry["n_points"]
    template_id = TEMPLATES[n]
    premise = geometry["premise"]
    points_a, points_b = geometry["points_a"], geometry["points_b"]
    gold_a, gold_b = geometry["gold_a"], geometry["gold_b"]

    knobs: dict[str, Any] = {
        "n_points": n,
        "min_chebyshev_spacing": 2,
        "x_flip_min_delta": 3,
        "margin_a": MARGIN_A,
        "template_id": template_id,
    }
    if premise is not None:
        knobs["premise_margin_a_observed"] = round(premise["margin_a"], 6)
        knobs["premise_margin_b_observed"] = round(premise["margin_b"], 6)
        if premise["transition"]:
            knobs["margin_b"] = MARGIN_B
            knobs["margin_d3"] = MARGIN_D3
        else:
            knobs["chained_stay_margin"] = CHAINED_STAY_MARGIN

    image_a = _render_high_entropy_coordinate_register(points_a)
    image_b = _render_high_entropy_coordinate_register(points_b)
    causal_swap = rng.random() < 0.5
    causal_pair_id = f"t4v2c_{intervention}_" + hashlib.sha256(
        json.dumps([spid, sorted(points_b.items()), geometry["target"]],
                   sort_keys=True, default=str).encode()
    ).hexdigest()[:16]
    causal_row = _save_b1_pair(
        out_dir=out_dir,
        pair_id=causal_pair_id,
        image_a=image_a,
        image_b=image_b,
        question=geometry["question"],
        answer_a=gold_a,
        answer_b=gold_b,
        allow_equal_answers=False,
        category="t4v2_premise_construct",
        template_id=template_id,
        provenance={
            "generator": "scripts.build_track4_premise_v2_dev_batch",
            "batch_seed": BATCH_SEED,
            "intervention_type": intervention,
            "scene_program_id": spid,
            "split": "development",
            "render_variant_b": "canonical",
        },
        verifier_results={
            "exact_by_construction": True,
            "intervention_type": intervention,
            "target_label": geometry["target"],
            "answers_equal": False,
            "difficulty_knobs": knobs,
        },
        swap_sides=causal_swap,
    )
    causal_row["intervention_type"] = intervention
    causal_row["answers_equal"] = False
    causal_row["scene_program_id"] = spid
    causal_row["split"] = "development"
    causal_row["difficulty_knobs"] = knobs
    causal_row["hard_negatives"] = hard_negatives(
        points_a, points_b, geometry["target"], str(causal_row["answer_a"]), str(causal_row["answer_b"])
    )
    causal_row["blind_solvability_qhat"] = None
    # physical-side scene programs: scene_points_a always describes image_a_path
    if causal_swap:
        causal_row["scene_points_a"] = serialize_points(points_b)
        causal_row["scene_points_b"] = serialize_points(points_a)
    else:
        causal_row["scene_points_a"] = serialize_points(points_a)
        causal_row["scene_points_b"] = serialize_points(points_b)
    if premise is not None:
        causal_row["premise_question"] = premise["question"]
        pa, pb = premise["answer_a"], premise["answer_b"]
        if causal_swap:
            pa, pb = pb, pa
        causal_row["premise_answer_a"] = pa
        causal_row["premise_answer_b"] = pb
        causal_row["premise_transition"] = premise["transition"]
        causal_row["premise_hard_negative_labels"] = premise["hard_negative_labels"]
    else:
        causal_row["premise_question"] = None
        causal_row["premise_answer_a"] = None
        causal_row["premise_answer_b"] = None
        causal_row["premise_transition"] = None

    points_inv = invariance["points_inv"]
    if invariance["invariance_kind"] == "style_twin":
        image_inv = render_style_variant(points_inv)
        render_variant = "style_variant"
    else:
        image_inv = _render_high_entropy_coordinate_register(points_inv)
        render_variant = "canonical"
    inv_pair_id = f"t4v2i_{intervention}_" + hashlib.sha256(
        json.dumps([spid, sorted(points_inv.items()), invariance["invariance_kind"]],
                   sort_keys=True, default=str).encode()
    ).hexdigest()[:16]
    inv_row = _save_b1_pair(
        out_dir=out_dir,
        pair_id=inv_pair_id,
        image_a=image_a,
        image_b=image_inv,
        question=geometry["question"],
        answer_a=gold_a,
        answer_b=gold_a,
        allow_equal_answers=True,
        category="t4v2_premise_construct",
        template_id=template_id,
        provenance={
            "generator": "scripts.build_track4_premise_v2_dev_batch",
            "batch_seed": BATCH_SEED,
            "intervention_type": intervention,
            "scene_program_id": spid,
            "split": "development",
            "invariance_kind": invariance["invariance_kind"],
            "moved_distractor": invariance.get("moved_distractor"),
            "render_variant_b": render_variant,
        },
        verifier_results={
            "exact_by_construction": True,
            "intervention_type": intervention,
            "target_label": geometry["target"],
            "answers_equal": True,
            "difficulty_knobs": knobs,
        },
        swap_sides=False,
    )
    inv_row["intervention_type"] = intervention
    inv_row["answers_equal"] = True
    inv_row["scene_program_id"] = spid
    inv_row["split"] = "development"
    inv_row["difficulty_knobs"] = knobs
    inv_row["blind_solvability_qhat"] = None
    inv_row["scene_points_a"] = serialize_points(points_a)
    inv_row["scene_points_b"] = serialize_points(points_inv)
    if premise is not None:
        inv_row["premise_question"] = premise["question"]
        inv_row["premise_answer_a"] = premise["answer_a"]
        inv_row["premise_answer_b"] = premise["answer_a"]  # invariance: premise unmoved
        inv_row["premise_transition"] = False
    else:
        inv_row["premise_question"] = None
        inv_row["premise_answer_a"] = None
        inv_row["premise_answer_b"] = None
        inv_row["premise_transition"] = None

    # ---- v2 group record (semantic sides, never the pair-level swap) ----
    if causal_swap:
        original_path, original_sha = causal_row["image_b_path"], causal_row["image_b_sha256"]
        causal_path, causal_sha = causal_row["image_a_path"], causal_row["image_a_sha256"]
    else:
        original_path, original_sha = causal_row["image_a_path"], causal_row["image_a_sha256"]
        causal_path, causal_sha = causal_row["image_b_path"], causal_row["image_b_sha256"]
    group_uid = f"t4v2_grp_{intervention}_{spid}"
    group: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION_V2,
        "group_uid": group_uid,
        "scene_program_id": spid,
        "intervention_type": intervention,
        "template_id": template_id,
        "template_family": TEMPLATE_FAMILY,
        "split": "development",
        "question": geometry["question"],
        "original": {
            "image_path": original_path,
            "image_sha256": original_sha,
            "answer": gold_a,
        },
        "members": [
            {
                "member_uid": f"{group_uid}::causal",
                "kind": "causal",
                "answer": gold_b,
                "image_path": causal_path,
                "image_sha256": causal_sha,
                "source_pair_id": causal_pair_id,
            },
            {
                "member_uid": f"{group_uid}::invariance",
                "kind": "invariance",
                "answer": gold_a,
                "image_path": inv_row["image_b_path"],
                "image_sha256": inv_row["image_b_sha256"],
                "invariance_kind": invariance["invariance_kind"],
                "source_pair_id": inv_pair_id,
            },
            {
                "member_uid": f"{group_uid}::nc_no_image",
                "kind": "negative_control",
                "condition": "no_image",
                "answer": gold_a,
            },
            {
                "member_uid": f"{group_uid}::nc_gray",
                "kind": "negative_control",
                "condition": "gray",
                "answer": gold_a,
            },
            {
                "member_uid": f"{group_uid}::nc_mismatched",
                "kind": "negative_control",
                "condition": "mismatched_real",
                "answer": gold_a,
                # image assigned in the cross-group pass after all groups exist
            },
        ],
        "difficulty": dict(knobs),
        "blind_solvability": {"q_real": None, "q_blind": None, "measurement_state": "pending"},
    }
    if premise is not None:
        group["premise"] = {"question": premise["question"]}
        group["original"]["premise_answer"] = premise["answer_a"]
        group["members"][0]["premise_answer"] = premise["answer_b"]
        group["members"][0]["premise_transition"] = premise["transition"]
        group["members"][1]["premise_answer"] = premise["answer_a"]

    return {
        "group": group,
        "causal_row": causal_row,
        "invariance_row": inv_row,
        "causal_swap": causal_swap,
    }


def premise_probe_row(causal_row: dict[str, Any]) -> dict[str, Any]:
    """Derived probe row: premise question with per-member premise golds.

    For chained items the golds are equal (equal-gold scorer branch, P0.2);
    for transition items they DIFFER, so pair_score applies the discriminative
    two-gold criterion — which is exactly the redefined transition metric's
    per-member requirement."""
    d = dict(causal_row)
    d["question"] = causal_row["premise_question"]
    d["answer_a"] = causal_row["premise_answer_a"]
    d["answer_b"] = causal_row["premise_answer_b"]
    d["answers_equal"] = causal_row["premise_answer_a"] == causal_row["premise_answer_b"]
    d["final_question_original"] = causal_row["question"]
    d["final_answer_a_original"] = causal_row["answer_a"]
    d["final_answer_b_original"] = causal_row["answer_b"]
    d["probe"] = "premise"
    return d


def build_batch(out_dir: Path) -> dict[str, Any]:
    groups: list[dict[str, Any]] = []
    causal_rows: list[dict[str, Any]] = []
    inv_rows: list[dict[str, Any]] = []
    attempts_by_type: dict[str, int] = {}
    built_index = 0
    for intervention, count in COUNTS.items():
        built = 0
        attempt = 0
        cap = count * 3000
        while built < count:
            attempt += 1
            if attempt > cap:
                raise RuntimeError(f"{intervention}: exhausted {cap} attempts at item {built}")
            rng = random.Random(attempt_seed(intervention, attempt))
            geometry = build_group_geometry(intervention, rng)
            if geometry is None:
                continue
            invariance = build_invariance_geometry(geometry, rng, prefer_style_twin=built_index % 2 == 0)
            result = materialize_group(out_dir=out_dir, geometry=geometry,
                                       invariance=invariance, rng=rng)
            groups.append(result["group"])
            causal_rows.append(result["causal_row"])
            inv_rows.append(result["invariance_row"])
            built += 1
            built_index += 1
        attempts_by_type[intervention] = attempt

    # gray control image, shared by every group
    gray_path = out_dir / "gray_1400x1240.png"
    Image.new("RGB", (1400, 1240), (127, 127, 127)).save(gray_path, format="PNG",
                                                         optimize=False, compress_level=9)
    gray_sha = hashlib.sha256(gray_path.read_bytes()).hexdigest()

    # cross-group pass: mismatched_real = next group's original (cyclic per type)
    by_type: dict[str, list[dict[str, Any]]] = {}
    for g in groups:
        by_type.setdefault(g["intervention_type"], []).append(g)
    for itype, gs in by_type.items():
        for i, g in enumerate(gs):
            donor = gs[(i + 1) % len(gs)]
            for m in g["members"]:
                if m.get("condition") == "mismatched_real":
                    m["image_path"] = donor["original"]["image_path"]
                    m["image_sha256"] = donor["original"]["image_sha256"]
                    m["mismatched_source_group"] = donor["group_uid"]
                if m.get("condition") == "gray":
                    m["image_path"] = str(gray_path)
                    m["image_sha256"] = gray_sha

    validate_batch_v2(groups, require_measured=False)

    return {
        "groups": groups,
        "causal_rows": causal_rows,
        "invariance_rows": inv_rows,
        "attempts_by_type": attempts_by_type,
        "gray_sha256": gray_sha,
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> str:
    blob = "".join(json.dumps(r, sort_keys=True, ensure_ascii=True, default=str) + "\n" for r in rows)
    path.write_text(blob, encoding="utf-8")
    return hashlib.sha256(blob.encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=ROOT / "data/track4_premise_v2_dev_v1")
    parser.add_argument("--report", type=Path,
                        default=ROOT / "reports/track4_premise_v2_dev_build_v1.json")
    args = parser.parse_args()
    manifest_path = args.out_dir / "manifest_causal_pairs.jsonl"
    if manifest_path.exists() or args.report.exists():
        raise FileExistsError("refusing to overwrite the declared Track-4 v2 development batch")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    result = build_batch(args.out_dir)
    groups, causal_rows, inv_rows = result["groups"], result["causal_rows"], result["invariance_rows"]
    n_expected = sum(COUNTS.values())
    if not (len(groups) == len(causal_rows) == len(inv_rows) == n_expected):
        raise AssertionError(f"declared batch size mismatch: {len(groups)}")

    probe_rows = [premise_probe_row(r) for r in causal_rows if r["premise_question"]]
    n_probe_expected = sum(c for t, c in COUNTS.items() if t != "fact_read")
    if len(probe_rows) != n_probe_expected:
        raise AssertionError(f"premise probe rows: {len(probe_rows)} != {n_probe_expected}")

    hashes = {
        "manifest_causal_pairs.jsonl": write_jsonl(manifest_path, causal_rows),
        "manifest_invariance_pairs.jsonl": write_jsonl(
            args.out_dir / "manifest_invariance_pairs.jsonl", inv_rows),
        "manifest_premise_probe.jsonl": write_jsonl(
            args.out_dir / "manifest_premise_probe.jsonl", probe_rows),
        "groups_v2.jsonl": write_jsonl(args.out_dir / "groups_v2.jsonl", groups),
    }

    # attacker-release packaging over the causal pairs (artifact gate input)
    release_dir = args.out_dir / "attacker_release"
    release_dir.mkdir(exist_ok=True)
    release_rows, key_rows = [], []
    for row in causal_rows:
        swapped = bool(row["provenance"]["semantic_side_assignment_swapped"])
        members, key_members = [], []
        for side in ("a", "b"):
            member_id = f"{row['pair_id']}_{side}"
            rel = Path(row[f"image_{side}_path"]).relative_to(args.out_dir)
            members.append({"member_id": member_id, "image_path": f"../{rel}"})
            semantic = {"a": "b", "b": "a"}[side] if swapped else side
            key_members.append({"member_id": member_id, "source_side": semantic})
        release_rows.append({"pair_id": row["pair_id"], "members": members})
        key_rows.append({"pair_id": row["pair_id"], "template_id": row["template_id"],
                         "members": key_members})
    hashes["attacker_release/manifest.jsonl"] = write_jsonl(release_dir / "manifest.jsonl", release_rows)
    hashes["attacker_key.jsonl"] = write_jsonl(args.out_dir / "attacker_key.jsonl", key_rows)

    # frozen-B1 disjointness check: no rendered image is shared with B1
    b1_manifest = ROOT / "data/b1_geometry_track_v1/manifest.jsonl"
    b1_shas: set[str] = set()
    if b1_manifest.exists():
        for line in b1_manifest.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                b1_shas.update({r.get("image_a_sha256"), r.get("image_b_sha256")})
    new_shas = {r[k] for r in causal_rows + inv_rows for k in ("image_a_sha256", "image_b_sha256")}
    b1_collisions = sorted(new_shas & b1_shas)

    per_type = {t: {"groups": c, "n_points": N_POINTS[t], "template_id": TEMPLATES[N_POINTS[t]]}
                for t, c in COUNTS.items()}
    invariance_kinds: dict[str, int] = {}
    for g in groups:
        for m in g["members"]:
            if m["kind"] == "invariance":
                invariance_kinds[m["invariance_kind"]] = invariance_kinds.get(m["invariance_kind"], 0) + 1

    git_hash = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True).stdout.strip()
    report = {
        "schema_version": "blind-gains.track4-premise-v2-dev-build.v1",
        "registration": "docs/registered_track4_premise_v2_design_v1.md",
        "batch_seed": BATCH_SEED,
        "declared_groups": len(groups),
        "per_intervention": per_type,
        "invariance_member_kinds": invariance_kinds,
        "premise_probe_rows": len(probe_rows),
        "premise_transition_rows": sum(1 for r in causal_rows if r.get("premise_transition")),
        "attempts_by_type": result["attempts_by_type"],
        "margins": {"margin_a": MARGIN_A, "margin_b": MARGIN_B, "margin_d3": MARGIN_D3,
                    "chained_stay_margin": CHAINED_STAY_MARGIN},
        "split_rule": {
            "buckets": SPLIT_BUCKETS,
            "hash": "sha256(scene_program_id + '|split-v1')[:8] % 100",
            "enforcement": "builder rejects any scene program outside the development bucket",
        },
        "group_schema_version": SCHEMA_VERSION_V2,
        "blind_solvability": "pending on every group; measured by the registered acceptance evals",
        "gray_control_sha256": result["gray_sha256"],
        "b1_image_sha_collisions": b1_collisions,
        "file_sha256": hashes,
        "out_dir": str(args.out_dir.relative_to(ROOT)),
        "node": socket.gethostname(),
        "git_hash": git_hash,
        "command": " ".join(sys.argv),
        "one_shot": "declared development batch; no acceptance iteration",
    }
    if b1_collisions:
        raise AssertionError(f"frozen-B1 image collision: {b1_collisions[:4]}")
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in
                      ("declared_groups", "premise_probe_rows", "premise_transition_rows",
                       "attempts_by_type", "file_sha256")}, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
