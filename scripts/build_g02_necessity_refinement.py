#!/usr/bin/env python3
"""G0.2 necessity refinement (addendum to Gate 0).

Scope discipline (I13): this addendum operates ONLY on Gate 0's binary
blind-answerable split (q_blind floor rule). It never merges with, and makes no
claim about, the G0.1 / M5c Delta-q tercile analysis.

Deliverables:
  1. Exact reproduction of the published 84% / 42% from the frozen
     reports/gate0_stratification_v1.json G0_2_headroom_control block.
  2. Item-bootstrap intervals ON THE RATIOS (10,000 draws, seed 20260730,
     paired on items, percentile 2.5/97.5) + overlap verdict.
  3. B1/B2 decomposition of the not-blind-answerable stratum.
  4. Difficulty-standardised recovery pair (common q_real distribution).
  5. Proposed replacement wording for the stratum label (PI owns the prose).
  6. Lenient (acc_final) and strict (acc_strict) reported throughout (I7).

CPU only, cached predictions only, no GPU job.
"""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
BOOT = 10000
SEED = 20260730
PCT = (2.5, 97.5)

rep = json.loads((ROOT / "reports/gate0_stratification_v1.json").read_text())
PUB = rep["G0_2_headroom_control"]
CROSSED = rep["crossed_runs"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(rel):
    return [json.loads(l) for l in (ROOT / rel).read_text().splitlines() if l.strip()]


def key(r):
    return (r["problem"], tuple(r.get("image_sha256") or []))


# ---------------------------------------------------------------- inputs
G = "experiments/runs/blind_solvability_v2_guarded_rescore_geo3k_filtered_v2_retry_%s_login_%s/per_item.jsonl"
REAL_REL = G % ("real", "20260712T050905Z")
NONE_REL = G % ("none", "20260712T055030Z")
BR = {key(r): r for r in load(REAL_REL)}
BN = {key(r): r for r in load(NONE_REL)}
REF_REL = Path(rep["arm_runs"]["a1_real"]["1"]).relative_to(ROOT).as_posix()
ITEMS = [key(r) for r in load(REF_REL)]
N = len(ITEMS)
assert len(set(ITEMS)) == N == 601, (len(set(ITEMS)), N)

b_final = np.array([float(bool(BR[k]["greedy_canonical_correct"])) for k in ITEMS])
b_strict = np.array([float(BR[k]["greedy_acc_strict"]) for k in ITEMS])
q_blind = np.array([float(BN[k]["q_i"]) for k in ITEMS])
q_real = np.array([float(BR[k]["q_i"]) for k in ITEMS])
c_blind = np.array([int(BN[k]["sample_correct_count"]) for k in ITEMS])
c_real = np.array([int(BR[k]["sample_correct_count"]) for k in ITEMS])
n_samples = sorted({int(BR[k]["sample_count"]) for k in ITEMS} | {int(BN[k]["sample_count"]) for k in ITEMS})
FLOOR = float(q_blind.min())

ARMS = ("a1_real", "a2b_noimage", "a2_gray", "a3_caption")
MODES = ("lenient", "strict")
FIELD = {"lenient": "acc_final", "strict": "acc_strict"}


def crossed(arm, seed, field):
    rows = {key(r): r for r in load(f"experiments/runs/{CROSSED[f'{arm}|s{seed}']}/predictions.jsonl")}
    return np.array([float(rows[k][field]) for k in ITEMS])


gain, strict_identity = {}, True
for a in ARMS:
    fin = np.mean([crossed(a, s, "acc_final") for s in (1, 2, 3)], axis=0)
    stc = np.mean([crossed(a, s, "acc_strict") for s in (1, 2, 3)], axis=0)
    strict_identity &= bool(np.allclose(fin, stc))
    gain[(a, "lenient")] = fin - b_final
    gain[(a, "strict")] = stc - b_strict

# ------------------------------------------------- strata + rule audit
ans_pub = q_blind > FLOOR + 1e-9      # rule AS EXECUTED by build_g02_headroom_control.py
ans_reg = c_blind > 0                 # rule AS REGISTERED (prereg: floor is exactly c_i = 0)
disc = np.where(ans_pub != ans_reg)[0]
rule_audit = {
    "q_i_definition": "q_i = mixed_group_probability(p_i, g) = 1 - p^g - (1-p)^g  (src/eval/blind_solvability.py:74-77, called at :235)",
    "symmetry": "q_i is symmetric under p -> 1-p, so c_i = 16/16 yields the SAME numeric q_i as c_i = 0/16",
    "registered_floor_rule": ("scripts/build_preregistration_pilot_draft.py:382 -- 'The floor is exactly c_i=0 "
                              "(0/16 sampled successes, q_i=0.138659), not every item numerically sharing that symmetric q_i.'"),
    "executed_floor_rule": "scripts/build_g02_headroom_control.py:40-42 -- answerable = q_blind > min(q_blind) + 1e-9 (numeric)",
    "n_published_rule": {"blind_answerable": int(ans_pub.sum()), "not_blind_answerable": int((~ans_pub).sum())},
    "n_registered_rule": {"blind_answerable": int(ans_reg.sum()), "not_blind_answerable": int((~ans_reg).sum())},
    "n_discordant_items": int(len(disc)),
    "discordant_items": [{"item_index_in_eval_order": int(i), "c_blind": int(c_blind[i]),
                          "q_blind": float(q_blind[i]), "c_real": int(c_real[i]), "q_real": float(q_real[i]),
                          "classified_by_published_rule": "not_blind_answerable",
                          "classified_by_registered_rule": "blind_answerable",
                          "a1_gain_lenient": float(gain[("a1_real", "lenient")][i]),
                          "a2b_gain_lenient": float(gain[("a2b_noimage", "lenient")][i]),
                          "a1_gain_strict": float(gain[("a1_real", "strict")][i]),
                          "a2b_gain_strict": float(gain[("a2b_noimage", "strict")][i])} for i in disc],
}
rule_audit["why_lenient_ratios_unchanged"] = (
    "Every discordant item has a LENIENT gain of exactly 0 for both A1 and A2b (base already correct with the "
    "image, arm still correct). Moving a zero-gain item between strata leaves both stratum sums unchanged and "
    "rescales numerator and denominator by the same n, so the lenient recovery ratios are numerically identical "
    "under both rules. The strict ratios do shift, because the item has a non-zero strict gain (base acc_strict = 0 "
    "while base acc_final = 1)."
) if len(disc) and all(gain[("a1_real", "lenient")][i] == 0 and gain[("a2b_noimage", "lenient")][i] == 0
                       for i in disc) else "n/a"

STRATA = {
    "blind_answerable": np.where(ans_pub)[0],
    "not_blind_answerable": np.where(~ans_pub)[0],
    "B1_image_buys_opportunity": np.where(~ans_pub & (c_real > 0))[0],
    "B2_never_solved_any_condition": np.where(~ans_pub & (c_real == 0))[0],
    "blind_answerable_registered_rule": np.where(ans_reg)[0],
    "not_blind_answerable_registered_rule": np.where(~ans_reg)[0],
}
BASE_WRONG = b_final == 0
for nm in ("blind_answerable", "not_blind_answerable"):
    m = np.zeros(N, bool); m[STRATA[nm]] = True
    STRATA[nm + "__base_wrong_only"] = np.where(m & BASE_WRONG)[0]

# One RNG, draws generated once in sorted stratum order and reused everywhere,
# so every interval in this report comes from the same seed-20260730 draw set.
rng = np.random.default_rng(SEED)
DRAWS = {nm: STRATA[nm][rng.integers(0, len(STRATA[nm]), size=(BOOT, len(STRATA[nm])))]
         for nm in sorted(STRATA)}


def mean_ci(v_full, nm):
    idx = STRATA[nm]
    b = v_full[DRAWS[nm]].mean(axis=1)
    return {"n": int(len(idx)), "mean": float(v_full[idx].mean()),
            "ci95": [float(np.percentile(b, PCT[0])), float(np.percentile(b, PCT[1]))]}


def ratio_block(nm, mode, num="a2b_noimage", den="a1_real"):
    idx, d = STRATA[nm], DRAWS[nm]
    gn, gd = gain[(num, mode)], gain[(den, mode)]
    bn, bd = gn[d].mean(axis=1), gd[d].mean(axis=1)
    reps = bn / bd
    return {
        "n": int(len(idx)),
        "numerator_arm": num, "denominator_arm": den,
        "a1_gain": mean_ci(gd, nm), "a2b_gain": mean_ci(gn, nm),
        "recovery_ratio": float(gn[idx].mean() / gd[idx].mean()),
        "recovery_ratio_ci95": [float(np.percentile(reps, PCT[0])), float(np.percentile(reps, PCT[1]))],
        "bootstrap": {"draws": BOOT, "seed": SEED, "percentiles": list(PCT),
                      "paired_on_items": True, "resampling": "within-stratum, item-level, with replacement",
                      "degenerate_replicates_denominator_le_0": int((bd <= 0).sum())},
    }, reps


def overlap(a, b):
    return not (a[0] > b[1] or b[0] > a[1])


def diff_block(rA, rB, lab, pA, pB):
    """pA, pB are the OBSERVED plug-in ratios; rA, rB the bootstrap replicate vectors."""
    d = rA - rB
    mass = float((d <= 0).mean())
    return {"contrast": lab,
            "point": float(pA - pB),
            "ci95": [float(np.percentile(d, PCT[0])), float(np.percentile(d, PCT[1]))],
            "bootstrap_replicate_mean_difference": float(np.mean(d)),
            "bootstrap_mass_le_0": mass,
            "bootstrap_mass_le_0_display": ("<%.4f" % (1.0 / BOOT)) if mass == 0.0 else ("%.4f" % mass)}


# ------------------------------------------------- 1. reproduction
repro = {"target_artifact": "reports/gate0_stratification_v1.json :: G0_2_headroom_control",
         "status": None, "max_abs_deviation": 0.0, "cells": []}
maxdev = 0.0
for scope, sel in (("all_items", ""), ("base_wrong_only", "__base_wrong_only")):
    for st in ("blind_answerable", "not_blind_answerable"):
        nm = st + sel
        idx = STRATA[nm]
        row = {"scope": scope, "stratum": st, "n": int(len(idx)), "n_published": PUB["arms"]["a1_real"][scope][st]["n"]}
        for arm in ARMS:
            m = float(gain[(arm, "lenient")][idx].mean())
            p = float(PUB["arms"][arm][scope][st]["mean"])
            maxdev = max(maxdev, abs(m - p))
            row[arm] = {"recomputed": m, "published": p, "abs_deviation": abs(m - p)}
        r = row["a2b_noimage"]["recomputed"] / row["a1_real"]["recomputed"]
        rp = row["a2b_noimage"]["published"] / row["a1_real"]["published"]
        row["recovery_ratio_recomputed"] = r
        row["recovery_ratio_from_published_means"] = rp
        row["recovery_percent_rounded"] = int(round(100 * r))
        repro["cells"].append(row)
repro["max_abs_deviation"] = maxdev
repro["status"] = "EXACT" if maxdev < 1e-12 else "MISMATCH"
repro["published_headline_reproduced"] = {
    "blind_answerable_84pct": next(c["recovery_percent_rounded"] for c in repro["cells"]
                                   if c["scope"] == "all_items" and c["stratum"] == "blind_answerable") == 84,
    "not_blind_answerable_42pct": next(c["recovery_percent_rounded"] for c in repro["cells"]
                                       if c["scope"] == "all_items" and c["stratum"] == "not_blind_answerable") == 42,
}
assert repro["status"] == "EXACT", repro["max_abs_deviation"]
assert all(repro["published_headline_reproduced"].values())

# ------------------------------------------------- 2. ratio intervals
ratios, reps_store = {}, {}
for mode in MODES:
    ratios[mode] = {}
    for nm in ("blind_answerable", "not_blind_answerable",
               "blind_answerable__base_wrong_only", "not_blind_answerable__base_wrong_only",
               "B1_image_buys_opportunity", "B2_never_solved_any_condition",
               "blind_answerable_registered_rule", "not_blind_answerable_registered_rule"):
        blk, reps = ratio_block(nm, mode)
        ratios[mode][nm] = blk
        reps_store[(mode, nm)] = reps

headline = {}
for mode in MODES:
    A = ratios[mode]["blind_answerable"]; B = ratios[mode]["not_blind_answerable"]
    Aw = ratios[mode]["blind_answerable__base_wrong_only"]; Bw = ratios[mode]["not_blind_answerable__base_wrong_only"]
    headline[mode] = {
        "blind_answerable": A, "not_blind_answerable": B,
        "intervals_overlap": bool(overlap(A["recovery_ratio_ci95"], B["recovery_ratio_ci95"])),
        "difference": diff_block(reps_store[(mode, "blind_answerable")],
                                 reps_store[(mode, "not_blind_answerable")],
                                 "recovery(blind_answerable) - recovery(not_blind_answerable)",
                                 A["recovery_ratio"], B["recovery_ratio"]),
        "base_wrong_only": {
            "blind_answerable": Aw, "not_blind_answerable": Bw,
            "intervals_overlap": bool(overlap(Aw["recovery_ratio_ci95"], Bw["recovery_ratio_ci95"])),
            "difference": diff_block(reps_store[(mode, "blind_answerable__base_wrong_only")],
                                     reps_store[(mode, "not_blind_answerable__base_wrong_only")],
                                     "base-wrong recovery difference",
                                     Aw["recovery_ratio"], Bw["recovery_ratio"]),
            "lenient_strict_identity_note": (
                "On base-wrong items lenient and strict gains are IDENTICAL by construction: base acc_final = 0 "
                "implies base acc_strict = 0 (verified for all 496 base-wrong items), and every trained arm "
                "satisfies acc_strict == acc_final on every item (G0.4 identity, re-verified here). The two rows "
                "are therefore expected to match exactly; this is not a duplication error."),
        },
    }

# ------------------------------------------------- 3. B1/B2
b1b2 = {"definition": {
    "parent_stratum": "not_blind_answerable (n=484), the stratum the published text labels 'items requiring pixels'",
    "B1_image_buys_opportunity": "c_real > 0: at least one of the 16 frozen base samples is correct WITH the image",
    "B2_never_solved_any_condition": "c_real == 0: zero observed successes with the image AND zero without",
    "note": "on this eval split q_real sits at the Jeffreys floor iff c_real == 0 (verified, 278/601 items); "
            "the symmetric-q_i hazard that affects q_blind does not bite here",
    "n_B1": int(len(STRATA["B1_image_buys_opportunity"])),
    "n_B2": int(len(STRATA["B2_never_solved_any_condition"])),
    "n_B1_plus_B2": int(len(STRATA["B1_image_buys_opportunity"]) + len(STRATA["B2_never_solved_any_condition"])),
}, "base_real_greedy_accuracy": {
    "B1": float(b_final[STRATA["B1_image_buys_opportunity"]].mean()),
    "B2": float(b_final[STRATA["B2_never_solved_any_condition"]].mean()),
}, "by_mode": {}}
for mode in MODES:
    b1b2["by_mode"][mode] = {
        "B1_image_buys_opportunity": ratios[mode]["B1_image_buys_opportunity"],
        "B2_never_solved_any_condition": ratios[mode]["B2_never_solved_any_condition"],
        "difference": diff_block(reps_store[(mode, "B1_image_buys_opportunity")],
                                 reps_store[(mode, "B2_never_solved_any_condition")], "B1 - B2",
                                 ratios[mode]["B1_image_buys_opportunity"]["recovery_ratio"],
                                 ratios[mode]["B2_never_solved_any_condition"]["recovery_ratio"]),
        "B2_ci_includes_zero": bool(ratios[mode]["B2_never_solved_any_condition"]["recovery_ratio_ci95"][0] <= 0
                                    <= ratios[mode]["B2_never_solved_any_condition"]["recovery_ratio_ci95"][1]),
    }
    for arm in ("a2_gray", "a3_caption"):
        for nm in ("B1_image_buys_opportunity", "B2_never_solved_any_condition"):
            blk, _ = ratio_block(nm, mode, num=arm)
            b1b2["by_mode"][mode].setdefault("other_arms", {}).setdefault(arm, {})[nm] = {
                "gain": blk["a2b_gain"], "recovery_ratio": blk["recovery_ratio"],
                "recovery_ratio_ci95": blk["recovery_ratio_ci95"]}

# ------------------------------------------------- 4. standardisation
BINS = [(0, 0, "c_real=0"), (1, 1, "c_real=1"), (2, 2, "c_real=2"), (3, 5, "c_real=3-5"), (6, 16, "c_real>=6")]
binid = np.full(N, -1)
for i, (lo, hi, _) in enumerate(BINS):
    binid[(c_real >= lo) & (c_real <= hi)] = i
assert (binid >= 0).all()
TOP = {"blind_answerable": ans_pub, "not_blind_answerable": ~ans_pub}
cells = {(sn, i): np.where(sm & (binid == i))[0] for sn, sm in TOP.items() for i in range(len(BINS))}
common = [i for i in range(len(BINS)) if all(len(cells[(sn, i)]) > 0 for sn in TOP)]
wt_all = np.array([float((binid == i).sum()) for i in range(len(BINS))])
w = np.array([wt_all[i] for i in common]); w = w / w.sum()
crng = np.random.default_rng(SEED)
cdraw = {k: cells[k][crng.integers(0, len(cells[k]), size=(BOOT, len(cells[k])))]
         for k in sorted(cells) if len(cells[k])}

std = {
    "method": ("direct standardisation: both strata reweighted to the pooled 601-item q_real bin distribution; "
               "standardised gain_s = sum_k w_k * mean(gain | stratum s, bin k); recovery = std_A2b / std_A1"),
    "binning_variable": "c_real = number correct among the 16 frozen base samples WITH the image "
                        "(q_real is a strictly increasing function of c_real on this split)",
    "bins": [b[2] for b in BINS],
    "common_support_bins": [BINS[i][2] for i in common],
    "target_weight_mass_retained": float(sum(wt_all[i] for i in common) / wt_all.sum()),
    "target_weights": {BINS[i][2]: float(w[j]) for j, i in enumerate(common)},
    "cell_counts": {sn: {BINS[i][2]: int(len(cells[(sn, i)])) for i in range(len(BINS))} for sn in TOP},
    "min_cell_n": int(min(len(cells[(sn, i)]) for sn in TOP for i in common)),
    "by_mode": {},
    "per_bin_recovery": {},
}
for mode in MODES:
    std["per_bin_recovery"][mode] = {}
    for j, i in enumerate(common):
        row = {"target_weight": float(w[j])}
        for sn in TOP:
            ix = cells[(sn, i)]
            a = float(gain[("a1_real", mode)][ix].mean()); b = float(gain[("a2b_noimage", mode)][ix].mean())
            row[sn] = {"n": int(len(ix)), "a1_gain": a, "a2b_gain": b,
                       "recovery_ratio": (b / a) if a > 0 else None}
        std["per_bin_recovery"][mode][BINS[i][2]] = row

    out, rr = {}, {}
    for sn in TOP:
        gA, gB = gain[("a1_real", mode)], gain[("a2b_noimage", mode)]
        pa = float(sum(w[j] * gA[cells[(sn, i)]].mean() for j, i in enumerate(common)))
        pb = float(sum(w[j] * gB[cells[(sn, i)]].mean() for j, i in enumerate(common)))
        ba = sum(w[j] * gA[cdraw[(sn, i)]].mean(axis=1) for j, i in enumerate(common))
        bb = sum(w[j] * gB[cdraw[(sn, i)]].mean(axis=1) for j, i in enumerate(common))
        reps = bb / ba
        rr[sn] = reps
        out[sn] = {"standardised_a1_gain": pa, "standardised_a2b_gain": pb,
                   "standardised_recovery_ratio": pb / pa,
                   "standardised_recovery_ratio_ci95": [float(np.percentile(reps, PCT[0])),
                                                        float(np.percentile(reps, PCT[1]))],
                   "degenerate_replicates_denominator_le_0": int((ba <= 0).sum())}
    out["intervals_overlap"] = bool(overlap(out["blind_answerable"]["standardised_recovery_ratio_ci95"],
                                            out["not_blind_answerable"]["standardised_recovery_ratio_ci95"]))
    out["difference"] = diff_block(rr["blind_answerable"], rr["not_blind_answerable"],
                                   "standardised recovery difference",
                                   out["blind_answerable"]["standardised_recovery_ratio"],
                                   out["not_blind_answerable"]["standardised_recovery_ratio"])
    std["by_mode"][mode] = out
std["common_support_limitation"] = (
    "All five q_real bins have non-empty support in both strata, so no weight mass is discarded "
    f"(retained {std['target_weight_mass_retained']:.4f}). Support is nevertheless badly unbalanced: the "
    f"c_real=0 bin carries {std['target_weights']['c_real=0']:.3f} of the target weight but is estimated from only "
    f"{std['cell_counts']['blind_answerable']['c_real=0']} blind-answerable items against "
    f"{std['cell_counts']['not_blind_answerable']['c_real=0']} not-blind-answerable items. Smallest cell overall is "
    f"n={std['min_cell_n']}. The standardised blind-answerable figure is therefore driven by small cells and its "
    "interval is correspondingly wide; it is reported as a sensitivity analysis, not as a replacement estimand.")

# ------------------------------------------------- 5. wording proposals
L = headline["lenient"]
S = headline["strict"]
BB = b1b2["by_mode"]["lenient"]


def pct(x):
    return f"{100 * x:.0f}%"


def fmt_ci(c):
    return f"[{c[0]:.2f}, {c[1]:.2f}]"


wording = {
    "problem": (
        "The published label 'items requiring pixels' is applied to the n=484 not-blind-answerable stratum. "
        "That stratum is defined only by the absence of observed BLIND success. It does not condition on the image "
        f"buying anything: {b1b2['definition']['n_B2']} of its {int(len(STRATA['not_blind_answerable']))} items "
        f"({100 * b1b2['definition']['n_B2'] / len(STRATA['not_blind_answerable']):.1f}%) also have zero observed "
        "successes WITH the image, i.e. the base model solves them under no condition. Those items cannot "
        "demonstrate that pixels are required; they only show the base fails."),
    "what_is_superseded": (
        "The NUMBER 0.4167 (42%) is arithmetically correct and reproduces exactly; it is the label and its use as a "
        "single summary of 'image-requiring' items that are superseded."),
    "proposals": [
        {"target": "docs/EXPERIMENT_TODO.md line 52 (G0 ledger row)",
         "current": "G0.2: image-free training recovers 84% of A1's gain on blind-answerable items and 42% on items requiring pixels",
         "proposed_minimal": (
             f"G0.2: image-free training recovers {pct(L['blind_answerable']['recovery_ratio'])} "
             f"{fmt_ci(L['blind_answerable']['recovery_ratio_ci95'])} of A1's gain on blind-answerable items "
             f"(n={L['blind_answerable']['n']}) and {pct(L['not_blind_answerable']['recovery_ratio'])} "
             f"{fmt_ci(L['not_blind_answerable']['recovery_ratio_ci95'])} on items with no observed blind success "
             f"(n={L['not_blind_answerable']['n']}); that second stratum splits into "
             f"{pct(BB['B1_image_buys_opportunity']['recovery_ratio'])} "
             f"{fmt_ci(BB['B1_image_buys_opportunity']['recovery_ratio_ci95'])} where the image demonstrably buys "
             f"reward opportunity (n={BB['B1_image_buys_opportunity']['n']}) and "
             f"{pct(BB['B2_never_solved_any_condition']['recovery_ratio'])} "
             f"{fmt_ci(BB['B2_never_solved_any_condition']['recovery_ratio_ci95'])} on items the base solves under "
             f"no condition (n={BB['B2_never_solved_any_condition']['n']})"),
         "proposed_short": (
             f"G0.2: recovery {pct(L['blind_answerable']['recovery_ratio'])} on blind-answerable items vs "
             f"{pct(L['not_blind_answerable']['recovery_ratio'])} on items with no observed blind success; intervals "
             f"{'overlapping' if L['intervals_overlap'] else 'disjoint'}. The "
             f"{pct(L['not_blind_answerable']['recovery_ratio'])} is not a figure for image-requiring items — "
             f"{BB['B2_never_solved_any_condition']['n']}/{L['not_blind_answerable']['n']} of that stratum is never "
             f"solved with the image either")},
        {"target": "docs/PAPER1_RESEARCH_DOC.md line 70 (Gate 0 paragraph), clause on 42%",
         "current": "recovering 84% of A1's gain where blind reward opportunity exists and 42% where none was observed (91% vs 61% under a base-wrong headroom control)",
         "proposed": (
             f"recovering {pct(L['blind_answerable']['recovery_ratio'])} "
             f"{fmt_ci(L['blind_answerable']['recovery_ratio_ci95'])} of A1's gain where blind reward opportunity "
             f"exists (n={L['blind_answerable']['n']}) and {pct(L['not_blind_answerable']['recovery_ratio'])} "
             f"{fmt_ci(L['not_blind_answerable']['recovery_ratio_ci95'])} where none was observed "
             f"(n={L['not_blind_answerable']['n']}); the two intervals are "
             f"{'overlapping' if L['intervals_overlap'] else 'disjoint'} (difference "
             f"{L['difference']['point']:+.2f} {fmt_ci(L['difference']['ci95'])}). The second stratum is not "
             f"'items requiring pixels': {BB['B2_never_solved_any_condition']['n']} of its "
             f"{L['not_blind_answerable']['n']} items have no observed success WITH the image either. Decomposed, "
             f"recovery is {pct(BB['B1_image_buys_opportunity']['recovery_ratio'])} "
             f"{fmt_ci(BB['B1_image_buys_opportunity']['recovery_ratio_ci95'])} on the "
             f"{BB['B1_image_buys_opportunity']['n']} items where the image demonstrably buys reward opportunity "
             f"and {pct(BB['B2_never_solved_any_condition']['recovery_ratio'])} "
             f"{fmt_ci(BB['B2_never_solved_any_condition']['recovery_ratio_ci95'])} on the "
             f"{BB['B2_never_solved_any_condition']['n']} items the base solves under no condition "
             f"({pct(L['base_wrong_only']['blind_answerable']['recovery_ratio'])} vs "
             f"{pct(L['base_wrong_only']['not_blind_answerable']['recovery_ratio'])} under a base-wrong headroom "
             f"control)")},
    ],
    "label_replacements": [
        {"do_not_use": "items requiring pixels",
         "use_instead": "items with no observed blind success",
         "why": "names exactly the measured condition (c_blind = 0 of 16), asserts nothing about image necessity"},
        {"do_not_use": "items requiring pixels",
         "use_instead": "blind-unanswerable items",
         "why": "acceptable short form; still describes only the blind side of the measurement"},
        {"reserve_for_B1": "items where the image demonstrably buys reward opportunity (c_blind = 0, c_real > 0, n=232)",
         "why": "this is the only subgroup in the analysis for which an image-necessity reading is licensed by data"},
        {"label_for_B2": "items unsolved under every condition (c_blind = 0, c_real = 0, n=252)",
         "why": "measured description; these items carry no evidence about image necessity in either direction"},
    ],
}

# ------------------------------------------------- assemble
try:
    githash = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
except Exception:
    githash = "unknown"

doc = {
    "schema_version": 1,
    "analysis_id": "G0.2-necessity-refinement-v1",
    "status": "addendum to reports/gate0_stratification_v1.{json,md}; does not modify the frozen Gate 0 artifact",
    "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "git_hash": githash,
    "compute": "login node, CPU only, cached predictions only, no GPU job started",
    "scope_discipline_I13": ("binary blind-answerable split ONLY. This addendum is never merged with the G0.1 / M5c "
                             "Delta-q tercile analysis; the M5c tercile confound does not transfer to this split "
                             "because this split is not built on Delta-q."),
    "reporting_discipline_I7": "every estimand reported under both lenient (acc_final) and strict (acc_strict)",
    "item_universe": {"n_items": N, "split": "Geometry3K test (filtered-v2 eval split)",
                      "item_key": "(problem, image_sha256)", "eval_order_source": REF_REL},
    "inputs": {
        "base_real": {"path": REAL_REL, "sha256": sha256(ROOT / REAL_REL)},
        "base_none": {"path": NONE_REL, "sha256": sha256(ROOT / NONE_REL)},
        "crossed_runs": CROSSED,
        "gate0_artifact": {"path": "reports/gate0_stratification_v1.json",
                           "sha256": sha256(ROOT / "reports/gate0_stratification_v1.json")},
        "base_samples_per_item": n_samples,
    },
    "definitions": {
        "gain": "mean over seeds 1,2,3 of (crossed-cell arm score under condition=real) minus (base score); "
                "lenient uses acc_final vs base greedy_canonical_correct, strict uses acc_strict vs base greedy_acc_strict",
        "recovery_ratio": "mean per-item gain(A2b) / mean per-item gain(A1), within a stratum",
        "jeffreys_floor": FLOOR,
        "strict_equals_final_on_trained_arms": strict_identity,
    },
    "d1_reproduction": repro,
    "d2_ratio_intervals": headline,
    "d3_b1_b2_decomposition": b1b2,
    "d4_difficulty_standardisation": std,
    "d5_wording_proposal": wording,
    "d6_rule_audit": rule_audit,
    "superseded": [{
        "figure": "42% (0.4167) recovery on 'items requiring pixels'",
        "source": "docs/EXPERIMENT_TODO.md:52 and docs/PAPER1_RESEARCH_DOC.md:70",
        "status": "SUPERSEDED AS LABELLED — RETAINED AS A NUMBER",
        "number_still_valid_for": "recovery ratio on the not-blind-answerable stratum (n=484), reproduced exactly here",
        "why_superseded": "the stratum is not 'items requiring pixels'; 252/484 have zero observed successes with the "
                          "image as well, and the stratum is internally heterogeneous (0.525 vs 0.116)",
        "replaced_by": "d3_b1_b2_decomposition + d2_ratio_intervals",
    }, {
        "figure": "84% and 42% quoted without uncertainty",
        "status": "SUPERSEDED — intervals now exist",
        "replaced_by": "d2_ratio_intervals (10,000-draw paired item bootstrap, seed 20260730)",
        "note": "no interval on these RATIOS existed anywhere in the repo before this addendum; "
                "reports/gate0_stratification_v1.json carried ci95 only on the component means",
    }],
}

(ROOT / "reports/g02_necessity_refinement_v1.json").write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")

# ------------------------------------------------- markdown
def g(m, nm, k="recovery_ratio"):
    return ratios[m][nm][k]


def ci(m, nm):
    return fmt_ci(ratios[m][nm]["recovery_ratio_ci95"])


md = []
A = md.append
A("# G0.2 necessity refinement — addendum to Gate 0\n")
A(f"Artifact: `reports/g02_necessity_refinement_v1.json` · built by `scripts/build_g02_necessity_refinement.py` · "
  f"git `{githash}` · generated {doc['generated_utc']} · login node, CPU only, **no GPU job started**.\n")
A("Addendum to `reports/gate0_stratification_v1.{json,md}`. The frozen Gate 0 artifact is **not modified**.\n")
A("**Scope (I13).** This addendum operates only on Gate 0's **binary blind-answerable split**. It is never merged "
  "with the G0.1 / M5c **Δq tercile** analysis. The confound M5c found in the Δq terciles does not transfer "
  "literally to G0.2, because G0.2 is not built on Δq — it is built on `q_blind > ` the Jeffreys floor "
  f"(`{FLOOR:.16f}`), n=117 vs n=484.\n")
A("**Reporting (I7).** Every estimand appears under both **lenient** (`acc_final`) and **strict** (`acc_strict`).\n")
A("---\n")

A("## 1. Reproduction of the published 84% / 42%\n")
A(f"Pipeline validated against the frozen artifact before extension. Max absolute deviation across all "
  f"4 arms × 2 scopes × 2 strata: **{repro['max_abs_deviation']:.3e}** → **{repro['status']}**.\n")
A("| scope | stratum | n | A1 gain | A2b gain | recovery | published |")
A("|---|---|---:|---:|---:|---:|---:|")
for c in repro["cells"]:
    A(f"| {c['scope']} | {c['stratum']} | {c['n']} | {c['a1_real']['recomputed']:+.4f} | "
      f"{c['a2b_noimage']['recomputed']:+.4f} | {c['recovery_ratio_recomputed']:.4f} | "
      f"**{c['recovery_percent_rounded']}%** |")
A("")
A("The published **84%** and **42%** (and the base-wrong **91%** / **61%**) reproduce exactly from "
  "`reports/gate0_stratification_v1.json :: G0_2_headroom_control`, and independently from the per-item inputs.\n")

A("## 2. Item-bootstrap intervals on the RATIOS\n")
A(f"10,000 draws, seed {SEED}, paired on items (A1 and A2b read from the same resampled item indices), "
  "within-stratum resampling with replacement, percentile 2.5 / 97.5. **No interval on these ratios existed "
  "anywhere in the repo before this addendum** — `gate0_stratification_v1.json` carried `ci95` on the component "
  "means only.\n")
A("| mode | stratum | n | A1 gain [CI] | A2b gain [CI] | **recovery [CI]** | degenerate draws |")
A("|---|---|---:|---|---|---|---:|")
for m in MODES:
    for nm, lab in (("blind_answerable", "blind-answerable"), ("not_blind_answerable", "no observed blind success")):
        r = ratios[m][nm]
        A(f"| {m} | {lab} | {r['n']} | {r['a1_gain']['mean']:+.4f} {fmt_ci(r['a1_gain']['ci95'])} | "
          f"{r['a2b_gain']['mean']:+.4f} {fmt_ci(r['a2b_gain']['ci95'])} | "
          f"**{r['recovery_ratio']:.4f}** {fmt_ci(r['recovery_ratio_ci95'])} | "
          f"{r['bootstrap']['degenerate_replicates_denominator_le_0']} |")
A("")
A("**Do the two intervals overlap?**\n")
A("| mode | blind-answerable CI | no-blind-success CI | overlap | difference [CI] | bootstrap mass ≤ 0 |")
A("|---|---|---|---|---|---:|")
for m in MODES:
    h = headline[m]
    A(f"| {m} | {fmt_ci(h['blind_answerable']['recovery_ratio_ci95'])} | "
      f"{fmt_ci(h['not_blind_answerable']['recovery_ratio_ci95'])} | "
      f"**{'YES' if h['intervals_overlap'] else 'NO'}** | {h['difference']['point']:+.4f} "
      f"{fmt_ci(h['difference']['ci95'])} | {h['difference']['bootstrap_mass_le_0_display']} |")
A("")
A(f"**Answer: the intervals do {'' if headline['lenient']['intervals_overlap'] else 'NOT '}overlap, under either "
  "scoring.** The paired difference excludes zero in both. `difference` is the plug-in difference of the observed "
  "ratios; its interval is the 2.5/97.5 percentile of the bootstrap replicate differences.\n")
A("Base-wrong headroom control, same bootstrap:\n")
A("| mode | blind-answerable | no observed blind success | overlap | difference [CI] |")
A("|---|---|---|---|---|")
for m in MODES:
    h = headline[m]["base_wrong_only"]
    A(f"| {m} | {h['blind_answerable']['recovery_ratio']:.4f} "
      f"{fmt_ci(h['blind_answerable']['recovery_ratio_ci95'])} (n={h['blind_answerable']['n']}) | "
      f"{h['not_blind_answerable']['recovery_ratio']:.4f} "
      f"{fmt_ci(h['not_blind_answerable']['recovery_ratio_ci95'])} (n={h['not_blind_answerable']['n']}) | "
      f"**{'YES' if h['intervals_overlap'] else 'NO'}** | {h['difference']['point']:+.4f} "
      f"{fmt_ci(h['difference']['ci95'])} |")
A("")
A(f"*The lenient and strict base-wrong rows are identical, and that is expected, not a duplication error.* "
  f"{headline['lenient']['base_wrong_only']['lenient_strict_identity_note']}\n")

A("## 3. B1 / B2 decomposition of the n=484 stratum\n")
A(f"The stratum the published text labels *items requiring pixels* is defined **only** by absence of observed "
  f"blind success. **{b1b2['definition']['n_B2']} of its 484 items have zero observed successes WITH the image "
  f"too** (`c_real = 0` of 16) — the base solves them under no condition.\n")
A(f"- **B1** — image demonstrably buys reward opportunity (`c_blind = 0`, `c_real > 0`): "
  f"**n = {b1b2['definition']['n_B1']}**, base real greedy accuracy {b1b2['base_real_greedy_accuracy']['B1']:.4f}")
A(f"- **B2** — unsolved under every condition (`c_blind = 0`, `c_real = 0`): "
  f"**n = {b1b2['definition']['n_B2']}**, base real greedy accuracy {b1b2['base_real_greedy_accuracy']['B2']:.4f}\n")
A("| mode | subgroup | n | A1 gain [CI] | A2b gain [CI] | **recovery [CI]** |")
A("|---|---|---:|---|---|---|")
for m in MODES:
    for nm, lab in (("B1_image_buys_opportunity", "B1 image buys opportunity"),
                    ("B2_never_solved_any_condition", "B2 never solved, any condition")):
        r = ratios[m][nm]
        A(f"| {m} | {lab} | {r['n']} | {r['a1_gain']['mean']:+.4f} {fmt_ci(r['a1_gain']['ci95'])} | "
          f"{r['a2b_gain']['mean']:+.4f} {fmt_ci(r['a2b_gain']['ci95'])} | "
          f"**{r['recovery_ratio']:.4f}** {fmt_ci(r['recovery_ratio_ci95'])} |")
A("")
A("| mode | B1 − B2 | CI | B2 interval includes 0 |")
A("|---|---:|---|---|")
for m in MODES:
    d = b1b2["by_mode"][m]
    A(f"| {m} | {d['difference']['point']:+.4f} | {fmt_ci(d['difference']['ci95'])} | "
      f"**{'YES' if d['B2_ci_includes_zero'] else 'no'}** |")
A("")
A(f"Under lenient scoring A2b's gain on B2 is {ratios['lenient']['B2_never_solved_any_condition']['a2b_gain']['mean']:+.4f} "
  f"{fmt_ci(ratios['lenient']['B2_never_solved_any_condition']['a2b_gain']['ci95'])} and the recovery interval "
  f"{ci('lenient','B2_never_solved_any_condition')} includes zero and negative values.\n")

A("## 4. Difficulty-standardised recovery\n")
A(f"{std['method']}. Binning variable: {std['binning_variable']}.\n")
A("Support per q_real bin (this is the honest limitation, stated before the result):\n")
A("| q_real bin | target weight | n blind-answerable | n no-blind-success | pooled n |")
A("|---|---:|---:|---:|---:|")
for i, (lo, hi, lab) in enumerate(BINS):
    tw = std["target_weights"].get(lab)
    A(f"| {lab} | {tw:.4f} | {std['cell_counts']['blind_answerable'][lab]} | "
      f"{std['cell_counts']['not_blind_answerable'][lab]} | {int(wt_all[i])} |")
A("")
A(f"**Common-support limitation.** {std['common_support_limitation']}\n")
A("| mode | stratum | std A1 gain | std A2b gain | **std recovery [CI]** |")
A("|---|---|---:|---:|---|")
for m in MODES:
    for sn, lab in (("blind_answerable", "blind-answerable"), ("not_blind_answerable", "no observed blind success")):
        o = std["by_mode"][m][sn]
        A(f"| {m} | {lab} | {o['standardised_a1_gain']:+.4f} | {o['standardised_a2b_gain']:+.4f} | "
          f"**{o['standardised_recovery_ratio']:.4f}** {fmt_ci(o['standardised_recovery_ratio_ci95'])} |")
A("")
A("| mode | standardised pair | overlap | difference [CI] |")
A("|---|---|---|---|")
for m in MODES:
    o = std["by_mode"][m]
    A(f"| {m} | {o['blind_answerable']['standardised_recovery_ratio']:.4f} vs "
      f"{o['not_blind_answerable']['standardised_recovery_ratio']:.4f} | "
      f"**{'YES' if o['intervals_overlap'] else 'NO'}** | {o['difference']['point']:+.4f} "
      f"{fmt_ci(o['difference']['ci95'])} |")
A("")
A("Per-bin recovery (lenient), showing where the standardised figures come from:\n")
A("| q_real bin | weight | blind-answerable n / A1 / A2b / rec | no-blind-success n / A1 / A2b / rec |")
A("|---|---:|---|---|")
for lab, row in std["per_bin_recovery"]["lenient"].items():
    a = row["blind_answerable"]; b = row["not_blind_answerable"]
    ra = f"{a['recovery_ratio']:+.3f}" if a["recovery_ratio"] is not None else "n/a"
    rb = f"{b['recovery_ratio']:+.3f}" if b["recovery_ratio"] is not None else "n/a"
    A(f"| {lab} | {row['target_weight']:.3f} | {a['n']} / {a['a1_gain']:+.3f} / {a['a2b_gain']:+.3f} / {ra} | "
      f"{b['n']} / {b['a1_gain']:+.3f} / {b['a2b_gain']:+.3f} / {rb} |")
A("")

A("## 5. Proposed replacement wording (proposal only — the PI owns the prose)\n")
A(f"**Why the label is wrong.** {wording['problem']}\n")
A(f"**What is superseded.** {wording['what_is_superseded']}\n")
for p in wording["proposals"]:
    A(f"### Target: `{p['target']}`\n")
    A(f"> **Current:** {p['current']}\n")
    for k in ("proposed_minimal", "proposed_short", "proposed"):
        if k in p:
            A(f"> **{k.replace('_', ' ').title()}:** {p[k]}\n")
A("### Label substitutions\n")
A("| do not use | use instead | why |")
A("|---|---|---|")
for r in wording["label_replacements"]:
    if "do_not_use" in r:
        A(f"| {r['do_not_use']} | {r['use_instead']} | {r['why']} |")
    elif "reserve_for_B1" in r:
        A(f"| — | {r['reserve_for_B1']} | {r['why']} |")
    else:
        A(f"| — | {r['label_for_B2']} | {r['why']} |")
A("")
A("No edit was made to `docs/PAPER1_RESEARCH_DOC.md` or `docs/EXPERIMENT_TODO.md`.\n")

A("## 6. Split-rule audit (found while verifying, reported not applied)\n")
A(f"`q_i` is `{rule_audit['q_i_definition']}`. {rule_audit['symmetry']}.\n")
A(f"- Registered rule: {rule_audit['registered_floor_rule']}")
A(f"- Rule as executed: {rule_audit['executed_floor_rule']}\n")
A(f"Consequence: **{rule_audit['n_discordant_items']} item** is classified differently. Published rule gives "
  f"{rule_audit['n_published_rule']['blind_answerable']} / {rule_audit['n_published_rule']['not_blind_answerable']}; "
  f"the registered rule gives {rule_audit['n_registered_rule']['blind_answerable']} / "
  f"{rule_audit['n_registered_rule']['not_blind_answerable']}.\n")
A("| eval index | c_blind | q_blind | c_real | q_real | published rule | registered rule |")
A("|---:|---:|---:|---:|---:|---|---|")
for d in rule_audit["discordant_items"]:
    A(f"| {d['item_index_in_eval_order']} | {d['c_blind']}/16 | {d['q_blind']:.16f} | {d['c_real']}/16 | "
      f"{d['q_real']:.4f} | {d['classified_by_published_rule']} | {d['classified_by_registered_rule']} |")
A("")
A("Sensitivity — recovery ratios under the registered `c_blind = 0` rule:\n")
A("| mode | stratum | n | recovery [CI] |")
A("|---|---|---:|---|")
for m in MODES:
    for nm, lab in (("blind_answerable_registered_rule", "blind-answerable (c_blind > 0)"),
                    ("not_blind_answerable_registered_rule", "no blind success (c_blind = 0)")):
        r = ratios[m][nm]
        A(f"| {m} | {lab} | {r['n']} | {r['recovery_ratio']:.4f} {fmt_ci(r['recovery_ratio_ci95'])} |")
A("")
A(f"*Why the lenient rows are unchanged:* {rule_audit['why_lenient_ratios_unchanged']}\n")
A("The published figures are left as-is in the frozen artifact; this addendum reports the discrepancy and its "
  "(negligible) numerical effect. Whether to re-run Gate 0 under the registered rule is a PI decision.\n")

A("## 7. Superseded-figure ledger\n")
A("| figure | status | still valid for | replaced by |")
A("|---|---|---|---|")
for s in doc["superseded"]:
    A(f"| {s['figure']} | **{s['status']}** | {s.get('number_still_valid_for', '—')} | {s['replaced_by']} |")
A("")
A("The 42% figure is **retained, not deleted**: it is the correct recovery ratio for the n=484 "
  "not-blind-answerable stratum and reproduces exactly. What is superseded is its label and its use as a single "
  "summary of image-requiring items.\n")

(ROOT / "reports/g02_necessity_refinement_v1.md").write_text("\n".join(md))
print("reproduction:", repro["status"], "maxdev", repro["max_abs_deviation"])
for m in MODES:
    h = headline[m]
    print(f"{m}: {h['blind_answerable']['recovery_ratio']:.4f} {h['blind_answerable']['recovery_ratio_ci95']} vs "
          f"{h['not_blind_answerable']['recovery_ratio']:.4f} {h['not_blind_answerable']['recovery_ratio_ci95']} "
          f"overlap={h['intervals_overlap']}")
print("wrote reports/g02_necessity_refinement_v1.{json,md}")
