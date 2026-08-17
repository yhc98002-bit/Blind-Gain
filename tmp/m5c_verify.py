#!/usr/bin/env python3
"""Independent verification of reports/m5c_item_substrate_v1.jsonl.

Re-reads the written substrate (NOT the in-memory objects) and re-derives every
count from it, then re-joins against the five source per_item.jsonl files to
confirm the substrate values equal the source values item-by-item.

Also computes a clearly-labelled reference quantity: the discordance that
independent per-item Bernoulli resampling would produce, using the 16-sample
per-item p_i that exists ONLY in the step-100 guarded-rescore run.
"""
from __future__ import annotations

import collections
import json
import math
import os
import sys

ROOT = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
os.chdir(ROOT)

RUNS = {
    "100": "experiments/runs/blind_solvability_v2_guarded_rescore_anchor_step100_geo3k_real_login_20260712T082107Z",
    "150": "experiments/runs/m5_geo3k_step150_an12_gpu4_20260718T051839Z",
    "200": "experiments/runs/m5_geo3k_step200_an29_gpu4_20260722T141052Z",
    "300": "experiments/runs/m5_geo3k_step300_an12_gpu0_20260726T083303Z",
    "400": "experiments/runs/m5_geo3k_step400_an12_gpu0_20260728T053115Z",
}
STEPS = ["100", "150", "200", "300", "400"]


def load_jsonl(p):
    with open(p, encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


sub = load_jsonl("reports/m5c_item_substrate_v1.jsonl")
report = {}
report["substrate_rows"] = len(sub)
report["substrate_unique_keys"] = len({r["item_key"] for r in sub})

# --- A. substrate values equal source values, item by item -----------------
src = {}
for s in STEPS:
    rows = [r for r in load_jsonl(os.path.join(RUNS[s], "per_item.jsonl")) if r.get("split") == "test"]
    src[s] = {
        (str(r["split"]), int(r["row_index"])): (
            int(bool(r.get("acc_final", r.get("greedy_correct")))),
            int(bool(r.get("acc_strict", r.get("greedy_acc_strict")))),
        )
        for r in rows
    }

bad = []
for r in sub:
    key = (r["split"], int(r["row_index"]))
    for s in STEPS:
        if key not in src[s]:
            bad.append((r["item_key"], s, "missing-in-source"))
            continue
        af, st = src[s][key]
        if r[f"acc_final_step{s}"] != af:
            bad.append((r["item_key"], s, "acc_final"))
        if r[f"acc_strict_step{s}"] != st:
            bad.append((r["item_key"], s, "acc_strict"))
report["substrate_vs_source_mismatches"] = len(bad)
report["substrate_vs_source_examples"] = bad[:10]
report["source_keys_absent_from_substrate"] = sorted(
    f"{k[0]}:{k[1]}" for k in set(src["100"]) - {(r["split"], int(r["row_index"])) for r in sub}
)

# --- B. re-derive transition counts straight from the substrate file -------
def rederive(a, b, suffix, metric):
    c = collections.Counter()
    for r in sub:
        x, y = r[f"{metric}_step{a}"], r[f"{metric}_step{b}"]
        lab = {(1, 1): "stable_correct", (0, 1): "gained",
               (1, 0): "lost", (0, 0): "stable_incorrect"}[(x, y)]
        c[lab] += 1
        stored = r.get(f"transition_{a}_{b}_{suffix}")
        if stored is not None and stored != lab:
            c["LABEL_MISMATCH"] += 1
    return dict(c)


report["rederived"] = {}
for a, b in [("100", "400"), ("100", "200"), ("200", "400")]:
    for suffix, metric in [("lenient", "acc_final"), ("strict", "acc_strict")]:
        report["rederived"][f"{a}->{b}|{metric}"] = rederive(a, b, suffix, metric)

turn = json.load(open("reports/m5c_turnover_v1.json", encoding="utf-8"))
report["matches_turnover_json"] = all(
    {k: v for k, v in report["rederived"][key].items() if k != "LABEL_MISMATCH"}
    == turn["transitions"][key]["counts"]
    for key in report["rederived"]
)

# --- C. lenient vs strict identity ----------------------------------------
report["lenient_equals_strict_per_item_all_steps"] = all(
    r[f"acc_final_step{s}"] == r[f"acc_strict_step{s}"] for r in sub for s in STEPS
)

# --- D. REFERENCE ONLY: independent-Bernoulli discordance from step-100 -----
# The step-100 guarded-rescore run carries 16 sampled generations per item.
# p_i = sample_correct_count / sample_count on the CANONICAL sampled scorer.
# Under an (assumption-heavy) model where each greedy eval is one independent
# Bernoulli(p_i) draw, the expected discordance between two evals is
#   sum_i 2 p_i (1 - p_i) / n.
# This is NOT a measurement of greedy-decode noise (greedy is deterministic);
# it is a temperature-sampling dispersion reference and is labelled as such.
rows100 = [r for r in load_jsonl(os.path.join(RUNS["100"], "per_item.jsonl"))
           if r.get("split") == "test"]
ps, ns = [], []
for r in rows100:
    cnt = r.get("sample_correct_count")
    tot = r.get("sample_count")
    if cnt is None or not tot:
        continue
    ps.append(float(cnt) / float(tot))
    ns.append(int(tot))
if ps:
    exp_disc_frac = sum(2 * p * (1 - p) for p in ps) / len(ps)
    report["sampling_dispersion_reference"] = {
        "caveat": "REFERENCE ONLY, not a noise test: derived from 16-sample temperature "
                  "decoding at step 100; greedy decoding is deterministic, so this does "
                  "not estimate greedy-eval replicate noise. No greedy replicate exists.",
        "n_items_with_samples": len(ps),
        "sample_count_values": sorted(set(ns)),
        "mean_p_i": sum(ps) / len(ps),
        "expected_discordance_fraction_two_indep_draws": exp_disc_frac,
        "expected_discordance_count": exp_disc_frac * len(ps),
        "observed_discordance_count_100_to_400": turn["transitions"]["100->400|acc_final"]["discordant_pairs"],
        "observed_discordance_fraction_100_to_400": turn["transitions"]["100->400|acc_final"]["turnover_fraction_of_n"],
    }
else:
    report["sampling_dispersion_reference"] = {"available": False, "reason": "no sample_count fields"}

# --- E. binomial CI on the gained/lost split (discordant pairs) ------------
def wilson(k, n, z=1.959963985):
    if n == 0:
        return (float("nan"), float("nan"))
    ph = k / n
    d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


for key in ("100->400|acc_final", "100->200|acc_final", "200->400|acc_final"):
    t = turn["transitions"][key]
    lo, hi = wilson(t["b01_gained"], t["discordant_pairs"])
    report.setdefault("gained_share_of_discordant", {})[key] = {
        "gained": t["b01_gained"], "lost": t["b10_lost"], "discordant": t["discordant_pairs"],
        "gained_share": t["b01_gained"] / t["discordant_pairs"],
        "wilson95": [lo, hi],
        "mcnemar_exact_p": t["mcnemar_exact_two_sided_p"],
    }

print(json.dumps(report, indent=2))
