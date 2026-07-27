#!/usr/bin/env python3
"""Cue ladder final readout: v2 gate outcome and the 2x2 it does support."""
import json
from pathlib import Path

import numpy as np

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
RNG = np.random.default_rng(20260727)
V1 = Path((ROOT / "tmp/cl_base.txt").read_text().strip())
V2 = Path((ROOT / "tmp/cl_v2base.txt").read_text().strip())
RUNS = {"exact": V1 / "exact", "region": V1 / "region", "none": V1 / "none",
        "decoy": V1 / "decoy", "named_exact": V2 / "named_exact",
        "named_region": V2 / "named_region"}


def rows(rung):
    man = {json.loads(l)["pair_id"]: json.loads(l)
           for l in open(ROOT / f"data/cue_ladder_v1/{rung}_manifest.jsonl")}
    preds = {json.loads(l)["pair_id"]: json.loads(l)
             for l in open(RUNS[rung] / "predictions.jsonl")}
    return {m["source_pair_id"]: preds[pid] for pid, m in man.items() if pid in preds}


data = {r: rows(r) for r in RUNS}
common = sorted(set.intersection(*[set(v) for v in data.values()]))
acc = {r: np.array([float(bool(data[r][i]["pair_correct"])) for i in common]) for r in RUNS}
strict = {r: np.array([float(bool(data[r][i]["strict_pair_correct"])) for i in common]) for r in RUNS}


def paired(a, b, n=20000):
    d = acc[a] - acc[b]
    idx = RNG.integers(0, len(d), size=(n, len(d)))
    bt = d[idx].mean(axis=1)
    return float(d.mean()), float(np.percentile(bt, 2.5)), float(np.percentile(bt, 97.5))


rep = {"n_items": len(common),
       "base_pair_accuracy": {r: float(acc[r].mean()) for r in RUNS},
       "base_strict_pair_accuracy": {r: float(strict[r].mean()) for r in RUNS},
       "contrasts": {}, "gates": {}}

for name, (a, b) in {
    "occlusion_cost_named_question": ("named_exact", "named_region"),
    "legend_star_value_named_question": ("named_region", "none"),
    "point_star_needed_when_star_is_the_identifier": ("exact", "region"),
    "decoy_cost_named_question": ("decoy", "none"),
    "question_form_with_point_mark": ("exact", "named_exact"),
    "question_form_with_legend_only": ("region", "named_region"),
}.items():
    d, lo, hi = paired(a, b)
    rep["contrasts"][name] = {"a": a, "b": b, "delta": d, "ci95": [lo, hi],
                              "excludes_zero": bool(lo > 0 or hi < 0)}

ne, nr, no = (float(acc[r].mean()) for r in ("named_exact", "named_region", "none"))
rep["gates"]["v2_gate_base_monotone"] = {
    "named_exact": ne, "named_region": nr, "none": no,
    "criterion": "named_exact >= named_region >= none",
    "passes": bool(ne >= nr >= no),
}

(ROOT / "reports/cue_ladder_readout_v1.json").write_text(json.dumps(rep, indent=2, sort_keys=True) + "\n")
print(f"n={len(common)}")
print("base pair accuracy by rung:")
for r in ("exact", "region", "named_exact", "named_region", "none", "decoy"):
    print(f"  {r:14s} {acc[r].mean():.4f}  (strict {strict[r].mean():.4f})")
print(f"\nv2 gate: {ne:.4f} >= {nr:.4f} >= {no:.4f} -> "
      f"{'PASS' if rep['gates']['v2_gate_base_monotone']['passes'] else 'FAIL'}")
print("\ncontrasts (paired, 95% CI):")
for k, v in rep["contrasts"].items():
    print(f"  {k:46s} {v['delta']:+.4f} [{v['ci95'][0]:+.4f},{v['ci95'][1]:+.4f}]"
          f"{'  *' if v['excludes_zero'] else ''}")
print("\nwrote reports/cue_ladder_readout_v1.json")
