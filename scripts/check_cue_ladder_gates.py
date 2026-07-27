#!/usr/bin/env python3
"""Cue-ladder build-validity gates, per docs/registered_cue_ladder_v1.md.

Gate 1: the `exact` rung must reproduce the R19 nine-series numbers.
Gate 2: the frozen base must degrade across exact -> region -> none, or the
        ladder is not measuring cue strength and branches (a)/(b) are void.
"""
import glob
import json
from pathlib import Path

import numpy as np

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
RNG = np.random.default_rng(20260727)
RUNGS = ("exact", "region", "none", "decoy")
O = Path((ROOT / "tmp/cl_base.txt").read_text().strip())


def load(p):
    return [json.loads(l) for l in open(p) if l.strip()]


# R19 nine-series base, keyed by source_pair_id
r19 = [json.loads(l) for f in sorted(glob.glob(str(
    ROOT / "experiments/runs/fliptrack_v02r19_packaged_qwen25vl3b_real_an29_20260710T142716Z/shards/*.jsonl")))
    for l in open(f) if l.strip()]
nine = {r["source_pair_id"]: r for r in r19
        if r.get("template_id") == "starred_series_value_nine_v07"}

rung_rows = {}
for rung in RUNGS:
    man = {json.loads(l)["pair_id"]: json.loads(l)
           for l in open(ROOT / f"data/cue_ladder_v1/{rung}_manifest.jsonl")}
    preds = {r["pair_id"]: r for r in load(O / rung / "predictions.jsonl")}
    rows = {}
    for pid, m in man.items():
        if pid in preds:
            rows[m["source_pair_id"]] = preds[pid]
    rung_rows[rung] = rows

common = sorted(set(nine) & set.intersection(*[set(v) for v in rung_rows.values()]))
print(f"items common to R19 and all four rungs: {len(common)}")

report = {"n_common": len(common), "rungs": {}, "gates": {}}


def acc(rows, ids, field="pair_correct"):
    return float(np.mean([float(bool(rows[i][field])) for i in ids]))


def boot_paired(x, y, n=10000):
    d = np.array(x, float) - np.array(y, float)
    idx = RNG.integers(0, len(d), size=(n, len(d)))
    b = d[idx].mean(axis=1)
    return float(d.mean()), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


for rung in RUNGS:
    report["rungs"][rung] = {
        "pair_accuracy": acc(rung_rows[rung], common),
        "strict_pair_accuracy": acc(rung_rows[rung], common, "strict_pair_correct"),
    }

# ---- Gate 1 ----
lad = [float(bool(rung_rows["exact"][i]["pair_correct"])) for i in common]
ref = [float(bool(nine[i]["pair_correct"])) for i in common]
d, lo, hi = boot_paired(lad, ref)
gate1 = bool(lo <= 0.0 <= hi)
report["gates"]["gate1_exact_reproduces_r19"] = {
    "ladder_exact": float(np.mean(lad)), "r19_nine_series": float(np.mean(ref)),
    "paired_delta": d, "ci95": [lo, hi],
    "discordant": int(sum(1 for a, b in zip(lad, ref) if a != b)),
    "passes": gate1,
    "criterion": "paired item-level 95% CI on the difference covers zero",
}

# ---- Gate 2 ----
e = report["rungs"]["exact"]["pair_accuracy"]
r = report["rungs"]["region"]["pair_accuracy"]
n = report["rungs"]["none"]["pair_accuracy"]
gate2 = bool(e >= r >= n)
report["gates"]["gate2_base_degrades_monotonically"] = {
    "exact": e, "region": r, "none": n, "passes": gate2,
    "criterion": "base pair accuracy must satisfy exact >= region >= none",
}

print(f"\nGate 1 — exact reproduces R19: ladder {np.mean(lad):.4f} vs R19 {np.mean(ref):.4f}, "
      f"paired delta {d:+.4f} CI[{lo:+.4f},{hi:+.4f}] -> {'PASS' if gate1 else 'FAIL'}")
print(f"Gate 2 — monotone degradation: exact {e:.4f} >= region {r:.4f} >= none {n:.4f} "
      f"-> {'PASS' if gate2 else 'FAIL'}")
print("\nAll rungs (base, pair accuracy):")
for rung in RUNGS:
    print(f"  {rung:8s} {report['rungs'][rung]['pair_accuracy']:.4f} "
          f"(strict {report['rungs'][rung]['strict_pair_accuracy']:.4f})")

(ROOT / "reports/cue_ladder_base_gates_v1.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n")
print("\nwrote reports/cue_ladder_base_gates_v1.json")
