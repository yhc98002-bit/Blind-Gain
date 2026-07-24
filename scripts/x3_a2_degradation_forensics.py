#!/usr/bin/env python3
"""X3 — A2 geometry degradation forensics (CPU, cached predictions only).

Re-scores the nine cached R19 prediction sets (base + four arms x two seeds,
step 100, real condition) with the current canonical pair scorer, builds the
per-seed geometry correct-to-wrong item sets for A2 gray, and computes the
registered forensics: Jaccard overlap with a permutation null, answer
transition directions classified against exactly replayed scene registers,
the same-wrong-answer rate, scene-feature comparisons, and the same items'
behavior under A1/A2b/A3. Facts only; no interpretation text.
"""
from __future__ import annotations

import datetime as dt
import glob
import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from scripts.build_x2_hard_negative_candidates import (
    levenshtein,
    nearest_gridline,
    replay_scene,
)
from src.eval.fliptrack_metrics import pair_score

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
TEMPLATE = "coordinate_register_twenty_point_x_v02"
SEED = 20260724
N_PERM = 10000

RUNS = {
    ("base", "shared"): "fliptrack_v02r19_packaged_qwen25vl3b_real_an29_20260710T142716Z",
    ("a1", "seed1"): "pilot_fliptrack_a1_real_seed1_step100_real_an12_20260715T195421Z",
    ("a2", "seed1"): "pilot_fliptrack_a2_gray_seed1_step100_real_an12_20260716T152519Z",
    ("a2b", "seed1"): "pilot_fliptrack_mech_a2b_noimage_seed1_step100_real_an29_20260715T184448Z",
    ("a3", "seed1"): "pilot_fliptrack_a3_caption_seed1_step100_real_an29_20260715T191451Z",
    ("a1", "seed2"): "pilot_fliptrack_a1_real_seed2_step100_real_an29_20260721T163422Z",
    ("a2", "seed2"): "pilot_fliptrack_a2_gray_seed2_step100_real_an29_20260721T163431Z",
    ("a2b", "seed2"): "pilot_fliptrack_a2b_noimage_seed2_step100_real_an29_20260721T163439Z",
    ("a3", "seed2"): "pilot_fliptrack_a3_caption_seed2_step100_real_an29_20260721T163448Z",
}

ANSWER_RE = re.compile(r"<answer>\s*(.*?)\s*</answer>", re.DOTALL)


def load_scored(run_name: str) -> dict[str, dict[str, Any]]:
    run_dir = ROOT / "experiments/runs" / run_name
    paths = sorted(glob.glob(str(run_dir / "shards" / "*.jsonl")))
    if not paths:
        paths = sorted(glob.glob(str(run_dir / "*.jsonl")))
    if not paths:
        raise ValueError(f"no prediction files under {run_name}")
    scored: dict[str, dict[str, Any]] = {}
    for path in paths:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("template_id") != TEMPLATE:
                continue
            fresh = pair_score(row)
            pair_id = str(row["pair_id"])
            if pair_id in scored:
                raise ValueError(f"duplicate pair {pair_id} in {run_name}")
            scored[pair_id] = {
                "correct_a": bool(fresh["correct_a"]),
                "correct_b": bool(fresh["correct_b"]),
                "pair_correct": bool(fresh["correct_a"] and fresh["correct_b"]),
                "prediction_a": str(row.get("prediction_a", "")),
                "prediction_b": str(row.get("prediction_b", "")),
                "answer_a": str(row["answer_a"]),
                "answer_b": str(row["answer_b"]),
            }
    if len(scored) != 600:
        raise ValueError(f"{run_name}: expected 600 geometry pairs, got {len(scored)}")
    return scored


def extract_answer(prediction: str) -> str | None:
    match = ANSWER_RE.search(prediction)
    if match:
        return match.group(1).strip()
    stripped = prediction.strip()
    return stripped if stripped else None


def classify_wrong(value: str | None, side: str, scene: dict[str, Any], registry_row: dict[str, Any]) -> str:
    if value is None:
        return "unparsed"
    swap = scene["swap"]
    member_scene = (scene["points_b"] if swap else scene["points_a"]) if side == "a" else (
        scene["points_a"] if swap else scene["points_b"]
    )
    target_label = scene["target_label"]
    own_gold = str(registry_row["answer_a"] if side == "a" else registry_row["answer_b"])
    twin_gold = str(registry_row["answer_b"] if side == "a" else registry_row["answer_a"])
    if value == twin_gold:
        return "twin_member_gold"
    if value == str(member_scene[target_label][1]):
        return "same_point_y"
    others = {label: point for label, point in member_scene.items() if label != target_label}
    target = member_scene[target_label]
    nn_label = min(
        sorted(others),
        key=lambda label: (math.hypot(others[label][0] - target[0], others[label][1] - target[1]), label),
    )
    if value == str(others[nn_label][0]):
        return "nearest_neighbor_x"
    sim_label = min(sorted(others), key=lambda label: (levenshtein(label, target_label), label))
    if value == str(others[sim_label][0]):
        return "most_similar_label_x"
    if value == str(nearest_gridline(int(own_gold))):
        return "nearest_gridline"
    scene_xs = {str(point[0]) for point in member_scene.values()}
    if value in scene_xs:
        return "other_scene_point_x"
    return "non_scene_value"


def feature_vector(scene: dict[str, Any]) -> dict[str, float]:
    points = scene["points_a"]
    target_label = scene["target_label"]
    target = points[target_label]
    others = {label: point for label, point in points.items() if label != target_label}
    distances = [math.hypot(p[0] - target[0], p[1] - target[1]) for p in others.values()]
    return {
        "target_x_negative": float(target[0] < 0 or scene["target_b"][0] < 0),
        "crowding_within_3": float(
            sum(1 for p in others.values() if max(abs(p[0] - target[0]), abs(p[1] - target[1])) <= 3)
        ),
        "min_label_levenshtein": float(min(levenshtein(l, target_label) for l in others)),
        "distance_to_nearest_point": float(min(distances)),
    }


def perm_pvalue_mean_diff(group: list[float], rest: list[float], rng: np.random.Generator) -> float:
    observed = abs(float(np.mean(group)) - float(np.mean(rest)))
    pooled = np.asarray(group + rest, dtype=np.float64)
    k = len(group)
    count = 0
    for _ in range(N_PERM):
        rng.shuffle(pooled)
        if abs(pooled[:k].mean() - pooled[k:].mean()) >= observed:
            count += 1
    return (count + 1) / (N_PERM + 1)


def main() -> None:
    out_json = ROOT / "reports/x3_a2_degradation_forensics_v1.json"
    out_md = ROOT / "reports/x3_a2_degradation_forensics_v1.md"
    if out_json.exists() or out_md.exists():
        raise FileExistsError("refusing to overwrite X3 artifacts")

    registry_rows = {}
    registry_path = ROOT / "data/fliptrack_r19_visual_evidence_candidates_v1.jsonl"
    for line in registry_path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("template_id") == TEMPLATE:
            registry_rows[str(row["pair_id"])] = row
    sources = {}
    for name in ("fliptrack_v02r10_source_manifest.jsonl", "fliptrack_v02r18_source_manifest.jsonl"):
        for line in (ROOT / "data" / name).read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row.get("template_id") == TEMPLATE:
                sources[str(row["pair_id"])] = row
    scenes: dict[str, dict[str, Any]] = {}
    for pair_id, registry_row in registry_rows.items():
        source_id = str(registry_row.get("source_pair_id") or pair_id)
        scenes[pair_id] = replay_scene(int(sources[source_id]["provenance"]["pair_seed"]))

    scored = {key: load_scored(run) for key, run in RUNS.items()}
    base = scored[("base", "shared")]
    base_correct = {p for p, row in base.items() if row["pair_correct"]}

    degraded: dict[str, set[str]] = {}
    gained: dict[str, set[str]] = {}
    accuracy: dict[str, dict[str, float]] = {}
    for seed in ("seed1", "seed2"):
        a2 = scored[("a2", seed)]
        degraded[seed] = {p for p in base_correct if not a2[p]["pair_correct"]}
        gained[seed] = {p for p in a2 if a2[p]["pair_correct"] and p not in base_correct}
        accuracy[seed] = {
            "a2_pair_accuracy": sum(1 for row in a2.values() if row["pair_correct"]) / 600,
            "net_delta_vs_base": (
                sum(1 for row in a2.values() if row["pair_correct"]) - len(base_correct)
            )
            / 600,
        }

    d1, d2 = degraded["seed1"], degraded["seed2"]
    intersection = d1 & d2
    union = d1 | d2
    jaccard = len(intersection) / len(union) if union else 0.0
    rng = np.random.default_rng(SEED)
    universe = sorted(base_correct)
    null_jaccards = []
    for _ in range(N_PERM):
        s1 = set(rng.choice(universe, size=len(d1), replace=False).tolist())
        s2 = set(rng.choice(universe, size=len(d2), replace=False).tolist())
        u = s1 | s2
        null_jaccards.append(len(s1 & s2) / len(u) if u else 0.0)
    null_arr = np.asarray(null_jaccards)
    p_value = float((np.sum(null_arr >= jaccard) + 1) / (N_PERM + 1))

    transitions: dict[str, Counter] = {"seed1": Counter(), "seed2": Counter()}
    member_direction: dict[str, Counter] = {"seed1": Counter(), "seed2": Counter()}
    wrong_answers: dict[str, dict[str, tuple[str, str | None]]] = {"seed1": {}, "seed2": {}}
    for seed in ("seed1", "seed2"):
        a2 = scored[("a2", seed)]
        for pair_id in degraded[seed]:
            row = a2[pair_id]
            wrong_sides = [s for s in ("a", "b") if not row[f"correct_{s}"]]
            member_direction[seed][
                "both_members" if len(wrong_sides) == 2 else f"member_{wrong_sides[0]}_only"
            ] += 1
            for side in wrong_sides:
                value = extract_answer(row[f"prediction_{side}"])
                label = classify_wrong(value, side, scenes[pair_id], registry_rows[pair_id])
                transitions[seed][label] += 1
                wrong_answers[seed][f"{pair_id}|{side}"] = (side, value)

    shared_keys = set(wrong_answers["seed1"]) & set(wrong_answers["seed2"])
    same_wrong = sum(
        1
        for key in shared_keys
        if wrong_answers["seed1"][key][1] is not None
        and wrong_answers["seed1"][key][1] == wrong_answers["seed2"][key][1]
    )
    same_wrong_rate = same_wrong / len(shared_keys) if shared_keys else None

    features = {p: feature_vector(scenes[p]) for p in base_correct}
    feature_stats: dict[str, Any] = {}
    rng2 = np.random.default_rng(SEED + 1)
    for feature_name in ("target_x_negative", "crowding_within_3", "min_label_levenshtein", "distance_to_nearest_point"):
        group = [features[p][feature_name] for p in sorted(union)]
        rest = [features[p][feature_name] for p in sorted(base_correct - union)]
        feature_stats[feature_name] = {
            "degraded_union_mean": float(np.mean(group)),
            "non_degraded_mean": float(np.mean(rest)),
            "perm_p_two_sided": perm_pvalue_mean_diff(group, rest, rng2),
        }

    cross_arm: dict[str, Any] = {}
    for arm in ("a1", "a2b", "a3"):
        cross_arm[arm] = {}
        for seed in ("seed1", "seed2"):
            rows = scored[(arm, seed)]
            cross_arm[arm][seed] = {
                "wrong_on_shared_degraded_items": sum(
                    1 for p in intersection if not rows[p]["pair_correct"]
                ),
                "shared_degraded_items": len(intersection),
                "wrong_on_all_base_correct": sum(
                    1 for p in base_correct if not rows[p]["pair_correct"]
                ),
                "base_correct_items": len(base_correct),
            }

    result = {
        "schema_version": "blind-gains.x3-a2-degradation-forensics.v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "template": TEMPLATE,
        "scorer": "src.eval.fliptrack_metrics.pair_score (current canonical parser, uniform re-score of cached predictions)",
        "runs": {f"{k[0]}|{k[1]}": v for k, v in RUNS.items()},
        "base_pair_accuracy": len(base_correct) / 600,
        "per_seed": {
            seed: {
                **accuracy[seed],
                "degraded_correct_to_wrong": len(degraded[seed]),
                "gained_wrong_to_correct": len(gained[seed]),
                "member_direction": dict(member_direction[seed]),
                "transition_taxonomy": dict(transitions[seed]),
            }
            for seed in ("seed1", "seed2")
        },
        "overlap": {
            "intersection": len(intersection),
            "union": len(union),
            "jaccard": jaccard,
            "permutation_null_mean_jaccard": float(null_arr.mean()),
            "permutation_p_value": p_value,
            "permutations": N_PERM,
            "permutation_seed": SEED,
        },
        "same_wrong_answer": {
            "shared_wrong_member_slots": len(shared_keys),
            "same_extracted_wrong_answer": same_wrong,
            "rate": same_wrong_rate,
        },
        "scene_features_degraded_vs_not": feature_stats,
        "cross_arm_on_shared_degraded_items": cross_arm,
    }

    lines = [
        "# X3 — A2 geometry degradation forensics (v1)",
        "",
        "Cached predictions only; uniform canonical re-scoring; scene features from",
        "exactly replayed generator registers. Facts only.",
        "",
        f"- Base geometry pair accuracy: {len(base_correct)/600:.4f} ({len(base_correct)}/600)",
        f"- A2 step-100 pair accuracy: seed1 {accuracy['seed1']['a2_pair_accuracy']:.4f},"
        f" seed2 {accuracy['seed2']['a2_pair_accuracy']:.4f}"
        f" (net vs base: {accuracy['seed1']['net_delta_vs_base']:+.4f} / {accuracy['seed2']['net_delta_vs_base']:+.4f})",
        f"- Correct-to-wrong sets: seed1 {len(d1)}, seed2 {len(d2)};"
        f" intersection {len(intersection)}, union {len(union)}",
        f"- Jaccard {jaccard:.4f} vs permutation null mean {float(null_arr.mean()):.4f};"
        f" p = {p_value:.5f} ({N_PERM} permutations, seed {SEED})",
        f"- Same-wrong-answer rate on shared wrong member slots: "
        + (f"{same_wrong_rate:.4f} ({same_wrong}/{len(shared_keys)})" if same_wrong_rate is not None else "n/a"),
        "",
        "## Transition taxonomy (wrong-member extracted answers)",
        "",
        "| taxon | seed1 | seed2 |",
        "|---|---|---|",
    ]
    taxa = sorted(set(transitions["seed1"]) | set(transitions["seed2"]))
    for taxon in taxa:
        lines.append(f"| {taxon} | {transitions['seed1'].get(taxon, 0)} | {transitions['seed2'].get(taxon, 0)} |")
    lines += [
        "",
        "## Member direction",
        "",
        "| direction | seed1 | seed2 |",
        "|---|---|---|",
    ]
    for direction in sorted(set(member_direction["seed1"]) | set(member_direction["seed2"])):
        lines.append(
            f"| {direction} | {member_direction['seed1'].get(direction, 0)} | {member_direction['seed2'].get(direction, 0)} |"
        )
    lines += [
        "",
        "## Scene features: degraded union vs non-degraded base-correct",
        "",
        "| feature | degraded mean | non-degraded mean | permutation p |",
        "|---|---|---|---|",
    ]
    for name, stats in feature_stats.items():
        lines.append(
            f"| {name} | {stats['degraded_union_mean']:.4f} | {stats['non_degraded_mean']:.4f} | {stats['perm_p_two_sided']:.5f} |"
        )
    lines += [
        "",
        "## Same items under the other arms (shared degraded items)",
        "",
        "| arm | seed | wrong on shared items | shared items | wrong on all base-correct | base-correct items |",
        "|---|---|---|---|---|---|",
    ]
    for arm in ("a1", "a2b", "a3"):
        for seed in ("seed1", "seed2"):
            entry = cross_arm[arm][seed]
            lines.append(
                f"| {arm} | {seed} | {entry['wrong_on_shared_degraded_items']} | {entry['shared_degraded_items']}"
                f" | {entry['wrong_on_all_base_correct']} | {entry['base_correct_items']} |"
            )
    lines.append("")

    out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md.write_text("\n".join(lines), encoding="utf-8")
    digest = hashlib.sha256(out_json.read_bytes()).hexdigest()
    print(
        json.dumps(
            {
                "jaccard": jaccard,
                "p": p_value,
                "d1": len(d1),
                "d2": len(d2),
                "intersection": len(intersection),
                "same_wrong_rate": same_wrong_rate,
                "output_sha256": digest,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
