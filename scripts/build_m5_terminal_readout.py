#!/usr/bin/env python3
"""M5 terminal readout (ladder R2), per docs/MAIN_PHASE_RULING_20260716.md R1.

    Delta = R19 geometry pair-acc(step 400) - pair-acc(step 100)

with an item-paired bootstrap 95% CI, and the registered verdict:

    FLAT          iff the CI is contained in [-0.05, +0.05]
    RISING        iff Delta >= +0.05 and the CI lower bound > 0
    FALLING       iff Delta <= -0.05 and the CI upper bound < 0
    INDETERMINATE otherwise, reported exactly as such

Step 400 is terminal: no extension or rerun under any outcome. Steps 150, 200
and 300 are descriptive and cannot select the endpoint -- they are tabled here
but play no part in the verdict.
"""
import argparse
import glob
import json
from pathlib import Path

import numpy as np

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
RNG = np.random.default_rng(20260727)
BOOT = 20000
GEO = "geometry_coordinate_indexing"
SESOI = 0.05

STEP100 = "experiments/runs/fliptrack_v02r19_anchor_step100_real_an12_20260712T085144Z/shards/*.jsonl"
DESCRIPTIVE = {
    150: "experiments/runs/fliptrack_aggregate_m5_step150_m5_anchor_longhorizon_400_an12_20260716t173030z_real_20260718T053827Z",
    200: "experiments/runs/fliptrack_aggregate_m5_step200_m5_anchor_longhorizon_400_resume150_an12_20260721t160431z_real_20260722T142942Z",
    300: "experiments/runs/fliptrack_aggregate_m5_step300_m5_anchor_longhorizon_segment250_300_an12_20260725t100517z_real_20260726T084430Z",
}


def geo_rows(pattern):
    rows = {}
    for f in sorted(glob.glob(str(ROOT / pattern))):
        for line in open(f):
            if line.strip():
                r = json.loads(line)
                if r.get("category") == GEO:
                    rows[r["pair_id"]] = r
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step400-shards", required=True,
                    help="glob for the step-400 R19 eval shards")
    args = ap.parse_args()

    a = geo_rows(STEP100)
    b = geo_rows(args.step400_shards)
    if len(a) != 600:
        raise SystemExit(f"step100 geometry rows = {len(a)}, expected 600")
    if len(b) != 600:
        raise SystemExit(f"step400 geometry rows = {len(b)}, expected 600")
    if set(a) != set(b):
        raise SystemExit("step100 and step400 pair_id sets differ")

    pids = sorted(a)
    x100 = np.array([float(bool(a[p]["pair_correct"])) for p in pids])
    x400 = np.array([float(bool(b[p]["pair_correct"])) for p in pids])
    s100 = np.array([float(bool(a[p]["strict_pair_correct"])) for p in pids])
    s400 = np.array([float(bool(b[p]["strict_pair_correct"])) for p in pids])

    d = x400 - x100
    idx = RNG.integers(0, len(d), size=(BOOT, len(d)))
    boots = d[idx].mean(axis=1)
    delta = float(d.mean())
    lo, hi = (float(v) for v in np.percentile(boots, [2.5, 97.5]))

    if lo >= -SESOI and hi <= SESOI:
        verdict = "FLAT"
    elif delta >= SESOI and lo > 0:
        verdict = "RISING"
    elif delta <= -SESOI and hi < 0:
        verdict = "FALLING"
    else:
        verdict = "INDETERMINATE"

    ds = s400 - s100
    bs = ds[idx].mean(axis=1)
    strict = {"delta": float(ds.mean()),
              "ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]}

    desc = {}
    for step, agg in DESCRIPTIVE.items():
        m = json.loads((ROOT / agg / "metrics.json").read_text())
        per = m.get("per_template", {})
        desc[step] = {"overall_pair_accuracy": m.get("pair_accuracy"),
                      "per_template_keys": sorted(per) if per else None}

    rep = {
        "schema_version": 1,
        "rule": "docs/MAIN_PHASE_RULING_20260716.md R1",
        "endpoint": "R19 geometry pair accuracy, step 400 minus step 100",
        "n_pairs": len(pids),
        "step100_pair_accuracy": float(x100.mean()),
        "step400_pair_accuracy": float(x400.mean()),
        "delta": delta, "ci95": [lo, hi], "sesoi": SESOI,
        "verdict": verdict,
        "strict_secondary": strict,
        "step100_strict": float(s100.mean()), "step400_strict": float(s400.mean()),
        "descriptive_only_steps": desc,
        "terminal": "step 400 is terminal; no extension or rerun under any outcome",
        "step400_shards": args.step400_shards,
    }
    (ROOT / "reports/m5_terminal_readout_v1.json").write_text(
        json.dumps(rep, indent=2, sort_keys=True) + "\n")

    print(f"n={len(pids)}  step100={x100.mean():.4f}  step400={x400.mean():.4f}")
    print(f"Delta = {delta:+.4f}  95% CI [{lo:+.4f}, {hi:+.4f}]  SESOI +/-{SESOI}")
    print(f"VERDICT: {verdict}")
    print(f"strict secondary: {strict['delta']:+.4f} "
          f"[{strict['ci95'][0]:+.4f}, {strict['ci95'][1]:+.4f}] "
          f"(step100 {s100.mean():.4f} -> step400 {s400.mean():.4f})")
    print("wrote reports/m5_terminal_readout_v1.json")


if __name__ == "__main__":
    main()
