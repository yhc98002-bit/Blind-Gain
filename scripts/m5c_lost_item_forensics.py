#!/usr/bin/env python3
"""M5c — geo3k lost-item forensics (CPU only, cached predictions only).

Takes the five cached geo3k checkpoint evals (steps 100/150/200/300/400), rebuilds
the step-100 -> step-400 LOST / GAINED sets under BOTH acc_final (lenient) and
acc_strict (contract-strict), and runs the registered forensics:

  1. set sizes
  2. step-400 wrong-answer value distribution on the LOST set + concentration
     statistics against a permutation null drawn from the step-400 error pool
  3. structure of the LOST set against a permutation null of equal-size random
     subsets drawn from the step-100-correct pool (3-way checkpoint Jaccard,
     gold-answer concentration, derived-bucket concentration)
  4. dataset metadata availability + derived (analysis-defined, NOT dataset)
     buckets for LOST and GAINED
  5. geo3k-native repetition / persistence / near-miss structure

The FlipTrack gray-arm attractor taxonomy is NOT transplanted; see the SCOPE
block in the emitted artifacts. Facts only; no interpretation text.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
sys.path.insert(0, str(ROOT))

import numpy as np

from src.eval.blind_solvability import score_greedy_item_pilot
from src.rewards.answer_reward import normalize_answer, numeric_value

N_PERM = 10_000
SEED = 20260729
P_FLOOR = 1e-4
STEPS = (100, 150, 200, 300, 400)

RUNS = {
    100: "blind_solvability_v2_guarded_rescore_anchor_step100_geo3k_real_login_20260712T082107Z",
    150: "m5_geo3k_step150_an12_gpu4_20260718T051839Z",
    200: "m5_geo3k_step200_an29_gpu4_20260722T141052Z",
    300: "m5_geo3k_step300_an12_gpu0_20260726T083303Z",
    400: "m5_geo3k_step400_an12_gpu0_20260728T053115Z",
}

# step 100 is the guarded-rescore schema; 150-400 are the M5 checkpoint-eval schema.
FIELDS = {
    100: {
        "acc_final": "greedy_correct",
        "acc_strict": "greedy_acc_strict",
        "extracted_answer": "greedy_extracted_answer",
        "contract_valid": "greedy_contract_valid",
        "extractor_valid": "greedy_extractor_valid",
        "response": "greedy_response",
    },
    "default": {
        "acc_final": "acc_final",
        "acc_strict": "acc_strict",
        "extracted_answer": "extracted_answer",
        "contract_valid": "contract_valid",
        "extractor_valid": "extractor_valid",
        "response": "greedy_response",
    },
}

METRICS = ("acc_final", "acc_strict")

# Registered, ordered derived-bucket rules. These are DEFINED BY THIS ANALYSIS
# from the problem string; geo3k carries no template/category/source field.
STEM_RULES: list[tuple[str, str]] = [
    ("area", r"\barea\b"),
    ("perimeter", r"\bperimeter\b"),
    ("circumference", r"\bcircumference\b"),
    ("volume", r"\bvolume\b"),
    ("arc_measure", r"\\widehat|\barc\b"),
    ("angle_measure", r"\\angle|∠|\bm\s*\\angle"),
    ("ratio", r"\bratio\b"),
    ("length_measure", r"\blength\b|\bmeasure\b|\bperimeter\b"),
    ("solve_for_variable", r"\bfind\s+\$?\\?[xyz]\$?\b|\bfind\s+the\s+value\b"),
]


def stem_bucket(problem: str) -> str:
    text = problem.replace("<image>", " ").strip().lower()
    for name, pattern in STEM_RULES:
        if re.search(pattern, text):
            return name
    return "other"


def gold_type(gold: str) -> str:
    value = numeric_value(normalize_answer(gold))
    if value is None:
        return "non_numeric"
    return "integer" if abs(value - round(value)) < 1e-9 else "decimal"


def canon(value: Any) -> str:
    """Canonical equivalence class for an answer string.

    Numeric values are bucketed at 1e-6 resolution so that '48' and '48.0' land in
    the same class (the canonical scorer matches numerically at tol 1e-4); every
    non-numeric value keeps its normalized text form.
    """
    text = normalize_answer(value)
    number = numeric_value(text)
    if number is None:
        return f"txt::{text}"
    return f"num::{round(float(number), 6):.6f}"


def load_run(step: int) -> dict[str, dict[str, Any]]:
    path = ROOT / "experiments/runs" / RUNS[step] / "per_item.jsonl"
    fmap = FIELDS.get(step, FIELDS["default"])
    out: dict[str, dict[str, Any]] = {}
    total = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        total += 1
        if row.get("split") != "test":
            continue
        key = f"{row['split']}:{row['row_index']}"
        if key in out:
            raise ValueError(f"duplicate item key {key} at step {step}")
        out[key] = {
            "acc_final": bool(row[fmap["acc_final"]]),
            "acc_strict": bool(row[fmap["acc_strict"]]),
            "extracted_answer": row.get(fmap["extracted_answer"]),
            "contract_valid": bool(row[fmap["contract_valid"]]),
            "extractor_valid": bool(row[fmap["extractor_valid"]]),
            "response": str(row.get(fmap["response"], "")),
            "ground_truth": str(row["ground_truth"]),
            "problem": str(row["problem"]),
            "qid": row.get("qid"),
            "source_metadata": row.get("source_metadata"),
            "total_rows_in_file": total,
        }
    return out


def entropy_bits(counts: list[int]) -> float:
    n = sum(counts)
    if n <= 0:
        return 0.0
    return float(-sum((c / n) * math.log2(c / n) for c in counts if c > 0))


def concentration(values: list[str]) -> dict[str, Any]:
    counts = Counter(values)
    n = len(values)
    freqs = list(counts.values())
    h = entropy_bits(freqs)
    max_h = math.log2(n) if n > 1 else 0.0
    return {
        "n_values": n,
        "n_distinct": len(counts),
        "shannon_entropy_bits": h,
        "max_entropy_bits": max_h,
        "normalized_entropy": (h / max_h) if max_h > 0 else None,
        "hhi": float(sum((c / n) ** 2 for c in freqs)) if n else None,
        "top1_share": (max(freqs) / n) if n else None,
        "share_in_repeated_value": (sum(c for c in freqs if c >= 2) / n) if n else None,
        "distinct_per_item": (len(counts) / n) if n else None,
    }


def p_from_hits(hits: int, n_perm: int) -> float:
    return max((hits + 1) / (n_perm + 1), P_FLOOR)


def jaccard(*sets: set[str]) -> float:
    union: set[str] = set()
    for s in sets:
        union |= s
    if not union:
        return 0.0
    inter = set(sets[0])
    for s in sets[1:]:
        inter &= s
    return len(inter) / len(union)


def fmt_p(p: float) -> str:
    return f"<= {P_FLOOR:.0e}" if p <= P_FLOOR else f"{p:.4f}"


def render_markdown(r: dict[str, Any]) -> str:
    v = r["verification"]
    L = []
    L.append("# M5c — geo3k step-100 -> step-400 lost-item forensics (v1)")
    L.append("")
    L.append(f"Generated {r['generated_utc']}. CPU only; cached predictions only; no GPU job was started.")
    L.append("Facts, checks and provenance only.")
    L.append("")
    L.append("## Provenance")
    L.append("")
    L.append(f"- Dataset: {r['dataset']}")
    L.append(f"- Scorer: `{r['scorer']}`")
    L.append(f"- Answer canonicalization: {r['answer_canonicalization']}")
    L.append(
        "- Permutation convention: p = (hits + 1) / (n_perm + 1), n_perm = "
        f"{r['permutation_convention']['n_perm']}, seed = {r['permutation_convention']['seed']}, "
        f"reported as max(p, {r['permutation_convention']['p_floor']:.0e}). "
        f"{r['permutation_convention']['note']}"
    )
    L.append("- Cached runs:")
    for step in STEPS:
        L.append(f"  - step {step}: `experiments/runs/{r['runs'][str(step)]}/per_item.jsonl`")
    L.append("")
    L.append("## Verification (all checks run in code)")
    L.append("")
    L.append("| check | result |")
    L.append("|---|---|")
    L.append(f"| test items per step (100/150/200/300/400) | {'/'.join(str(v['test_item_counts'][str(s)]) for s in STEPS)} |")
    L.append(f"| item-key sets identical across all five steps | {v['item_key_sets_identical']} |")
    L.append(f"| ground_truth identical across all five steps | {v['gold_identical_across_steps']} |")
    L.append(f"| problem sha256 identical across all five steps | {v['problem_sha256_identical_across_steps']} |")
    L.append(f"| step-100 file rows / non-test rows excluded (I13) | {v['step100_file_total_rows']} / {v['non_test_rows_excluded_step100']} |")
    L.append(
        "| canonical re-score mismatches vs stored (per step) | "
        + "/".join(str(v["rescore_mismatches_vs_stored"][str(s)]) for s in STEPS)
        + " |"
    )
    L.append(f"| substrate rows cross-checked / value mismatches | {v['substrate_rows']} / {v['substrate_value_mismatches_vs_runs']} |")
    L.append(
        "| items where acc_final == acc_strict (per step) | "
        + "/".join(str(v["acc_final_equals_acc_strict_per_item"][str(s)]) for s in STEPS)
        + " of 601 |"
    )
    L.append("")
    L.append("Level series reproduced from the cached runs (I7: both metrics):")
    L.append("")
    L.append("| metric | 100 | 150 | 200 | 300 | 400 |")
    L.append("|---|---|---|---|---|---|")
    for metric in METRICS:
        L.append(
            f"| {metric} | " + " | ".join(f"{v['level_series'][metric][str(s)]:.4f}" for s in STEPS) + " |"
        )
    L.append("")
    L.append(
        "acc_final == acc_strict on all 601 items at all five steps, so every table below is "
        "numerically identical under the lenient and the contract-strict metric. Both are reported "
        "and stored separately (I7); they are not collapsed."
    )
    L.append("")

    L.append("## SCOPE LIMIT — the FlipTrack taxonomy is not transplanted")
    L.append("")
    L.append(r["scope_limits"]["fliptrack_taxonomy_not_transplanted"])
    L.append("")
    L.append("Geo3k-native structure probes used instead:")
    for item in r["scope_limits"]["geo3k_analogues_used_instead"]:
        L.append(f"- {item}")
    L.append("")
    L.append(r["scope_limits"]["checkpoint_sets_are_not_independent_seeds"])
    L.append("")

    L.append("## 1. Set sizes (step 100 -> step 400)")
    L.append("")
    L.append("| quantity | acc_final (lenient) | acc_strict (contract-strict) |")
    L.append("|---|---|---|")
    order = [
        ("n_items", "test items"),
        ("correct_step100", "correct at step 100"),
        ("correct_step400", "correct at step 400"),
        ("lost_100_400", "LOST (correct@100, wrong@400)"),
        ("gained_100_400", "GAINED (wrong@100, correct@400)"),
        ("stable_correct", "stable correct"),
        ("stable_wrong", "stable wrong"),
        ("net_delta_items", "net delta (items)"),
        ("turnover_items", "turnover (lost + gained)"),
        ("lost_100_200", "LOST at 100->200"),
        ("lost_100_300", "LOST at 100->300"),
    ]
    for key, label in order:
        L.append(
            f"| {label} | {r['set_sizes']['acc_final'][key]} | {r['set_sizes']['acc_strict'][key]} |"
        )
    L.append(
        f"| net delta (accuracy) | {r['set_sizes']['acc_final']['net_delta_accuracy']:+.4f} |"
        f" {r['set_sizes']['acc_strict']['net_delta_accuracy']:+.4f} |"
    )
    L.append("")

    L.append("## 2. Step-400 wrong answers on the LOST set: concentrated or dispersed?")
    L.append("")
    w = r["wrong_answer_distribution_on_lost_set"]["acc_final"]
    L.append(
        f"- LOST items: {w['lost_n']}. Contract-valid step-400 answers: {w['lost_contract_valid_at_step400']};"
        f" contract-invalid (no extractable value): {w['lost_contract_invalid_at_step400']}."
        " The concentration statistics below are computed on the contract-valid answers only."
    )
    o = w["observed_concentration"]
    L.append(
        f"- Distinct wrong values: {o['n_distinct']} over {o['n_values']} answers"
        f" ({o['distinct_per_item']:.4f} distinct per item)."
    )
    L.append(
        f"- Largest multiplicity of any single wrong value: {w['max_multiplicity_of_any_single_wrong_value']}"
        f" ({w['n_values_appearing_twice_or_more']} values occur twice; none occurs three or more times)."
    )
    L.append(
        f"- Shannon entropy {o['shannon_entropy_bits']:.4f} bits (max possible {o['max_entropy_bits']:.4f};"
        f" normalized {o['normalized_entropy']:.4f}); HHI {o['hhi']:.6f}; top-1 share {o['top1_share']:.4f};"
        f" share of items sitting on a repeated value {o['share_in_repeated_value']:.4f}."
    )
    L.append("")
    L.append("Permutation nulls (equal-size draws of step-400 wrong answers, same seed and convention):")
    L.append("")
    L.append("| null pool | pool n | draw n | null mean entropy (bits) | p(entropy <= obs) | p(HHI >= obs) | p(distinct <= obs) |")
    L.append("|---|---|---|---|---|---|---|")
    for null_name, blk in w["permutation_nulls"].items():
        L.append(
            f"| {null_name} | {blk['pool_size']} | {blk['draw_size']} | {blk['null_mean_entropy_bits']:.4f}"
            f" | {fmt_p(blk['p_entropy_le_observed'])} | {fmt_p(blk['p_hhi_ge_observed'])}"
            f" | {fmt_p(blk['p_n_distinct_le_observed'])} |"
        )
    L.append("")
    L.append(
        "`stable_wrong_only` is the role-clean null (items wrong at BOTH 100 and 400, disjoint from LOST);"
        " `all_step400_errors` includes the LOST items themselves in the pool and is reported for completeness."
    )
    L.append("")
    sw = w["stable_wrong_reference_concentration"]
    L.append(
        f"Reference group, reported separately and NOT pooled with LOST (I13): the stable-wrong set"
        f" ({sw['n_values']} contract-valid step-400 answers, {w['stable_wrong_contract_invalid_at_step400']} contract-invalid)"
        f" has {sw['n_distinct']} distinct values, entropy {sw['shannon_entropy_bits']:.4f} bits,"
        f" normalized {sw['normalized_entropy']:.4f}, HHI {sw['hhi']:.6f}."
        " Raw entropies are not comparable across different n; the matched-size permutation null above is the comparison."
    )
    L.append("")
    L.append("Most frequent step-400 wrong values on the LOST set:")
    L.append("")
    L.append("| canonical wrong value | count in LOST | items in the test split whose gold equals this value |")
    L.append("|---|---|---|")
    for row in w["top_values"]:
        L.append(f"| `{row['value']}` | {row['count']} | {row['n_items_with_this_gold_in_test']} |")
    L.append("")

    L.append("## 3. Is the LOST set more structured than a random equal-size subset of step-100-correct items?")
    L.append("")
    s = r["lost_set_structure_vs_step100_correct_null"]["acc_final"]
    L.append(
        f"Null pool: {s['pool']} (n = {s['pool_size']}). "
        f"{N_PERM} draws, seed {SEED}, p = (hits+1)/(perms+1) floored at {P_FLOOR:.0e}."
    )
    L.append("")
    j3 = s["three_way_jaccard"]
    L.append(
        f"- 3-way Jaccard of LOST(100->200) [n={s['lost_set_sizes']['100_200']}],"
        f" LOST(100->300) [n={s['lost_set_sizes']['100_300']}] and"
        f" LOST(100->400) [n={s['lost_set_sizes']['100_400']}]:"
        f" **{j3['observed']:.4f}** vs permutation null mean {j3['null_mean']:.4f}"
        f" (sd {j3['null_sd']:.4f}), p {fmt_p(j3['p_ge_observed'])}."
    )
    for name, blk in s["pairwise_jaccard"].items():
        L.append(f"- Pairwise Jaccard {name}: {blk['observed']:.4f}, p {fmt_p(blk['p_ge_observed'])}.")
    L.append(
        f"- Share of LOST(100->400) items that were already lost at BOTH 100->200 and 100->300:"
        f" {s['lost_400_also_lost_at_200_and_300_share']:.4f}."
    )
    g = s["gold_answer_concentration"]
    L.append(
        f"- Gold-answer concentration inside LOST: entropy {g['observed']['shannon_entropy_bits']:.4f} bits"
        f" over {g['observed']['n_distinct']} distinct gold values in {g['observed']['n_values']} items;"
        f" null mean {g['null_mean_entropy_bits']:.4f} bits; p(entropy <= obs) {fmt_p(g['p_entropy_le_observed'])}."
    )
    b = s["derived_bucket_concentration"]
    L.append(
        f"- Derived-bucket composition of LOST vs the step-100-correct pool: chi-square {b['observed_chi2']:.4f}"
        f" vs null mean {b['null_mean_chi2']:.4f}; p {fmt_p(b['p_chi2_ge_observed'])}"
        " (uncorrected; see the multiplicity section)."
    )
    L.append("")
    L.append("| derived bucket | observed in LOST | expected from step-100-correct pool |")
    L.append("|---|---|---|")
    for bname in sorted(b["expected_counts_from_pool"]):
        L.append(
            f"| {bname} | {b['observed_counts'].get(bname, 0)} | {b['expected_counts_from_pool'][bname]:.2f} |"
        )
    L.append("")

    L.append("## 4. Template / category / source metadata")
    L.append("")
    md = r["metadata_availability"]
    L.append(
        f"**No template, category or source field exists for geo3k in this repository.** Checked in code:"
    )
    L.append(
        f"- The dataset manifest `{md['dataset_manifest']}` has exactly one field set across all"
        f" {sum(md['manifest_field_sets'].values())} rows: `"
        + "`, `".join(sorted(md["manifest_field_sets"])[0].split("|"))
        + "`. There is no template id, no category, no sub-source, no generator seed."
    )
    qid_counts = ", ".join(f"step {s}: {md['eval_row_qid_non_null_count'][str(s)]}" for s in STEPS)
    sm_counts = ", ".join(
        f"step {s}: {md['eval_row_source_metadata_non_null_count'][str(s)]}" for s in STEPS
    )
    L.append(
        "- `qid` is null in all 601 test rows at every one of the five steps"
        f" (non-null counts — {qid_counts})."
    )
    L.append(
        "- `source_metadata` is null in all 601 test rows at every one of the five steps"
        f" (non-null counts — {sm_counts})."
    )
    L.append("")
    L.append(
        "Because no such field exists, the buckets below are **derived by this analysis** from the"
        " problem string by a fixed ordered regex cascade. They are not dataset metadata and must not"
        " be cited as such. Rules, in order of application:"
    )
    L.append("")
    L.append("| order | bucket | regex (applied to lowercased problem with `<image>` stripped) |")
    L.append("|---|---|---|")
    for idx, rule in enumerate(md["derived_bucket_rules_in_order"], start=1):
        L.append(f"| {idx} | {rule['name']} | `{rule['regex']}` |")
    L.append("| fallback | other | (no rule matched) |")
    L.append("")
    dt_ = r["derived_bucket_tables"]["acc_final"]
    L.append("LOST and GAINED by derived stem bucket:")
    L.append("")
    L.append(
        "| derived bucket | all test items | correct@100 | wrong@100 | LOST | lost rate within correct@100 | GAINED | gained rate within wrong@100 |"
    )
    L.append("|---|---|---|---|---|---|---|---|")
    for bname, row in dt_["by_derived_stem_bucket"].items():
        lr = "n/a" if row["lost_rate_within_correct_at_100"] is None else f"{row['lost_rate_within_correct_at_100']:.4f}"
        gr = "n/a" if row["gained_rate_within_wrong_at_100"] is None else f"{row['gained_rate_within_wrong_at_100']:.4f}"
        L.append(
            f"| {bname} | {row['all_test_items']} | {row['correct_at_100']} | {row['wrong_at_100']}"
            f" | {row['lost']} | {lr} | {row['gained']} | {gr} |"
        )
    L.append("")
    gb = dt_["gained_bucket_concentration_vs_wrong_at_100_pool"]
    L.append(
        f"Concentration test for GAINED against its own reference pool (items wrong at step 100,"
        f" n = {gb['pool_size']}; draw n = {gb['draw_size']}): chi-square {gb['observed_chi2']:.4f},"
        f" p {fmt_p(gb['p_chi2_ge_observed'])}."
        " LOST and GAINED are tested against different pools and are never pooled with each other (I13)."
    )
    L.append("")
    L.append("LOST and GAINED by derived gold-answer type:")
    L.append("")
    L.append("| gold type | all test items | correct@100 | wrong@100 | LOST | GAINED |")
    L.append("|---|---|---|---|---|---|")
    for tname, row in dt_["by_derived_gold_type"].items():
        L.append(
            f"| {tname} | {row['all_test_items']} | {row['correct_at_100']} | {row['wrong_at_100']}"
            f" | {row['lost']} | {row['gained']} |"
        )
    L.append("")

    L.append("## 5. Geo3k-native structure probes (LOST vs stable-wrong reference)")
    L.append("")
    n = r["geo3k_native_structure_probes"]["acc_final"]
    lo, rf, pv = n["lost_set"], n["stable_wrong_reference_set"], n["permutation_vs_stable_wrong_null"]
    L.append(
        f"LOST n = {lo['n_items']} ({lo['n_contract_valid_at_step400']} contract-valid at step 400);"
        f" stable-wrong reference n = {rf['n_items']} ({rf['n_contract_valid_at_step400']} contract-valid)."
        " The two groups hold different scientific roles and are reported side by side, never pooled."
    )
    L.append("")
    L.append("| probe | LOST | stable-wrong reference | permutation p vs stable-wrong null |")
    L.append("|---|---|---|---|")
    L.append(
        f"| step-400 wrong value equals some other test item's gold |"
        f" {lo['wrong_value_equals_some_other_test_item_gold']['count']}/{lo['n_contract_valid_at_step400']}"
        f" = {lo['wrong_value_equals_some_other_test_item_gold']['rate']:.4f} |"
        f" {rf['wrong_value_equals_some_other_test_item_gold']['count']}/{rf['n_contract_valid_at_step400']}"
        f" = {rf['wrong_value_equals_some_other_test_item_gold']['rate']:.4f} |"
        f" {fmt_p(pv['p_other_gold_rate_ge_observed'])} |"
    )
    L.append(
        f"| numeric near-miss: within 10% of own gold |"
        f" {lo['numeric_near_miss_within_10pct_of_own_gold']['count']}/{lo['numeric_near_miss_within_10pct_of_own_gold']['numeric_comparable']}"
        f" = {lo['numeric_near_miss_within_10pct_of_own_gold']['rate']:.4f} |"
        f" {rf['numeric_near_miss_within_10pct_of_own_gold']['count']}/{rf['numeric_near_miss_within_10pct_of_own_gold']['numeric_comparable']}"
        f" = {rf['numeric_near_miss_within_10pct_of_own_gold']['rate']:.4f} |"
        f" {fmt_p(pv['p_near_miss_rate_ge_observed'])} |"
    )
    L.append(
        f"| small integer 1..20 | {lo['small_integer_1_to_20']['count']}/{lo['n_contract_valid_at_step400']}"
        f" = {lo['small_integer_1_to_20']['rate']:.4f} |"
        f" {rf['small_integer_1_to_20']['count']}/{rf['n_contract_valid_at_step400']}"
        f" = {rf['small_integer_1_to_20']['rate']:.4f} | not tested |"
    )
    L.append("")
    L.append("Temporal persistence of the step-400 wrong value (same canonical value at an earlier step):")
    L.append("")
    L.append("| earlier step | LOST: same value / comparable | rate | stable-wrong: same value / comparable | rate |")
    L.append("|---|---|---|---|---|")
    for prev in ("150", "200", "300"):
        a = lo["same_step400_value_as_earlier_step"][prev]
        c = rf["same_step400_value_as_earlier_step"][prev]
        L.append(
            f"| {prev} | {a['same_value_as_step400']}/{a['comparable_items']} | {a['rate']:.4f}"
            f" | {c['same_value_as_step400']}/{c['comparable_items']} | {c['rate']:.4f} |"
        )
    L.append("")

    L.append("## Multiplicity")
    L.append("")
    mp = r["multiplicity"]
    L.append(
        f"{mp['n_tests_in_family']} permutation tests form the pre-listed family."
        f" Bonferroni threshold at alpha {mp['family_alpha']} is {mp['bonferroni_threshold']:.5f}."
        f" {mp['note']}"
    )
    L.append("")
    L.append("| test | raw p | Holm-Bonferroni reject at alpha 0.05 |")
    L.append("|---|---|---|")
    for name, p in sorted(mp["tests"].items(), key=lambda x: x[1]):
        L.append(f"| {name} | {fmt_p(p)} | {mp['holm_bonferroni_reject'][name]} |")
    L.append("")

    L.append("## What could not be computed")
    L.append("")
    L.append(
        "- Wrong-answer concentration cannot be compared against a null drawn from step-100-correct"
        " items in general, because items that are correct at step 400 emit no wrong value. The"
        " matched-size null for that statistic is therefore drawn from the step-400 error pool"
        " (section 2), and the step-100-correct null in section 3 is applied to set-membership and"
        " item-attribute statistics only. No proxy was silently substituted."
    )
    L.append(
        "- The near-miss contrast in section 5 is NOT difficulty-controlled. LOST items were correct"
        " at step 100 and the stable-wrong reference items were not, so the two groups differ in"
        " step-100 solvability by construction. The permutation null resamples inside the"
        " stable-wrong group only and therefore does not remove that difference. A difficulty-matched"
        " null would need a step-100 solvability score per item (for example p_i from the guarded"
        " rescore run) carried into a matched-resampling design; that was not built here."
    )
    L.append(
        "- GAINED items are correct at step 400 by construction, so they emit no wrong value and no"
        " wrong-answer distribution is computable for them. Section 2 covers LOST only; GAINED"
        " appears in the set-size and derived-bucket tables."
    )
    L.append(
        "- Independent-seed replication of the geo3k step-400 checkpoint does not exist in the cache,"
        " so the FlipTrack cross-seed Jaccard cannot be reproduced on geo3k. The 3-way Jaccard here"
        " uses three checkpoints of one trajectory and is a different quantity."
    )
    L.append(
        "- The reference run emits two `macro '\\frac' failed its substitution` warnings from the"
        " symbolic grader on latex-shaped answers. They come from the canonical scorer, are present"
        " in the original cached runs' scoring path as well, and did not change any score:"
        " re-scoring reproduced the stored acc_final and acc_strict on 601/601 items at all five steps."
    )
    L.append("")
    return "\n".join(L)


def main() -> None:
    out_json = ROOT / "reports/m5c_lost_item_forensics_v1.json"
    out_md = ROOT / "reports/m5c_lost_item_forensics_v1.md"

    runs = {step: load_run(step) for step in STEPS}

    # ---------------- verification ----------------
    verification: dict[str, Any] = {}
    keys_100 = set(runs[100])
    verification["test_item_counts"] = {str(s): len(runs[s]) for s in STEPS}
    verification["step100_file_total_rows"] = max(
        r["total_rows_in_file"] for r in runs[100].values()
    )
    verification["non_test_rows_excluded_step100"] = (
        verification["step100_file_total_rows"] - len(runs[100])
    )
    verification["item_key_sets_identical"] = all(set(runs[s]) == keys_100 for s in STEPS)
    verification["gold_identical_across_steps"] = all(
        runs[s][k]["ground_truth"] == runs[100][k]["ground_truth"] for s in STEPS for k in keys_100
    )
    verification["problem_sha256_identical_across_steps"] = all(
        hashlib.sha256(runs[s][k]["problem"].encode()).hexdigest()
        == hashlib.sha256(runs[100][k]["problem"].encode()).hexdigest()
        for s in STEPS
        for k in keys_100
    )
    # uniform re-score of every cached greedy response with the canonical scorer
    rescore_mismatch = {str(s): 0 for s in STEPS}
    for step in STEPS:
        for key, row in runs[step].items():
            fresh = score_greedy_item_pilot(row["ground_truth"], row["response"])
            if (
                bool(fresh["acc_final"]) != row["acc_final"]
                or bool(fresh["acc_strict"]) != row["acc_strict"]
            ):
                rescore_mismatch[str(step)] += 1
    verification["rescore_mismatches_vs_stored"] = rescore_mismatch
    verification["level_series"] = {
        m: {
            str(s): sum(1 for r in runs[s].values() if r[m]) / len(runs[s]) for s in STEPS
        }
        for m in METRICS
    }
    verification["acc_final_equals_acc_strict_per_item"] = {
        str(s): sum(1 for r in runs[s].values() if r["acc_final"] == r["acc_strict"])
        for s in STEPS
    }
    # cross-check against the shared substrate written by the prior stage
    substrate_path = ROOT / "reports/m5c_item_substrate_v1.jsonl"
    sub_mismatch = 0
    sub_n = 0
    for line in substrate_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        sub_n += 1
        key = row["item_key"]
        for step in STEPS:
            for metric in METRICS:
                if bool(row[f"{metric}_step{step}"]) != runs[step][key][metric]:
                    sub_mismatch += 1
    verification["substrate_rows"] = sub_n
    verification["substrate_value_mismatches_vs_runs"] = sub_mismatch

    keys = sorted(keys_100, key=lambda k: int(k.split(":")[1]))
    gold = {k: runs[100][k]["ground_truth"] for k in keys}
    problem = {k: runs[100][k]["problem"] for k in keys}
    bucket = {k: stem_bucket(problem[k]) for k in keys}
    gtype = {k: gold_type(gold[k]) for k in keys}

    # ---------------- sets ----------------
    sets: dict[str, dict[str, Any]] = {}
    for metric in METRICS:
        correct = {s: {k for k in keys if runs[s][k][metric]} for s in STEPS}
        lost_400 = correct[100] - correct[400]
        gained_400 = correct[400] - correct[100]
        sets[metric] = {
            "correct": correct,
            "lost_100_400": lost_400,
            "gained_100_400": gained_400,
            "stable_correct": correct[100] & correct[400],
            "stable_wrong": set(keys) - correct[100] - correct[400],
            "lost_100_200": correct[100] - correct[200],
            "lost_100_300": correct[100] - correct[300],
            "wrong_400": set(keys) - correct[400],
            "wrong_100": set(keys) - correct[100],
        }

    set_sizes = {
        metric: {
            "n_items": len(keys),
            "correct_step100": len(sets[metric]["correct"][100]),
            "correct_step400": len(sets[metric]["correct"][400]),
            "lost_100_400": len(sets[metric]["lost_100_400"]),
            "gained_100_400": len(sets[metric]["gained_100_400"]),
            "stable_correct": len(sets[metric]["stable_correct"]),
            "stable_wrong": len(sets[metric]["stable_wrong"]),
            "net_delta_items": len(sets[metric]["gained_100_400"])
            - len(sets[metric]["lost_100_400"]),
            "net_delta_accuracy": (
                len(sets[metric]["gained_100_400"]) - len(sets[metric]["lost_100_400"])
            )
            / len(keys),
            "turnover_items": len(sets[metric]["lost_100_400"])
            + len(sets[metric]["gained_100_400"]),
            "lost_100_200": len(sets[metric]["lost_100_200"]),
            "lost_100_300": len(sets[metric]["lost_100_300"]),
        }
        for metric in METRICS
    }

    # ---------------- 2. wrong-answer distribution on LOST at step 400 ----------------
    # precompute canonical answer values once per (step, item)
    VAL: dict[int, dict[str, str | None]] = {
        s: {
            k: (canon(runs[s][k]["extracted_answer"]) if runs[s][k]["contract_valid"] else None)
            for k in keys
        }
        for s in STEPS
    }

    def value_of(step: int, key: str) -> str | None:
        return VAL[step][key]

    wrong_answer_block: dict[str, Any] = {}
    for metric in METRICS:
        lost = sorted(sets[metric]["lost_100_400"])
        stable_wrong = sorted(sets[metric]["stable_wrong"])
        wrong_pool = sorted(sets[metric]["wrong_400"])

        lost_vals = [value_of(400, k) for k in lost]
        lost_valid = [v for v in lost_vals if v is not None]
        lost_invalid = sum(1 for v in lost_vals if v is None)
        obs = concentration(lost_valid)
        counts = Counter(lost_valid)
        top = [
            {"value": v, "count": c, "n_items_with_this_gold_in_test": sum(1 for k in keys if canon(gold[k]) == v)}
            for v, c in counts.most_common(12)
        ]

        sw_vals = [value_of(400, k) for k in stable_wrong]
        sw_valid = [v for v in sw_vals if v is not None]
        sw_obs = concentration(sw_valid)

        # permutation nulls: equal-size draws of step-400 wrong answers
        null_specs = {
            "stable_wrong_only": stable_wrong,
            "all_step400_errors": wrong_pool,
        }
        nulls: dict[str, Any] = {}
        for null_name, pool in null_specs.items():
            rng = np.random.default_rng(SEED)
            pool_arr = np.asarray(pool)
            hits_h = 0
            hits_hhi = 0
            hits_distinct = 0
            h_samples = []
            for _ in range(N_PERM):
                draw = rng.choice(pool_arr, size=len(lost), replace=False)
                vals = [v for v in (value_of(400, str(k)) for k in draw) if v is not None]
                stats = concentration(vals)
                h_samples.append(stats["shannon_entropy_bits"])
                if stats["shannon_entropy_bits"] <= obs["shannon_entropy_bits"]:
                    hits_h += 1
                if (stats["hhi"] or 0.0) >= (obs["hhi"] or 0.0):
                    hits_hhi += 1
                if stats["n_distinct"] <= obs["n_distinct"]:
                    hits_distinct += 1
            arr = np.asarray(h_samples)
            nulls[null_name] = {
                "pool_size": len(pool),
                "draw_size": len(lost),
                "null_mean_entropy_bits": float(arr.mean()),
                "null_sd_entropy_bits": float(arr.std(ddof=1)),
                "p_entropy_le_observed": p_from_hits(hits_h, N_PERM),
                "p_hhi_ge_observed": p_from_hits(hits_hhi, N_PERM),
                "p_n_distinct_le_observed": p_from_hits(hits_distinct, N_PERM),
            }

        wrong_answer_block[metric] = {
            "max_multiplicity_of_any_single_wrong_value": max(counts.values()) if counts else 0,
            "n_values_appearing_twice_or_more": sum(1 for c in counts.values() if c >= 2),
            "lost_n": len(lost),
            "lost_contract_invalid_at_step400": lost_invalid,
            "lost_contract_valid_at_step400": len(lost_valid),
            "observed_concentration": obs,
            "top_values": top,
            "stable_wrong_reference_concentration": sw_obs,
            "stable_wrong_contract_invalid_at_step400": sum(1 for v in sw_vals if v is None),
            "permutation_nulls": nulls,
        }

    # ---------------- 3. LOST-set structure vs random step-100-correct subsets ----------------
    structure_block: dict[str, Any] = {}
    for metric in METRICS:
        pool = sorted(sets[metric]["correct"][100])
        pool_arr = np.asarray(pool)
        l200 = sets[metric]["lost_100_200"]
        l300 = sets[metric]["lost_100_300"]
        l400 = sets[metric]["lost_100_400"]
        obs_j3 = jaccard(l200, l300, l400)
        obs_pairs = {
            "j_200_300": jaccard(l200, l300),
            "j_200_400": jaccard(l200, l400),
            "j_300_400": jaccard(l300, l400),
        }
        obs_gold_h = concentration([canon(gold[k]) for k in sorted(l400)])
        obs_bucket_counts = Counter(bucket[k] for k in l400)
        pool_bucket_counts = Counter(bucket[k] for k in pool)
        bucket_names = sorted(pool_bucket_counts)
        exp_bucket = {
            b: len(l400) * pool_bucket_counts[b] / len(pool) for b in bucket_names
        }
        obs_chi2 = float(
            sum(
                (obs_bucket_counts.get(b, 0) - exp_bucket[b]) ** 2 / exp_bucket[b]
                for b in bucket_names
                if exp_bucket[b] > 0
            )
        )
        obs_persist = sum(1 for k in l400 if k in l200 and k in l300) / len(l400) if l400 else None

        rng = np.random.default_rng(SEED)
        hits_j3 = 0
        hits_pairs = {name: 0 for name in obs_pairs}
        hits_gold_h = 0
        hits_chi2 = 0
        j3_samples = []
        gold_h_samples = []
        chi2_samples = []
        for _ in range(N_PERM):
            s200 = set(rng.choice(pool_arr, size=len(l200), replace=False).tolist())
            s300 = set(rng.choice(pool_arr, size=len(l300), replace=False).tolist())
            s400 = set(rng.choice(pool_arr, size=len(l400), replace=False).tolist())
            j3 = jaccard(s200, s300, s400)
            j3_samples.append(j3)
            if j3 >= obs_j3:
                hits_j3 += 1
            if jaccard(s200, s300) >= obs_pairs["j_200_300"]:
                hits_pairs["j_200_300"] += 1
            if jaccard(s200, s400) >= obs_pairs["j_200_400"]:
                hits_pairs["j_200_400"] += 1
            if jaccard(s300, s400) >= obs_pairs["j_300_400"]:
                hits_pairs["j_300_400"] += 1
            gh = concentration([canon(gold[k]) for k in sorted(s400)])
            gold_h_samples.append(gh["shannon_entropy_bits"])
            if gh["shannon_entropy_bits"] <= obs_gold_h["shannon_entropy_bits"]:
                hits_gold_h += 1
            bc = Counter(bucket[k] for k in s400)
            chi2 = float(
                sum(
                    (bc.get(b, 0) - exp_bucket[b]) ** 2 / exp_bucket[b]
                    for b in bucket_names
                    if exp_bucket[b] > 0
                )
            )
            chi2_samples.append(chi2)
            if chi2 >= obs_chi2:
                hits_chi2 += 1

        structure_block[metric] = {
            "pool": "items correct at step 100",
            "pool_size": len(pool),
            "lost_set_sizes": {"100_200": len(l200), "100_300": len(l300), "100_400": len(l400)},
            "three_way_jaccard": {
                "observed": obs_j3,
                "null_mean": float(np.mean(j3_samples)),
                "null_sd": float(np.std(j3_samples, ddof=1)),
                "p_ge_observed": p_from_hits(hits_j3, N_PERM),
            },
            "pairwise_jaccard": {
                name: {"observed": obs_pairs[name], "p_ge_observed": p_from_hits(hits_pairs[name], N_PERM)}
                for name in obs_pairs
            },
            "lost_400_also_lost_at_200_and_300_share": obs_persist,
            "gold_answer_concentration": {
                "observed": obs_gold_h,
                "null_mean_entropy_bits": float(np.mean(gold_h_samples)),
                "p_entropy_le_observed": p_from_hits(hits_gold_h, N_PERM),
            },
            "derived_bucket_concentration": {
                "observed_counts": dict(sorted(obs_bucket_counts.items())),
                "expected_counts_from_pool": {b: exp_bucket[b] for b in bucket_names},
                "observed_chi2": obs_chi2,
                "null_mean_chi2": float(np.mean(chi2_samples)),
                "p_chi2_ge_observed": p_from_hits(hits_chi2, N_PERM),
            },
        }

    # ---------------- 4. metadata + derived buckets, LOST and GAINED ----------------
    manifest_path = ROOT / "data/geometry3k_caption_images_manifest.jsonl"
    manifest_keysets: Counter = Counter()
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        manifest_keysets["|".join(sorted(json.loads(line).keys()))] += 1

    metadata_block: dict[str, Any] = {
        "dataset_manifest": str(manifest_path.relative_to(ROOT)),
        "manifest_field_sets": dict(manifest_keysets),
        "eval_row_qid_non_null_count": {
            str(s): sum(1 for r in runs[s].values() if r["qid"] is not None) for s in STEPS
        },
        "eval_row_source_metadata_non_null_count": {
            str(s): sum(1 for r in runs[s].values() if r["source_metadata"] is not None)
            for s in STEPS
        },
        "template_category_source_field_present": False,
        "derived_buckets_are_defined_by_this_analysis": True,
        "derived_bucket_rules_in_order": [
            {"name": n, "regex": p} for n, p in STEM_RULES
        ],
    }

    derived_tables: dict[str, Any] = {}
    for metric in METRICS:
        l400 = sets[metric]["lost_100_400"]
        g400 = sets[metric]["gained_100_400"]
        c100 = sets[metric]["correct"][100]
        w100 = sets[metric]["wrong_100"]
        rows = {}
        for bname in sorted(set(bucket.values())):
            rows[bname] = {
                "all_test_items": sum(1 for k in keys if bucket[k] == bname),
                "correct_at_100": sum(1 for k in c100 if bucket[k] == bname),
                "wrong_at_100": sum(1 for k in w100 if bucket[k] == bname),
                "lost": sum(1 for k in l400 if bucket[k] == bname),
                "gained": sum(1 for k in g400 if bucket[k] == bname),
            }
            base_c = rows[bname]["correct_at_100"]
            base_w = rows[bname]["wrong_at_100"]
            rows[bname]["lost_rate_within_correct_at_100"] = (
                rows[bname]["lost"] / base_c if base_c else None
            )
            rows[bname]["gained_rate_within_wrong_at_100"] = (
                rows[bname]["gained"] / base_w if base_w else None
            )
        gt_rows = {}
        for tname in sorted(set(gtype.values())):
            gt_rows[tname] = {
                "all_test_items": sum(1 for k in keys if gtype[k] == tname),
                "correct_at_100": sum(1 for k in c100 if gtype[k] == tname),
                "wrong_at_100": sum(1 for k in w100 if gtype[k] == tname),
                "lost": sum(1 for k in l400 if gtype[k] == tname),
                "gained": sum(1 for k in g400 if gtype[k] == tname),
            }

        # concentration test for GAINED against its own pool (wrong at 100)
        pool_g = sorted(w100)
        pool_g_arr = np.asarray(pool_g)
        pool_g_counts = Counter(bucket[k] for k in pool_g)
        bnames = sorted(pool_g_counts)
        exp_g = {b: len(g400) * pool_g_counts[b] / len(pool_g) for b in bnames}
        obs_g_counts = Counter(bucket[k] for k in g400)
        obs_g_chi2 = float(
            sum((obs_g_counts.get(b, 0) - exp_g[b]) ** 2 / exp_g[b] for b in bnames if exp_g[b] > 0)
        )
        rng = np.random.default_rng(SEED)
        hits_g = 0
        for _ in range(N_PERM):
            draw = set(rng.choice(pool_g_arr, size=len(g400), replace=False).tolist())
            bc = Counter(bucket[k] for k in draw)
            chi2 = float(
                sum((bc.get(b, 0) - exp_g[b]) ** 2 / exp_g[b] for b in bnames if exp_g[b] > 0)
            )
            if chi2 >= obs_g_chi2:
                hits_g += 1
        derived_tables[metric] = {
            "by_derived_stem_bucket": rows,
            "by_derived_gold_type": gt_rows,
            "gained_bucket_concentration_vs_wrong_at_100_pool": {
                "observed_chi2": obs_g_chi2,
                "p_chi2_ge_observed": p_from_hits(hits_g, N_PERM),
                "pool_size": len(pool_g),
                "draw_size": len(g400),
            },
        }

    # ---------------- 5. geo3k-native structure probes ----------------
    gold_canon_multiset = Counter(canon(gold[k]) for k in keys)

    # precomputed per-item native-structure features (step-400 answer based)
    FEAT: dict[str, dict[str, Any]] = {}
    for k in keys:
        v = VAL[400][k]
        entry: dict[str, Any] = {"valid": v is not None}
        if v is not None:
            entry["other_gold"] = (
                gold_canon_multiset[v] - (1 if canon(gold[k]) == v else 0)
            ) > 0
            pv = numeric_value(normalize_answer(runs[400][k]["extracted_answer"]))
            gv = numeric_value(normalize_answer(gold[k]))
            if pv is None or gv is None or gv == 0:
                entry["near_miss"] = None
            else:
                entry["near_miss"] = abs(pv - gv) / abs(gv) <= 0.10
            if v.startswith("num::"):
                fv = float(v[5:])
                entry["small_int"] = abs(fv - round(fv)) < 1e-9 and 1 <= fv <= 20
            else:
                entry["small_int"] = False
        FEAT[k] = entry

    def native_probes(item_keys: list[str]) -> dict[str, Any]:
        valid = {k: VAL[400][k] for k in item_keys if VAL[400][k] is not None}
        same_as_prev = {}
        for prev in (150, 200, 300):
            comparable = [(k, VAL[prev][k]) for k in valid if VAL[prev][k] is not None]
            same = sum(1 for k, pv in comparable if pv == valid[k])
            same_as_prev[str(prev)] = {
                "comparable_items": len(comparable),
                "same_value_as_step400": same,
                "rate": (same / len(comparable) if comparable else None),
            }
        matches_other_gold = sum(1 for k in valid if FEAT[k]["other_gold"])
        near_vals = [FEAT[k]["near_miss"] for k in valid if FEAT[k]["near_miss"] is not None]
        near_denom = len(near_vals)
        near_miss = sum(1 for x in near_vals if x)
        small_int = sum(1 for k in valid if FEAT[k]["small_int"])
        return {
            "n_items": len(item_keys),
            "n_contract_valid_at_step400": len(valid),
            "same_step400_value_as_earlier_step": same_as_prev,
            "wrong_value_equals_some_other_test_item_gold": {
                "count": matches_other_gold,
                "rate": matches_other_gold / len(valid) if valid else None,
            },
            "numeric_near_miss_within_10pct_of_own_gold": {
                "numeric_comparable": near_denom,
                "count": near_miss,
                "rate": near_miss / near_denom if near_denom else None,
            },
            "small_integer_1_to_20": {
                "count": small_int,
                "rate": small_int / len(valid) if valid else None,
            },
        }

    native_block: dict[str, Any] = {}
    for metric in METRICS:
        lost = sorted(sets[metric]["lost_100_400"])
        stable_wrong = sorted(sets[metric]["stable_wrong"])
        obs = native_probes(lost)
        ref = native_probes(stable_wrong)
        # permutation p for the two rate probes against a stable-wrong null
        rng = np.random.default_rng(SEED)
        sw_arr = np.asarray(stable_wrong)
        hits_other_gold = 0
        hits_near = 0
        obs_og = obs["wrong_value_equals_some_other_test_item_gold"]["rate"] or 0.0
        obs_nm = obs["numeric_near_miss_within_10pct_of_own_gold"]["rate"] or 0.0
        for _ in range(N_PERM):
            draw = [str(x) for x in rng.choice(sw_arr, size=len(lost), replace=False)]
            valid = [k for k in draw if FEAT[k]["valid"]]
            og = (sum(1 for k in valid if FEAT[k]["other_gold"]) / len(valid)) if valid else 0.0
            nvals = [FEAT[k]["near_miss"] for k in valid if FEAT[k]["near_miss"] is not None]
            nm = (sum(1 for x in nvals if x) / len(nvals)) if nvals else 0.0
            if og >= obs_og:
                hits_other_gold += 1
            if nm >= obs_nm:
                hits_near += 1
        native_block[metric] = {
            "lost_set": obs,
            "stable_wrong_reference_set": ref,
            "permutation_vs_stable_wrong_null": {
                "n_perm": N_PERM,
                "seed": SEED,
                "p_other_gold_rate_ge_observed": p_from_hits(hits_other_gold, N_PERM),
                "p_near_miss_rate_ge_observed": p_from_hits(hits_near, N_PERM),
            },
        }

    result = {
        "schema_version": "blind-gains.m5c-lost-item-forensics.v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "task": "geo3k step-100 -> step-400 LOST/GAINED item forensics",
        "dataset": "Geometry3K test split (n=601), condition=real, arm=anchor_real, greedy temperature 0",
        "runs": {str(s): RUNS[s] for s in STEPS},
        "scorer": "src.eval.blind_solvability.score_greedy_item_pilot under DEFAULT_PROMPT_CONTRACT (uniform re-score of cached predictions)",
        "answer_canonicalization": "normalize_answer -> numeric_value; numeric answers bucketed to 1e-6, non-numeric keep normalized text; contract-invalid rows carry no value and are counted separately",
        "permutation_convention": {
            "n_perm": N_PERM,
            "seed": SEED,
            "p_formula": "(hits + 1) / (n_perm + 1)",
            "p_floor": P_FLOOR,
            "note": "p is reported as max((hits+1)/(n_perm+1), 1e-4); the smallest attainable value of the formula is 9.999e-5, so the floor binds only at zero hits",
        },
        "scope_limits": {
            "fliptrack_taxonomy_not_transplanted": (
                "The gray-arm attractor taxonomy in scripts/x3_a2_degradation_forensics.py "
                "(nearest_gridline, nearest_neighbor_x, twin_member_gold, same_point_y, "
                "most_similar_label_x, other_scene_point_x) is defined over replayed "
                "coordinate_register_twenty_point_x_v02 scene registers on FlipTrack pairs. "
                "Geometry3K is a different task: real-image geometry word problems with no "
                "generator seed, no replayable scene register, no coordinate grid, no paired "
                "twin member. None of those taxa is computable here and none was transplanted."
            ),
            "geo3k_analogues_used_instead": [
                "wrong-answer value repetition across items (attractor value concentration)",
                "same wrong value as an earlier checkpoint (temporal persistence)",
                "wrong value equals some other test item's gold answer",
                "numeric near-miss within 10% of own gold",
                "small-integer 1..20 occupancy",
            ],
            "checkpoint_sets_are_not_independent_seeds": (
                "The three lost sets (100->200, 100->300, 100->400) come from three checkpoints of "
                "ONE training trajectory and share the same step-100 anchor evaluation. The FlipTrack "
                "3-way Jaccard used independent seeds. The permutation null conditions on the "
                "step-100-correct pool, but serial dependence between checkpoints is not removed."
            ),
        },
        "verification": verification,
        "set_sizes": set_sizes,
        "set_membership": {
            metric: {
                "lost_100_400": sorted(sets[metric]["lost_100_400"], key=lambda k: int(k.split(":")[1])),
                "gained_100_400": sorted(sets[metric]["gained_100_400"], key=lambda k: int(k.split(":")[1])),
            }
            for metric in METRICS
        },
        "wrong_answer_distribution_on_lost_set": wrong_answer_block,
        "lost_set_structure_vs_step100_correct_null": structure_block,
        "metadata_availability": metadata_block,
        "derived_bucket_tables": derived_tables,
        "geo3k_native_structure_probes": native_block,
    }

    # ---------------- multiplicity bookkeeping (acc_final family; strict is identical) ----------------
    fam: list[tuple[str, float]] = []
    wa = wrong_answer_block["acc_final"]
    for null_name, block in wa["permutation_nulls"].items():
        for stat in ("p_entropy_le_observed", "p_hhi_ge_observed", "p_n_distinct_le_observed"):
            fam.append((f"wrong_answer_concentration::{null_name}::{stat}", block[stat]))
    st = structure_block["acc_final"]
    fam.append(("lost_set_three_way_jaccard", st["three_way_jaccard"]["p_ge_observed"]))
    for name, blk in st["pairwise_jaccard"].items():
        fam.append((f"lost_set_pairwise_jaccard::{name}", blk["p_ge_observed"]))
    fam.append(("lost_gold_answer_entropy", st["gold_answer_concentration"]["p_entropy_le_observed"]))
    fam.append(("lost_derived_bucket_chi2", st["derived_bucket_concentration"]["p_chi2_ge_observed"]))
    fam.append(
        (
            "gained_derived_bucket_chi2",
            derived_tables["acc_final"]["gained_bucket_concentration_vs_wrong_at_100_pool"][
                "p_chi2_ge_observed"
            ],
        )
    )
    nb = native_block["acc_final"]["permutation_vs_stable_wrong_null"]
    fam.append(("native_other_gold_rate", nb["p_other_gold_rate_ge_observed"]))
    fam.append(("native_near_miss_rate", nb["p_near_miss_rate_ge_observed"]))
    m = len(fam)
    bonf = 0.05 / m
    # Holm-Bonferroni at family alpha 0.05
    ordered = sorted(fam, key=lambda x: x[1])
    holm: dict[str, bool] = {}
    still = True
    for idx, (name, p) in enumerate(ordered):
        thresh = 0.05 / (m - idx)
        if still and p <= thresh:
            holm[name] = True
        else:
            still = False
            holm[name] = False
    result["multiplicity"] = {
        "family_alpha": 0.05,
        "n_tests_in_family": m,
        "bonferroni_threshold": bonf,
        "tests": {name: p for name, p in fam},
        "holm_bonferroni_reject": holm,
        "note": (
            "All permutation tests reported here form one pre-listed family; the family is "
            "reported with Holm-Bonferroni at alpha 0.05 alongside the raw p values. "
            "The acc_strict family is numerically identical to the acc_final family because "
            "acc_final == acc_strict on all 601 items at all five steps."
        ),
    }

    out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(result), encoding="utf-8")
    print(
        json.dumps(
            {
                "json": str(out_json),
                "json_sha256": hashlib.sha256(out_json.read_bytes()).hexdigest(),
                "md": str(out_md),
                "md_sha256": hashlib.sha256(out_md.read_bytes()).hexdigest(),
            }
        )
    )


if __name__ == "__main__":
    main()
