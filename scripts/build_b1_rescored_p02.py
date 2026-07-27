#!/usr/bin/env python3
"""Rescore B1 under the P0.2-fixed scorer.

`reports/b1_trained_scoring_v1` scored the invariance types (`style_twin` 14/14
and `distractor_only` 16/16 equal-gold) with a single-gold workaround, because
the pre-fix scorer returned 0 on every equal-gold item. P0.2 removed the need for
that workaround; this recomputes the table from the same cached predictions with
the fixed scorer and reports what moved.

Roles are kept separate (I13): intervention types are never averaged together.
"""
import json
from collections import defaultdict
from pathlib import Path

from src.eval.fliptrack_metrics import pair_score

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
CELLS = {
    "base": (ROOT / "tmp/b1_base_final.txt").read_text().strip() + "/predictions.jsonl",
    "a1_seed1": "experiments/runs/b1_trained_a1_seed1_step100_real_an12_gpu4_20260726T155217Z/predictions.jsonl",
    "a1_seed2": "experiments/runs/b1_trained_a1_seed2_step100_real_an12_gpu5_20260726T155219Z/predictions.jsonl",
    "a2b_seed1": "experiments/runs/b1_trained_a2b_seed1_step100_real_an12_gpu6_20260726T155219Z/predictions.jsonl",
    "a3_seed1": "experiments/runs/b1_trained_a3_seed1_step100_real_an12_gpu7_20260726T155220Z/predictions.jsonl",
}
PUBLISHED_PAIR = {  # reports/b1_trained_scoring_v1.md, pre-fix
    "fact_read": {"base": 0.600, "a1_seed1": 0.550, "a1_seed2": 0.500, "a2b_seed1": 0.500, "a3_seed1": 0.500},
    "chained_premise": {"base": 0.000, "a1_seed1": 0.000, "a1_seed2": 0.000, "a2b_seed1": 0.000, "a3_seed1": 0.000},
    "binding_swap": {"base": 0.188, "a1_seed1": 0.188, "a1_seed2": 0.188, "a2b_seed1": 0.188, "a3_seed1": 0.188},
    "distractor_only": {"base": 0.438, "a1_seed1": 0.375, "a1_seed2": 0.438, "a2b_seed1": 0.438, "a3_seed1": 0.375},
    "style_twin": {"base": 0.643, "a1_seed1": 0.643, "a1_seed2": 0.714, "a2b_seed1": 0.571, "a3_seed1": 0.643},
    "prior_conflict": {"base": 0.143, "a1_seed1": 0.357, "a1_seed2": 0.286, "a2b_seed1": 0.429, "a3_seed1": 0.429},
}
manifest = {json.loads(l)["pair_id"]: json.loads(l)
            for l in (ROOT / "data/b1_geometry_track_v1/manifest.jsonl").read_text().splitlines() if l.strip()}
EQUAL_GOLD_TYPES = {"style_twin", "distractor_only"}

out = {"scorer": "P0.2-fixed", "cells": {}, "equal_gold_types": sorted(EQUAL_GOLD_TYPES)}
for cell, rel in CELLS.items():
    rows = [json.loads(l) for l in open(ROOT / rel) if l.strip()]
    by_type = defaultdict(lambda: {"pair": [], "member": []})
    for r in rows:
        man = manifest[r["pair_id"]]
        s = pair_score(dict(r, answer_a=man["answer_a"], answer_b=man["answer_b"]),
                       prompt_contract=None)
        t = man["intervention_type"]
        by_type[t]["pair"].append(bool(s["pair_correct"]))
        by_type[t]["member"] += [bool(s["correct_a"]), bool(s["correct_b"])]
    out["cells"][cell] = {t: {"n": len(v["pair"]),
                              "pair_correct": sum(v["pair"]) / len(v["pair"]),
                              "member_correct": sum(v["member"]) / len(v["member"])}
                          for t, v in by_type.items()}

TYPES = ["fact_read", "chained_premise", "binding_swap", "distractor_only", "style_twin", "prior_conflict"]
print(f"{'intervention':<18}{'cell':<11}{'published':>10}{'refixed':>9}{'delta':>8}")
moved = []
for t in TYPES:
    for cell in CELLS:
        new = out["cells"][cell][t]["pair_correct"]
        old = PUBLISHED_PAIR[t][cell]
        d = new - old
        flag = " <-- MOVED" if abs(d) > 0.001 else ""
        if flag:
            moved.append((t, cell, old, new))
        print(f"{t:<18}{cell:<11}{old:>10.3f}{new:>9.3f}{d:>+8.3f}{flag}")
out["moved"] = [{"intervention": t, "cell": c, "published": o, "refixed": n} for t, c, o, n in moved]
(ROOT / "reports/b1_rescored_p02_v1.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
print(f"\n{len(moved)} of {len(TYPES)*len(CELLS)} cells moved under the fixed scorer")
print("wrote reports/b1_rescored_p02_v1.json")
