#!/usr/bin/env python3
"""D4 caption-column readout.

Primary estimand registered in docs/registered_d4_ordering_addendum_v1.md BEFORE
any cell ran: is the readout policy pixel-specific or evidence-general? Compare
the arm ORDERING under caption-at-test against the ordering under real-at-test,
and the caption column's spread against the blind columns' spreads.
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
RNG = np.random.default_rng(20260728)
BOOT = 20000

# base row, pinned from the registered arm step-0 evaluations (not re-measured)
BASE = {"real": 0.174709, "gray": 0.089850, "none": 0.068220, "caption": 0.209651}
ARMS = {"a1": "A1 real", "a3": "A3 caption", "a2b": "A2b no-image", "a2": "A2 gray"}
# image-present column from D3/Gate 0, for the ordering comparison
REAL_GAIN = {"a1": 0.243483, "a3": 0.174709, "a2b": 0.128674, "a2": 0.118691}
GRAY_GAIN = {"a1": 0.019, "a3": 0.024, "a2b": 0.017, "a2": 0.016}
NONE_GAIN = {"a1": 0.036, "a3": 0.037, "a2b": 0.046, "a2": 0.033}

rec = json.loads((ROOT / "reports/d4_cell_reconciliation_v1.json").read_text())
kept = rec["kept"]

per_item = {}
for cell, info in kept.items():
    rows = [json.loads(l) for l in
            (ROOT / "experiments/runs" / info["run"] / "predictions.jsonl").read_text().splitlines()
            if l.strip()]
    key = lambda r: (r["problem"], tuple(r.get("image_sha256") or []))
    per_item[cell] = {key(r): float(bool(r["acc_final"])) for r in rows}
    if len(per_item[cell]) != 601:
        raise SystemExit(f"{cell}: {len(per_item[cell])} items")

items = sorted(set.intersection(*[set(v) for v in per_item.values()]))
if len(items) != 601:
    raise SystemExit(f"common items {len(items)}")


def arm_gain(arm):
    """Mean over seeds of (caption accuracy - pinned base caption)."""
    vals, per_seed = [], []
    for s in (1, 2, 3):
        v = np.array([per_item[f"{arm}_seed{s}"][i] for i in items])
        per_seed.append(float(v.mean() - BASE["caption"]))
        vals.append(v)
    stacked = np.mean(vals, axis=0) - BASE["caption"]
    idx = RNG.integers(0, len(stacked), size=(BOOT, len(stacked)))
    b = stacked[idx].mean(axis=1)
    return {"mean": float(stacked.mean()),
            "ci95": [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))],
            "per_seed": per_seed,
            "raw_accuracy": float(np.mean([v.mean() for v in vals]))}


cap = {a: arm_gain(a) for a in ARMS}


def rank(d):
    order = sorted(d, key=lambda k: -d[k])
    return {k: i for i, k in enumerate(order)}


def spearman(a, b):
    ra, rb = rank(a), rank(b)
    x = np.array([ra[k] for k in ARMS]); y = np.array([rb[k] for k in ARMS])
    return float(np.corrcoef(x, y)[0, 1])


cap_gain = {a: cap[a]["mean"] for a in ARMS}
rho = spearman(cap_gain, REAL_GAIN)
spread = lambda d: max(d.values()) - min(d.values())
s_cap, s_real = spread(cap_gain), spread(REAL_GAIN)
s_gray, s_none = spread(GRAY_GAIN), spread(NONE_GAIN)
s_blind_max = max(s_gray, s_none)

evidence_general = rho >= 0.70 and s_cap >= 2 * s_blind_max
pixel_specific = (min(s_gray, s_none) <= s_cap <= s_blind_max) and rho < 0.70
branch = "(a) evidence-general" if evidence_general else (
    "(b) pixel-specific" if pixel_specific else "(c) intermediate — descriptive")

# secondary: A3 matched (caption) vs crossed (real)
a3_matched = cap["a3"]["mean"]
a3_crossed = REAL_GAIN["a3"]
a3_ratio = a3_crossed / a3_matched if a3_matched else float("nan")

out = {"schema_version": 1,
       "registration": "docs/registered_d4_ordering_addendum_v1.md",
       "base_caption_pinned": BASE["caption"], "n_items": len(items),
       "caption_column": {a: cap[a] for a in ARMS},
       "spearman_caption_vs_real": rho,
       "spreads": {"caption": s_cap, "real": s_real, "gray": s_gray, "none": s_none},
       "branch": branch,
       "a3_matched_vs_crossed": {"matched_caption": a3_matched, "crossed_real": a3_crossed,
                                 "ratio": a3_ratio},
       "cells": {c: kept[c]["run"] for c in sorted(kept)}}
(ROOT / "reports/d4_caption_column_v1.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")

print(f"n={len(items)}  base caption (pinned) = {BASE['caption']:.4f}\n")
print(f"{'arm':<16}{'caption acc':>12}{'gain':>10}{'95% CI':>22}")
for a in ARMS:
    c = cap[a]
    print(f"{ARMS[a]:<16}{c['raw_accuracy']:>12.4f}{c['mean']:>+10.4f}"
          f"   [{c['ci95'][0]:+.4f}, {c['ci95'][1]:+.4f}]")
print(f"\nordering caption: {[ARMS[k] for k in sorted(cap_gain, key=lambda k:-cap_gain[k])]}")
print(f"ordering real:    {[ARMS[k] for k in sorted(REAL_GAIN, key=lambda k:-REAL_GAIN[k])]}")
print(f"Spearman rho = {rho:+.3f}")
print(f"spreads: caption {s_cap:.4f} | real {s_real:.4f} | gray {s_gray:.4f} | none {s_none:.4f}")
print(f"\nBRANCH: {branch}")
print(f"A3 matched(caption) {a3_matched:+.4f} vs crossed(real) {a3_crossed:+.4f} ratio {a3_ratio:.2f}")
print("wrote reports/d4_caption_column_v1.json")
