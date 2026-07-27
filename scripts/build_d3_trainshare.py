#!/usr/bin/env python3
"""D3 TrainShare with paired item-level CIs (PAPER1 §8).

    TrainShare = [Acc(train-blind, test-real) - Acc(base, test-real)]
                 / [Acc(A1, test-real)       - Acc(base, test-real)]

Pre-committed branches: >=0.35 headline at full strength; 0.15-0.35 "a
substantial minority of the gain is image-free"; <0.15 training-time access
dominates.

ORDERING DISCLOSURE. All 36 D3 cells were read under
`docs/registered_d3_condition_matrix_v1.md`, whose branches are ratio-based.
This TrainShare computation is therefore a **declared post-hoc recomputation of
already-read data**, not a pre-registered reading, and does not satisfy I9. It is
reported because PAPER1 §8 names this estimand; it is labeled everywhere so no
reader can mistake it for a sealed result. Both readings agree, which is the only
reason the agreement is worth stating at all.
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
RNG = np.random.default_rng(20260727)
BOOT = 20000
gate0 = json.loads((ROOT / "reports/gate0_stratification_v1.json").read_text())
CROSSED = gate0["crossed_runs"]
G = "experiments/runs/blind_solvability_v2_guarded_rescore_geo3k_filtered_v2_retry_real_login_20260712T050905Z/per_item.jsonl"


def load(rel):
    return [json.loads(l) for l in (ROOT / rel).read_text().splitlines() if l.strip()]


def key(r):
    return (r["problem"], tuple(r.get("image_sha256") or []))


base = {key(r): r for r in load(G)}
ref = load(Path(gate0["arm_runs"]["a1_real"]["1"]).relative_to(ROOT).as_posix())
ITEMS = [key(r) for r in ref]
b = np.array([float(bool(base[k]["greedy_canonical_correct"])) for k in ITEMS])


def crossed(arm, seed):
    rows = {key(r): r for r in load(f"experiments/runs/{CROSSED[f'{arm}|s{seed}']}/predictions.jsonl")}
    return np.array([float(bool(rows[k]["acc_final"])) for k in ITEMS])


def branch(v):
    if v >= 0.35:
        return "headline at full strength"
    if v >= 0.15:
        return "a substantial minority of the gain is image-free"
    return "training-time access dominates; F1 becomes a secondary ablation-practice finding"


rep = {"schema_version": 1, "estimand": "TrainShare (PAPER1 §8)",
       "ordering_disclosure": (
           "Declared post-hoc recomputation. All 36 D3 cells were read under the "
           "ratio-based registration docs/registered_d3_condition_matrix_v1.md before "
           "this estimand was computed. Not pre-registered; does not satisfy I9."),
       "n_items": len(ITEMS), "bootstrap_draws": BOOT, "per_seed": {}, "pooled": {}}

n = len(ITEMS)
draws = RNG.integers(0, n, size=(BOOT, n))

for arm in ("a2_gray", "a2b_noimage", "a3_caption"):
    per_seed = []
    for seed in (1, 2, 3):
        num = crossed(arm, seed) - b
        den = crossed("a1_real", seed) - b
        ts = float(num.mean() / den.mean())
        # paired item-level bootstrap: resample items, recompute the ratio
        bn = num[draws].mean(axis=1)
        bd = den[draws].mean(axis=1)
        ok = np.abs(bd) > 1e-9
        ratios = bn[ok] / bd[ok]
        lo, hi = np.percentile(ratios, [2.5, 97.5])
        per_seed.append({"seed": seed, "train_share": ts,
                         "ci95": [float(lo), float(hi)],
                         "numerator_gain": float(num.mean()),
                         "denominator_gain": float(den.mean()),
                         "branch": branch(ts)})
    vals = [p["train_share"] for p in per_seed]
    # pooled: average numerator and denominator across seeds, then ratio
    nump = np.mean([crossed(arm, s) - b for s in (1, 2, 3)], axis=0)
    denp = np.mean([crossed("a1_real", s) - b for s in (1, 2, 3)], axis=0)
    tsp = float(nump.mean() / denp.mean())
    bn, bd = nump[draws].mean(axis=1), denp[draws].mean(axis=1)
    ok = np.abs(bd) > 1e-9
    lo, hi = np.percentile(bn[ok] / bd[ok], [2.5, 97.5])
    rep["per_seed"][arm] = per_seed
    rep["pooled"][arm] = {"train_share": tsp, "ci95": [float(lo), float(hi)],
                          "branch": branch(tsp),
                          "all_seeds_same_branch": len({p["branch"] for p in per_seed}) == 1,
                          "min_seed": min(vals), "max_seed": max(vals)}

(ROOT / "reports/d3_trainshare_v1.json").write_text(json.dumps(rep, indent=2, sort_keys=True) + "\n")
for arm, p in rep["pooled"].items():
    seeds = ", ".join(f"{x['train_share']:.3f}" for x in rep["per_seed"][arm])
    print(f"{arm:14s} pooled={p['train_share']:.3f} CI[{p['ci95'][0]:.3f},{p['ci95'][1]:.3f}] "
          f"seeds=({seeds}) -> {p['branch']}")
print("wrote reports/d3_trainshare_v1.json")
