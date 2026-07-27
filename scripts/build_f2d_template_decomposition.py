#!/usr/bin/env python3
"""F2d — template decomposition of the overall R19 movement.

PAPER1 §3 F2 states the mechanism as: the saturated header table sits at 1.000
for every model and contributes nothing to any delta, so the movement
concentrates on the oracle-localized readout control while the primary anchor
stays flat. This tests that claim on cached per-item predictions -- no new
inference -- and reports each task in its own role (I13), never aggregated.
"""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
RNG = np.random.default_rng(20260727)
BOOT = 10000
BASE = ("experiments/runs/fliptrack_v02r19_packaged_qwen25vl3b_real_"
        "an29_20260710T142716Z/shards/*.jsonl")
ARMS = ("a1_real", "a2_gray", "a2b_noimage", "a3_caption")
ROLE = {
    "coordinate_register_twenty_point_x_v02": "primary visual anchor (search + binding + read)",
    "header_cued_table_code_v02": "saturated positive control / retention canary",
    "starred_series_value_nine_v07": "oracle-localized readout control",
}


def load_glob(pattern):
    import glob
    rows = []
    for f in sorted(glob.glob(str(ROOT / pattern))):
        rows += [json.loads(l) for l in open(f) if l.strip()]
    return rows


def resolve():
    out = {a: {} for a in ARMS}
    for seed in (1, 2, 3):
        res = json.loads((ROOT / f"reports/pilot_4arm_seed{seed}_results_v1.json").read_text())
        for arm, per in res["provenance"]["r19_markers"].items():
            rec = per["100"]
            blob = (ROOT / rec["path"]).read_bytes()
            if hashlib.sha256(blob).hexdigest() != rec["sha256"]:
                raise SystemExit(f"{arm} s{seed}: marker sha mismatch")
            out[arm][seed] = json.loads(blob)["evaluation_run"]
    return out


base_rows = load_glob(BASE)
by_tpl_base = {}
for r in base_rows:
    by_tpl_base.setdefault(r["template_id"], {})[r["pair_id"]] = r
TPLS = sorted(by_tpl_base)
if sorted(TPLS) != sorted(ROLE):
    raise SystemExit(f"templates {TPLS}")

arm_runs = resolve()
rep = {"schema_version": 1, "roles": ROLE, "n_by_template": {t: len(by_tpl_base[t]) for t in TPLS},
       "base": {}, "arms": {}, "overall": {}}


def ci(v):
    d = RNG.integers(0, len(v), size=(BOOT, len(v)))
    b = v[d].mean(axis=1)
    return float(v.mean()), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


for t in TPLS:
    pids = sorted(by_tpl_base[t])
    lp = np.array([float(by_tpl_base[t][p]["pair_correct"]) for p in pids])
    sp = np.array([float(by_tpl_base[t][p]["strict_pair_correct"]) for p in pids])
    mem = np.array([float(bool(by_tpl_base[t][p]["correct_a"])) for p in pids]
                   + [float(bool(by_tpl_base[t][p]["correct_b"])) for p in pids])
    rep["base"][t] = {"n_pairs": len(pids), "pair_accuracy": float(lp.mean()),
                      "strict_pair_accuracy": float(sp.mean()),
                      "member_accuracy": float(mem.mean())}

all_pids = {t: sorted(by_tpl_base[t]) for t in TPLS}
N_TOTAL = sum(len(v) for v in all_pids.values())

for arm in ARMS:
    entry = {"per_template": {}, "overall_delta_per_seed": []}
    per_seed_tpl = {t: [] for t in TPLS}
    for seed in (1, 2, 3):
        rows = load_glob(f"{arm_runs[arm][seed]}/shards/*.jsonl")
        idx = {}
        for r in rows:
            idx.setdefault(r["template_id"], {})[r["pair_id"]] = r
        tot = 0.0
        for t in TPLS:
            pids = all_pids[t]
            if set(idx.get(t, {})) != set(pids):
                raise SystemExit(f"{arm} s{seed} {t}: pair set differs")
            d = np.array([float(idx[t][p]["pair_correct"]) - float(by_tpl_base[t][p]["pair_correct"])
                          for p in pids])
            per_seed_tpl[t].append(d)
            tot += d.sum()
        entry["overall_delta_per_seed"].append(tot / N_TOTAL)
    for t in TPLS:
        stacked = np.mean(per_seed_tpl[t], axis=0)
        m, lo, hi = ci(stacked)
        contrib = m * len(all_pids[t]) / N_TOTAL
        entry["per_template"][t] = {
            "role": ROLE[t], "n_pairs": len(all_pids[t]),
            "mean_delta": m, "ci95": [lo, hi],
            "per_seed_delta": [float(np.mean(x)) for x in per_seed_tpl[t]],
            "contribution_to_overall": contrib,
            "share_of_overall_pct": None,
        }
    ov = float(np.mean(entry["overall_delta_per_seed"]))
    entry["overall_delta_mean"] = ov
    for t in TPLS:
        c = entry["per_template"][t]["contribution_to_overall"]
        entry["per_template"][t]["share_of_overall_pct"] = (100.0 * c / ov) if ov else None
    rep["arms"][arm] = entry

(ROOT / "reports/f2d_template_decomposition_v1.json").write_text(json.dumps(rep, indent=2, sort_keys=True) + "\n")

print("BASE by template:")
for t in TPLS:
    b = rep["base"][t]
    print(f"  {t:42s} n={b['n_pairs']:4d} pair={b['pair_accuracy']:.4f} "
          f"strict={b['strict_pair_accuracy']:.4f} member={b['member_accuracy']:.4f}")
for arm in ARMS:
    e = rep["arms"][arm]
    print(f"\n{arm}  overall delta {e['overall_delta_mean']:+.4f} "
          f"(per seed {[round(x,4) for x in e['overall_delta_per_seed']]})")
    for t in TPLS:
        c = e["per_template"][t]
        print(f"  {t:42s} d={c['mean_delta']:+.4f} [{c['ci95'][0]:+.4f},{c['ci95'][1]:+.4f}] "
              f"contrib={c['contribution_to_overall']:+.4f} share={c['share_of_overall_pct']:.1f}%")
print("\nwrote reports/f2d_template_decomposition_v1.json")
