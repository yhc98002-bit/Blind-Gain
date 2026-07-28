#!/usr/bin/env python3
"""X3 — seed-3 replication of the A2-gray structured corrosion (CPU, cached only).

Applies the frozen seed-1/seed-2 method (scripts/x3_a2_degradation_forensics.py)
to the seed-3 A2-gray arm. The scoring loader, the wrong-answer extractor, the
transition classifier, the scene feature vector and the mean-difference
permutation test are IMPORTED from that frozen script so the method is identical
by construction rather than by transcription.

Everything derived (deltas, Jaccards, rates, retention) is recomputed here from
the cached prediction rows; nothing is carried over from the v1 report.

Both the lenient (acc_final / pair_correct) and the contract-strict
(acc_strict / strict_pair_correct) tracks are computed. Facts only.
"""
from __future__ import annotations

import datetime as dt
import glob
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")

import numpy as np

from scripts.build_x2_hard_negative_candidates import levenshtein, nearest_gridline, replay_scene
from scripts.x3_a2_degradation_forensics import (
    N_PERM,
    ROOT,
    TEMPLATE,
    classify_wrong,
    extract_answer,
    feature_vector,
    load_scored,
    perm_pvalue_mean_diff,
)
from src.eval.fliptrack_metrics import pair_score

# Permutation / bootstrap seed for THIS report. The seed-1/2 null used 20260724;
# the seed-3 null is recomputed with a fresh seed and fresh set sizes.
SEED3 = 20260728
N_BOOT = 10000

RUNS = {
    ("base", "shared"): "fliptrack_v02r19_packaged_qwen25vl3b_real_an29_20260710T142716Z",
    ("a2", "seed1"): "pilot_fliptrack_a2_gray_seed1_step100_real_an12_20260716T152519Z",
    ("a2", "seed2"): "pilot_fliptrack_a2_gray_seed2_step100_real_an29_20260721T163431Z",
    ("a2", "seed3"): "pilot_fliptrack_a2_gray_seed3_step100_real_an29_20260725T092515Z",
    ("a1", "seed3"): "pilot_fliptrack_a1_real_seed3_step100_real_an29_20260725T092506Z",
    ("a2b", "seed3"): "pilot_fliptrack_a2b_noimage_seed3_step100_real_an29_20260725T092523Z",
    ("a3", "seed3"): "pilot_fliptrack_a3_caption_seed3_step100_real_an29_20260725T092532Z",
}
SEEDS = ("seed1", "seed2", "seed3")


def load_scored_strict(run_name: str) -> dict[str, dict[str, Any]]:
    """Same loader as the frozen one, but retaining the contract-strict fields."""
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
                "correct_a": bool(fresh["strict_correct_a"]),
                "correct_b": bool(fresh["strict_correct_b"]),
                "pair_correct": bool(fresh["strict_pair_correct"]),
                "prediction_a": str(row.get("prediction_a", "")),
                "prediction_b": str(row.get("prediction_b", "")),
                "answer_a": str(row["answer_a"]),
                "answer_b": str(row["answer_b"]),
            }
    if len(scored) != 600:
        raise ValueError(f"{run_name}: expected 600 geometry pairs, got {len(scored)}")
    return scored


def wilson(k: int, n: int, z: float = 1.959963984540054) -> list[float] | None:
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0.0, centre - half), min(1.0, centre + half)]


def paired_delta_bootstrap(
    base: dict[str, dict[str, Any]], arm: dict[str, dict[str, Any]], rng: np.random.Generator
) -> dict[str, float]:
    ids = sorted(base)
    b = np.asarray([1.0 if base[p]["pair_correct"] else 0.0 for p in ids])
    a = np.asarray([1.0 if arm[p]["pair_correct"] else 0.0 for p in ids])
    diff = a - b
    n = len(ids)
    idx = rng.integers(0, n, size=(N_BOOT, n))
    boot = diff[idx].mean(axis=1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return {
        "delta": float(diff.mean()),
        "ci95_lo": float(lo),
        "ci95_hi": float(hi),
        "n_pairs": n,
        "bootstrap_resamples": N_BOOT,
        "bootstrap_seed": SEED3,
    }


def jaccard(x: set[str], y: set[str]) -> float:
    u = x | y
    return len(x & y) / len(u) if u else 0.0


def null_pairwise(
    universe: list[str], n_x: int, n_y: int, observed: float, rng: np.random.Generator
) -> dict[str, float]:
    vals = np.empty(N_PERM, dtype=np.float64)
    for i in range(N_PERM):
        s1 = set(rng.choice(universe, size=n_x, replace=False).tolist())
        s2 = set(rng.choice(universe, size=n_y, replace=False).tolist())
        u = s1 | s2
        vals[i] = len(s1 & s2) / len(u) if u else 0.0
    return {
        "observed_jaccard": observed,
        "null_mean_jaccard": float(vals.mean()),
        "null_p95_jaccard": float(np.percentile(vals, 95)),
        "null_max_jaccard": float(vals.max()),
        "p_value": float((int(np.sum(vals >= observed)) + 1) / (N_PERM + 1)),
        "permutations": N_PERM,
        "permutation_seed": SEED3,
        "universe_size": len(universe),
        "set_sizes": [n_x, n_y],
    }


def null_triple(
    universe: list[str], sizes: tuple[int, int, int], observed: float, rng: np.random.Generator
) -> dict[str, float]:
    vals = np.empty(N_PERM, dtype=np.float64)
    for i in range(N_PERM):
        sets = [set(rng.choice(universe, size=s, replace=False).tolist()) for s in sizes]
        inter = sets[0] & sets[1] & sets[2]
        uni = sets[0] | sets[1] | sets[2]
        vals[i] = len(inter) / len(uni) if uni else 0.0
    return {
        "observed_jaccard3": observed,
        "null_mean_jaccard3": float(vals.mean()),
        "null_p95_jaccard3": float(np.percentile(vals, 95)),
        "null_max_jaccard3": float(vals.max()),
        "p_value": float((int(np.sum(vals >= observed)) + 1) / (N_PERM + 1)),
        "permutations": N_PERM,
        "permutation_seed": SEED3,
        "universe_size": len(universe),
        "set_sizes": list(sizes),
    }


def analyse(
    scored: dict[tuple[str, str], dict[str, dict[str, Any]]],
    scenes: dict[str, dict[str, Any]],
    registry_rows: dict[str, dict[str, Any]],
    strict_mode: bool,
) -> dict[str, Any]:
    base = scored[("base", "shared")]
    base_correct = {p for p, row in base.items() if row["pair_correct"]}

    degraded: dict[str, set[str]] = {}
    gained: dict[str, set[str]] = {}
    per_seed: dict[str, Any] = {}
    rng_boot = np.random.default_rng(SEED3)
    for seed in SEEDS:
        a2 = scored[("a2", seed)]
        n_correct = sum(1 for row in a2.values() if row["pair_correct"])
        degraded[seed] = {p for p in base_correct if not a2[p]["pair_correct"]}
        gained[seed] = {p for p in a2 if a2[p]["pair_correct"] and p not in base_correct}
        per_seed[seed] = {
            "a2_pair_accuracy": n_correct / 600,
            "a2_pair_accuracy_ci95_wilson": wilson(n_correct, 600),
            "a2_pair_correct_n": n_correct,
            "net_delta_vs_base": (n_correct - len(base_correct)) / 600,
            "net_delta_vs_base_paired_bootstrap": paired_delta_bootstrap(base, a2, rng_boot),
            "degraded_correct_to_wrong": len(degraded[seed]),
            "gained_wrong_to_correct": len(gained[seed]),
        }

    # transitions / member direction / wrong-slot answers
    transitions: dict[str, Counter] = {s: Counter() for s in SEEDS}
    member_direction: dict[str, Counter] = {s: Counter() for s in SEEDS}
    wrong_answers: dict[str, dict[str, str | None]] = {s: {} for s in SEEDS}
    for seed in SEEDS:
        a2 = scored[("a2", seed)]
        for pair_id in degraded[seed]:
            row = a2[pair_id]
            wrong_sides = [s for s in ("a", "b") if not row[f"correct_{s}"]]
            member_direction[seed][
                "both_members" if len(wrong_sides) == 2 else f"member_{wrong_sides[0]}_only"
            ] += 1
            for side in wrong_sides:
                value = extract_answer(row[f"prediction_{side}"])
                own_gold = str(registry_rows[pair_id]["answer_a" if side == "a" else "answer_b"])
                if strict_mode and value is not None and value == own_gold:
                    label = "gold_value_contract_invalid"
                else:
                    label = classify_wrong(value, side, scenes[pair_id], registry_rows[pair_id])
                transitions[seed][label] += 1
                wrong_answers[seed][f"{pair_id}|{side}"] = value
        per_seed[seed]["member_direction"] = dict(member_direction[seed])
        per_seed[seed]["transition_taxonomy"] = dict(transitions[seed])
        per_seed[seed]["wrong_member_slots"] = sum(transitions[seed].values())
        per_seed[seed]["nearest_gridline_count"] = transitions[seed].get("nearest_gridline", 0)
        per_seed[seed]["nearest_gridline_share_of_wrong_slots"] = (
            transitions[seed].get("nearest_gridline", 0) / sum(transitions[seed].values())
            if sum(transitions[seed].values())
            else None
        )
        per_seed[seed]["nearest_gridline_share_ci95_wilson"] = wilson(
            transitions[seed].get("nearest_gridline", 0), sum(transitions[seed].values())
        )

    # overlaps
    universe = sorted(base_correct)
    rng_perm = np.random.default_rng(SEED3 + 100)
    overlap: dict[str, Any] = {}
    for a, b in (("seed3", "seed1"), ("seed3", "seed2"), ("seed1", "seed2")):
        da, db = degraded[a], degraded[b]
        obs = jaccard(da, db)
        entry = {
            "sets": [a, b],
            "size_a": len(da),
            "size_b": len(db),
            "intersection": len(da & db),
            "union": len(da | db),
            "jaccard": obs,
        }
        entry["permutation_null"] = null_pairwise(universe, len(da), len(db), obs, rng_perm)
        overlap[f"{a}__{b}"] = entry

    d1, d2, d3 = degraded["seed1"], degraded["seed2"], degraded["seed3"]
    inter3 = d1 & d2 & d3
    union3 = d1 | d2 | d3
    j3 = len(inter3) / len(union3) if union3 else 0.0
    overlap["three_seed"] = {
        "sizes": [len(d1), len(d2), len(d3)],
        "intersection_all_three": len(inter3),
        "union_all_three": len(union3),
        "jaccard3": j3,
        "seed3_recovers_of_seed12_intersection": len(d3 & (d1 & d2)),
        "seed12_intersection_size": len(d1 & d2),
        "seed3_recovery_rate_of_seed12_intersection": (
            len(d3 & (d1 & d2)) / len(d1 & d2) if (d1 & d2) else None
        ),
        "seed3_recovery_rate_ci95_wilson": wilson(len(d3 & (d1 & d2)), len(d1 & d2)),
        "permutation_null": null_triple(universe, (len(d1), len(d2), len(d3)), j3, rng_perm),
    }

    # identical extracted wrong answer, pairwise across seeds
    same_wrong: dict[str, Any] = {}
    for a, b in (("seed3", "seed1"), ("seed3", "seed2"), ("seed1", "seed2")):
        shared = set(wrong_answers[a]) & set(wrong_answers[b])
        n_same = sum(
            1
            for k in shared
            if wrong_answers[a][k] is not None and wrong_answers[a][k] == wrong_answers[b][k]
        )
        same_wrong[f"{a}__{b}"] = {
            "shared_wrong_member_slots": len(shared),
            "same_extracted_wrong_answer": n_same,
            "rate": n_same / len(shared) if shared else None,
            "rate_ci95_wilson": wilson(n_same, len(shared)),
        }
    shared3 = set(wrong_answers["seed1"]) & set(wrong_answers["seed2"]) & set(wrong_answers["seed3"])
    n_same3 = sum(
        1
        for k in shared3
        if wrong_answers["seed1"][k] is not None
        and wrong_answers["seed1"][k] == wrong_answers["seed2"][k] == wrong_answers["seed3"][k]
    )
    same_wrong["three_seed"] = {
        "shared_wrong_member_slots": len(shared3),
        "same_extracted_wrong_answer": n_same3,
        "rate": n_same3 / len(shared3) if shared3 else None,
        "rate_ci95_wilson": wilson(n_same3, len(shared3)),
    }

    # scene features: seed3 degraded vs non-degraded base-correct, and 3-seed union
    features = {p: feature_vector(scenes[p]) for p in base_correct}
    feature_stats: dict[str, Any] = {}
    rng_feat = np.random.default_rng(SEED3 + 1)
    for group_name, group_set in (("seed3_degraded", d3), ("three_seed_union", union3)):
        feature_stats[group_name] = {}
        for fname in (
            "target_x_negative",
            "crowding_within_3",
            "min_label_levenshtein",
            "distance_to_nearest_point",
        ):
            grp = [features[p][fname] for p in sorted(group_set)]
            rest = [features[p][fname] for p in sorted(base_correct - group_set)]
            feature_stats[group_name][fname] = {
                "group_mean": float(np.mean(grp)),
                "group_n": len(grp),
                "rest_mean": float(np.mean(rest)),
                "rest_n": len(rest),
                "perm_p_two_sided": perm_pvalue_mean_diff(grp, rest, rng_feat),
                "permutations": N_PERM,
            }

    # cross-arm behaviour of the seed-3 shared degraded items
    shared_items = d3 & d1 & d2
    cross_arm: dict[str, Any] = {}
    for arm in ("a1", "a2b", "a3"):
        rows = scored[(arm, "seed3")]
        cross_arm[arm] = {
            "seed": "seed3",
            "wrong_on_three_seed_shared_items": sum(1 for p in shared_items if not rows[p]["pair_correct"]),
            "three_seed_shared_items": len(shared_items),
            "wrong_on_seed3_degraded_items": sum(1 for p in d3 if not rows[p]["pair_correct"]),
            "seed3_degraded_items": len(d3),
            "wrong_on_all_base_correct": sum(1 for p in base_correct if not rows[p]["pair_correct"]),
            "base_correct_items": len(base_correct),
        }

    n_base = len(base_correct)
    return {
        "base_pair_correct_n": n_base,
        "base_pair_accuracy": n_base / 600,
        "base_pair_accuracy_ci95_wilson": wilson(n_base, 600),
        "n_geometry_pairs": 600,
        "per_seed": per_seed,
        "overlap": overlap,
        "same_wrong_answer": same_wrong,
        "scene_features": feature_stats,
        "cross_arm_seed3": cross_arm,
        "degraded_sets_sha256": {
            s: hashlib.sha256("\n".join(sorted(degraded[s])).encode()).hexdigest() for s in SEEDS
        },
    }


def _ci(ci: list[float] | None) -> str:
    return "n/a" if ci is None else f"[{ci[0]:.4f}, {ci[1]:.4f}]"


def render_md(r: dict[str, Any]) -> str:
    L, S = r["lenient"], r["strict"]
    ag = r["frozen_v1_agreement"]
    out: list[str] = []
    A = out.append

    A("# X3 — seed-3 replication of the A2-gray structured corrosion (v1)")
    A("")
    A("Cached predictions only; uniform canonical re-scoring; scene features from exactly")
    A("replayed generator registers. The seed-1/2 method in")
    A("`scripts/x3_a2_degradation_forensics.py` is applied unchanged (helpers imported, not")
    A("transcribed) to the seed-3 A2-gray arm. All values below are recomputed from the cached")
    A("prediction rows. Facts only.")
    A("")
    A(f"- Generated (UTC): {r['generated_utc']}; git {r['git_hash']}")
    A(f"- Template: `{r['template']}`; n = {L['n_geometry_pairs']} geometry pairs per run")
    A(f"- Seed-3 marker chain: `{r['seed3_marker_chain']['results_file']}`")
    A(f"  -> `{r['seed3_marker_chain']['marker']}`")
    A(f"  -> eval run `{r['seed3_marker_chain']['evaluation_run']}`")
    A(f"- Base run: `{r['runs']['base|shared']}`")
    A(f"- Permutation / bootstrap seed for this report: {r['permutation_seed_seed3']}"
      f" ({r['permutations']} permutations, {r['bootstrap_resamples']} bootstrap resamples)")
    A(f"- Permutation p-values are computed as (hits + 1) / (permutations + 1) and are floored at"
      f" {1 / (r['permutations'] + 1):.5f}; a reported {1 / (r['permutations'] + 1):.5f} means"
      f" 0 of {r['permutations']} draws reached the observed statistic, i.e. p is at the"
      f" resolution limit, not measured below it.")
    A("")

    A("## Method-agreement check against the frozen v1 report")
    A("")
    A(f"Reference: `{ag['reference_report']}` (sha256 `{ag['reference_sha256']}`)")
    A("")
    A(f"- Seed-1/seed-2 fields recomputed and compared: {ag['fields_equal']}/{ag['fields_checked']} equal"
      f" (all_equal = {ag['all_equal']})")
    A(f"- Seed1-vs-seed2 permutation null, frozen (seed 20260724) mean Jaccard"
      f" {ag['frozen_seed1_seed2_null_mean_jaccard']:.4f}, p = {ag['frozen_seed1_seed2_permutation_p_value']:.5f};"
      f" recomputed here (seed {r['permutation_seed_seed3']}) mean Jaccard"
      f" {ag['recomputed_seed1_seed2_null_mean_jaccard']:.4f}, p ="
      f" {ag['recomputed_seed1_seed2_permutation_p_value']:.5f}. Independent draws; not asserted equal.")
    if not ag["all_equal"]:
        A("")
        A("| field | frozen v1 | recomputed | equal |")
        A("|---|---|---|---|")
        for c in ag["checks"]:
            if not c["equal"]:
                A(f"| {c['field']} | {c['frozen_v1']} | {c['recomputed']} | {c['equal']} |")
    A("")

    for track, res in (("Lenient (acc_final / pair_correct)", L), ("Contract-strict (acc_strict / strict_pair_correct)", S)):
        A(f"## {track}")
        A("")
        A(f"Base geometry pair accuracy: {res['base_pair_accuracy']:.4f}"
          f" ({res['base_pair_correct_n']}/600), Wilson 95% CI {_ci(res['base_pair_accuracy_ci95_wilson'])}")
        A("")
        A("### A2-gray step-100 accuracy and delta vs base")
        A("")
        A("| seed | A2 pair acc | n correct / n | Wilson 95% CI | net delta vs base | delta n items | paired bootstrap 95% CI | correct->wrong | wrong->correct |")
        A("|---|---|---|---|---|---|---|---|---|")
        for seed in SEEDS:
            p = res["per_seed"][seed]
            b = p["net_delta_vs_base_paired_bootstrap"]
            A(f"| {seed} | {p['a2_pair_accuracy']:.4f} | {p['a2_pair_correct_n']}/600 |"
              f" {_ci(p['a2_pair_accuracy_ci95_wilson'])} | {p['net_delta_vs_base']:+.4f} |"
              f" {p['a2_pair_correct_n'] - res['base_pair_correct_n']:+d}/600 |"
              f" [{b['ci95_lo']:+.4f}, {b['ci95_hi']:+.4f}] |"
              f" {p['degraded_correct_to_wrong']} | {p['gained_wrong_to_correct']} |")
        A("")
        A("### Correct-to-wrong set overlap (universe = base-correct items)")
        A("")
        A("| comparison | size A | size B | intersection | union | Jaccard | null mean | null p95 | null max | p |")
        A("|---|---|---|---|---|---|---|---|---|---|")
        for key in ("seed3__seed1", "seed3__seed2", "seed1__seed2"):
            e = res["overlap"][key]
            n = e["permutation_null"]
            A(f"| {e['sets'][0]} vs {e['sets'][1]} | {e['size_a']} | {e['size_b']} | {e['intersection']} |"
              f" {e['union']} | {e['jaccard']:.4f} | {n['null_mean_jaccard']:.4f} |"
              f" {n['null_p95_jaccard']:.4f} | {n['null_max_jaccard']:.4f} | {n['p_value']:.5f} |")
        t = res["overlap"]["three_seed"]
        n3 = t["permutation_null"]
        A(f"| all three (3-way) | sizes {t['sizes']} | | {t['intersection_all_three']} |"
          f" {t['union_all_three']} | {t['jaccard3']:.4f} | {n3['null_mean_jaccard3']:.4f} |"
          f" {n3['null_p95_jaccard3']:.4f} | {n3['null_max_jaccard3']:.4f} | {n3['p_value']:.5f} |")
        A("")
        A(f"- Universe (base-correct items) n = {res['base_pair_correct_n']};"
          f" nulls drawn with permutation seed {r['permutation_seed_seed3']},"
          f" {r['permutations']} permutations, set sizes held at the observed sizes.")
        A(f"- Seed-3 recovers {t['seed3_recovers_of_seed12_intersection']}/{t['seed12_intersection_size']}"
          f" of the seed1-and-seed2 shared degraded pairs"
          + (f" = {t['seed3_recovery_rate_of_seed12_intersection']:.4f}," if t['seed3_recovery_rate_of_seed12_intersection'] is not None else ",")
          + f" Wilson 95% CI {_ci(t['seed3_recovery_rate_ci95_wilson'])}")
        A("")
        A("### Identical extracted wrong answer on shared wrong member slots")
        A("")
        A("| comparison | same answer | shared wrong member slots | rate | Wilson 95% CI |")
        A("|---|---|---|---|---|")
        for key in ("seed3__seed1", "seed3__seed2", "seed1__seed2", "three_seed"):
            e = res["same_wrong_answer"][key]
            rate = "n/a" if e["rate"] is None else f"{e['rate']:.4f}"
            label = "all three (3-way)" if key == "three_seed" else key.replace("__", " vs ")
            A(f"| {label} | {e['same_extracted_wrong_answer']} |"
              f" {e['shared_wrong_member_slots']} | {rate} | {_ci(e['rate_ci95_wilson'])} |")
        A("")
        A("### Transition taxonomy (per-seed counts of wrong member slots)")
        A("")
        A("Counts are per-seed counts of wrong member slots, not a numerator/denominator pair.")
        A("The per-seed denominator (total wrong member slots for that seed) is the last row.")
        A("")
        A("| taxon | " + " | ".join(SEEDS) + " |")
        A("|---|" + "---|" * len(SEEDS))
        taxa = sorted(set().union(*(set(res["per_seed"][s]["transition_taxonomy"]) for s in SEEDS)))
        for taxon in taxa:
            A(f"| {taxon} | "
              + " | ".join(str(res["per_seed"][s]["transition_taxonomy"].get(taxon, 0)) for s in SEEDS)
              + " |")
        A("| **total wrong member slots (denominator)** | "
          + " | ".join(str(res["per_seed"][s]["wrong_member_slots"]) for s in SEEDS) + " |")
        A("")
        A("| nearest-gridline off-by-one | " + " | ".join(SEEDS) + " |")
        A("|---|" + "---|" * len(SEEDS))
        A("| count | " + " | ".join(str(res["per_seed"][s]["nearest_gridline_count"]) for s in SEEDS) + " |")
        A("| denominator (wrong member slots) | "
          + " | ".join(str(res["per_seed"][s]["wrong_member_slots"]) for s in SEEDS) + " |")
        A("| share | " + " | ".join(
            "n/a" if res["per_seed"][s]["nearest_gridline_share_of_wrong_slots"] is None
            else f"{res['per_seed'][s]['nearest_gridline_share_of_wrong_slots']:.4f}" for s in SEEDS) + " |")
        A("| share Wilson 95% CI | "
          + " | ".join(_ci(res["per_seed"][s]["nearest_gridline_share_ci95_wilson"]) for s in SEEDS) + " |")
        A("")
        A("### Member direction (counts of degraded pairs)")
        A("")
        A("| direction | " + " | ".join(SEEDS) + " |")
        A("|---|" + "---|" * len(SEEDS))
        dirs = sorted(set().union(*(set(res["per_seed"][s]["member_direction"]) for s in SEEDS)))
        for d in dirs:
            A(f"| {d} | " + " | ".join(str(res["per_seed"][s]["member_direction"].get(d, 0)) for s in SEEDS) + " |")
        A("| **total degraded pairs** | "
          + " | ".join(str(res["per_seed"][s]["degraded_correct_to_wrong"]) for s in SEEDS) + " |")
        A("")
        A("### Scene features (permutation test on mean difference)")
        A("")
        A("| group | feature | group mean | group n | rest mean | rest n | perm p (two-sided) |")
        A("|---|---|---|---|---|---|---|")
        for gname, feats in res["scene_features"].items():
            for fname, st in feats.items():
                A(f"| {gname} | {fname} | {st['group_mean']:.4f} | {st['group_n']} |"
                  f" {st['rest_mean']:.4f} | {st['rest_n']} | {st['perm_p_two_sided']:.5f} |")
        A("")
        A("### Seed-3 shared degraded items under the other seed-3 arms")
        A("")
        A("| arm | wrong on 3-seed shared | 3-seed shared n | wrong on seed3 degraded | seed3 degraded n | wrong on all base-correct | base-correct n |")
        A("|---|---|---|---|---|---|---|")
        for arm in ("a1", "a2b", "a3"):
            e = res["cross_arm_seed3"][arm]
            A(f"| {arm} | {e['wrong_on_three_seed_shared_items']} | {e['three_seed_shared_items']} |"
              f" {e['wrong_on_seed3_degraded_items']} | {e['seed3_degraded_items']} |"
              f" {e['wrong_on_all_base_correct']} | {e['base_correct_items']} |")
        A("")
        A("### Degraded-set fingerprints (sha256 of sorted pair ids)")
        A("")
        for s in SEEDS:
            A(f"- {s}: `{res['degraded_sets_sha256'][s]}`")
        A("")

    A("## Notes on the contract-strict track")
    A("")
    A(r["strict_taxonomy_note"])
    A("")
    A("## Runs re-scored")
    A("")
    A("| arm | seed | run |")
    A("|---|---|---|")
    for k in sorted(r["runs"]):
        arm, seed = k.split("|", 1)
        A(f"| {arm} | {seed} | `{r['runs'][k]}` |")
    A("")
    return "\n".join(out) + "\n"


def main() -> None:
    out_json = ROOT / "reports/x3_seed3_corrosion_replication_v1.json"
    out_md = ROOT / "reports/x3_seed3_corrosion_replication_v1.md"

    if "--md-only" in sys.argv:
        # Re-render the markdown view from the already-written JSON. Numbers are
        # read back from the JSON, never recomputed differently.
        payload = json.loads(out_json.read_text(encoding="utf-8"))
        out_md.write_text(render_md(payload), encoding="utf-8")
        print(
            json.dumps(
                {
                    "md_only": True,
                    "json_sha256": hashlib.sha256(out_json.read_bytes()).hexdigest(),
                    "md_sha256": hashlib.sha256(out_md.read_bytes()).hexdigest(),
                },
                sort_keys=True,
            )
        )
        return

    if out_json.exists() or out_md.exists():
        raise FileExistsError("refusing to overwrite existing seed-3 replication artifacts")

    registry_rows: dict[str, dict[str, Any]] = {}
    registry_path = ROOT / "data/fliptrack_r19_visual_evidence_candidates_v1.jsonl"
    for line in registry_path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("template_id") == TEMPLATE:
            registry_rows[str(row["pair_id"])] = row
    sources: dict[str, dict[str, Any]] = {}
    for name in ("fliptrack_v02r10_source_manifest.jsonl", "fliptrack_v02r18_source_manifest.jsonl"):
        for line in (ROOT / "data" / name).read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row.get("template_id") == TEMPLATE:
                sources[str(row["pair_id"])] = row
    scenes: dict[str, dict[str, Any]] = {}
    for pair_id, registry_row in registry_rows.items():
        source_id = str(registry_row.get("source_pair_id") or pair_id)
        scenes[pair_id] = replay_scene(int(sources[source_id]["provenance"]["pair_seed"]))

    lenient = {key: load_scored(run) for key, run in RUNS.items()}
    strict = {key: load_scored_strict(run) for key, run in RUNS.items()}

    res_lenient = analyse(lenient, scenes, registry_rows, strict_mode=False)
    res_strict = analyse(strict, scenes, registry_rows, strict_mode=True)

    try:
        git_hash = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(ROOT), capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        git_hash = None

    # ---- agreement check: recomputed lenient seed-1/2 values vs the frozen v1 report ----
    frozen_path = ROOT / "reports/x3_a2_degradation_forensics_v1.json"
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    checks: list[dict[str, Any]] = []

    def chk(name: str, frozen_value: Any, recomputed_value: Any) -> None:
        checks.append(
            {
                "field": name,
                "frozen_v1": frozen_value,
                "recomputed": recomputed_value,
                "equal": frozen_value == recomputed_value,
            }
        )

    L = res_lenient
    chk("base_pair_accuracy", frozen["base_pair_accuracy"], L["base_pair_accuracy"])
    for seed in ("seed1", "seed2"):
        for key in (
            "a2_pair_accuracy",
            "net_delta_vs_base",
            "degraded_correct_to_wrong",
            "gained_wrong_to_correct",
            "member_direction",
            "transition_taxonomy",
        ):
            chk(f"per_seed.{seed}.{key}", frozen["per_seed"][seed][key], L["per_seed"][seed][key])
    for key in ("intersection", "union", "jaccard"):
        chk(f"overlap.seed1_seed2.{key}", frozen["overlap"][key], L["overlap"]["seed1__seed2"][key])
    for key in ("shared_wrong_member_slots", "same_extracted_wrong_answer", "rate"):
        chk(
            f"same_wrong_answer.seed1_seed2.{key}",
            frozen["same_wrong_answer"][key],
            L["same_wrong_answer"]["seed1__seed2"][key],
        )
    agreement = {
        "reference_report": "reports/x3_a2_degradation_forensics_v1.json",
        "reference_sha256": hashlib.sha256(frozen_path.read_bytes()).hexdigest(),
        "fields_checked": len(checks),
        "fields_equal": sum(1 for c in checks if c["equal"]),
        "all_equal": all(c["equal"] for c in checks),
        "checks": checks,
        "null_not_compared_note": (
            "The seed1-vs-seed2 permutation null is recomputed here with permutation seed "
            f"{SEED3} and is therefore a different random draw from the frozen v1 null "
            f"(seed {frozen['overlap']['permutation_seed']}); it is reported side by side, "
            "not asserted equal."
        ),
        "frozen_seed1_seed2_null_mean_jaccard": frozen["overlap"]["permutation_null_mean_jaccard"],
        "recomputed_seed1_seed2_null_mean_jaccard": L["overlap"]["seed1__seed2"]["permutation_null"][
            "null_mean_jaccard"
        ],
        "frozen_seed1_seed2_permutation_p_value": frozen["overlap"]["permutation_p_value"],
        "recomputed_seed1_seed2_permutation_p_value": L["overlap"]["seed1__seed2"]["permutation_null"][
            "p_value"
        ],
    }

    result = {
        "schema_version": "blind-gains.x3-seed3-corrosion-replication.v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_hash": git_hash,
        "template": TEMPLATE,
        "scorer": "src.eval.fliptrack_metrics.pair_score (current canonical parser, uniform re-score of cached predictions)",
        "method_source": "scripts/x3_a2_degradation_forensics.py (helpers imported, not transcribed)",
        "method_note": (
            "load_scored, extract_answer, classify_wrong, feature_vector and "
            "perm_pvalue_mean_diff are imported from the frozen seed-1/2 script. "
            "Every number in this file is recomputed from cached predictions; "
            "no value is copied from reports/x3_a2_degradation_forensics_v1.json."
        ),
        "strict_taxonomy_note": (
            "In the contract-strict track a member slot can be wrong solely because the "
            "response violates the answer-tag contract while still carrying the gold value. "
            "Those slots are labelled gold_value_contract_invalid; the frozen classifier is "
            "applied unchanged to all other strict-wrong slots."
        ),
        "runs": {f"{k[0]}|{k[1]}": v for k, v in RUNS.items()},
        "seed3_marker_chain": {
            "results_file": "reports/pilot_4arm_seed3_results_v1.json",
            "marker": "experiments/runs/mech_a2_gray_seed3_an12_20260722T145916Z/step100_fliptrack_complete.json",
            "evaluation_run": RUNS[("a2", "seed3")],
        },
        "permutation_seed_seed3": SEED3,
        "permutations": N_PERM,
        "bootstrap_resamples": N_BOOT,
        "frozen_v1_agreement": agreement,
        "lenient": res_lenient,
        "strict": res_strict,
    }

    out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md.write_text(render_md(result), encoding="utf-8")
    print(
        json.dumps(
            {
                "agreement_all_equal": agreement["all_equal"],
                "agreement_fields": [agreement["fields_equal"], agreement["fields_checked"]],
                "lenient_seed3_delta": L["per_seed"]["seed3"]["net_delta_vs_base"],
                "lenient_seed3_degraded": L["per_seed"]["seed3"]["degraded_correct_to_wrong"],
                "lenient_j31": L["overlap"]["seed3__seed1"]["jaccard"],
                "lenient_j32": L["overlap"]["seed3__seed2"]["jaccard"],
                "lenient_j3way": L["overlap"]["three_seed"]["jaccard3"],
                "json_sha256": hashlib.sha256(out_json.read_bytes()).hexdigest(),
                "md_sha256": hashlib.sha256(out_md.read_bytes()).hexdigest(),
            },
            sort_keys=True,
        )
    )
    print("WROTE", out_json)
    print("WROTE", out_md)


if __name__ == "__main__":
    main()
