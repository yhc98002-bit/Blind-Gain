#!/usr/bin/env python3
"""Reconnaissance for m5b trajectory: verify joins, counts, equal-gold, contract ids."""
from __future__ import annotations

import json
import glob
import os
import sys

ROOT = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT  # noqa: E402
from src.eval.fliptrack_metrics import golds_equivalent  # noqa: E402

GEO_RUNS = {
    "base": "experiments/runs/blind_solvability_v2_guarded_rescore_geo3k_filtered_v2_retry_real_login_20260712T050905Z/per_item.jsonl",
    "100": "experiments/runs/blind_solvability_v2_guarded_rescore_anchor_step100_geo3k_real_login_20260712T082107Z/per_item.jsonl",
    "150": "experiments/runs/m5_geo3k_step150_an12_gpu4_20260718T051839Z/per_item.jsonl",
    "200": "experiments/runs/m5_geo3k_step200_an29_gpu4_20260722T141052Z/per_item.jsonl",
    "300": "experiments/runs/m5_geo3k_step300_an12_gpu0_20260726T083303Z/per_item.jsonl",
    "400": "experiments/runs/m5_geo3k_step400_an12_gpu0_20260728T053115Z/per_item.jsonl",
}

R19_RUNS = {
    "base": "experiments/runs/fliptrack_v02r19_packaged_qwen25vl3b_real_an29_20260710T142716Z/shards/*.jsonl",
    "100": "experiments/runs/fliptrack_v02r19_anchor_step100_real_an12_20260712T085144Z/shards/*.jsonl",
    "150": "experiments/runs/m5_r19_step150_real_an12_20260718T051758Z/shards/*.jsonl",
    "200": "experiments/runs/m5_r19_step200_real_an29_20260722T141033Z/shards/*.jsonl",
    "300": "experiments/runs/m5_r19_step300_real_an12_20260726T083248Z/shards/*.jsonl",
    "400": "experiments/runs/m5_r19_step400_real_an12_20260728T052218Z/shards/*.jsonl",
    "400_gray": "experiments/runs/m5_r19_step400_gray_an12_20260728T054005Z/shards/*.jsonl",
    "400_noise": "experiments/runs/m5_r19_step400_noise_an12_20260728T054005Z/shards/*.jsonl",
}


def load_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


print("DEFAULT_PROMPT_CONTRACT sha256:", DEFAULT_PROMPT_CONTRACT.sha256)
print()
print("=== GEO3K ===")
geo = {}
for key, path in GEO_RUNS.items():
    rows = load_jsonl(path)
    test = [r for r in rows if r.get("split") == "test"]
    geo[key] = test
    resp_key = "greedy_response"
    has_pilot = "greedy_correct" in rows[0] or "acc_final" in rows[0]
    print(
        f"{key:5s} total={len(rows):5d} test={len(test):4d} "
        f"contract={rows[0].get('prompt_contract_sha256')} parser={rows[0].get('parser_version')} "
        f"scoring={rows[0].get('scoring_mode')} schema={rows[0].get('schema_version')}"
    )

ref = {(r["split"], r["row_index"]): r for r in geo["100"]}
for key in GEO_RUNS:
    cur = {(r["split"], r["row_index"]): r for r in geo[key]}
    common = set(ref) & set(cur)
    gt_mismatch = sum(1 for k in common if str(ref[k]["ground_truth"]) != str(cur[k]["ground_truth"]))
    prob_mismatch = sum(1 for k in common if str(ref[k]["problem"]) != str(cur[k]["problem"]))
    qid_mismatch = sum(1 for k in common if str(ref[k].get("qid")) != str(cur[k].get("qid")))
    img_mismatch = sum(1 for k in common if json.dumps(ref[k].get("image_sha256")) != json.dumps(cur[k].get("image_sha256")))
    print(f"  join {key:5s}: n_common={len(common)} gt_mismatch={gt_mismatch} prob_mismatch={prob_mismatch} qid_mismatch={qid_mismatch} img_mismatch={img_mismatch}")

print()
print("=== R19 ===")
r19 = {}
for key, pat in R19_RUNS.items():
    files = sorted(glob.glob(pat))
    rows = []
    for f in files:
        rows.extend(load_jsonl(f))
    geom = [r for r in rows if r.get("category") == "geometry_coordinate_indexing"]
    r19[key] = geom
    eq = sum(1 for r in geom if golds_equivalent(r["answer_a"], r["answer_b"]))
    print(
        f"{key:10s} files={len(files)} total={len(rows):5d} geom={len(geom):4d} equal_gold={eq} "
        f"contract={rows[0].get('prompt_contract_sha256')} parser={rows[0].get('parser_version')} "
        f"schema={rows[0].get('schema_version')}"
    )

refp = {r["pair_id"]: r for r in r19["100"]}
for key in R19_RUNS:
    cur = {r["pair_id"]: r for r in r19[key]}
    common = set(refp) & set(cur)
    a_mis = sum(1 for k in common if str(refp[k]["answer_a"]) != str(cur[k]["answer_a"]))
    b_mis = sum(1 for k in common if str(refp[k]["answer_b"]) != str(cur[k]["answer_b"]))
    q_mis = sum(1 for k in common if str(refp[k]["question"]) != str(cur[k]["question"]))
    tmpl = sorted({str(r.get("template_id")) for r in cur.values()})
    print(f"  join {key:10s}: n_common={len(common)} dup={len(r19[key]) - len(cur)} ans_a_mis={a_mis} ans_b_mis={b_mis} q_mis={q_mis} templates={len(tmpl)}")

print()
print("sample geometry row keys:", sorted(r19["base"][0].keys()))
print("base row prompt_contract_id:", r19["base"][0].get("prompt_contract_id"))
