#!/usr/bin/env python3
"""G0.2 headroom control -- the analysis that freezes Paper 1's title claim.

Raw G0.2 finds A2b's image-present gain larger on items with at least one
observed blind success. Those items are easier, so base real accuracy is higher
there and the comparison is confounded by headroom in both directions. This
re-runs the contrast restricted to items the base model gets WRONG with the
image, where every arm has the same 0 -> 1 headroom, and reports base accuracy
per stratum so the confound is visible rather than assumed away.
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
RNG = np.random.default_rng(20260727)
BOOT = 10000
rep = json.loads((ROOT / "reports/gate0_stratification_v1.json").read_text())


def load(rel):
    return [json.loads(l) for l in (ROOT / rel).read_text().splitlines() if l.strip()]


def key(r):
    return (r["problem"], tuple(r.get("image_sha256") or []))


G = "experiments/runs/blind_solvability_v2_guarded_rescore_geo3k_filtered_v2_retry_%s_login_%s/per_item.jsonl"
base_real = {key(r): r for r in load(G % ("real", "20260712T050905Z"))}
base_none = {key(r): r for r in load(G % ("none", "20260712T055030Z"))}
CROSSED = rep["crossed_runs"]
ref = list(load(Path(rep["arm_runs"]["a1_real"]["1"]).relative_to(ROOT).as_posix()))
ITEMS = [key(r) for r in ref]

b_final = np.array([float(bool(base_real[k]["greedy_canonical_correct"])) for k in ITEMS])
q_blind = np.array([float(base_none[k]["q_i"]) for k in ITEMS])
# "blind-answerable" = at least one observed blind success; the Jeffreys floor
# marks items with zero successes
FLOOR = float(np.min(q_blind))
answerable = q_blind > FLOOR + 1e-9


def crossed_final(arm, seed):
    rows = {key(r): r for r in load(f"experiments/runs/{CROSSED[f'{arm}|s{seed}']}/predictions.jsonl")}
    return np.array([float(bool(rows[k]["acc_final"])) for k in ITEMS])


def ci(v):
    if len(v) == 0:
        return None
    d = RNG.integers(0, len(v), size=(BOOT, len(v)))
    b = v[d].mean(axis=1)
    return {"n": int(len(v)), "mean": float(v.mean()),
            "ci95": [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]}


out = {"jeffreys_floor": FLOOR,
       "n_blind_answerable": int(answerable.sum()),
       "n_not_blind_answerable": int((~answerable).sum()),
       "note": ("blind-answerable = at least one observed blind success; the rest sit "
                "at the Jeffreys floor with zero successes"),
       "base_accuracy_by_stratum": {
           "blind_answerable": float(b_final[answerable].mean()),
           "not_blind_answerable": float(b_final[~answerable].mean())},
       "arms": {}}

for arm in ("a1_real", "a2b_noimage", "a2_gray", "a3_caption"):
    gain = np.mean([crossed_final(arm, s) - b_final for s in (1, 2, 3)], axis=0)
    # recovery restricted to base-wrong items: identical 0->1 headroom everywhere
    bw = b_final == 0
    out["arms"][arm] = {
        "all_items": {"blind_answerable": ci(gain[answerable]),
                      "not_blind_answerable": ci(gain[~answerable])},
        "base_wrong_only": {"blind_answerable": ci(gain[answerable & bw]),
                            "not_blind_answerable": ci(gain[~answerable & bw])},
    }

rep["G0_2_headroom_control"] = out
(ROOT / "reports/gate0_stratification_v1.json").write_text(json.dumps(rep, indent=2, sort_keys=True) + "\n")

print(f"Jeffreys floor {FLOOR:.4f}; blind-answerable {int(answerable.sum())}, "
      f"not {int((~answerable).sum())}")
print(f"base real acc: blind-answerable {b_final[answerable].mean():.4f} | "
      f"not {b_final[~answerable].mean():.4f}")
print(f"{'arm':<14}{'ALL: ans':>14}{'ALL: not':>14}{'BASEWRONG: ans':>17}{'BASEWRONG: not':>17}")
for arm, v in out["arms"].items():
    a1 = v["all_items"]["blind_answerable"]; a2 = v["all_items"]["not_blind_answerable"]
    b1 = v["base_wrong_only"]["blind_answerable"]; b2 = v["base_wrong_only"]["not_blind_answerable"]
    print(f"{arm:<14}{a1['mean']:>+14.4f}{a2['mean']:>+14.4f}{b1['mean']:>+17.4f}{b2['mean']:>+17.4f}")
print("updated reports/gate0_stratification_v1.json")
