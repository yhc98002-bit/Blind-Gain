#!/usr/bin/env python3
"""Adversarial pass 2: taxonomy, same-wrong slots, gold-value inflation, McNemar."""
from __future__ import annotations

import glob
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
sys.path.insert(0, str(ROOT))
from src.eval.fliptrack_metrics import pair_score
from scripts.build_x2_hard_negative_candidates import levenshtein, nearest_gridline, replay_scene
from scripts.x3_a2_degradation_forensics import classify_wrong, extract_answer, feature_vector

TEMPLATE = "coordinate_register_twenty_point_x_v02"
RUNS = {
    "base": "fliptrack_v02r19_packaged_qwen25vl3b_real_an29_20260710T142716Z",
    "seed1": "pilot_fliptrack_a2_gray_seed1_step100_real_an12_20260716T152519Z",
    "seed2": "pilot_fliptrack_a2_gray_seed2_step100_real_an29_20260721T163431Z",
    "seed3": "pilot_fliptrack_a2_gray_seed3_step100_real_an29_20260725T092515Z",
}


def load(run):
    d = ROOT / "experiments/runs" / run
    paths = sorted(glob.glob(str(d / "shards" / "*.jsonl")))
    rows = {}
    for p in paths:
        for line in Path(p).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("template_id") != TEMPLATE:
                continue
            rows[str(r["pair_id"])] = r
    return rows


data = {k: load(v) for k, v in RUNS.items()}
out = {}

# base row keys sanity
out["base_row_has_contract_fields"] = sorted(
    k for k in next(iter(data["base"].values())) if "contract" in k or "strict" in k
)
out["arm_row_has_contract_fields"] = sorted(
    k for k in next(iter(data["seed3"].values())) if "contract" in k or "strict" in k
)

# scenes
registry_rows = {}
for line in (ROOT / "data/fliptrack_r19_visual_evidence_candidates_v1.jsonl").read_text().splitlines():
    r = json.loads(line)
    if r.get("template_id") == TEMPLATE:
        registry_rows[str(r["pair_id"])] = r
sources = {}
for name in ("fliptrack_v02r10_source_manifest.jsonl", "fliptrack_v02r18_source_manifest.jsonl"):
    for line in (ROOT / "data" / name).read_text().splitlines():
        r = json.loads(line)
        if r.get("template_id") == TEMPLATE:
            sources[str(r["pair_id"])] = r
scenes = {}
for pid, rr in registry_rows.items():
    sid = str(rr.get("source_pair_id") or pid)
    scenes[pid] = replay_scene(int(sources[sid]["provenance"]["pair_seed"]))
out["n_registry_rows"] = len(registry_rows)
out["registry_covers_all_600"] = set(registry_rows) >= set(data["base"])

scored = {}
for k, rows in data.items():
    scored[k] = {pid: pair_score(r) for pid, r in rows.items()}


def analyse(strict):
    fp = "strict_pair_correct" if strict else "pair_correct"
    fa = "strict_correct_a" if strict else "correct_a"
    fb = "strict_correct_b" if strict else "correct_b"
    base_correct = {p for p, s in scored["base"].items() if s[fp]}
    degr = {}
    tax = {}
    wrong_vals = {}
    slot_isgold = {}
    slot_lenient_ok = {}
    for s in ("seed1", "seed2", "seed3"):
        degr[s] = {p for p in base_correct if not scored[s][p][fp]}
        c = Counter()
        wv = {}
        ig = {}
        lo = {}
        for pid in degr[s]:
            sc = scored[s][pid]
            for side in ("a", "b"):
                if sc[fa if side == "a" else fb]:
                    continue
                val = extract_answer(data[s][pid][f"prediction_{side}"])
                own_gold = str(registry_rows[pid]["answer_a" if side == "a" else "answer_b"])
                key = f"{pid}|{side}"
                is_gold = val is not None and val == own_gold
                if strict and is_gold:
                    lab = "gold_value_contract_invalid"
                else:
                    lab = classify_wrong(val, side, scenes[pid], registry_rows[pid])
                c[lab] += 1
                wv[key] = val
                ig[key] = is_gold
                lo[key] = bool(sc["correct_a" if side == "a" else "correct_b"])
        tax[s] = dict(c)
        wrong_vals[s] = wv
        slot_isgold[s] = ig
        slot_lenient_ok[s] = lo
    res = {"taxonomy": tax, "n_slots": {s: sum(tax[s].values()) for s in tax}}
    sw = {}
    for a, b in (("seed3", "seed1"), ("seed3", "seed2"), ("seed1", "seed2")):
        shared = set(wrong_vals[a]) & set(wrong_vals[b])
        same = [k for k in shared if wrong_vals[a][k] is not None and wrong_vals[a][k] == wrong_vals[b][k]]
        gold_same = [k for k in same if slot_isgold[a][k] and slot_isgold[b][k]]
        sw[f"{a}__{b}"] = {
            "shared": len(shared),
            "same": len(same),
            "rate": len(same) / len(shared),
            "same_that_are_gold_value": len(gold_same),
            "same_nongold": len(same) - len(gold_same),
            "shared_nongold": len([k for k in shared if not (slot_isgold[a][k] and slot_isgold[b][k])]),
        }
    sh3 = set(wrong_vals["seed1"]) & set(wrong_vals["seed2"]) & set(wrong_vals["seed3"])
    s3 = [k for k in sh3 if wrong_vals["seed1"][k] is not None and wrong_vals["seed1"][k] == wrong_vals["seed2"][k] == wrong_vals["seed3"][k]]
    sw["three"] = {"shared": len(sh3), "same": len(s3), "rate": len(s3) / len(sh3)}
    res["same_wrong"] = sw
    if strict:
        res["gold_slot_lenient_status"] = {
            s: {
                "gold_value_slots": sum(1 for k, v in slot_isgold[s].items() if v),
                "of_which_lenient_correct": sum(1 for k, v in slot_isgold[s].items() if v and slot_lenient_ok[s][k]),
                "of_which_lenient_wrong": sum(1 for k, v in slot_isgold[s].items() if v and not slot_lenient_ok[s][k]),
                "nongold_slots_lenient_correct": sum(
                    1 for k, v in slot_isgold[s].items() if not v and slot_lenient_ok[s][k]
                ),
                "total_strict_wrong_slots_lenient_correct": sum(1 for k in slot_lenient_ok[s] if slot_lenient_ok[s][k]),
            }
            for s in ("seed1", "seed2", "seed3")
        }
    return res, degr, base_correct


out["lenient"], degr_l, base_l = analyse(False)
out["strict"], degr_s, base_s = analyse(True)

# scene features recomputation
feats = {p: feature_vector(scenes[p]) for p in base_l}
d1, d2, d3 = degr_l["seed1"], degr_l["seed2"], degr_l["seed3"]
u3 = d1 | d2 | d3


def perm_p(group, rest, rng, nperm=10000):
    obs = abs(np.mean(group) - np.mean(rest))
    pooled = np.asarray(group + rest, dtype=np.float64)
    k = len(group)
    cnt = 0
    for _ in range(nperm):
        rng.shuffle(pooled)
        if abs(pooled[:k].mean() - pooled[k:].mean()) >= obs:
            cnt += 1
    return (cnt + 1) / (nperm + 1)


rng = np.random.default_rng(555000111)
sf = {}
for gname, gset in (("seed3_degraded", d3), ("three_seed_union", u3)):
    sf[gname] = {}
    for f in ("target_x_negative", "crowding_within_3", "min_label_levenshtein", "distance_to_nearest_point"):
        g = [feats[p][f] for p in sorted(gset)]
        r = [feats[p][f] for p in sorted(base_l - gset)]
        sf[gname][f] = {
            "group_mean": float(np.mean(g)), "group_n": len(g),
            "rest_mean": float(np.mean(r)), "rest_n": len(r),
            "p_indep_seed": perm_p(g, r, rng),
        }
out["scene_features_indep"] = sf

# McNemar between arms (lenient), 600 pairs
def mcnemar(a, b):
    ids = sorted(scored[a])
    b01 = sum(1 for p in ids if (not scored[a][p]["pair_correct"]) and scored[b][p]["pair_correct"])
    b10 = sum(1 for p in ids if scored[a][p]["pair_correct"] and (not scored[b][p]["pair_correct"]))
    n = b01 + b10
    k = min(b01, b10)
    pv = 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n))
    return {"b01": b01, "b10": b10, "p_exact": pv}


out["mcnemar_lenient"] = {
    "seed1_vs_seed3": mcnemar("seed1", "seed3"),
    "seed2_vs_seed3": mcnemar("seed2", "seed3"),
    "seed1_vs_seed2": mcnemar("seed1", "seed2"),
}
out["mcnemar_note"] = "b01 = a wrong & b correct; b10 = a correct & b wrong"

# multiple comparisons count on scene features
print(json.dumps(out, indent=1, sort_keys=True, default=str))
