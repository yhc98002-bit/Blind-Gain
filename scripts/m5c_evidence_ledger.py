#!/usr/bin/env python3
"""M5c Task C -- evidence ledger for the geo3k step-100 -> step-400 turnover finding.

CPU only. Cached predictions + the existing substrate only. No GPU job is started.

Computes:
  1. problem-type (derived stem bucket) x {lost, gained, stable} table with exact counts;
     LOST and GAINED bucket chi-squares recomputed with 10,000 permutations, seed 20260729
  2. difficulty control for the numeric near-miss result
  3. margin / logprob field census (facts only; no proxy)
  4. five-step pattern structure vs three nulls
  5. Holm-Bonferroni over the family of tests run here + the evidence ledger table

Bucket rules are REUSED by importing scripts.m5c_lost_item_forensics (no re-derivation);
the imported rules are asserted equal to the rules recorded in the published artifact.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
sys.path.insert(0, str(ROOT))

# --- reuse the forensics module verbatim (bucket rules, loader, canonicalisation) ---
_spec = importlib.util.spec_from_file_location(
    "m5c_forensics", ROOT / "scripts/m5c_lost_item_forensics.py"
)
FZ = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FZ)

from src.rewards.answer_reward import normalize_answer, numeric_value  # noqa: E402

N_PERM = 10_000
SEED = 20260729
P_FLOOR = 1e-4
STEPS = FZ.STEPS
METRICS = FZ.METRICS
RUNS = FZ.RUNS

FORENSICS_JSON = ROOT / "reports/m5c_lost_item_forensics_v1.json"
TURNOVER_JSON = ROOT / "reports/m5c_turnover_v1.json"
NOISE_JSON = ROOT / "reports/m5c_noise_floor_replicate_v1.json"
SUBSTRATE = ROOT / "reports/m5c_item_substrate_v1.jsonl"

OUT_JSON = ROOT / "reports/m5c_evidence_ledger_v1.json"
OUT_MD = ROOT / "reports/m5c_evidence_ledger_v1.md"


def p_from_hits(hits: int, n_perm: int) -> float:
    return max((hits + 1) / (n_perm + 1), P_FLOOR)


def fmt_p(p: float | None) -> str:
    if p is None:
        return "n/a"
    return f"<= {P_FLOOR:.0e}" if p <= P_FLOOR else f"{p:.4f}"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def holm(tests: list[tuple[str, float]]) -> dict[str, dict[str, Any]]:
    """Holm-Bonferroni: adjusted p and reject flag at family alpha 0.05."""
    m = len(tests)
    order = sorted(range(m), key=lambda i: tests[i][1])
    adj: dict[str, float] = {}
    running = 0.0
    for rank, idx in enumerate(order):
        name, p = tests[idx]
        val = min(1.0, (m - rank) * p)
        running = max(running, val)
        adj[name] = running
    out: dict[str, dict[str, Any]] = {}
    still = True
    for rank, idx in enumerate(order):
        name, p = tests[idx]
        thresh = 0.05 / (m - rank)
        if still and p <= thresh:
            rej = True
        else:
            still = False
            rej = False
        out[name] = {
            "p_raw": p,
            "p_holm_adjusted": adj[name],
            "holm_threshold_at_rank": thresh,
            "rank": rank + 1,
            "reject_at_family_alpha_0.05": rej,
        }
    return out


# =====================================================================================
def main() -> None:
    forensics = json.loads(FORENSICS_JSON.read_text())
    turnover = json.loads(TURNOVER_JSON.read_text())
    noise = json.loads(NOISE_JSON.read_text())

    verification: dict[str, Any] = {}

    # ---- bucket-rule reuse check --------------------------------------------------
    published_rules = [
        (r["name"], r["regex"])
        for r in forensics["metadata_availability"]["derived_bucket_rules_in_order"]
    ]
    imported_rules = [(n, p) for n, p in FZ.STEM_RULES]
    verification["bucket_rules_imported_from"] = "scripts/m5c_lost_item_forensics.py::STEM_RULES"
    verification["bucket_rules_match_published_artifact"] = published_rules == imported_rules
    verification["bucket_rules_in_order"] = [{"name": n, "regex": p} for n, p in imported_rules]
    if published_rules != imported_rules:
        raise SystemExit("bucket rules diverged from the published artifact; refusing to continue")

    # ---- load the five cached runs -------------------------------------------------
    runs = {s: FZ.load_run(s) for s in STEPS}
    keys = sorted(runs[100], key=lambda k: int(k.split(":")[1]))
    verification["test_item_counts"] = {str(s): len(runs[s]) for s in STEPS}
    verification["item_key_sets_identical"] = all(set(runs[s]) == set(keys) for s in STEPS)
    if not verification["item_key_sets_identical"]:
        raise SystemExit("item key sets differ across steps")

    gold = {k: runs[100][k]["ground_truth"] for k in keys}
    verification["gold_identical_across_steps"] = all(
        runs[s][k]["ground_truth"] == gold[k] for s in STEPS for k in keys
    )
    verification["problem_sha256_identical_across_steps"] = all(
        hashlib.sha256(runs[s][k]["problem"].encode()).hexdigest()
        == hashlib.sha256(runs[100][k]["problem"].encode()).hexdigest()
        for s in STEPS
        for k in keys
    )

    bucket = {k: FZ.stem_bucket(runs[100][k]["problem"]) for k in keys}
    gtype = {k: FZ.gold_type(gold[k]) for k in keys}
    bucket_names = sorted(set(bucket.values()))

    # cross-check against the substrate file
    sub_rows = [
        json.loads(line)
        for line in SUBSTRATE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    sub = {r["item_key"]: r for r in sub_rows}
    mism = 0
    for k in keys:
        for s in STEPS:
            for m in METRICS:
                if bool(sub[k][f"{m}_step{s}"]) != bool(runs[s][k][m]):
                    mism += 1
    verification["substrate_rows"] = len(sub_rows)
    verification["substrate_value_mismatches_vs_runs"] = mism
    verification["substrate_sha256"] = sha256_file(SUBSTRATE)

    # ---- sets ----------------------------------------------------------------------
    sets: dict[str, dict[str, set[str]]] = {}
    for m in METRICS:
        c = {s: {k for k in keys if runs[s][k][m]} for s in STEPS}
        sets[m] = {
            "correct_100": c[100],
            "wrong_100": set(keys) - c[100],
            "correct_400": c[400],
            "wrong_400": set(keys) - c[400],
            "lost": c[100] - c[400],
            "gained": c[400] - c[100],
            "stable_correct": c[100] & c[400],
            "stable_wrong": set(keys) - c[100] - c[400],
            "by_step": c,
        }
    verification["set_sizes_reproduce_forensics_artifact"] = {
        "lost": len(sets["acc_final"]["lost"]) == forensics["set_sizes"]["acc_final"]["lost_100_400"],
        "gained": len(sets["acc_final"]["gained"])
        == forensics["set_sizes"]["acc_final"]["gained_100_400"],
        "stable_correct": len(sets["acc_final"]["stable_correct"])
        == forensics["set_sizes"]["acc_final"]["stable_correct"],
        "stable_wrong": len(sets["acc_final"]["stable_wrong"])
        == forensics["set_sizes"]["acc_final"]["stable_wrong"],
    }
    verification["acc_final_equals_acc_strict_all_items_all_steps"] = all(
        runs[s][k]["acc_final"] == runs[s][k]["acc_strict"] for s in STEPS for k in keys
    )

    # canonical per-step answer values (None when contract-invalid) -- same rule as forensics
    VAL = {
        s: {
            k: (FZ.canon(runs[s][k]["extracted_answer"]) if runs[s][k]["contract_valid"] else None)
            for k in keys
        }
        for s in STEPS
    }

    # near-miss feature at an arbitrary step, identical rule to the forensics artifact
    def near_miss_at(step: int, k: str) -> bool | None:
        if VAL[step][k] is None:
            return None
        pv = numeric_value(normalize_answer(runs[step][k]["extracted_answer"]))
        gv = numeric_value(normalize_answer(gold[k]))
        if pv is None or gv is None or gv == 0:
            return None
        return abs(pv - gv) / abs(gv) <= 0.10

    NM = {s: {k: near_miss_at(s, k) for k in keys} for s in STEPS}

    # =================================================================================
    # 1. PROBLEM-TYPE CONCENTRATION
    # =================================================================================
    task1: dict[str, Any] = {}
    for m in METRICS:
        S = sets[m]
        rows: dict[str, Any] = {}
        for b in bucket_names:
            inb = [k for k in keys if bucket[k] == b]
            n_lost = sum(1 for k in inb if k in S["lost"])
            n_gain = sum(1 for k in inb if k in S["gained"])
            n_sc = sum(1 for k in inb if k in S["stable_correct"])
            n_sw = sum(1 for k in inb if k in S["stable_wrong"])
            n_c100 = sum(1 for k in inb if k in S["correct_100"])
            n_w100 = len(inb) - n_c100
            rows[b] = {
                "total_items": len(inb),
                "lost": n_lost,
                "gained": n_gain,
                "stable": n_sc + n_sw,
                "stable_correct": n_sc,
                "stable_wrong": n_sw,
                "correct_at_100": n_c100,
                "wrong_at_100": n_w100,
                "lost_rate_within_correct_at_100": (n_lost / n_c100) if n_c100 else None,
                "gained_rate_within_wrong_at_100": (n_gain / n_w100) if n_w100 else None,
                "share_of_all_lost": n_lost / len(S["lost"]) if S["lost"] else None,
                "share_of_all_gained": n_gain / len(S["gained"]) if S["gained"] else None,
            }
        col_tot = {
            "total_items": len(keys),
            "lost": len(S["lost"]),
            "gained": len(S["gained"]),
            "stable": len(S["stable_correct"]) + len(S["stable_wrong"]),
            "stable_correct": len(S["stable_correct"]),
            "stable_wrong": len(S["stable_wrong"]),
            "correct_at_100": len(S["correct_100"]),
            "wrong_at_100": len(S["wrong_100"]),
        }
        # row/col sum checks
        checks = {
            "row_sums_equal_total": all(
                rows[b]["lost"] + rows[b]["gained"] + rows[b]["stable"] == rows[b]["total_items"]
                for b in bucket_names
            ),
            "col_lost_sums": sum(rows[b]["lost"] for b in bucket_names) == col_tot["lost"],
            "col_gained_sums": sum(rows[b]["gained"] for b in bucket_names) == col_tot["gained"],
            "col_stable_sums": sum(rows[b]["stable"] for b in bucket_names) == col_tot["stable"],
            "grand_total": sum(rows[b]["total_items"] for b in bucket_names) == len(keys),
        }

        def chi2_test(draw_set: set[str], pool: set[str], tag: str) -> dict[str, Any]:
            pool_l = sorted(pool)
            pool_arr = np.asarray(pool_l)
            pc = Counter(bucket[k] for k in pool_l)
            bn = sorted(pc)
            n_draw = len(draw_set)
            exp = {b: n_draw * pc[b] / len(pool_l) for b in bn}
            obs_c = Counter(bucket[k] for k in draw_set)
            obs_chi2 = float(
                sum((obs_c.get(b, 0) - exp[b]) ** 2 / exp[b] for b in bn if exp[b] > 0)
            )
            rng = np.random.default_rng(SEED)
            hits = 0
            samples = np.empty(N_PERM)
            for i in range(N_PERM):
                d = rng.choice(pool_arr, size=n_draw, replace=False)
                bc = Counter(bucket[k] for k in d.tolist())
                c2 = float(sum((bc.get(b, 0) - exp[b]) ** 2 / exp[b] for b in bn if exp[b] > 0))
                samples[i] = c2
                if c2 >= obs_chi2:
                    hits += 1
            return {
                "tag": tag,
                "pool": ("items correct at step 100" if tag == "lost" else "items wrong at step 100"),
                "pool_size": len(pool_l),
                "draw_size": n_draw,
                "n_buckets_with_positive_expectation": sum(1 for b in bn if exp[b] > 0),
                "asymptotic_df_reference_only": sum(1 for b in bn if exp[b] > 0) - 1,
                "observed_counts": {b: obs_c.get(b, 0) for b in bn},
                "expected_counts_from_pool": {b: exp[b] for b in bn},
                "observed_chi2": obs_chi2,
                "null_mean_chi2": float(samples.mean()),
                "null_sd_chi2": float(samples.std(ddof=1)),
                "null_q95_chi2": float(np.quantile(samples, 0.95)),
                "n_perm": N_PERM,
                "seed": SEED,
                "perm_hits_ge_observed": hits,
                "p_chi2_ge_observed": p_from_hits(hits, N_PERM),
            }

        lost_chi2 = chi2_test(S["lost"], S["correct_100"], "lost")
        gain_chi2 = chi2_test(S["gained"], S["wrong_100"], "gained")
        task1[m] = {
            "table_by_derived_stem_bucket": rows,
            "column_totals": col_tot,
            "table_consistency_checks": checks,
            "lost_bucket_concentration": lost_chi2,
            "gained_bucket_concentration": gain_chi2,
        }

    # statistic-identity check vs the published artifact (acc_final)
    pub_lost_chi2 = forensics["lost_set_structure_vs_step100_correct_null"]["acc_final"][
        "derived_bucket_concentration"
    ]["observed_chi2"]
    pub_gain_chi2 = forensics["derived_bucket_tables"]["acc_final"][
        "gained_bucket_concentration_vs_wrong_at_100_pool"
    ]["observed_chi2"]
    verification["chi2_statistics_reproduce_published_artifact"] = {
        "lost_observed_chi2_here": task1["acc_final"]["lost_bucket_concentration"]["observed_chi2"],
        "lost_observed_chi2_published": pub_lost_chi2,
        "lost_match_1e-9": abs(
            task1["acc_final"]["lost_bucket_concentration"]["observed_chi2"] - pub_lost_chi2
        )
        < 1e-9,
        "gained_observed_chi2_here": task1["acc_final"]["gained_bucket_concentration"][
            "observed_chi2"
        ],
        "gained_observed_chi2_published": pub_gain_chi2,
        "gained_match_1e-9": abs(
            task1["acc_final"]["gained_bucket_concentration"]["observed_chi2"] - pub_gain_chi2
        )
        < 1e-9,
        "published_lost_p": forensics["multiplicity"]["tests"]["lost_derived_bucket_chi2"],
        "published_gained_p": forensics["multiplicity"]["tests"]["gained_derived_bucket_chi2"],
        "note": (
            "The chi-square STATISTIC is deterministic and must match to machine precision. "
            "The permutation p may differ in the 3rd decimal from the published value because "
            "the published run drew its permutations from an RNG stream shared with the Jaccard "
            "and gold-entropy statistics, whereas this run uses a dedicated stream at the same "
            "seed. Both are valid Monte-Carlo estimates of the same p."
        ),
    }

    # =================================================================================
    # 2. DIFFICULTY CONTROL FOR THE NEAR-MISS RESULT
    # =================================================================================
    def rate(items: list[str], step_of: dict[str, int]) -> dict[str, Any]:
        vals = [(k, NM[step_of[k]][k]) for k in items]
        comp = [(k, v) for k, v in vals if v is not None]
        cnt = sum(1 for _, v in comp if v)
        return {
            "n_items": len(items),
            "numeric_comparable": len(comp),
            "near_miss_count": cnt,
            "near_miss_rate": (cnt / len(comp)) if comp else None,
            "excluded_not_numeric_comparable": len(items) - len(comp),
        }

    def label_perm_test(
        a_items: list[str], b_items: list[str], step_of: dict[str, int]
    ) -> dict[str, Any]:
        """Permute arm labels; statistic = rate(A) - rate(B) on numeric-comparable items."""
        a_set = set(a_items)
        pool = [(k, NM[step_of[k]][k]) for k in a_items + b_items]
        comp = [(k, bool(v)) for k, v in pool if v is not None]
        vals = np.asarray([1 if v else 0 for _, v in comp])
        n = len(vals)
        a_mask = np.asarray([k in a_set for k, _ in comp], dtype=bool)
        na = int(a_mask.sum())
        if na == 0 or na == n:
            return {"computable": False, "reason": "one arm has no numeric-comparable items"}
        obs_a = vals[a_mask].mean()
        obs_b = vals[~a_mask].mean()
        obs = float(obs_a - obs_b)
        rng = np.random.default_rng(SEED)
        hits_one = 0
        hits_two = 0
        diffs = np.empty(N_PERM)
        for i in range(N_PERM):
            perm = rng.permutation(n)
            aa = vals[perm[:na]].mean()
            bb = vals[perm[na:]].mean()
            d = float(aa - bb)
            diffs[i] = d
            if d >= obs:
                hits_one += 1
            if abs(d) >= abs(obs):
                hits_two += 1
        return {
            "computable": True,
            "arm_a_numeric_comparable": int(a_mask.sum()),
            "arm_b_numeric_comparable": int((~a_mask).sum()),
            "arm_a_rate": float(obs_a),
            "arm_b_rate": float(obs_b),
            "observed_rate_difference_a_minus_b": obs,
            "null_mean_difference": float(diffs.mean()),
            "null_sd_difference": float(diffs.std(ddof=1)),
            "n_perm": N_PERM,
            "seed": SEED,
            "p_one_sided_diff_ge_observed": p_from_hits(hits_one, N_PERM),
            "p_two_sided_absdiff_ge_observed": p_from_hits(hits_two, N_PERM),
            "convention": "arm-label permutation (exchangeability of arm membership)",
        }

    task2: dict[str, Any] = {}
    for m in METRICS:
        S = sets[m]
        lost = sorted(S["lost"])
        stable_wrong = sorted(S["stable_wrong"])
        stable_correct = sorted(S["stable_correct"])
        at400 = {k: 400 for k in keys}

        # published permutation convention: draw an equal-size subset of the reference set and
        # compare ITS near-miss rate to the observed LOST rate (one arm carries the variance)
        def subset_draw_test(obs_rate: float, ref_items: list[str], n_draw: int) -> dict[str, Any]:
            arr = np.asarray(ref_items)
            rng2 = np.random.default_rng(SEED)
            hits = 0
            rates = np.empty(N_PERM)
            for i in range(N_PERM):
                d = [str(x) for x in rng2.choice(arr, size=n_draw, replace=False)]
                vals = [NM[400][k] for k in d if VAL[400][k] is not None and NM[400][k] is not None]
                rt = (sum(1 for x in vals if x) / len(vals)) if vals else 0.0
                rates[i] = rt
                if rt >= obs_rate:
                    hits += 1
            return {
                "convention": (
                    "equal-size subset draw from the reference set; statistic = the drawn subset's "
                    "near-miss rate compared to the OBSERVED LOST rate (this is the convention used "
                    "in reports/m5c_lost_item_forensics_v1.json)"
                ),
                "draw_size": n_draw,
                "reference_pool_size": len(ref_items),
                "observed_lost_rate": obs_rate,
                "null_mean_rate": float(rates.mean()),
                "null_sd_rate": float(rates.std(ddof=1)),
                "n_perm": N_PERM,
                "seed": SEED,
                "p_rate_ge_observed": p_from_hits(hits, N_PERM),
            }

        lost_rate_obs = rate(lost, at400)["near_miss_rate"] or 0.0

        # (a) reproduce the UNCONTROLLED contrast from the artifact
        uncontrolled = {
            "design": "LOST(100->400) step-400 answer vs STABLE-WRONG step-400 answer",
            "lost": rate(lost, at400),
            "stable_wrong": rate(stable_wrong, at400),
            "difficulty_controlled": False,
            "confound": (
                "LOST items were correct at step 100 by construction; STABLE-WRONG items were "
                "wrong at step 100. The arms are not matched on step-100 correctness."
            ),
            "test": label_perm_test(lost, stable_wrong, at400),
            "test_published_subset_draw_convention": subset_draw_test(
                lost_rate_obs, stable_wrong, len(lost)
            ),
            "published_p_for_comparison": forensics["multiplicity"]["tests"]["native_near_miss_rate"],
        }

        # (b) the literal matched pool requested: LOST vs STABLE_CORRECT at step 400
        lit = {
            "design": "LOST(100->400) step-400 answer vs STABLE_CORRECT step-400 answer",
            "lost": rate(lost, at400),
            "stable_correct": rate(stable_correct, at400),
            "matched_on": "correct at step 100 (both arms, by construction)",
        }
        lit["degenerate"] = lit["stable_correct"]["near_miss_rate"] == 1.0
        lit["degeneracy_reason"] = (
            "STABLE_CORRECT items are CORRECT at step 400 by definition, so their step-400 "
            "extracted answer equals gold and |pred-gold|/|gold| = 0 <= 0.10 for every "
            "numeric-comparable item. The reference near-miss rate is therefore 1.0 by "
            "construction and the contrast cannot test the hypothesis in this direction."
        )

        # (c) non-degenerate matched design: both arms correct at 100, both measured on a WRONG answer
        dip_arm: list[str] = []
        dip_step: dict[str, int] = {}
        for k in sorted(S["correct_100"] & S["correct_400"]):
            for s in (150, 200, 300):
                if not runs[s][k][m]:
                    dip_arm.append(k)
                    dip_step[k] = s
                    break
        step_of_c = {k: 400 for k in lost}
        step_of_c.update(dip_step)
        matched = {
            "design": (
                "Both arms restricted to items CORRECT at step 100, and both arms measured on a "
                "WRONG answer. Arm A = LOST(100->400), wrong answer taken at step 400. "
                "Arm B = DIP-AND-RECOVER: correct at 100, correct at 400, wrong at at least one "
                "of steps 150/200/300; wrong answer taken at the FIRST such step."
            ),
            "rationale": (
                "Among items correct at step 100, 'wrong at step S' IS the definition of "
                "LOST(100->S). There is therefore no set that is simultaneously matched on "
                "step-100 correctness, measured on a wrong answer, and not lost at the same step. "
                "The only free axis is the step at which the wrong answer is read, so the matched "
                "reference must be read at an earlier checkpoint. That checkpoint difference is a "
                "genuine limitation of this design and is not removed."
            ),
            "matched_on": "correct at step 100 (both arms); wrong answer measured (both arms)",
            "arm_a_lost_400": rate(lost, step_of_c),
            "arm_b_dip_and_recover": rate(dip_arm, step_of_c),
            "arm_b_dip_step_histogram": dict(Counter(dip_step.values())),
            "arm_b_size": len(dip_arm),
            "test": label_perm_test(lost, dip_arm, step_of_c),
        }

        # (d) gold-magnitude stratified LOST vs STABLE-WRONG (controls the scale confound)
        def gv_of(k: str) -> float | None:
            v = numeric_value(normalize_answer(gold[k]))
            return None if v is None else float(abs(v))

        pool_items = [
            k for k in lost + stable_wrong if NM[400][k] is not None and gv_of(k) is not None
        ]
        mags = np.asarray([gv_of(k) for k in pool_items])
        qs = np.quantile(mags, [0.25, 0.5, 0.75])
        def stratum(k: str) -> int:
            v = gv_of(k)
            return int(np.searchsorted(qs, v, side="right"))

        strat_of = {k: stratum(k) for k in pool_items}
        y = np.asarray([1 if NM[400][k] else 0 for k in pool_items])
        is_a = np.asarray([k in set(lost) for k in pool_items])
        strat_arr = np.asarray([strat_of[k] for k in pool_items])
        strata_detail = {}
        num = 0.0
        den = 0.0
        for sv in sorted(set(strat_arr.tolist())):
            msk = strat_arr == sv
            na_ = int((msk & is_a).sum())
            nb_ = int((msk & ~is_a).sum())
            ra = float(y[msk & is_a].mean()) if na_ else None
            rb = float(y[msk & ~is_a].mean()) if nb_ else None
            w = (na_ * nb_) / (na_ + nb_) if (na_ + nb_) else 0.0
            if ra is not None and rb is not None:
                num += w * (ra - rb)
                den += w
            strata_detail[str(sv)] = {
                "abs_gold_range": [
                    float(mags[msk].min()) if msk.any() else None,
                    float(mags[msk].max()) if msk.any() else None,
                ],
                "n_lost": na_,
                "n_stable_wrong": nb_,
                "near_miss_rate_lost": ra,
                "near_miss_rate_stable_wrong": rb,
                "weight": w,
            }
        obs_strat = num / den if den else None

        def strat_stat(labels: np.ndarray) -> float:
            n_, d_ = 0.0, 0.0
            for sv in sorted(set(strat_arr.tolist())):
                msk = strat_arr == sv
                a_ = msk & labels
                b_ = msk & ~labels
                if a_.sum() and b_.sum():
                    w = (a_.sum() * b_.sum()) / (a_.sum() + b_.sum())
                    n_ += w * (y[a_].mean() - y[b_].mean())
                    d_ += w
            return n_ / d_ if d_ else 0.0

        rng = np.random.default_rng(SEED)
        hits_s = 0
        samp = np.empty(N_PERM)
        for i in range(N_PERM):
            lab = is_a.copy()
            for sv in sorted(set(strat_arr.tolist())):
                msk = strat_arr == sv
                idx = np.flatnonzero(msk)
                perm = rng.permutation(idx)
                lab[idx] = is_a[perm]
            v = strat_stat(lab)
            samp[i] = v
            if v >= obs_strat:
                hits_s += 1
        stratified = {
            "design": (
                "LOST(100->400) vs STABLE-WRONG at step 400, stratified by |gold| quartile of the "
                "pooled numeric-comparable items; arm labels permuted WITHIN stratum."
            ),
            "controls": (
                "the answer-scale confound: the near-miss window is +/-10% of gold, so its width "
                "scales with |gold|. It does NOT control step-100 correctness."
            ),
            "abs_gold_quartile_cuts": [float(x) for x in qs],
            "median_abs_gold_lost": float(
                np.median([gv_of(k) for k in lost if gv_of(k) is not None])
            ),
            "median_abs_gold_stable_wrong": float(
                np.median([gv_of(k) for k in stable_wrong if gv_of(k) is not None])
            ),
            "strata": strata_detail,
            "observed_stratified_rate_difference": obs_strat,
            "null_mean": float(samp.mean()),
            "null_sd": float(samp.std(ddof=1)),
            "n_perm": N_PERM,
            "seed": SEED,
            "p_one_sided_ge_observed": p_from_hits(hits_s, N_PERM),
        }

        task2[m] = {
            "near_miss_rule": (
                "step-S extracted answer must be contract-valid; pred and gold must both parse "
                "numerically and gold != 0; near miss iff |pred-gold|/|gold| <= 0.10. Identical "
                "rule to reports/m5c_lost_item_forensics_v1.json."
            ),
            "uncontrolled_reference": uncontrolled,
            "literal_matched_pool_lost_vs_stable_correct": lit,
            "matched_design_dip_and_recover": matched,
            "stratified_by_gold_magnitude": stratified,
            "permutation_convention_matters": {
                "note": (
                    "The published p for the uncontrolled near-miss contrast (5.0e-4) uses the "
                    "subset-draw convention, in which only the small arm carries sampling variance. "
                    "The same data under arm-label permutation, which treats both arms as "
                    "exchangeable, gives a much larger p. The matched design CANNOT be run under "
                    "the subset-draw convention because its reference arm has fewer "
                    "numeric-comparable items than the LOST arm, so a same-size subset cannot be "
                    "drawn. The like-for-like comparison of unmatched vs matched is therefore "
                    "arm-label vs arm-label."
                ),
                "uncontrolled_subset_draw_p": None,  # filled below
                "uncontrolled_arm_label_p": uncontrolled["test"]["p_one_sided_diff_ge_observed"],
                "matched_arm_label_p": matched["test"]["p_one_sided_diff_ge_observed"],
                "like_for_like_unmatched_to_matched": None,  # filled below
            },
        }
        task2[m]["permutation_convention_matters"]["uncontrolled_subset_draw_p"] = uncontrolled[
            "test_published_subset_draw_convention"
        ]["p_rate_ge_observed"]
        task2[m]["permutation_convention_matters"]["like_for_like_unmatched_to_matched"] = (
            f"arm-label p {uncontrolled['test']['p_one_sided_diff_ge_observed']:.4f} (unmatched, "
            f"effect {uncontrolled['test']['observed_rate_difference_a_minus_b']:+.4f}) -> "
            f"{matched['test']['p_one_sided_diff_ge_observed']:.4f} (matched, effect "
            f"{matched['test']['observed_rate_difference_a_minus_b']:+.4f}); the effect SIZE is "
            f"preserved or larger under matching, the p rises because the matched reference arm has "
            f"only {matched['arm_b_dip_and_recover']['numeric_comparable']} numeric-comparable items."
        )

    # =================================================================================
    # 3. MARGIN / LOGPROB FIELD CENSUS
    # =================================================================================
    CANDIDATES = [
        "logprob", "logprobs", "log_prob", "cumulative_logprob", "token_logprob",
        "avg_logprob", "mean_logprob", "logit", "margin", "score", "confidence",
        "entropy", "perplexity", "nll", "top_logprobs", "seq_logprob",
    ]
    field_census: dict[str, Any] = {}
    for s in STEPS:
        path = ROOT / "experiments/runs" / RUNS[s] / "per_item.jsonl"
        names: set[str] = set()
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                names |= set(json.loads(line).keys())
        matches = sorted(n for n in names if any(c in n.lower() for c in CANDIDATES))
        field_census[str(s)] = {
            "per_item_path": str(path.relative_to(ROOT)),
            "n_fields": len(names),
            "all_field_names": sorted(names),
            "fields_matching_logprob_score_margin_candidates": matches,
        }
    # step-100 sampling summary fields, described for what they are
    s100_conf_fields = [
        f for f in field_census["100"]["all_field_names"]
        if f in {
            "p_greedy", "p_sample", "p_i_jeffreys", "canonical_p_sample", "variance_proxy",
            "q_i", "pass_at_k16", "pass_at_g", "sample_count", "sample_correct_count",
            "canonical_sample_correct_count",
        }
    ]
    p_greedy_vals = Counter()
    for line in (ROOT / "experiments/runs" / RUNS[100] / "per_item.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("split") == "test":
                p_greedy_vals[r.get("p_greedy")] += 1

    task3: dict[str, Any] = {
        "question": (
            "Do the cached geo3k prediction rows carry a logprob / score / margin field that "
            "would let us compare the decoding margin of LOST items against reference sets?"
        ),
        "answer": "NO. No logprob, token-probability, logit, decoding-score or margin field "
        "exists in any of the five cached geo3k per-item files.",
        "field_census": field_census,
        "matched_candidate_fields_by_step": {
            s: field_census[s]["fields_matching_logprob_score_margin_candidates"] for s in field_census
        },
        "matched_candidate_fields_are_substring_false_positives": (
            "The only substring hits anywhere are at step 100: guarded_rescore_source_row_sha256, "
            "guarded_rescore_source_run and guarded_rescore_version. They match because 'rescore' "
            "contains 'score'. They are a provenance sha256, a run id and a version string. Steps "
            "150/200/300/400 have zero substring hits. There is no true logprob/score/margin field "
            "at any step."
        ),
        "step_100_sampling_summary_fields_present": s100_conf_fields,
        "step_100_p_greedy_value_census_test_rows": {str(k): v for k, v in sorted(p_greedy_vals.items(), key=lambda t: (t[0] is None, t[0]))},
        "why_the_step_100_fields_are_not_a_margin": (
            "The step-100 guarded-rescore file carries p_greedy, p_sample, canonical_p_sample, "
            "p_i_jeffreys, variance_proxy, q_i and pass_at_k16. These are summaries of a 16-sample "
            "temperature-1.0 decode (sample_count = 16) plus the binary greedy outcome. They are "
            "empirical correctness FREQUENCIES, not token logprobs and not a decoding margin. "
            "Steps 150/200/300/400 have no sampled decode at all: the only numeric non-binary "
            "fields there are format_reward / training_reward / canonical_eval_reward / "
            "pilot_accuracy_reward, which are deterministic functions of the binary correctness and "
            "format flags (verified: those four fields take exactly 4 distinct joint values across "
            "601 items at step 400)."
        ),
        "verdict": (
            "NOT MEASURABLE. The requested comparisons -- step-100 margin of LOST vs "
            "STABLE_CORRECT, and step-400 margin of LOST vs STABLE_WRONG -- cannot be run on "
            "cached data. No proxy is substituted for the margin."
        ),
        "step_400_margin_is_unavailable_even_from_sampling": (
            "There is no sampled decode at step 400 in the cached set, so not even a sampled "
            "pass-rate analogue exists at the second endpoint. A step-400 16-sample run "
            "(experiments/runs/m5c_sampled_m5c-taskb-step400_an29_gpu4_20260730T122620Z) was "
            "in flight for M5C Task B while this report was being written and was incomplete; it "
            "is not used here."
        ),
    }

    # side measurement, explicitly NOT the margin test
    side: dict[str, Any] = {}
    p_sample = {}
    for line in (ROOT / "experiments/runs" / RUNS[100] / "per_item.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("split") == "test":
                p_sample[f"{r['split']}:{r['row_index']}"] = r.get("canonical_p_sample")
    for m in METRICS:
        S = sets[m]
        a = [p_sample[k] for k in sorted(S["lost"]) if p_sample.get(k) is not None]
        b = [p_sample[k] for k in sorted(S["stable_correct"]) if p_sample.get(k) is not None]
        va, vb = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
        obs = float(va.mean() - vb.mean())
        allv = np.concatenate([va, vb])
        rng = np.random.default_rng(SEED)
        hits1 = 0
        hits2 = 0
        for _ in range(N_PERM):
            perm = rng.permutation(len(allv))
            d = float(allv[perm[: len(va)]].mean() - allv[perm[len(va) :]].mean())
            if d <= obs:
                hits1 += 1
            if abs(d) >= abs(obs):
                hits2 += 1
        side[m] = {
            "n_lost": int(va.size),
            "n_stable_correct": int(vb.size),
            "mean_canonical_p_sample_lost": float(va.mean()),
            "mean_canonical_p_sample_stable_correct": float(vb.mean()),
            "median_lost": float(np.median(va)),
            "median_stable_correct": float(np.median(vb)),
            "observed_mean_difference_lost_minus_stable_correct": obs,
            "n_perm": N_PERM,
            "seed": SEED,
            "p_one_sided_diff_le_observed": p_from_hits(hits1, N_PERM),
            "p_two_sided": p_from_hits(hits2, N_PERM),
        }
    task3["side_measurement_not_the_margin_test"] = {
        "what_it_is": (
            "step-100 16-sample temperature-1.0 empirical pass rate (canonical_p_sample) of "
            "LOST(100->400) items vs STABLE_CORRECT items, both correct at greedy step 100."
        ),
        "what_it_is_not": (
            "It is NOT the logprob/margin comparison requested, and it is NOT offered as a proxy "
            "for one. The margin comparison stays NOT MEASURABLE. This is a separate, directly "
            "measured quantity from a different decode (temperature 1.0, n=16) that exists only at "
            "step 100. It is reported as its own line in the ledger and is included in the "
            "Holm family. A reader who wants only the requested test should read the verdict above."
        ),
        "results": side,
    }

    # =================================================================================
    # 4. FIVE-STEP PATTERN STRUCTURE vs INDEPENDENCE
    # =================================================================================
    ALL_PAT = [format(i, "05b") for i in range(32)]

    def flips(mat: np.ndarray) -> int:
        return int((mat[:, :-1] != mat[:, 1:]).sum())

    def pat_counts(mat: np.ndarray) -> np.ndarray:
        codes = (mat * (2 ** np.arange(4, -1, -1))).sum(axis=1)
        return np.bincount(codes, minlength=32)

    def g2_x2(obs: np.ndarray, exp: np.ndarray) -> tuple[float, float]:
        g = 0.0
        x = 0.0
        for o, e in zip(obs, exp):
            if e > 0:
                x += (o - e) ** 2 / e
                if o > 0:
                    g += 2 * o * math.log(o / e)
        return float(g), float(x)

    task4: dict[str, Any] = {}
    for m in METRICS:
        mat = np.asarray([[1 if runs[s][k][m] else 0 for s in STEPS] for k in keys], dtype=int)
        n, T = mat.shape
        pi = mat.mean(axis=0)
        obs_counts = pat_counts(mat)
        exp_probs = np.asarray(
            [
                math.prod(pi[j] if b[j] == "1" else (1 - pi[j]) for j in range(5))
                for b in ALL_PAT
            ]
        )
        exp_counts = n * exp_probs
        obs_g2, obs_x2 = g2_x2(obs_counts, exp_counts)
        obs_flips = flips(mat)
        obs_never = int((mat.sum(axis=1) == 0).sum())
        obs_always = int((mat.sum(axis=1) == 5).sum())
        obs_moved = n - obs_never - obs_always
        obs_zero_flip = int(((mat[:, :-1] != mat[:, 1:]).sum(axis=1) == 0).sum())
        exp_flips = float(
            n * sum(pi[j] * (1 - pi[j + 1]) + (1 - pi[j]) * pi[j + 1] for j in range(4))
        )

        # --- N1: independent Bernoulli at the observed per-step marginals -------------
        rng = np.random.default_rng(SEED)
        n1 = {"g2": np.empty(N_PERM), "x2": np.empty(N_PERM), "flips": np.empty(N_PERM),
              "never": np.empty(N_PERM), "always": np.empty(N_PERM), "zero_flip": np.empty(N_PERM)}
        h_g2 = h_x2 = h_fl_le = h_nev = h_alw = h_zf = 0
        for i in range(N_PERM):
            sim = (rng.random((n, 5)) < pi).astype(int)
            spi = sim.mean(axis=0)
            sexp = n * np.asarray(
                [math.prod(spi[j] if b[j] == "1" else (1 - spi[j]) for j in range(5))
                 for b in ALL_PAT]
            )
            g, x = g2_x2(pat_counts(sim), sexp)
            f = flips(sim)
            nev = int((sim.sum(axis=1) == 0).sum())
            alw = int((sim.sum(axis=1) == 5).sum())
            zf = int(((sim[:, :-1] != sim[:, 1:]).sum(axis=1) == 0).sum())
            n1["g2"][i], n1["x2"][i], n1["flips"][i] = g, x, f
            n1["never"][i], n1["always"][i], n1["zero_flip"][i] = nev, alw, zf
            h_g2 += g >= obs_g2
            h_x2 += x >= obs_x2
            h_fl_le += f <= obs_flips
            h_nev += nev >= obs_never
            h_alw += alw >= obs_always
            h_zf += zf >= obs_zero_flip

        # --- N2: within-item permutation of the five step labels ---------------------
        rng = np.random.default_rng(SEED)
        n2_flips = np.empty(N_PERM)
        h2 = 0
        for i in range(N_PERM):
            sim = mat.copy()
            # independent random permutation of each row (preserves row sums)
            order = rng.random(sim.shape).argsort(axis=1)
            sim = np.take_along_axis(sim, order, axis=1)
            f = flips(sim)
            n2_flips[i] = f
            h2 += f <= obs_flips

        # --- N3: row AND column margin preserving swaps (curveball) ------------------
        rng = np.random.default_rng(SEED)
        cur = mat.copy()
        row_sums = mat.sum(axis=1)
        col_sums = mat.sum(axis=0)

        def curveball_sweep(M: np.ndarray, n_trades: int) -> None:
            for _ in range(n_trades):
                i1, i2 = rng.integers(0, M.shape[0], size=2)
                if i1 == i2:
                    continue
                r1, r2 = M[i1], M[i2]
                diff = np.flatnonzero(r1 != r2)
                if diff.size < 2:
                    continue
                k1 = int(r1[diff].sum())
                perm = rng.permutation(diff)
                r1[diff] = 0
                r2[diff] = 0
                r1[perm[:k1]] = 1
                r2[perm[k1:]] = 1

        curveball_sweep(cur, 20_000)  # burn-in
        n3_flips = np.empty(N_PERM)
        h3 = 0
        margin_ok = True
        for i in range(N_PERM):
            curveball_sweep(cur, 200)
            if not (
                np.array_equal(cur.sum(axis=1), row_sums)
                and np.array_equal(cur.sum(axis=0), col_sums)
            ):
                margin_ok = False
            f = flips(cur)
            n3_flips[i] = f
            h3 += f <= obs_flips

        pattern_table = {}
        for idx, b in enumerate(ALL_PAT):
            pattern_table[b] = {
                "observed": int(obs_counts[idx]),
                "expected_under_independence": float(exp_counts[idx]),
                "obs_minus_exp": float(obs_counts[idx] - exp_counts[idx]),
                "n_steps_correct": b.count("1"),
                "n_adjacent_flips": sum(1 for j in range(4) if b[j] != b[j + 1]),
            }

        task4[m] = {
            "step_order": "digits are steps 100/150/200/300/400",
            "n_items": n,
            "per_step_marginal_accuracy": {str(s): float(pi[j]) for j, s in enumerate(STEPS)},
            "n_distinct_patterns_observed": int((obs_counts > 0).sum()),
            "n_possible_patterns": 32,
            "never_correct": obs_never,
            "always_correct": obs_always,
            "moved_at_least_once": obs_moved,
            "observed_total_adjacent_flips": obs_flips,
            "observed_items_with_zero_flips": obs_zero_flip,
            "pattern_table": pattern_table,
            "null_N1_independent_bernoulli_at_observed_step_marginals": {
                "definition": (
                    "Each item's state at each step is an independent Bernoulli draw at that "
                    "step's OBSERVED marginal accuracy; items are exchangeable. Per replicate the "
                    "expected pattern counts are refit from the replicate's own marginals "
                    "(parametric bootstrap), so the statistic is calibrated the same way as the "
                    "observed one."
                ),
                "expected_pattern_counts_from_observed_marginals": {
                    b: float(exp_counts[i]) for i, b in enumerate(ALL_PAT)
                },
                "observed_G2_likelihood_ratio": obs_g2,
                "observed_pearson_X2": obs_x2,
                "asymptotic_df_reference_only": {"32_cells_minus_1": 31, "minus_5_fitted_marginals": 26},
                "null_mean_G2": float(n1["g2"].mean()),
                "null_sd_G2": float(n1["g2"].std(ddof=1)),
                "null_q999_G2": float(np.quantile(n1["g2"], 0.999)),
                "null_max_G2": float(n1["g2"].max()),
                "p_G2_ge_observed": p_from_hits(int(h_g2), N_PERM),
                "null_mean_X2": float(n1["x2"].mean()),
                "null_max_X2": float(n1["x2"].max()),
                "p_X2_ge_observed": p_from_hits(int(h_x2), N_PERM),
                "expected_total_adjacent_flips_analytic": exp_flips,
                "null_mean_total_flips": float(n1["flips"].mean()),
                "null_sd_total_flips": float(n1["flips"].std(ddof=1)),
                "null_min_total_flips": int(n1["flips"].min()),
                "p_total_flips_le_observed": p_from_hits(int(h_fl_le), N_PERM),
                "null_mean_never_correct": float(n1["never"].mean()),
                "p_never_correct_ge_observed": p_from_hits(int(h_nev), N_PERM),
                "null_mean_always_correct": float(n1["always"].mean()),
                "p_always_correct_ge_observed": p_from_hits(int(h_alw), N_PERM),
                "null_mean_items_with_zero_flips": float(n1["zero_flip"].mean()),
                "p_items_with_zero_flips_ge_observed": p_from_hits(int(h_zf), N_PERM),
                "n_perm": N_PERM,
                "seed": SEED,
            },
            "null_N2_within_item_label_permutation": {
                "definition": (
                    "Each item keeps its own number of correct steps; the five step labels are "
                    "permuted uniformly within the item. Item difficulty is held fixed and only "
                    "the temporal ORDER is randomised. Does not preserve per-step column margins."
                ),
                "observed_total_adjacent_flips": obs_flips,
                "null_mean_total_flips": float(n2_flips.mean()),
                "null_sd_total_flips": float(n2_flips.std(ddof=1)),
                "null_min_total_flips": int(n2_flips.min()),
                "p_total_flips_le_observed": p_from_hits(int(h2), N_PERM),
                "n_perm": N_PERM,
                "seed": SEED,
            },
            "null_N3_row_and_column_margin_preserving_curveball": {
                "definition": (
                    "Curveball trades on the 601x5 binary matrix, preserving every item's number "
                    "of correct steps AND every step's accuracy count exactly. 20000 burn-in "
                    "trades, 200 trades between successive samples."
                ),
                "margins_preserved_at_every_sample": bool(margin_ok),
                "row_sums_target": [int(x) for x in np.bincount(row_sums, minlength=6)],
                "col_sums_target": [int(x) for x in col_sums],
                "observed_total_adjacent_flips": obs_flips,
                "null_mean_total_flips": float(n3_flips.mean()),
                "null_sd_total_flips": float(n3_flips.std(ddof=1)),
                "null_min_total_flips": int(n3_flips.min()),
                "p_total_flips_le_observed": p_from_hits(int(h3), N_PERM),
                "n_perm": N_PERM,
                "seed": SEED,
            },
            "direction": {
                "vs_N1_independence": (
                    "MORE PERSISTENCE than independence: observed total adjacent flips "
                    f"{obs_flips} vs null mean {float(n1['flips'].mean()):.1f}; observed items "
                    f"with zero flips {obs_zero_flip} vs null mean "
                    f"{float(n1['zero_flip'].mean()):.1f}; observed never-correct {obs_never} vs "
                    f"null mean {float(n1['never'].mean()):.1f}; observed always-correct "
                    f"{obs_always} vs null mean {float(n1['always'].mean()):.1f}."
                ),
                "vs_N2_and_N3_given_item_difficulty": (
                    f"observed flips {obs_flips} vs N2 null mean {float(n2_flips.mean()):.1f} and "
                    f"N3 null mean {float(n3_flips.mean()):.1f}. Sign of "
                    "(observed - null mean) determines whether states are sticky (negative) or "
                    "alternating (positive) once each item's own number of correct steps is held "
                    "fixed."
                ),
                "n2_observed_minus_null_mean": obs_flips - float(n2_flips.mean()),
                "n3_observed_minus_null_mean": obs_flips - float(n3_flips.mean()),
                "n1_observed_minus_null_mean": obs_flips - float(n1["flips"].mean()),
            },
        }

    # =================================================================================
    # 5. HOLM FAMILY + LEDGER
    # =================================================================================
    A = "acc_final"
    fam: list[tuple[str, float]] = [
        ("T1_lost_bucket_chi2", task1[A]["lost_bucket_concentration"]["p_chi2_ge_observed"]),
        ("T2_gained_bucket_chi2", task1[A]["gained_bucket_concentration"]["p_chi2_ge_observed"]),
        (
            "T3_near_miss_matched_dip_and_recover_one_sided",
            task2[A]["matched_design_dip_and_recover"]["test"]["p_one_sided_diff_ge_observed"],
        ),
        (
            "T4_near_miss_gold_magnitude_stratified_one_sided",
            task2[A]["stratified_by_gold_magnitude"]["p_one_sided_ge_observed"],
        ),
        (
            "T5_step100_sampled_pass_rate_lost_vs_stable_correct_two_sided",
            task3["side_measurement_not_the_margin_test"]["results"][A]["p_two_sided"],
        ),
        (
            "T6_pattern_G2_vs_independence",
            task4[A]["null_N1_independent_bernoulli_at_observed_step_marginals"]["p_G2_ge_observed"],
        ),
        (
            "T7_pattern_X2_vs_independence",
            task4[A]["null_N1_independent_bernoulli_at_observed_step_marginals"]["p_X2_ge_observed"],
        ),
        (
            "T8_total_flips_vs_independence",
            task4[A]["null_N1_independent_bernoulli_at_observed_step_marginals"][
                "p_total_flips_le_observed"
            ],
        ),
        (
            "T9_total_flips_vs_within_item_order_permutation",
            task4[A]["null_N2_within_item_label_permutation"]["p_total_flips_le_observed"],
        ),
        (
            "T10_total_flips_vs_row_col_margin_preserving",
            task4[A]["null_N3_row_and_column_margin_preserving_curveball"][
                "p_total_flips_le_observed"
            ],
        ),
    ]
    holm_res = holm(fam)
    prior_fam = [(n, p) for n, p in forensics["multiplicity"]["tests"].items()]
    prior_holm = holm(prior_fam)

    multiplicity = {
        "family_alpha": 0.05,
        "family_definition": (
            "The ten permutation tests COMPUTED IN THIS REPORT under acc_final. The acc_strict "
            "family is numerically identical because acc_final == acc_strict on all 601 items at "
            "all five steps (verified here)."
        ),
        "n_tests_in_family": len(fam),
        "bonferroni_threshold": 0.05 / len(fam),
        "holm": holm_res,
        "excluded_from_family_and_why": {
            "literal_matched_pool_lost_vs_stable_correct": (
                "DEGENERATE by construction (reference rate = 1.0 because STABLE_CORRECT items are "
                "correct at step 400), so it is not a test of the hypothesis and no p is entered "
                "into the family."
            ),
            "uncontrolled_near_miss_contrast": (
                "Already published and Holm-corrected inside the 15-test family of "
                "reports/m5c_lost_item_forensics_v1.json; recomputed here for continuity, not "
                "re-entered into this family."
            ),
            "prior_published_tests": (
                "McNemar exact p values, the 3-way/pairwise Jaccard tests and the wrong-answer "
                "concentration tests belong to the earlier families in "
                "reports/m5c_turnover_v1.json and reports/m5c_lost_item_forensics_v1.json; their "
                "own corrections are carried through into the ledger and are not recomputed."
            ),
        },
        "prior_family_holm_from_forensics_artifact": forensics["multiplicity"],
        "prior_family_holm_adjusted_p_recomputed_here": prior_holm,
    }

    # ---- LEDGER --------------------------------------------------------------------
    t1l = task1[A]["lost_bucket_concentration"]
    t1g = task1[A]["gained_bucket_concentration"]
    t2u = task2[A]["uncontrolled_reference"]
    t2l = task2[A]["literal_matched_pool_lost_vs_stable_correct"]
    t2m = task2[A]["matched_design_dip_and_recover"]
    t2s = task2[A]["stratified_by_gold_magnitude"]
    t4n1 = task4[A]["null_N1_independent_bernoulli_at_observed_step_marginals"]
    t4n2 = task4[A]["null_N2_within_item_label_permutation"]
    t4n3 = task4[A]["null_N3_row_and_column_margin_preserving_curveball"]
    t3s = task3["side_measurement_not_the_margin_test"]["results"][A]
    tr = turnover["transitions"]

    def H(name: str) -> float:
        return holm_res[name]["p_holm_adjusted"]

    ledger: list[dict[str, Any]] = [
        {
            "id": "L01",
            "claim_supported": "The step-100 -> step-400 NET accuracy change is not distinguishable from zero.",
            "statistic": "McNemar exact two-sided on 71 gained / 66 lost; net +5 items, +0.008319",
            "null": "no net asymmetry between gained and lost (binomial 137 discordant pairs, p=0.5)",
            "p": tr["100->400|acc_final"]["mcnemar_exact_two_sided_p"],
            "p_adjusted": None,
            "adjustment": "none (single pre-registered primary endpoint of the turnover report)",
            "verdict": "SUPPORTS",
            "note": "This is the only thing McNemar tests. It does NOT bound total turnover.",
            "source": "reports/m5c_turnover_v1.json",
        },
        {
            "id": "L02",
            "claim_supported": "137 of 601 items (22.80%) change state between step 100 and step 400 -- turnover 27.4x the net.",
            "statistic": "discordant pairs 137/601 = 0.227953; turnover/|net| = 27.4",
            "null": "descriptive count -- no null; the noise question is answered by L03",
            "p": None,
            "p_adjusted": None,
            "adjustment": "n/a",
            "verdict": "SUPPORTS",
            "note": "Count, not a test. Its interpretation depends entirely on the noise floor (L03).",
            "source": "reports/m5c_turnover_v1.json",
        },
        {
            "id": "L03",
            "claim_supported": "The 137-item turnover is NOT evaluation or decoding noise.",
            "statistic": "replicate discordance 0/601 on acc_final AND 0/601 on acc_strict at BOTH step 400 and step 100; all 601 greedy response strings byte-identical; per_item.jsonl bit-identical (step-400 sha256 60eac65a8b5bb9b3..., step-100 4a4a840f9a3edb1b...)",
            "null": "directly measured replicate floor -- no model needed",
            "p": None,
            "p_adjusted": None,
            "adjustment": "n/a (a measured floor, not a test)",
            "verdict": "SUPPORTS",
            "note": "Floor = 0 items, so turnover/floor is undefined (zero denominator) and floor-subtracted turnover = 137 - 0 = 137. TASK A.",
            "source": "reports/m5c_noise_floor_replicate_v1.json",
        },
        {
            "id": "L04",
            "claim_supported": "(prior weakest link) 16-sample dispersion implies expected discordance 0.2133 vs 0.2280 observed.",
            "statistic": "expected discordance fraction 0.21327735 between two independent Bernoulli(p_i) draws at step 100",
            "null": "temperature-1.0 sampling dispersion -- NOT the greedy harness",
            "p": None,
            "p_adjusted": None,
            "adjustment": "n/a",
            "verdict": "DOES NOT SUPPORT (and was never a test)",
            "note": "Explicitly labelled not-a-test when recorded; superseded by the measured zero floor in L03. It describes temperature-1.0 sampling, not replicate noise of the greedy eval that produced the 137.",
            "source": "reports/m5c_turnover_v1.json :: noise_reference_not_a_test; superseded per reports/m5c_noise_floor_replicate_v1.json :: superseded_reference",
        },
        {
            "id": "L05",
            "claim_supported": "Intermediate hops move accuracy significantly in BOTH directions, so the flat endpoint is a cancellation.",
            "statistic": "100->200: +86/-54, net +32; 200->400: +44/-71, net -27 (McNemar exact two-sided)",
            "null": "no net asymmetry at each hop",
            "p": f"{tr['100->200|acc_final']['mcnemar_exact_two_sided_p']:.6f} (100->200); {tr['200->400|acc_final']['mcnemar_exact_two_sided_p']:.6f} (200->400)",
            "p_adjusted": None,
            "adjustment": "not corrected in the source report; 7 hop tests exist, Bonferroni 0.05/7 = 0.00714 -> 100->200 survives, 200->400 does not",
            "verdict": "SUPPORTS (100->200); QUALIFIES (200->400 does not survive a 7-hop Bonferroni)",
            "note": "Correction arithmetic stated here explicitly; the source report reports the raw p only.",
            "source": "reports/m5c_turnover_v1.json",
        },
        {
            "id": "L06",
            "claim_supported": "WHICH items are lost is reproducible across checkpoints.",
            "statistic": "3-way Jaccard of LOST(100->200), LOST(100->300), LOST(100->400) = 0.3118 vs permutation null mean 0.0221",
            "null": "10,000 equal-size random subsets of the step-100-correct pool (n=262), seed 20260729",
            "p": forensics["multiplicity"]["tests"]["lost_set_three_way_jaccard"],
            "p_adjusted": prior_holm["lost_set_three_way_jaccard"]["p_holm_adjusted"],
            "adjustment": f"Holm-Bonferroni, {len(prior_fam)}-test family in the forensics artifact (reject: {prior_holm['lost_set_three_way_jaccard']['reject_at_family_alpha_0.05']})",
            "verdict": "SUPPORTS",
            "note": "Robust to per-item noise in either direction: noise would REDUCE cross-checkpoint agreement, not manufacture it. Limitation: the three lost sets share one step-100 anchor eval and come from one training trajectory, so serial dependence is not removed.",
            "source": "reports/m5c_lost_item_forensics_v1.json",
        },
        {
            "id": "L07",
            "claim_supported": "LOST items concentrate by problem type (derived stem bucket).",
            "statistic": f"chi-square {t1l['observed_chi2']:.4f} on {t1l['n_buckets_with_positive_expectation']} buckets (null mean {t1l['null_mean_chi2']:.4f}, 95th pct {t1l['null_q95_chi2']:.4f}); angle_measure lost rate {task1[A]['table_by_derived_stem_bucket']['angle_measure']['lost_rate_within_correct_at_100']:.4f}",
            "null": f"10,000 random equal-size ({t1l['draw_size']}) subsets of the step-100-correct pool (n={t1l['pool_size']}), seed {SEED}",
            "p": t1l["p_chi2_ge_observed"],
            "p_adjusted": H("T1_lost_bucket_chi2"),
            "adjustment": "Holm-Bonferroni over the 10 tests computed in this report",
            "verdict": None,
            "note": "Buckets are DEFINED BY THE ANALYSIS from the problem string (regex, fixed order, reused verbatim); geo3k carries no template/category/source field and qid and source_metadata are null on all 601 rows at all five steps.",
            "source": "this report, task 1",
        },
        {
            "id": "L08",
            "claim_supported": "GAINED items concentrate by problem type.",
            "statistic": f"chi-square {t1g['observed_chi2']:.4f} (null mean {t1g['null_mean_chi2']:.4f}, 95th pct {t1g['null_q95_chi2']:.4f})",
            "null": f"10,000 random equal-size ({t1g['draw_size']}) subsets of the step-100-WRONG pool (n={t1g['pool_size']}), seed {SEED}",
            "p": t1g["p_chi2_ge_observed"],
            "p_adjusted": H("T2_gained_bucket_chi2"),
            "adjustment": "Holm-Bonferroni over the 10 tests computed in this report",
            "verdict": None,
            "note": "Asymmetry with L07 is the substantive point: losses look type-structured, gains less so.",
            "source": "this report, task 1",
        },
        {
            "id": "L09",
            "claim_supported": "(uncontrolled) LOST items land on a numeric near-miss more often than stable-wrong items.",
            "statistic": f"{t2u['lost']['near_miss_count']}/{t2u['lost']['numeric_comparable']} = {t2u['lost']['near_miss_rate']:.4f} vs {t2u['stable_wrong']['near_miss_count']}/{t2u['stable_wrong']['numeric_comparable']} = {t2u['stable_wrong']['near_miss_rate']:.4f}",
            "null": "equal-size random subsets of the stable-wrong set (published) / arm-label permutation (here)",
            "p": forensics["multiplicity"]["tests"]["native_near_miss_rate"],
            "p_adjusted": prior_holm["native_near_miss_rate"]["p_holm_adjusted"],
            "adjustment": f"Holm-Bonferroni, {len(prior_fam)}-test forensics family (reject: {prior_holm['native_near_miss_rate']['reject_at_family_alpha_0.05']})",
            "verdict": "QUALIFIES",
            "note": (
                "NOT difficulty-controlled: LOST items were correct at step 100 by construction, "
                "stable-wrong items were not. See L10-L12. The raw p is also convention-dependent: "
                f"the published subset-draw convention reproduces here at "
                f"{fmt_p(t2u['test_published_subset_draw_convention']['p_rate_ge_observed'])}, but "
                f"arm-label permutation on the same data gives "
                f"{fmt_p(t2u['test']['p_one_sided_diff_ge_observed'])}. The subset-draw null puts "
                "sampling variance on one arm only."
            ),
            "source": "reports/m5c_lost_item_forensics_v1.json; recomputed here",
        },
        {
            "id": "L10",
            "claim_supported": "The near-miss effect survives matching on step-100 correctness using STABLE_CORRECT as reference.",
            "statistic": f"LOST {t2l['lost']['near_miss_count']}/{t2l['lost']['numeric_comparable']} = {t2l['lost']['near_miss_rate']:.4f} vs STABLE_CORRECT {t2l['stable_correct']['near_miss_count']}/{t2l['stable_correct']['numeric_comparable']} = {t2l['stable_correct']['near_miss_rate']:.4f}",
            "null": "none run -- the comparison is degenerate",
            "p": None,
            "p_adjusted": None,
            "adjustment": "excluded from the Holm family (not a test)",
            "verdict": "DOES NOT SUPPORT -- the requested matched comparison is DEGENERATE",
            "note": "STABLE_CORRECT items are correct at step 400 by definition, so their step-400 answer IS gold and their near-miss rate is 1.0 by construction. The matched pool as literally specified cannot test the hypothesis.",
            "source": "this report, task 2",
        },
        {
            "id": "L11",
            "claim_supported": "The near-miss effect survives a non-degenerate match on step-100 correctness.",
            "statistic": f"LOST(100->400) at step 400 {t2m['arm_a_lost_400']['near_miss_count']}/{t2m['arm_a_lost_400']['numeric_comparable']} = {t2m['arm_a_lost_400']['near_miss_rate']:.4f} vs DIP-AND-RECOVER at first dip step {t2m['arm_b_dip_and_recover']['near_miss_count']}/{t2m['arm_b_dip_and_recover']['numeric_comparable']} = {t2m['arm_b_dip_and_recover']['near_miss_rate']:.4f}; difference {t2m['test']['observed_rate_difference_a_minus_b']:+.4f}",
            "null": f"10,000 arm-label permutations, seed {SEED}",
            "p": t2m["test"]["p_one_sided_diff_ge_observed"],
            "p_adjusted": H("T3_near_miss_matched_dip_and_recover_one_sided"),
            "adjustment": "Holm-Bonferroni over the 10 tests computed in this report",
            "verdict": None,
            "note": (
                "Both arms are correct at step 100 and both are scored on a WRONG answer. "
                "Like-for-like (arm-label permutation on both sides): "
                + task2[A]["permutation_convention_matters"]["like_for_like_unmatched_to_matched"]
                + " Residual limitation: the reference arm's wrong answer is read at step "
                "150/200/300, not 400, because among step-100-correct items 'wrong at step S' IS "
                "lost-at-S."
            ),
            "source": "this report, task 2",
        },
        {
            "id": "L12",
            "claim_supported": "The near-miss effect is not an artefact of LOST items having larger gold answers (the +/-10% window widens with |gold|).",
            "statistic": f"|gold|-quartile-stratified rate difference {t2s['observed_stratified_rate_difference']:+.4f} (median |gold| LOST {t2s['median_abs_gold_lost']:.2f} vs stable-wrong {t2s['median_abs_gold_stable_wrong']:.2f})",
            "null": f"10,000 within-stratum arm-label permutations, seed {SEED}",
            "p": t2s["p_one_sided_ge_observed"],
            "p_adjusted": H("T4_near_miss_gold_magnitude_stratified_one_sided"),
            "adjustment": "Holm-Bonferroni over the 10 tests computed in this report",
            "verdict": None,
            "note": "Controls answer SCALE, not step-100 correctness. Complementary to L11, not a substitute.",
            "source": "this report, task 2",
        },
        {
            "id": "L13",
            "claim_supported": "LOST items were already marginal at step 100 in the decoder's own margin / logprob.",
            "statistic": "not computable",
            "null": "n/a",
            "p": None,
            "p_adjusted": None,
            "adjustment": "n/a",
            "verdict": "NOT MEASURABLE",
            "note": "No logprob, token-probability, logit, decoding-score or margin field exists in any of the five cached geo3k per-item files (full field census in the JSON). Steps 150/200/300/400 additionally have no sampled decode of any kind. No proxy is substituted.",
            "source": "this report, task 3",
        },
        {
            "id": "L14",
            "claim_supported": "(separate quantity, NOT the L13 margin test) LOST items had a lower step-100 16-sample pass rate than STABLE_CORRECT items.",
            "statistic": f"mean canonical_p_sample {t3s['mean_canonical_p_sample_lost']:.4f} (n={t3s['n_lost']}) vs {t3s['mean_canonical_p_sample_stable_correct']:.4f} (n={t3s['n_stable_correct']}); difference {t3s['observed_mean_difference_lost_minus_stable_correct']:+.4f}",
            "null": f"10,000 arm-label permutations, seed {SEED}",
            "p": t3s["p_two_sided"],
            "p_adjusted": H("T5_step100_sampled_pass_rate_lost_vs_stable_correct_two_sided"),
            "adjustment": "Holm-Bonferroni over the 10 tests computed in this report",
            "verdict": None,
            "note": "This is a temperature-1.0 n=16 empirical PASS RATE, not a decoding margin, and it exists only at step 100. It is reported as its own line so that L13 stays honestly NOT MEASURABLE. A reader wanting only the requested margin test should read L13.",
            "source": "this report, task 3 (side measurement)",
        },
        {
            "id": "L15",
            "claim_supported": "The five-step correctness patterns are not what independent per-step flipping produces.",
            "statistic": f"G2 = {t4n1['observed_G2_likelihood_ratio']:.2f} and Pearson X2 = {t4n1['observed_pearson_X2']:.2f} over 32 patterns (null max G2 across 10,000 replicates = {t4n1['null_max_G2']:.2f}, null mean {t4n1['null_mean_G2']:.2f})",
            "null": f"10,000 parametric-bootstrap datasets in which each item flips independently between steps at the observed per-step marginal accuracies, seed {SEED}",
            "p": t4n1["p_G2_ge_observed"],
            "p_adjusted": H("T6_pattern_G2_vs_independence"),
            "adjustment": "Holm-Bonferroni over the 10 tests computed in this report",
            "verdict": None,
            "note": f"Direction: MORE PERSISTENCE. never-correct {task4[A]['never_correct']} vs null mean {t4n1['null_mean_never_correct']:.1f}; always-correct {task4[A]['always_correct']} vs {t4n1['null_mean_always_correct']:.1f}; total adjacent flips {task4[A]['observed_total_adjacent_flips']} vs {t4n1['null_mean_total_flips']:.1f}.",
            "source": "this report, task 4",
        },
        {
            "id": "L16",
            "claim_supported": "Correctness is stickier in TIME than chance, holding each item's own number of correct steps fixed.",
            "statistic": f"total adjacent flips {task4[A]['observed_total_adjacent_flips']} vs within-item order-permutation null mean {t4n2['null_mean_total_flips']:.2f} (sd {t4n2['null_sd_total_flips']:.2f}) and row+column-margin-preserving null mean {t4n3['null_mean_total_flips']:.2f} (sd {t4n3['null_sd_total_flips']:.2f})",
            "null": f"N2: 10,000 within-item permutations of the five step labels. N3: 10,000 curveball samples preserving every item's correct-step count AND every step's accuracy count. seed {SEED}",
            "p": f"N2 {fmt_p(t4n2['p_total_flips_le_observed'])}; N3 {fmt_p(t4n3['p_total_flips_le_observed'])}",
            "p_adjusted": f"N2 {H('T9_total_flips_vs_within_item_order_permutation'):.4f}; N3 {H('T10_total_flips_vs_row_col_margin_preserving'):.4f}",
            "adjustment": "Holm-Bonferroni over the 10 tests computed in this report",
            "verdict": None,
            "note": "This is the test that separates 'items differ in difficulty' (already implied by L15) from 'movement is temporally ordered'. N3 is the strict version: it fixes both margins.",
            "source": "this report, task 4",
        },
    ]

    # fill verdicts that depend on Holm outcomes
    by_id = {row["id"]: row for row in ledger}
    n_fam = len(fam)

    def graded(tname: str, praw: float, pos_dir: bool) -> str:
        if not pos_dir:
            return "DOES NOT SUPPORT (effect is absent or runs the other way)"
        if holm_res[tname]["reject_at_family_alpha_0.05"]:
            return "SUPPORTS"
        if praw <= 0.05:
            return (
                "QUALIFIES -- raw p significant at 0.05 but does NOT survive Holm over this "
                f"report's {n_fam}-test family"
            )
        return "DOES NOT SUPPORT"

    for lid, tname, praw, pos_dir in [
        ("L07", "T1_lost_bucket_chi2", t1l["p_chi2_ge_observed"], True),
        ("L08", "T2_gained_bucket_chi2", t1g["p_chi2_ge_observed"], True),
        ("L11", "T3_near_miss_matched_dip_and_recover_one_sided",
         t2m["test"]["p_one_sided_diff_ge_observed"],
         t2m["test"]["observed_rate_difference_a_minus_b"] > 0),
        ("L12", "T4_near_miss_gold_magnitude_stratified_one_sided",
         t2s["p_one_sided_ge_observed"], (t2s["observed_stratified_rate_difference"] or 0) > 0),
        ("L14", "T5_step100_sampled_pass_rate_lost_vs_stable_correct_two_sided",
         t3s["p_two_sided"], t3s["observed_mean_difference_lost_minus_stable_correct"] < 0),
        ("L15", "T6_pattern_G2_vs_independence", t4n1["p_G2_ge_observed"], True),
    ]:
        by_id[lid]["verdict"] = graded(tname, praw, bool(pos_dir))
    n2_sticky = task4[A]["direction"]["n2_observed_minus_null_mean"] < 0
    n3_sticky = task4[A]["direction"]["n3_observed_minus_null_mean"] < 0
    if n2_sticky and n3_sticky:
        both = holm_res["T9_total_flips_vs_within_item_order_permutation"][
            "reject_at_family_alpha_0.05"
        ] and holm_res["T10_total_flips_vs_row_col_margin_preserving"][
            "reject_at_family_alpha_0.05"
        ]
        by_id["L16"]["verdict"] = "SUPPORTS" if both else (
            "QUALIFIES -- direction is sticky but at least one of the two nulls does not survive Holm"
        )
    else:
        by_id["L16"]["verdict"] = (
            "DOES NOT SUPPORT -- observed flips are not below the order-randomised nulls "
            f"(N2 delta {task4[A]['direction']['n2_observed_minus_null_mean']:+.2f}, "
            f"N3 delta {task4[A]['direction']['n3_observed_minus_null_mean']:+.2f})"
        )

    # Task B status (in flight while this report was written)
    taskb_dirs = {
        "step400_sampled": "experiments/runs/m5c_sampled_m5c-taskb-step400_an29_gpu4_20260730T122620Z",
        "step100_sampled_repro": "experiments/runs/m5c_sampled_m5c-taskb-step100-repro_an29_gpu5_20260730T122701Z",
    }
    taskb = {"report_exists": False, "runs": {}}
    for tag, rel in taskb_dirs.items():
        p = ROOT / rel / "per_item.jsonl"
        taskb["runs"][tag] = {
            "path": rel,
            "rows_written_at_read_time": (
                sum(1 for line in p.read_text().splitlines() if line.strip()) if p.exists() else 0
            ),
            "target_rows": 601,
        }
    taskb["status"] = (
        "M5C Task B (expected-discordance null from sampled p_i at both endpoints) had NOT emitted "
        "a report at the time this ledger was written; its two sampled evals were still writing "
        "rows. The ledger therefore carries Task A's measured floor (L03) and the superseded prior "
        "reference (L04) but no Task B result. This is a gap in the ledger, not a null result."
    )

    git_hash = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()

    result = {
        "schema_version": "blind-gains.m5c-evidence-ledger.v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_hash": git_hash,
        "task": "M5C Task C -- systematicity evidence + evidence ledger for the geo3k step-100 -> step-400 turnover finding",
        "compute": "CPU only on the login node; cached predictions and the existing substrate only; no GPU job started",
        "dataset": "Geometry3K test split (n=601), condition=real, arm=anchor_real, greedy temperature 0, seed 20260710",
        "runs": {str(s): RUNS[s] for s in STEPS},
        "scorer": forensics["scorer"],
        "permutation_convention": {
            "n_perm": N_PERM,
            "seed": SEED,
            "p_formula": "(hits + 1) / (n_perm + 1)",
            "p_floor": P_FLOOR,
            "note": "reported as max((hits+1)/(n_perm+1), 1e-4); the floor binds only at zero hits",
        },
        "source_artifacts": {
            "substrate": {"path": "reports/m5c_item_substrate_v1.jsonl", "sha256": sha256_file(SUBSTRATE)},
            "turnover": {"path": "reports/m5c_turnover_v1.json", "sha256": sha256_file(TURNOVER_JSON)},
            "forensics": {"path": "reports/m5c_lost_item_forensics_v1.json", "sha256": sha256_file(FORENSICS_JSON)},
            "noise_floor_task_a": {"path": "reports/m5c_noise_floor_replicate_v1.json", "sha256": sha256_file(NOISE_JSON)},
        },
        "verification": verification,
        "task1_problem_type_concentration": task1,
        "task2_near_miss_difficulty_control": task2,
        "task3_margin_field_census": task3,
        "task4_five_step_pattern_structure": task4,
        "multiplicity": multiplicity,
        "task_b_status": taskb,
        "evidence_ledger": ledger,
        "scope_limits": {
            "derived_buckets_are_analysis_defined": (
                "The problem-type buckets are regex rules defined by the earlier forensics analysis "
                "and reused verbatim here. They are NOT dataset metadata: qid and source_metadata "
                "are null on all 601 test rows at all five steps and the manifest carries only "
                "answer/images/problem/row_index/split. Any bucket-level result is a result about "
                "these rules, not about a curated taxonomy."
            ),
            "serial_dependence": (
                "All five checkpoints come from ONE training trajectory. Permutation nulls here "
                "randomise item membership or within-item temporal order; none of them removes "
                "dependence between checkpoints of the same run."
            ),
            "no_second_trajectory": (
                "There is no second training seed for this trajectory in this analysis, so nothing "
                "here separates 'this run's churn' from 'churn of this recipe'."
            ),
            "matched_near_miss_caveat": (
                "The only non-degenerate step-100-matched reference for the near-miss contrast "
                "reads its wrong answer at an EARLIER checkpoint than the LOST arm. That asymmetry "
                "is inherent to the design space, not a choice that could have been avoided."
            ),
        },
    }

    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_md(result), encoding="utf-8")
    print(json.dumps({
        "json": str(OUT_JSON), "json_sha256": sha256_file(OUT_JSON),
        "md": str(OUT_MD), "md_sha256": sha256_file(OUT_MD),
    }, indent=2))


# =====================================================================================
def render_md(r: dict[str, Any]) -> str:
    A = "acc_final"
    t1 = r["task1_problem_type_concentration"][A]
    t2 = r["task2_near_miss_difficulty_control"][A]
    t3 = r["task3_margin_field_census"]
    t4 = r["task4_five_step_pattern_structure"][A]
    mp = r["multiplicity"]
    L: list[str] = []
    ap = L.append

    ap("# M5c — evidence ledger for the geo3k step-100 → step-400 turnover finding (v1)")
    ap("")
    ap(f"Generated {r['generated_utc']}. git `{r['git_hash']}`. {r['compute']}.")
    ap("Facts, checks and provenance only.")
    ap("")

    ap("## THE LEDGER")
    ap("")
    ap("One row per piece of evidence. `p` is raw; `p (adj)` is Holm-adjusted where a correction applies.")
    ap("")
    ap("| # | claim it supports | statistic | null | p | p (adj) | verdict |")
    ap("|---|---|---|---|---|---|---|")
    def esc(x: str) -> str:
        return str(x).replace("|", "\\|")

    for row in r["evidence_ledger"]:
        p = row["p"]
        ps = "—" if p is None else (fmt_p(p) if isinstance(p, float) else esc(p))
        pa = row["p_adjusted"]
        pas = "—" if pa is None else (f"{pa:.4f}" if isinstance(pa, float) else esc(pa))
        ap(
            f"| {row['id']} | {esc(row['claim_supported'])} | {esc(row['statistic'])} | "
            f"{esc(row['null'])} | {ps} | {pas} | **{esc(row['verdict'])}** |"
        )
    ap("")
    ap("Row notes:")
    ap("")
    for row in r["evidence_ledger"]:
        ap(f"- **{row['id']}** — {row['note']} _(source: {row['source']}; adjustment: {row['adjustment']})_")
    ap("")

    ap("## Verification")
    ap("")
    v = r["verification"]
    ap("| check | result |")
    ap("|---|---|")
    ap(f"| bucket rules imported from | `{v['bucket_rules_imported_from']}` |")
    ap(f"| imported bucket rules identical to the published artifact's recorded rules | {v['bucket_rules_match_published_artifact']} |")
    ap(f"| test items per step (100/150/200/300/400) | {'/'.join(str(v['test_item_counts'][str(s)]) for s in (100,150,200,300,400))} |")
    ap(f"| item-key sets identical across all five steps | {v['item_key_sets_identical']} |")
    ap(f"| ground_truth identical across all five steps | {v['gold_identical_across_steps']} |")
    ap(f"| problem sha256 identical across all five steps | {v['problem_sha256_identical_across_steps']} |")
    ap(f"| substrate rows / value mismatches vs the cached runs | {v['substrate_rows']} / {v['substrate_value_mismatches_vs_runs']} |")
    ap(f"| acc_final == acc_strict on every item at every step | {v['acc_final_equals_acc_strict_all_items_all_steps']} |")
    ap(f"| set sizes reproduce the forensics artifact (lost/gained/stable_correct/stable_wrong) | {v['set_sizes_reproduce_forensics_artifact']} |")
    c = v["chi2_statistics_reproduce_published_artifact"]
    ap(f"| LOST bucket chi-square reproduces published statistic to 1e-9 | {c['lost_match_1e-9']} ({c['lost_observed_chi2_here']:.6f} vs {c['lost_observed_chi2_published']:.6f}) |")
    ap(f"| GAINED bucket chi-square reproduces published statistic to 1e-9 | {c['gained_match_1e-9']} ({c['gained_observed_chi2_here']:.6f} vs {c['gained_observed_chi2_published']:.6f}) |")
    ap("")
    ap(c["note"])
    ap("")
    ap("Everything below is reported under acc_final. acc_strict is stored separately in the JSON and is numerically identical, because acc_final == acc_strict on all 601 items at all five steps.")
    ap("")

    # --- task 1
    ap("## 1. Problem-type concentration, corrected")
    ap("")
    ap("Full derived-bucket × transition table. `stable` = stable_correct + stable_wrong; the four transition columns partition all 601 items.")
    ap("")
    ap("| derived bucket | total | lost | gained | stable | stable_correct | stable_wrong | correct@100 | wrong@100 | lost rate within correct@100 | gained rate within wrong@100 |")
    ap("|---|---|---|---|---|---|---|---|---|---|---|")
    tab = t1["table_by_derived_stem_bucket"]
    for b in sorted(tab):
        d = tab[b]
        lr = "—" if d["lost_rate_within_correct_at_100"] is None else f"{d['lost_rate_within_correct_at_100']:.4f}"
        gr = "—" if d["gained_rate_within_wrong_at_100"] is None else f"{d['gained_rate_within_wrong_at_100']:.4f}"
        ap(f"| {b} | {d['total_items']} | {d['lost']} | {d['gained']} | {d['stable']} | {d['stable_correct']} | {d['stable_wrong']} | {d['correct_at_100']} | {d['wrong_at_100']} | {lr} | {gr} |")
    ct = t1["column_totals"]
    ap(f"| **TOTAL** | **{ct['total_items']}** | **{ct['lost']}** | **{ct['gained']}** | **{ct['stable']}** | **{ct['stable_correct']}** | **{ct['stable_wrong']}** | **{ct['correct_at_100']}** | **{ct['wrong_at_100']}** | | |")
    ap("")
    ap(f"Table consistency checks (all run in code): {t1['table_consistency_checks']}")
    ap("")
    for tag, key in (("LOST", "lost_bucket_concentration"), ("GAINED", "gained_bucket_concentration")):
        b = t1[key]
        ap(
            f"- **{tag}** bucket concentration vs {b['pool']} (pool n = {b['pool_size']}, draw {b['draw_size']}): "
            f"chi-square **{b['observed_chi2']:.4f}**, null mean {b['null_mean_chi2']:.4f} "
            f"(sd {b['null_sd_chi2']:.4f}, 95th pct {b['null_q95_chi2']:.4f}), "
            f"{b['n_perm']} permutations at seed {b['seed']}, raw p **{fmt_p(b['p_chi2_ge_observed'])}**."
        )
    ap("")
    lostname = "T1_lost_bucket_chi2"
    gname = "T2_gained_bucket_chi2"
    hl, hg = mp["holm"][lostname], mp["holm"][gname]
    ap(
        f"**Does LOST concentration survive correction?** Raw p {fmt_p(hl['p_raw'])}; Holm-adjusted p "
        f"**{hl['p_holm_adjusted']:.4f}** over the {mp['n_tests_in_family']}-test family computed in this "
        f"report; Holm reject at family alpha 0.05: **{hl['reject_at_family_alpha_0.05']}**. "
        f"It also failed Holm inside the earlier 15-test forensics family "
        f"(reject: {mp['prior_family_holm_from_forensics_artifact']['holm_bonferroni_reject']['lost_derived_bucket_chi2']})."
    )
    ap(
        f"GAINED: raw p {fmt_p(hg['p_raw'])}, Holm-adjusted {hg['p_holm_adjusted']:.4f}, "
        f"reject: {hg['reject_at_family_alpha_0.05']}."
    )
    ap("")

    # --- task 2
    ap("## 2. Difficulty control for the near-miss result")
    ap("")
    ap(f"Near-miss rule (identical to the forensics artifact): {t2['near_miss_rule']}")
    ap("")
    u, lit, m2, s2 = (
        t2["uncontrolled_reference"], t2["literal_matched_pool_lost_vs_stable_correct"],
        t2["matched_design_dip_and_recover"], t2["stratified_by_gold_magnitude"],
    )
    ap("| design | arm A | rate A | arm B | rate B | difference | raw p | Holm p | controlled for |")
    ap("|---|---|---|---|---|---|---|---|---|")
    ap(
        f"| uncontrolled (published) | LOST @400 | {u['lost']['near_miss_count']}/{u['lost']['numeric_comparable']} = {u['lost']['near_miss_rate']:.4f} | "
        f"stable-wrong @400 | {u['stable_wrong']['near_miss_count']}/{u['stable_wrong']['numeric_comparable']} = {u['stable_wrong']['near_miss_rate']:.4f} | "
        f"{u['test']['observed_rate_difference_a_minus_b']:+.4f} | {fmt_p(u['test']['p_one_sided_diff_ge_observed'])} | — | nothing |"
    )
    ap(
        f"| literal matched pool | LOST @400 | {lit['lost']['near_miss_count']}/{lit['lost']['numeric_comparable']} = {lit['lost']['near_miss_rate']:.4f} | "
        f"stable_correct @400 | {lit['stable_correct']['near_miss_count']}/{lit['stable_correct']['numeric_comparable']} = {lit['stable_correct']['near_miss_rate']:.4f} | "
        f"— | DEGENERATE | — | step-100 correctness |"
    )
    ap(
        f"| matched, non-degenerate | LOST @400 | {m2['arm_a_lost_400']['near_miss_count']}/{m2['arm_a_lost_400']['numeric_comparable']} = {m2['arm_a_lost_400']['near_miss_rate']:.4f} | "
        f"dip-and-recover @first dip | {m2['arm_b_dip_and_recover']['near_miss_count']}/{m2['arm_b_dip_and_recover']['numeric_comparable']} = {m2['arm_b_dip_and_recover']['near_miss_rate']:.4f} | "
        f"{m2['test']['observed_rate_difference_a_minus_b']:+.4f} | {fmt_p(m2['test']['p_one_sided_diff_ge_observed'])} | "
        f"{mp['holm']['T3_near_miss_matched_dip_and_recover_one_sided']['p_holm_adjusted']:.4f} | step-100 correctness |"
    )
    ap(
        f"| \\|gold\\|-stratified | LOST @400 | — | stable-wrong @400 | — | "
        f"{s2['observed_stratified_rate_difference']:+.4f} | {fmt_p(s2['p_one_sided_ge_observed'])} | "
        f"{mp['holm']['T4_near_miss_gold_magnitude_stratified_one_sided']['p_holm_adjusted']:.4f} | answer scale |"
    )
    ap("")
    pcm = t2["permutation_convention_matters"]
    ap(f"**The permutation convention matters.** {pcm['note']}")
    ap("")
    ap(
        f"Published subset-draw convention reproduced here: p {fmt_p(pcm['uncontrolled_subset_draw_p'])} "
        f"(published value {fmt_p(u['published_p_for_comparison'])}). Same data, arm-label permutation: "
        f"p {fmt_p(pcm['uncontrolled_arm_label_p'])}. Matched design, arm-label permutation: "
        f"p {fmt_p(pcm['matched_arm_label_p'])}."
    )
    ap("")
    ap(f"Like-for-like: {pcm['like_for_like_unmatched_to_matched']}")
    ap("")
    ap(f"**Why the literal matched pool is degenerate.** {lit['degeneracy_reason']}")
    ap("")
    ap(f"**The non-degenerate matched design.** {m2['design']}")
    ap("")
    ap(m2["rationale"])
    ap("")
    ap(f"Reference arm size {m2['arm_b_size']}; first-dip step histogram {m2['arm_b_dip_step_histogram']}.")
    ap("")
    ap(f"**Scale control.** {s2['controls']} |gold| quartile cuts {[round(x,4) for x in s2['abs_gold_quartile_cuts']]}; median |gold| LOST {s2['median_abs_gold_lost']:.2f} vs stable-wrong {s2['median_abs_gold_stable_wrong']:.2f}.")
    ap("")
    ap("| \\|gold\\| stratum | range | n LOST | n stable-wrong | near-miss rate LOST | near-miss rate stable-wrong |")
    ap("|---|---|---|---|---|---|")
    for sv in sorted(s2["strata"], key=int):
        d = s2["strata"][sv]
        ra = "—" if d["near_miss_rate_lost"] is None else f"{d['near_miss_rate_lost']:.4f}"
        rb = "—" if d["near_miss_rate_stable_wrong"] is None else f"{d['near_miss_rate_stable_wrong']:.4f}"
        lo, hi = d["abs_gold_range"]
        ap(f"| {sv} | [{lo:.3g}, {hi:.3g}] | {d['n_lost']} | {d['n_stable_wrong']} | {ra} | {rb} |")
    ap("")
    ap("**Does the effect survive matching?** " + r["evidence_ledger"][10]["verdict"] + " (row L11); scale-stratified: " + r["evidence_ledger"][11]["verdict"] + " (row L12).")
    ap("")

    # --- task 3
    ap("## 3. Margin / confidence collapse — field census")
    ap("")
    ap(f"**{t3['answer']}**")
    ap("")
    ap("| step | per_item.jsonl | fields | fields matching logprob/score/margin candidates |")
    ap("|---|---|---|---|")
    for s in ("100", "150", "200", "300", "400"):
        f = t3["field_census"][s]
        mm = f["fields_matching_logprob_score_margin_candidates"]
        ap(f"| {s} | `{f['per_item_path']}` | {f['n_fields']} | {', '.join(f'`{x}`' for x in mm) if mm else '**none**'} |")
    ap("")
    ap(t3["matched_candidate_fields_are_substring_false_positives"])
    ap("")
    ap(t3["why_the_step_100_fields_are_not_a_margin"])
    ap("")
    ap(f"**Verdict: {t3['verdict']}**")
    ap("")
    ap(t3["step_400_margin_is_unavailable_even_from_sampling"])
    ap("")
    sm = t3["side_measurement_not_the_margin_test"]
    ap("### Separate measurement that is NOT the margin test")
    ap("")
    ap(f"What it is: {sm['what_it_is']}")
    ap("")
    ap(f"What it is not: {sm['what_it_is_not']}")
    ap("")
    d = sm["results"][A]
    ap(
        f"LOST mean canonical_p_sample {d['mean_canonical_p_sample_lost']:.4f} (median {d['median_lost']:.4f}, n={d['n_lost']}) "
        f"vs STABLE_CORRECT {d['mean_canonical_p_sample_stable_correct']:.4f} (median {d['median_stable_correct']:.4f}, n={d['n_stable_correct']}); "
        f"difference {d['observed_mean_difference_lost_minus_stable_correct']:+.4f}; "
        f"two-sided permutation p {fmt_p(d['p_two_sided'])}, Holm-adjusted "
        f"{mp['holm']['T5_step100_sampled_pass_rate_lost_vs_stable_correct_two_sided']['p_holm_adjusted']:.4f}."
    )
    ap("")

    # --- task 4
    ap("## 4. Five-step pattern structure vs independence")
    ap("")
    ap(f"Per-step marginal accuracy: " + ", ".join(f"step {s} = {t4['per_step_marginal_accuracy'][s]:.6f}" for s in ("100","150","200","300","400")) + ".")
    ap(
        f"{t4['n_distinct_patterns_observed']} of {t4['n_possible_patterns']} possible 5-bit patterns occur. "
        f"never correct {t4['never_correct']}, always correct {t4['always_correct']}, moved at least once {t4['moved_at_least_once']}. "
        f"Total adjacent flips {t4['observed_total_adjacent_flips']}; items with zero flips {t4['observed_items_with_zero_flips']}."
    )
    ap("")
    n1 = t4["null_N1_independent_bernoulli_at_observed_step_marginals"]
    ap("### Null N1 — each item flips independently between steps at the observed per-step rates")
    ap("")
    ap(n1["definition"])
    ap("")
    ap("| statistic | observed | null mean | null sd | null extreme | raw p | Holm p |")
    ap("|---|---|---|---|---|---|---|")
    ap(f"| G² likelihood ratio (32 patterns) | {n1['observed_G2_likelihood_ratio']:.4f} | {n1['null_mean_G2']:.4f} | {n1['null_sd_G2']:.4f} | max {n1['null_max_G2']:.4f} | {fmt_p(n1['p_G2_ge_observed'])} | {mp['holm']['T6_pattern_G2_vs_independence']['p_holm_adjusted']:.4f} |")
    ap(f"| Pearson X² (32 patterns) | {n1['observed_pearson_X2']:.4f} | {n1['null_mean_X2']:.4f} | — | max {n1['null_max_X2']:.4f} | {fmt_p(n1['p_X2_ge_observed'])} | {mp['holm']['T7_pattern_X2_vs_independence']['p_holm_adjusted']:.4f} |")
    ap(f"| total adjacent flips | {t4['observed_total_adjacent_flips']} | {n1['null_mean_total_flips']:.2f} | {n1['null_sd_total_flips']:.2f} | min {n1['null_min_total_flips']} | {fmt_p(n1['p_total_flips_le_observed'])} | {mp['holm']['T8_total_flips_vs_independence']['p_holm_adjusted']:.4f} |")
    ap(f"| never correct | {t4['never_correct']} | {n1['null_mean_never_correct']:.2f} | — | — | {fmt_p(n1['p_never_correct_ge_observed'])} | not in family |")
    ap(f"| always correct | {t4['always_correct']} | {n1['null_mean_always_correct']:.2f} | — | — | {fmt_p(n1['p_always_correct_ge_observed'])} | not in family |")
    ap(f"| items with zero flips | {t4['observed_items_with_zero_flips']} | {n1['null_mean_items_with_zero_flips']:.2f} | — | — | {fmt_p(n1['p_items_with_zero_flips_ge_observed'])} | not in family |")
    ap("")
    ap(f"Analytic expected total flips under N1: {n1['expected_total_adjacent_flips_analytic']:.2f}. Asymptotic df, reference only: {n1['asymptotic_df_reference_only']}.")
    ap("")
    ap(f"**Direction vs N1:** {t4['direction']['vs_N1_independence']}")
    ap("")
    n2, n3 = t4["null_N2_within_item_label_permutation"], t4["null_N3_row_and_column_margin_preserving_curveball"]
    ap("### Nulls N2 and N3 — hold each item's own difficulty fixed, randomise only the temporal order")
    ap("")
    ap(f"- **N2.** {n2['definition']} Observed flips {n2['observed_total_adjacent_flips']} vs null mean {n2['null_mean_total_flips']:.2f} (sd {n2['null_sd_total_flips']:.2f}, min {n2['null_min_total_flips']}), raw p(flips ≤ observed) {fmt_p(n2['p_total_flips_le_observed'])}, Holm {mp['holm']['T9_total_flips_vs_within_item_order_permutation']['p_holm_adjusted']:.4f}.")
    ap(f"- **N3.** {n3['definition']} Margins preserved at every sample: {n3['margins_preserved_at_every_sample']}. Observed flips {n3['observed_total_adjacent_flips']} vs null mean {n3['null_mean_total_flips']:.2f} (sd {n3['null_sd_total_flips']:.2f}, min {n3['null_min_total_flips']}), raw p(flips ≤ observed) {fmt_p(n3['p_total_flips_le_observed'])}, Holm {mp['holm']['T10_total_flips_vs_row_col_margin_preserving']['p_holm_adjusted']:.4f}.")
    ap("")
    ap(f"**Direction vs N2/N3:** {t4['direction']['vs_N2_and_N3_given_item_difficulty']}")
    ap("")
    ap("Observed − null-mean flips: " + f"N1 {t4['direction']['n1_observed_minus_null_mean']:+.2f}, N2 {t4['direction']['n2_observed_minus_null_mean']:+.2f}, N3 {t4['direction']['n3_observed_minus_null_mean']:+.2f}.")
    ap("")
    ap("Pattern-by-pattern observed vs independence expectation (steps 100/150/200/300/400):")
    ap("")
    ap("| pattern | steps correct | flips | observed | expected under N1 | obs − exp |")
    ap("|---|---|---|---|---|---|")
    for pat in sorted(t4["pattern_table"], key=lambda b: -t4["pattern_table"][b]["observed"]):
        d = t4["pattern_table"][pat]
        ap(f"| `{pat}` | {d['n_steps_correct']} | {d['n_adjacent_flips']} | {d['observed']} | {d['expected_under_independence']:.2f} | {d['obs_minus_exp']:+.2f} |")
    ap("")

    # --- multiplicity
    ap("## 5. Multiplicity")
    ap("")
    ap(mp["family_definition"])
    ap(f"Family alpha {mp['family_alpha']}, {mp['n_tests_in_family']} tests, plain Bonferroni threshold {mp['bonferroni_threshold']:.6f}.")
    ap("")
    ap("| test | raw p | Holm rank | Holm threshold | Holm-adjusted p | reject at 0.05 |")
    ap("|---|---|---|---|---|---|")
    for name in sorted(mp["holm"], key=lambda n: mp["holm"][n]["rank"]):
        h = mp["holm"][name]
        ap(f"| `{name}` | {fmt_p(h['p_raw'])} | {h['rank']} | {h['holm_threshold_at_rank']:.6f} | {h['p_holm_adjusted']:.4f} | {h['reject_at_family_alpha_0.05']} |")
    ap("")
    ap("Excluded from this family, and why:")
    for k, why in mp["excluded_from_family_and_why"].items():
        ap(f"- `{k}` — {why}")
    ap("")

    ap("## Task B status")
    ap("")
    tb = r["task_b_status"]
    ap(tb["status"])
    ap("")
    for tag, d in tb["runs"].items():
        ap(f"- `{tag}`: `{d['path']}` — {d['rows_written_at_read_time']}/{d['target_rows']} rows written when this report read it.")
    ap("")

    ap("## Scope limits")
    ap("")
    for k, why in r["scope_limits"].items():
        ap(f"- **{k}** — {why}")
    ap("")
    ap("## Provenance")
    ap("")
    for tag, d in r["source_artifacts"].items():
        ap(f"- {tag}: `{d['path']}` sha256 `{d['sha256']}`")
    for s in ("100", "150", "200", "300", "400"):
        ap(f"- step {s}: `experiments/runs/{r['runs'][s]}/per_item.jsonl`")
    ap(f"- scorer: `{r['scorer']}`")
    pc = r["permutation_convention"]
    ap(f"- permutation convention: p = (hits+1)/(n_perm+1), n_perm = {pc['n_perm']}, seed = {pc['seed']}, reported as max(p, {pc['p_floor']:.0e}); {pc['note']}")
    ap("")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
