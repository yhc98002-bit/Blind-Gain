#!/usr/bin/env python3
"""B1 — renderable geometry track prototype (docs/EXPERIMENT_TODO.md Track B).

One declared 100-pair calibration batch over six intervention types on the
twenty-point coordinate-register visual language:

  fact_read (20)         flip the queried point's x (R19-style)
  chained_premise (20)   nearest-point chain with a stored premise probe
  binding_swap (16)      swap two labels, positions unchanged
  distractor_only (16)   move a non-queried point; answer must not change
  style_twin (14)        same facts, variant rendering; answer must not change
  prior_conflict (14)    label digit primes an x value; member A aligns with
                         the prior, member B contradicts it

Per-item metadata: intervention type, premise question/answer (chained),
prior answer (prior-conflict), structured hard negatives (same-point y,
nearest-neighbor x, most-similar-label x, nearest gridline, twin gold),
difficulty knobs, answers_equal flag. Blind-solvability q-hat is attached
empirically by the calibration scoring report, not at build time.

Seeded and one-shot: no acceptance iteration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from PIL import Image, ImageDraw

from src.fliptrack.build_v02 import (
    COLORS,
    _answers_distinguishable,
    _exact_change_mask,
    _font,
    _render_high_entropy_coordinate_register,
    _sample_high_entropy_points,
)
from src.fliptrack.schema import pair_record


def _save_b1_pair(
    *,
    out_dir: Path,
    pair_id: str,
    image_a: Image.Image,
    image_b: Image.Image,
    question: str,
    answer_a: str,
    answer_b: str,
    category: str,
    template_id: str,
    provenance: dict[str, Any],
    verifier_results: dict[str, Any],
    swap_sides: bool = False,
    allow_equal_answers: bool = False,
) -> dict[str, Any]:
    """Clone of the frozen FlipTrack saver that additionally admits
    consistency pairs (identical gold on both members) for the
    distractor-only and style-twin interventions."""
    if swap_sides:
        image_a, image_b = image_b, image_a
        answer_a, answer_b = answer_b, answer_a
    provenance = dict(provenance)
    provenance["semantic_side_assignment_swapped"] = swap_sides
    verifier_results = dict(verifier_results)
    verifier_results["semantic_side_assignment_swapped"] = swap_sides
    if image_a.size != image_b.size:
        raise ValueError(f"pair dimensions differ for {pair_id}")
    if not allow_equal_answers and not _answers_distinguishable(answer_a, answer_b):
        raise ValueError(f"degenerate answers for {pair_id}: {answer_a!r}, {answer_b!r}")
    if allow_equal_answers and answer_a != answer_b:
        raise ValueError(f"consistency pair has differing answers: {pair_id}")
    image_dir = out_dir / "images"
    mask_dir = out_dir / "masks"
    image_dir.mkdir(parents=True, exist_ok=True)
    mask_dir.mkdir(parents=True, exist_ok=True)
    image_a_path = image_dir / f"{pair_id}_a.png"
    image_b_path = image_dir / f"{pair_id}_b.png"
    mask_a_path = mask_dir / f"{pair_id}_a_mask.png"
    mask_b_path = mask_dir / f"{pair_id}_b_mask.png"
    mask = _exact_change_mask(image_a, image_b)
    if not np.any(np.asarray(mask)):
        raise ValueError(f"pair has no pixel change: {pair_id}")
    image_a.save(image_a_path, format="PNG", optimize=False, compress_level=9)
    image_b.save(image_b_path, format="PNG", optimize=False, compress_level=9)
    mask.save(mask_a_path, format="PNG", optimize=False, compress_level=9)
    mask.save(mask_b_path, format="PNG", optimize=False, compress_level=9)
    return pair_record(
        pair_id=pair_id,
        image_a_path=str(image_a_path),
        image_b_path=str(image_b_path),
        changed_region_mask_a=str(mask_a_path),
        changed_region_mask_b=str(mask_b_path),
        question=question,
        answer_a=answer_a,
        answer_b=answer_b,
        category=category,
        template_id=template_id,
        provenance=provenance,
        verifier_results=verifier_results,
    )
from scripts.build_x2_hard_negative_candidates import (
    levenshtein,
    nearest_gridline,
)

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
BATCH_SEED = 20260725
LABEL_POOL = [f"{letter}{digit}" for letter in "BCDFGHJKLMNPRSTVWXYZ" for digit in "23456789"]
TEMPLATE = "b1_coordinate_register_v1"
COUNTS = {
    "fact_read": 20,
    "chained_premise": 20,
    "binding_swap": 16,
    "distractor_only": 16,
    "style_twin": 14,
    "prior_conflict": 14,
}


def render_style_variant(points: dict[str, tuple[int, int]]) -> Image.Image:
    width, height = 1400, 1240
    image = Image.new("RGB", (width, height), (243, 246, 250))
    draw = ImageDraw.Draw(image)
    draw.text((width // 2, 38), "Coordinate Survey Register", anchor="mm", font=_font(28, True), fill=(20, 30, 45))
    origin = (700, 650)
    scale = 68
    plot_left, plot_right = origin[0] - 7 * scale, origin[0] + 7 * scale
    plot_top, plot_bottom = origin[1] - 7 * scale, origin[1] + 7 * scale
    draw.rectangle((plot_left, plot_top, plot_right, plot_bottom), fill=(252, 252, 249), outline=(90, 90, 110), width=3)
    for value in range(-7, 8):
        x = origin[0] + value * scale
        y = origin[1] - value * scale
        draw.line((x, plot_top, x, plot_bottom), fill=(214, 220, 231), width=1)
        draw.line((plot_left, y, plot_right, y), fill=(214, 220, 231), width=1)
        if value:
            draw.text((x, origin[1] + 21), str(value), anchor="mm", font=_font(14), fill=(60, 66, 80))
            draw.text((origin[0] - 22, y), str(value), anchor="mm", font=_font(14), fill=(60, 66, 80))
    draw.line((plot_left, origin[1], plot_right, origin[1]), fill=(30, 36, 52), width=4)
    draw.line((origin[0], plot_top, origin[0], plot_bottom), fill=(30, 36, 52), width=4)
    for index, (label, point) in enumerate(points.items()):
        x = origin[0] + point[0] * scale
        y = origin[1] - point[1] * scale
        color = COLORS[(index + 3) % len(COLORS)]
        draw.rectangle((x - 9, y - 9, x + 9, y + 9), fill=color, outline="white", width=2)
        label_x = x + (18 if point[0] <= 0 else -18)
        draw.text(
            (label_x, y - 17),
            label,
            anchor="lm" if point[0] <= 0 else "rm",
            font=_font(21, True),
            fill=(15, 15, 25),
            stroke_width=2,
            stroke_fill="white",
        )
    draw.text(
        (plot_left, 1186),
        "Locate the requested label, then read its coordinate from the numbered axes.",
        font=_font(15),
        fill=(66, 72, 86),
    )
    return image


def spacing_ok(candidate: tuple[int, int], others: set[tuple[int, int]]) -> bool:
    return all(max(abs(candidate[0] - x), abs(candidate[1] - y)) >= 2 for x, y in others)


def nearest_info(points: dict[str, tuple[int, int]], target: str) -> tuple[str, float, float]:
    target_point = points[target]
    ranked = sorted(
        (
            (math.hypot(p[0] - target_point[0], p[1] - target_point[1]), label)
            for label, p in points.items()
            if label != target
        )
    )
    return ranked[0][1], ranked[0][0], ranked[1][0]


def hard_negatives(points_a: dict, points_b: dict, target: str, gold_a: str, gold_b: str) -> list[dict[str, Any]]:
    values: dict[str, set[str]] = {}

    def add(value: Any, role: str) -> None:
        values.setdefault(str(value), set()).add(role)

    add(gold_a, "gold_member_a")
    add(gold_b, "gold_member_b")
    add(gold_b, "twin_member_gold_for_a")
    add(gold_a, "twin_member_gold_for_b")
    for tag, scene in (("member_a", points_a), ("member_b", points_b)):
        add(scene[target][1], f"same_point_y_{tag}")
        others = {label: p for label, p in scene.items() if label != target}
        nn_label = min(
            sorted(others),
            key=lambda l: (math.hypot(others[l][0] - scene[target][0], others[l][1] - scene[target][1]), l),
        )
        add(others[nn_label][0], f"nearest_neighbor_x_{tag}")
    sim_label = min(
        sorted(l for l in points_a if l != target),
        key=lambda l: (levenshtein(l, target), l),
    )
    add(points_a[sim_label][0], "most_similar_label_x")
    add(nearest_gridline(int(gold_a)), "nearest_gridline_member_a")
    add(nearest_gridline(int(gold_b)), "nearest_gridline_member_b")
    return [
        {"answer": value, "negative_types": sorted(roles)}
        for value, roles in sorted(values.items())
    ]


def base_scene(rng: random.Random, n_points: int = 20) -> tuple[list[str], dict[str, tuple[int, int]]]:
    labels = rng.sample(LABEL_POOL, n_points)
    coordinates = _sample_high_entropy_points(rng, n_points)
    return labels, dict(zip(labels, coordinates))


def flip_targets(points: dict[str, tuple[int, int]], rng: random.Random) -> tuple[str, tuple[int, int]] | None:
    options = []
    for label, point in points.items():
        others = {p for l, p in points.items() if l != label}
        candidates = [
            (x, point[1])
            for x in range(-7, 8)
            if x != 0
            and abs(x - point[0]) >= 3
            and _answers_distinguishable(str(point[0]), str(x))
            and spacing_ok((x, point[1]), others)
        ]
        if candidates:
            options.append((label, candidates))
    if not options:
        return None
    label, candidates = options[rng.randrange(len(options))]
    return label, candidates[rng.randrange(len(candidates))]


def build_items(out_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    item_index = 0
    for intervention, count in COUNTS.items():
        built = 0
        attempt = 0
        while built < count:
            attempt += 1
            if attempt > count * 400:
                raise RuntimeError(f"{intervention}: exhausted attempts at item {built}")
            pair_seed = BATCH_SEED * 1000003 + item_index * 104729 + attempt
            rng = random.Random(pair_seed)
            labels, points_a = base_scene(rng)
            renderer_b = _render_high_entropy_coordinate_register
            question: str
            premise_question = None
            premise_answer = None
            prior_answer = None
            answers_equal = False
            knobs = {"n_points": 20, "min_chebyshev_spacing": 2, "x_flip_min_delta": 3}

            if intervention == "fact_read":
                flip = flip_targets(points_a, rng)
                if flip is None:
                    continue
                target, new_point = flip
                points_b = dict(points_a)
                points_b[target] = new_point
                question = f"What is the x-coordinate of point {target}?"
                gold_a, gold_b = str(points_a[target][0]), str(new_point[0])
            elif intervention == "chained_premise":
                target = rng.choice(labels)
                nn_label, d1, d2 = nearest_info(points_a, target)
                if d2 - d1 < 1.0:
                    continue
                nn_point = points_a[nn_label]
                others = {p for l, p in points_a.items() if l != nn_label}
                target_point = points_a[target]
                candidates = [
                    (x, nn_point[1])
                    for x in range(-7, 8)
                    if x != 0
                    and abs(x - nn_point[0]) >= 3
                    and _answers_distinguishable(str(nn_point[0]), str(x))
                    and spacing_ok((x, nn_point[1]), others)
                    and math.hypot(x - target_point[0], nn_point[1] - target_point[1]) < d2 - 0.5
                ]
                if not candidates:
                    continue
                new_nn = candidates[rng.randrange(len(candidates))]
                points_b = dict(points_a)
                points_b[nn_label] = new_nn
                nn_label_b, _, _ = nearest_info(points_b, target)
                if nn_label_b != nn_label:
                    continue
                question = (
                    f"Consider the point nearest to point {target}. "
                    "What is the x-coordinate of that nearest point?"
                )
                premise_question = f"Which labeled point is nearest to point {target}?"
                premise_answer = nn_label
                gold_a, gold_b = str(nn_point[0]), str(new_nn[0])
                if not _answers_distinguishable(gold_a, gold_b):
                    continue
            elif intervention == "binding_swap":
                pool = [
                    (p, q)
                    for i, p in enumerate(labels)
                    for q in labels[i + 1 :]
                    if abs(points_a[p][0] - points_a[q][0]) >= 3
                    and _answers_distinguishable(str(points_a[p][0]), str(points_a[q][0]))
                ]
                if not pool:
                    continue
                p_label, q_label = pool[rng.randrange(len(pool))]
                points_b = dict(points_a)
                points_b[p_label], points_b[q_label] = points_a[q_label], points_a[p_label]
                target = p_label
                question = f"What is the x-coordinate of point {target}?"
                gold_a, gold_b = str(points_a[p_label][0]), str(points_a[q_label][0])
            elif intervention == "distractor_only":
                target = rng.choice(labels)
                distractors = [l for l in labels if l != target]
                moved = rng.choice(distractors)
                others = {p for l, p in points_a.items() if l != moved}
                point = points_a[moved]
                candidates = [
                    (x, point[1])
                    for x in range(-7, 8)
                    if x != 0 and abs(x - point[0]) >= 3 and spacing_ok((x, point[1]), others)
                ]
                if not candidates:
                    continue
                points_b = dict(points_a)
                points_b[moved] = candidates[rng.randrange(len(candidates))]
                question = f"What is the x-coordinate of point {target}?"
                gold_a = gold_b = str(points_a[target][0])
                answers_equal = True
                knobs["moved_distractor"] = moved
            elif intervention == "style_twin":
                target = rng.choice(labels)
                points_b = dict(points_a)
                renderer_b = render_style_variant
                question = f"What is the x-coordinate of point {target}?"
                gold_a = gold_b = str(points_a[target][0])
                answers_equal = True
            else:  # prior_conflict
                digit_targets = [
                    label for label in labels if label[1] in "234567"
                ]
                if not digit_targets:
                    continue
                target = rng.choice(digit_targets)
                digit = int(target[1])
                others = {p for l, p in points_a.items() if l != target}
                y = points_a[target][1]
                if not spacing_ok((digit, y), others):
                    continue
                conflict_candidates = [
                    (x, y)
                    for x in range(-7, 8)
                    if x != 0
                    and abs(x - digit) >= 3
                    and _answers_distinguishable(str(digit), str(x))
                    and spacing_ok((x, y), others)
                ]
                if not conflict_candidates:
                    continue
                points_a = dict(points_a)
                points_a[target] = (digit, y)
                points_b = dict(points_a)
                points_b[target] = conflict_candidates[rng.randrange(len(conflict_candidates))]
                question = f"What is the x-coordinate of point {target}?"
                gold_a, gold_b = str(digit), str(points_b[target][0])
                prior_answer = str(digit)

            image_a = _render_high_entropy_coordinate_register(points_a)
            image_b = renderer_b(points_b)
            pair_id = f"b1_{intervention}_" + hashlib.sha256(
                json.dumps([pair_seed, sorted(points_a.items()), sorted(points_b.items()), target],
                           sort_keys=True, default=str).encode()
            ).hexdigest()[:16]
            row = _save_b1_pair(
                out_dir=out_dir,
                pair_id=pair_id,
                image_a=image_a,
                image_b=image_b,
                question=question,
                answer_a=gold_a,
                answer_b=gold_b,
                allow_equal_answers=answers_equal,
                category="b1_geometry_track",
                template_id=TEMPLATE,
                provenance={
                    "generator": "scripts.build_b1_geometry_track_prototype",
                    "pair_seed": pair_seed,
                    "batch_seed": BATCH_SEED,
                    "intervention_type": intervention,
                    "render_variant_b": "style_variant" if intervention == "style_twin" else "canonical",
                },
                verifier_results={
                    "exact_by_construction": True,
                    "intervention_type": intervention,
                    "target_label": target,
                    "answers_equal": answers_equal,
                    "premise_question": premise_question,
                    "premise_answer": premise_answer,
                    "prior_answer": prior_answer,
                    "difficulty_knobs": knobs,
                },
                swap_sides=False if answers_equal else rng.random() < 0.5,
            )
            row["intervention_type"] = intervention
            row["answers_equal"] = answers_equal
            row["premise_question"] = premise_question
            row["premise_answer"] = premise_answer
            row["prior_answer"] = prior_answer
            row["difficulty_knobs"] = knobs
            row["hard_negatives"] = hard_negatives(
                points_a, points_b, target, str(row["answer_a"]), str(row["answer_b"])
            )
            row["blind_solvability_qhat"] = None
            rows.append(row)
            built += 1
            item_index += 1
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=ROOT / "data/b1_geometry_track_v1")
    parser.add_argument(
        "--report", type=Path, default=ROOT / "reports/geometry_track_prototype_build_v1.json"
    )
    args = parser.parse_args()
    manifest_path = args.out_dir / "manifest.jsonl"
    if manifest_path.exists() or args.report.exists():
        raise FileExistsError("refusing to overwrite the declared B1 batch")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rows = build_items(args.out_dir)
    if len(rows) != sum(COUNTS.values()):
        raise AssertionError(f"declared batch size mismatch: {len(rows)}")
    with manifest_path.open("x", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True, default=str) + "\n")
    digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    report = {
        "schema_version": "blind-gains.b1-geometry-track-build.v1",
        "batch_seed": BATCH_SEED,
        "declared_pairs": len(rows),
        "per_intervention": COUNTS,
        "manifest": str(manifest_path.relative_to(ROOT)),
        "manifest_sha256": digest,
        "one_shot": "declared batch; no acceptance iteration per docs/EXPERIMENT_TODO.md",
    }
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
