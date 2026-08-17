#!/usr/bin/env python3
"""Dump formatted tables from m5b_trajectory_v1.json + cross-run contract checks."""
from __future__ import annotations

import glob
import json
import os
import sys

ROOT = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
os.chdir(ROOT)
sys.path.insert(0, ROOT)

payload = json.load(open("reports/m5b_trajectory_v1.json", encoding="utf-8"))
STEPS = ["100", "150", "200", "300", "400"]

print("=== CROSS-RUN LOCKED-CONTRACT CHECKS (geo3k) ===")
fields = ["decoding", "format_prompt_sha256", "source_manifest_sha256", "prompt_contract_sha256", "parser_version", "scoring_mode", "symbolic_grader_guard_version", "symbolic_grader_timeout_seconds", "format_weight"]
seen = {}
for key, prov in payload["benchmark_axis"]["provenance"].items():
    row = json.loads(open(prov["per_item"], encoding="utf-8").readline())
    seen[key] = {f: row.get(f) for f in fields}
for f in fields:
    vals = {json.dumps(seen[k][f], sort_keys=True) for k in seen}
    print(f"  {f}: identical_across_runs={len(vals) == 1}  value={list(vals)[0] if len(vals) == 1 else sorted(vals)}")

print()
print("=== CROSS-RUN LOCKED-CONTRACT CHECKS (R19) ===")
for key, prov in payload["grounding_axis"]["provenance"].items():
    print(f"  {key:10s} data_manifest_hash={prov['data_manifest_hash']} image_mode={prov['image_mode']} max_new_tokens={prov['max_new_tokens']} shards={len(prov['shard_files'])} model={prov['model_revision']}")
for key in ("400_gray", "400_noise"):
    m = json.load(open(os.path.join(payload["grounding_axis"]["provenance"]["400"]["run"], "run_manifest.json"), encoding="utf-8"))
for key in ("400_gray", "400_noise"):
    run = {"400_gray": "experiments/runs/m5_r19_step400_gray_an12_20260728T054005Z", "400_noise": "experiments/runs/m5_r19_step400_noise_an12_20260728T054005Z"}[key]
    m = json.load(open(os.path.join(run, "run_manifest.json"), encoding="utf-8"))
    print(f"  {key:10s} data_manifest_hash={m.get('data_manifest_hash')} image_mode={m.get('image_mode')} max_new_tokens={m.get('max_new_tokens')} noise_seed={m.get('noise_seed')} model={m.get('model_path')}")

def fmt(x, sign=False):
    if x != x:
        return "nan"
    return f"{x:+.4f}" if sign else f"{x:.4f}"

b = payload["benchmark_axis"]
g = payload["grounding_axis"]

print()
print("=== BENCHMARK AXIS LEVELS (n=%d) ===" % b["n"])
print("step | acc_final [95% CI]           | acc_strict [95% CI]          | canonical [95% CI]           | contract_valid")
for k in ["base"] + STEPS:
    lv = b["levels"][k]
    def cell(m):
        e = lv[m]
        return f"{fmt(e['value'])} [{fmt(e['ci_low'])},{fmt(e['ci_high'])}]"
    print(f"{k:5s}| {cell('acc_final'):28s} | {cell('acc_strict'):28s} | {cell('canonical_correct'):28s} | {fmt(lv['contract_valid']['value'])}")

print()
print("=== GROUNDING AXIS LEVELS (n=%d) ===" % g["n"])
print("step | pair_correct [95% CI]        | strict_pair [95% CI]         | collapse | contract_valid")
for k in ["base"] + STEPS:
    lv = g["levels"][k]
    def cell(m):
        e = lv[m]
        return f"{fmt(e['value'])} [{fmt(e['ci_low'])},{fmt(e['ci_high'])}]"
    print(f"{k:5s}| {cell('pair_correct'):28s} | {cell('strict_pair_correct'):28s} | {fmt(lv['collapsed']['value'])}   | {fmt(lv['contract_valid']['value'])}")

print()
print("=== DELTAS vs STEP 100 ===")
for name, block, metrics in (
    ("BENCH acc_final", b["delta_vs_step100"], "acc_final"),
    ("BENCH acc_strict", b["delta_vs_step100"], "acc_strict"),
    ("BENCH canonical", b["delta_vs_step100_canonical"], None),
    ("GROUND pair_correct", g["delta_vs_step100"], "pair_correct"),
    ("GROUND strict_pair", g["delta_vs_step100"], "strict_pair_correct"),
):
    for k in ["base"] + STEPS:
        d = block[k] if metrics is None else block[k][metrics]
        print(f"  {name:20s} {k:5s} {fmt(d['delta'],1)} [{fmt(d['ci_low'],1)},{fmt(d['ci_high'],1)}] b01={int(d['b_gain_only'])} b10={int(d['b_loss_only'])} p={d['mcnemar_exact_p']:.4g}")
    print()

print("=== DELTAS vs FROZEN BASE ===")
for name, block, metrics in (
    ("BENCH acc_final", b["delta_vs_frozen_base"], "acc_final"),
    ("BENCH acc_strict", b["delta_vs_frozen_base"], "acc_strict"),
    ("BENCH canonical", b["delta_vs_frozen_base_canonical"], None),
    ("GROUND pair_correct", g["delta_vs_frozen_base"], "pair_correct"),
    ("GROUND strict_pair", g["delta_vs_frozen_base"], "strict_pair_correct"),
):
    for k in STEPS:
        d = block[k] if metrics is None else block[k][metrics]
        print(f"  {name:20s} {k:5s} {fmt(d['delta'],1)} [{fmt(d['ci_low'],1)},{fmt(d['ci_high'],1)}] b01={int(d['b_gain_only'])} b10={int(d['b_loss_only'])} p={d['mcnemar_exact_p']:.4g}")
    print()

print("=== BLIND FLOORS (step 400, geometry slice, n=600) ===")
for k, lv in payload["blind_floors_step400"].items():
    print(f"  {k}: pair_correct={fmt(lv['pair_correct']['value'])} [{fmt(lv['pair_correct']['ci_low'])},{fmt(lv['pair_correct']['ci_high'])}] "
          f"strict={fmt(lv['strict_pair_correct']['value'])} collapse={fmt(lv['collapsed']['value'])} contract_valid={fmt(lv['contract_valid']['value'])}")
    for m in ("pair_correct", "strict_pair_correct"):
        d = lv["delta_vs_step400_real"][m]
        print(f"      delta vs step400 real ({m}): {fmt(d['delta'],1)} [{fmt(d['ci_low'],1)},{fmt(d['ci_high'],1)}] p={d['mcnemar_exact_p']:.4g}")

print()
print("=== PLANNING-GREP COMPARISON ===")
plan_geo = {"100": 0.4309, "150": 0.4692, "200": 0.4892, "300": 0.4742, "400": 0.4443}
plan_gnd = {"100": 0.4800, "150": 0.4733, "200": 0.4633, "300": 0.4467, "400": 0.4133}
for k in STEPS:
    af = b["levels"][k]["acc_final"]["value"]
    cn = b["levels"][k]["canonical_correct"]["value"]
    print(f"  geo3k step {k}: planning={plan_geo[k]:.4f}  recomputed acc_final={af:.4f} (d={af - plan_geo[k]:+.4f})  canonical={cn:.4f} (d={cn - plan_geo[k]:+.4f})")
for k in STEPS:
    pc = g["levels"][k]["pair_correct"]["value"]
    print(f"  R19   step {k}: planning={plan_gnd[k]:.4f}  recomputed pair_correct={pc:.4f} (d={pc - plan_gnd[k]:+.4f})")
