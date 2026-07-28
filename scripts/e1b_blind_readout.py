#!/usr/bin/env python3
"""E1b blind-column readout, bound to the CHANCE reporting contract.

Registered in docs/registered_e1b_external_access_matrix_v1.md. Tests P1 (the
blind gain transfers out of domain) and P2 (it does not require training-time
image access).

Contract obligations honoured here:
  - the null is set per item by answer format (MC -> 1/k from that item's own
    option_labels; free-form -> 0), never one global null
  - MathVista is mixed and is SPLIT into MC and free-form; no whole-benchmark
    number is produced for it
  - lenient (acc_final) and strict (acc_strict) are both reported
  - CIs are paired item bootstrap; arms and base are scored on the same item ids
"""
import json
import statistics
from pathlib import Path

import numpy as np

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
RUNS = ROOT / "experiments/runs"
BASE = {
    "mmstar": RUNS / "layer1_blind_mmstar3b_an29_20260710T023019Z/predictions.jsonl",
    "mathvista": RUNS / "layer1_blind_mathvista3b_an29_20260710T023019Z/predictions.jsonl",
}
ARMS = ["a1_real", "a2_gray", "a2b_noimage", "a3_caption"]
SEEDS = [1, 2, 3]
RNG = np.random.default_rng(20260728)
REPS = 10000


def load(p):
    rows = {}
    for line in Path(p).read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        rows[str(r["index"])] = r
    return rows


def item_null(r):
    labels = r.get("option_labels") or []
    return 1.0 / len(labels) if labels else 0.0


def subsets(bench, base_rows):
    """Return {subset_name: [item ids]} honouring the mixed-benchmark split."""
    if bench == "mmstar":
        return {"all items (MC pooled)": sorted(base_rows)}
    mc = sorted(i for i, r in base_rows.items() if (r.get("option_labels") or []))
    ff = sorted(i for i, r in base_rows.items() if not (r.get("option_labels") or []))
    return {"MC pooled": mc, "free-form": ff}


def boot_delta(arm_vec, base_vec):
    n = len(arm_vec)
    idx = RNG.integers(0, n, size=(REPS, n))
    d = arm_vec[idx].mean(axis=1) - base_vec[idx].mean(axis=1)
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


out = {"schema_version": "blind-gains.e1b-blind.v1",
       "registration": "docs/registered_e1b_external_access_matrix_v1.md",
       "contract": "CHANCE null-corrected reporting; per-item format null; mixed benchmarks split",
       "bootstrap": {"reps": REPS, "seed": 20260728, "unit": "item", "paired": True},
       "rows": [], "notes": []}

for bench, basep in BASE.items():
    if not basep.is_file():
        out["notes"].append(f"{bench}: base blind predictions absent at {basep}")
        continue
    base_rows = load(basep)

    arm_rows = {}
    for arm in ARMS:
        per_seed = []
        for s in SEEDS:
            hits = sorted(RUNS.glob(f"e1b_{arm}_seed{s}_{bench}_blind_an12_*/predictions.jsonl"))
            if not hits:
                out["notes"].append(f"missing cell: {arm} seed{s} {bench}")
                continue
            per_seed.append(load(hits[-1]))
        if per_seed:
            arm_rows[arm] = per_seed

    for sub_name, ids in subsets(bench, base_rows).items():
        ids = [i for i in ids if all(i in ps for a in arm_rows.values() for ps in a)]
        if not ids:
            continue
        nulls = np.array([item_null(base_rows[i]) for i in ids])

        for metric in ("acc_final", "acc_strict"):
            base_vec = np.array([float(base_rows[i][metric]) for i in ids])
            row_base = {
                "benchmark": bench, "subset": sub_name, "metric": metric,
                "n": len(ids), "null": float(nulls.mean()),
                "arm": "BASE (frozen)", "seeds": 0,
                "blind_acc": float(base_vec.mean()),
                "delta_vs_base": 0.0, "ci95": [0.0, 0.0], "per_seed": [],
            }
            out["rows"].append(row_base)

            for arm, per_seed in arm_rows.items():
                seed_means, seed_vecs = [], []
                for ps in per_seed:
                    v = np.array([float(ps[i][metric]) for i in ids])
                    seed_vecs.append(v)
                    seed_means.append(float(v.mean()))
                arm_vec = np.mean(seed_vecs, axis=0)
                lo, hi = boot_delta(arm_vec, base_vec)
                out["rows"].append({
                    "benchmark": bench, "subset": sub_name, "metric": metric,
                    "n": len(ids), "null": float(nulls.mean()),
                    "arm": arm, "seeds": len(seed_vecs),
                    "blind_acc": float(arm_vec.mean()),
                    "blind_acc_per_seed": seed_means,
                    "blind_acc_seed_sd": (float(statistics.stdev(seed_means))
                                          if len(seed_means) > 1 else None),
                    "delta_vs_base": float(arm_vec.mean() - base_vec.mean()),
                    "ci95": [lo, hi],
                    "excludes_zero": bool(lo > 0 or hi < 0),
                    "above_null": bool(arm_vec.mean() > nulls.mean()),
                })

p = ROOT / "reports/e1b_blind_readout_v1.json"
p.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")

# ------------------------------- console table ------------------------------
print(f"{'bench':<10} {'subset':<22} {'metric':<10} {'arm':<15} "
      f"{'n':>5} {'null':>6} {'blind':>7} {'Δ vs base':>10} {'95% CI':>20} {'>0':>4}")
for r in out["rows"]:
    ci = f"[{r['ci95'][0]:+.4f}, {r['ci95'][1]:+.4f}]" if r["arm"] != "BASE (frozen)" else ""
    star = "yes" if r.get("excludes_zero") else ""
    print(f"{r['benchmark']:<10} {r['subset']:<22} {r['metric']:<10} {r['arm']:<15} "
          f"{r['n']:>5} {r['null']:>6.4f} {r['blind_acc']:>7.4f} "
          f"{r['delta_vs_base']:>+10.4f} {ci:>20} {star:>4}")
for n in out["notes"]:
    print("NOTE:", n)
print(f"\nwrote {p.relative_to(ROOT)}")
