#!/usr/bin/env python3
"""Adversarial independent recomputation of SEED3g headline numbers.

Deliberately does NOT import scripts/x3_seed3_corrosion_replication.py.
Reads shards directly, uses cached row fields as an independent route where
possible, and re-derives everything.
"""
from __future__ import annotations

import glob
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
import sys
sys.path.insert(0, str(ROOT))
from src.eval.fliptrack_metrics import pair_score

TEMPLATE = "coordinate_register_twenty_point_x_v02"

RUNS = {
    "base": "fliptrack_v02r19_packaged_qwen25vl3b_real_an29_20260710T142716Z",
    "a2|seed1": "pilot_fliptrack_a2_gray_seed1_step100_real_an12_20260716T152519Z",
    "a2|seed2": "pilot_fliptrack_a2_gray_seed2_step100_real_an29_20260721T163431Z",
    "a2|seed3": "pilot_fliptrack_a2_gray_seed3_step100_real_an29_20260725T092515Z",
    "a1|seed3": "pilot_fliptrack_a1_real_seed3_step100_real_an29_20260725T092506Z",
    "a2b|seed3": "pilot_fliptrack_a2b_noimage_seed3_step100_real_an29_20260725T092523Z",
    "a3|seed3": "pilot_fliptrack_a3_caption_seed3_step100_real_an29_20260725T092532Z",
}

out = {}


def load(run):
    d = ROOT / "experiments/runs" / run
    paths = sorted(glob.glob(str(d / "shards" / "*.jsonl"))) or sorted(glob.glob(str(d / "*.jsonl")))
    rows_all = 0
    tmpl_counter = Counter()
    rows = {}
    dups = 0
    for p in paths:
        for line in Path(p).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            rows_all += 1
            tmpl_counter[r.get("template_id")] += 1
            if r.get("template_id") != TEMPLATE:
                continue
            pid = str(r["pair_id"])
            if pid in rows:
                dups += 1
            rows[pid] = r
    return rows, rows_all, tmpl_counter, dups


data = {}
meta = {}
for k, run in RUNS.items():
    rows, n_all, tc, dups = load(run)
    data[k] = rows
    meta[k] = {
        "run": run,
        "rows_total_all_templates": n_all,
        "n_templates": len(tc),
        "n_geometry_rows": len(rows),
        "dup_pair_ids": dups,
    }
out["run_meta"] = meta

# cached-vs-fresh scoring agreement (independent route)
agree = {}
for k, rows in data.items():
    mism_len = mism_str = 0
    for pid, r in rows.items():
        fresh = pair_score(r)
        if bool(r.get("pair_correct")) != bool(fresh["pair_correct"]):
            mism_len += 1
        if bool(r.get("acc_strict")) != bool(fresh["strict_pair_correct"]):
            mism_str += 1
    agree[k] = {"lenient_cached_vs_fresh_mismatch": mism_len, "strict_cached_vs_fresh_mismatch": mism_str}
out["cached_vs_fresh"] = agree

# contract ids present
cids = {}
for k, rows in data.items():
    cids[k] = sorted({str(r.get("prompt_contract_id")) for r in rows.values()})
out["prompt_contract_ids"] = cids

# pair-id universe identity across runs
base_ids = set(data["base"])
out["pair_id_sets_identical"] = {k: sorted(set(v)) == sorted(base_ids) for k, v in data.items()}


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0.0, c - h), min(1.0, c + h)]


def track(field_pair, field_a, field_b, name):
    res = {}
    corr = {}
    for k, rows in data.items():
        corr[k] = {pid: bool(pair_score(r)[field_pair]) for pid, r in rows.items()}
    base_correct = {p for p, v in corr["base"].items() if v}
    res["base_n"] = len(base_correct)
    res["base_acc"] = len(base_correct) / 600
    res["base_wilson"] = wilson(len(base_correct), 600)
    degr, gain = {}, {}
    per = {}
    for s in ("seed1", "seed2", "seed3"):
        c = corr[f"a2|{s}"]
        nc = sum(1 for v in c.values() if v)
        degr[s] = {p for p in base_correct if not c[p]}
        gain[s] = {p for p, v in c.items() if v and p not in base_correct}
        per[s] = {
            "n_correct": nc,
            "acc": nc / 600,
            "wilson": wilson(nc, 600),
            "delta": (nc - len(base_correct)) / 600,
            "delta_items": nc - len(base_correct),
            "c2w": len(degr[s]),
            "w2c": len(gain[s]),
            "identity_check_delta_eq_w2c_minus_c2w": (nc - len(base_correct)) == (len(gain[s]) - len(degr[s])),
        }
    res["per_seed"] = per
    res["degraded_sha256"] = {
        s: hashlib.sha256("\n".join(sorted(degr[s])).encode()).hexdigest() for s in degr
    }
    d1, d2, d3 = degr["seed1"], degr["seed2"], degr["seed3"]
    ov = {}
    for a, b, da, db in (("seed3", "seed1", d3, d1), ("seed3", "seed2", d3, d2), ("seed1", "seed2", d1, d2)):
        inter, uni = da & db, da | db
        ov[f"{a}__{b}"] = {
            "size_a": len(da), "size_b": len(db), "inter": len(inter), "union": len(uni),
            "jaccard": len(inter) / len(uni),
            "incl_excl_ok": len(uni) == len(da) + len(db) - len(inter),
        }
    i3, u3 = d1 & d2 & d3, d1 | d2 | d3
    ov["three"] = {
        "inter": len(i3), "union": len(u3), "j3": len(i3) / len(u3),
        "recovery_num": len(d3 & (d1 & d2)), "recovery_den": len(d1 & d2),
        "recovery": len(d3 & (d1 & d2)) / len(d1 & d2),
        "recovery_wilson": wilson(len(d3 & (d1 & d2)), len(d1 & d2)),
    }
    res["overlap"] = ov

    # independent permutation null with a DIFFERENT seed
    rng = np.random.default_rng(987654321)
    universe = sorted(base_correct)
    nulls = {}
    for a, b, da, db in (("seed3", "seed1", d3, d1), ("seed3", "seed2", d3, d2), ("seed1", "seed2", d1, d2)):
        obs = len(da & db) / len(da | db)
        vals = np.empty(10000)
        for i in range(10000):
            s1 = set(rng.choice(universe, size=len(da), replace=False).tolist())
            s2 = set(rng.choice(universe, size=len(db), replace=False).tolist())
            vals[i] = len(s1 & s2) / len(s1 | s2)
        nulls[f"{a}__{b}"] = {
            "null_mean": float(vals.mean()), "null_p95": float(np.percentile(vals, 95)),
            "null_max": float(vals.max()),
            "p": float((int((vals >= obs).sum()) + 1) / 10001),
        }
    vals = np.empty(10000)
    obs3 = len(i3) / len(u3)
    for i in range(10000):
        ss = [set(rng.choice(universe, size=n, replace=False).tolist()) for n in (len(d1), len(d2), len(d3))]
        vals[i] = len(ss[0] & ss[1] & ss[2]) / len(ss[0] | ss[1] | ss[2])
    nulls["three"] = {
        "null_mean": float(vals.mean()), "null_p95": float(np.percentile(vals, 95)),
        "null_max": float(vals.max()), "p": float((int((vals >= obs3).sum()) + 1) / 10001),
    }
    res["null_indep_seed987654321"] = nulls

    # paired bootstrap with a different seed
    rng2 = np.random.default_rng(13572468)
    ids = sorted(base_correct | set(corr["base"]))
    ids = sorted(corr["base"])
    bvec = np.array([1.0 if corr["base"][p] else 0.0 for p in ids])
    boots = {}
    idx = rng2.integers(0, len(ids), size=(10000, len(ids)))
    for s in ("seed1", "seed2", "seed3"):
        avec = np.array([1.0 if corr[f"a2|{s}"][p] else 0.0 for p in ids])
        diff = avec - bvec
        bs = diff[idx].mean(axis=1)
        lo, hi = np.percentile(bs, [2.5, 97.5])
        boots[s] = {"delta": float(diff.mean()), "lo": float(lo), "hi": float(hi)}
    res["bootstrap_indep"] = boots

    # cross arm on seed3
    ca = {}
    for arm in ("a1", "a2b", "a3"):
        c = corr[f"{arm}|seed3"]
        ca[arm] = {
            "wrong_on_3seed_shared": sum(1 for p in i3 if not c[p]),
            "wrong_on_seed3_degraded": sum(1 for p in d3 if not c[p]),
            "wrong_on_base_correct": sum(1 for p in base_correct if not c[p]),
        }
    res["cross_arm_seed3"] = ca

    # member-level slot counting
    slots = {}
    for s in ("seed1", "seed2", "seed3"):
        rows = data[f"a2|{s}"]
        md = Counter()
        n_slots = 0
        for p in degr[s]:
            fresh = pair_score(rows[p])
            ws = [x for x in ("a", "b") if not bool(fresh[field_a if x == "a" else field_b])]
            md["both_members" if len(ws) == 2 else f"member_{ws[0]}_only"] += 1
            n_slots += len(ws)
        slots[s] = {"member_direction": dict(md), "wrong_slots": n_slots}
    res["slots"] = slots
    return res, degr, corr


lenient, degr_l, corr_l = track("pair_correct", "correct_a", "correct_b", "lenient")
strict, degr_s, corr_s = track("strict_pair_correct", "strict_correct_a", "strict_correct_b", "strict")
out["lenient"] = lenient
out["strict"] = strict

print(json.dumps(out, indent=1, sort_keys=True, default=str))
