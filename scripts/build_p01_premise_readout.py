#!/usr/bin/env python3
"""P0.1 — premise-probe readout, five separate numbers.

Required by EXPERIMENT_TODO Part 2B and PAPER2 §4 Track 4: premise accuracy,
reasoning-given-correct-premise, member accuracy, pair accuracy, and
premise-transition accuracy, reported separately and never aggregated.

Premise predictions come from the registered probe run; final-answer predictions
are the cached B1 runs on the identical 20 chained_premise items. Everything is
rescored in-process with the P0.2-fixed scorer, because the premise manifest is
equal-gold by construction and the pre-fix scorer returns 0.000 on every such
item regardless of content.
"""
import glob
import json
from pathlib import Path

from src.eval.fliptrack_metrics import pair_score

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
PROBE = Path((ROOT / "tmp/b1_premise_probe.txt").read_text().strip())
CONTRACT = None  # resolves to DEFAULT_PROMPT_CONTRACT (contract_id=answer-tags-v1)

FINAL_RUNS = {
    "a1_seed1_step100": "experiments/runs/b1_trained_a1_seed1_step100_real_an12_gpu4_20260726T155217Z",
    "a1_seed2_step100": "experiments/runs/b1_trained_a1_seed2_step100_real_an12_gpu5_20260726T155219Z",
    "a2b_seed1_step100": "experiments/runs/b1_trained_a2b_seed1_step100_real_an12_gpu6_20260726T155219Z",
    "a3_seed1_step100": "experiments/runs/b1_trained_a3_seed1_step100_real_an12_gpu7_20260726T155220Z",
}
BASE_FINAL_GLOB = open(ROOT / "tmp/b1_base_final.txt").read().strip() + "/predictions.jsonl"

manifest = {json.loads(l)["pair_id"]: json.loads(l)
            for l in (ROOT / "data/b1_geometry_track_v1/manifest.jsonl").read_text().splitlines() if l.strip()}
CHAINED = sorted(p for p, r in manifest.items() if r["intervention_type"] == "chained_premise")
assert len(CHAINED) == 20, len(CHAINED)


def load(path_or_glob):
    files = sorted(glob.glob(str(ROOT / path_or_glob)))
    out = {}
    for f in files:
        for l in open(f):
            if l.strip():
                r = json.loads(l)
                out[r["pair_id"]] = r
    return out


def rescore(row, gold_a, gold_b):
    r = dict(row)
    r["answer_a"], r["answer_b"] = gold_a, gold_b
    return pair_score(r, prompt_contract=CONTRACT)


report = {"schema_version": 1, "n_items": len(CHAINED),
          "registration": "docs/registered_b1_premise_probe_v1.md",
          "scorer": "P0.2-fixed (equal-gold branch); premise manifest is equal-gold by construction",
          "probe_run": str(PROBE), "cells": {}}

final_sets = {"base": load(BASE_FINAL_GLOB)}
for k, v in FINAL_RUNS.items():
    final_sets[k] = load(f"{v}/predictions.jsonl")

for cell in ("base", "a1_seed1_step100", "a1_seed2_step100", "a2b_seed1_step100", "a3_seed1_step100"):
    prem_rows = load(f"{PROBE.relative_to(ROOT)}/{cell}/predictions.jsonl")
    fin_rows = final_sets[cell]
    missing = [p for p in CHAINED if p not in prem_rows or p not in fin_rows]
    if missing:
        raise SystemExit(f"FAIL {cell}: missing {len(missing)} items e.g. {missing[:2]}")

    pm = pf = fm = fp = trans = 0
    reason_num = reason_den = 0
    for pid in CHAINED:
        man = manifest[pid]
        pa = man["premise_answer"]
        ps = rescore(prem_rows[pid], pa, pa)          # equal-gold: premise invariant
        fs = rescore(fin_rows[pid], man["answer_a"], man["answer_b"])  # causal: distinct golds

        pm += bool(ps["correct_a"]) + bool(ps["correct_b"])
        pf += bool(ps["pair_correct"])
        fm += bool(fs["correct_a"]) + bool(fs["correct_b"])
        fp += bool(fs["pair_correct"])
        # premise transition: the premise is invariant here, so a correct
        # transition means the same premise is produced on both members
        same = (ps.get("extracted_answer_a") or "").strip().lower() == \
               (ps.get("extracted_answer_b") or "").strip().lower()
        trans += bool(same and ps["pair_correct"])
        # reasoning | correct premise, evaluated per member
        for side in ("a", "b"):
            if ps[f"correct_{side}"]:
                reason_den += 1
                reason_num += bool(fs[f"correct_{side}"])

    n, nm = len(CHAINED), 2 * len(CHAINED)
    report["cells"][cell] = {
        "premise_member_accuracy": pm / nm,
        "premise_pair_accuracy": pf / n,
        "premise_transition_accuracy": trans / n,
        "final_member_accuracy": fm / nm,
        "final_pair_accuracy": fp / n,
        "reasoning_given_correct_premise": (reason_num / reason_den) if reason_den else None,
        "reasoning_denominator": reason_den,
    }

(ROOT / "reports/p01_premise_probe_v1.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

hdr = f"{'cell':<20}{'premise_mem':>12}{'premise_pair':>13}{'transition':>11}{'final_mem':>10}{'final_pair':>11}{'reason|prem':>12}{'n_den':>6}"
print(hdr)
for c, v in report["cells"].items():
    rg = v["reasoning_given_correct_premise"]
    print(f"{c:<20}{v['premise_member_accuracy']:>12.3f}{v['premise_pair_accuracy']:>13.3f}"
          f"{v['premise_transition_accuracy']:>11.3f}{v['final_member_accuracy']:>10.3f}"
          f"{v['final_pair_accuracy']:>11.3f}"
          f"{('n/a' if rg is None else f'{rg:.3f}'):>12}{v['reasoning_denominator']:>6}")
print("\nwrote reports/p01_premise_probe_v1.json")
