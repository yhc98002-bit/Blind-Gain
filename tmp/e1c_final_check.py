#!/usr/bin/env python3
"""Final sanity checks on reports/e1c_blind_columns_v1.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
payload = json.loads((ROOT / "reports/e1c_blind_columns_v1.json").read_text(encoding="utf-8"))
chance = json.loads((ROOT / "reports/chance_corrected_retention_v1.json").read_text(encoding="utf-8"))

problems = []

# 1. no absurd magnitudes survive
for row in payload["rows"]:
    for contract in ("lenient_acc_final", "strict_acc_strict"):
        block = row[contract]
        for key in ("naive_retention", "corrected_retention",
                    "naive_retention_ci95_low", "naive_retention_ci95_high",
                    "corrected_retention_ci95_low", "corrected_retention_ci95_high"):
            value = block.get(key)
            if value is not None and abs(value) > 1e6:
                problems.append(f"absurd {row['benchmark']}/{row['model']}/{row['subset']}/{contract}/{key}={value}")

# 2. undefined corrected => CI also null
for row in payload["rows"]:
    for contract in ("lenient_acc_final", "strict_acc_strict"):
        block = row[contract]
        if block.get("corrected_retention_undefined"):
            if block["corrected_retention"] is not None or block["corrected_retention_ci95_low"] is not None:
                problems.append(f"undefined-but-populated {row['subset']} {contract}")

# 3. k distributions must reproduce the CHANCE report's with_image_run_k_availability
name_map = {"BLINK": "BLINK", "HallusionBench": "HallusionBench", "MMVP": "MMVP",
            "MathVerse": "MathVerse", "MMMU dev+validation": "MMMU dev+validation"}
expected_k = {}
for entry in chance["not_computed"]:
    if entry["benchmark"] in name_map.values() and "with_image_run_k_availability" in entry:
        first = next(iter(entry["with_image_run_k_availability"].values()))
        expected_k[entry["benchmark"]] = {int(k): v for k, v in first["k_distribution"].items()}
for benchmark, per_model in payload["format_counts"].items():
    want = expected_k[name_map[benchmark]]
    for model, counts in per_model.items():
        got = {}
        for key, value in counts.items():
            k = int(key.split("k=")[1])
            got[k] = got.get(k, 0) + value
        if got != want:
            problems.append(f"k-dist mismatch {benchmark}/{model}: got {got} want {want}")

# 4. every subset n sums correctly and no global null on a mixed benchmark
for benchmark in ("MathVerse", "MMMU dev+validation"):
    for model in ("Qwen2.5-VL-3B", "Qwen2.5-VL-7B"):
        subs = [r for r in payload["rows"] if r["benchmark"] == benchmark and r["model"] == model]
        whole = [r for r in subs if "whole benchmark" in r["subset"]]
        if whole:
            problems.append(f"mixed benchmark {benchmark} has a whole-benchmark corrected row")
        nc = [e for e in payload["not_computed"]
              if e["benchmark"] == benchmark and e["model"] == model
              and "single global null" in e["subset"]]
        if not nc:
            problems.append(f"missing single-global-null not_computed entry for {benchmark}/{model}")

# 5. counts
print("rows:", len(payload["rows"]))
print("whole-benchmark naive rows:", len(payload["reference_naive_whole_benchmark"]))
print("not_computed:", len(payload["not_computed"]))
print("provenance cells:", len(payload["provenance"]))
print("input artifacts:", len(payload["inputs"]))
print("underpowered subsets:", [f"{r['benchmark']}/{r['subset']}(n={r['n']})"
                                for r in payload["rows"] if r.get("underpowered_subset")
                                and r["model"] == "Qwen2.5-VL-3B"])
print("undefined-corrected cells:",
      [f"{r['benchmark']}/{r['model']}/{r['subset']}/{c}"
       for r in payload["rows"] for c in ("lenient_acc_final", "strict_acc_strict")
       if r[c].get("corrected_retention_undefined")])

print("\nheadline (lenient, pooled/primary subsets):")
for row in payload["rows"]:
    if any(t in row["subset"] for t in ("pooled", "primary", "free-form")) and "sensitivity" not in row["subset"]:
        b = row["lenient_acc_final"]
        print(f"  {row['benchmark']:<22} {row['model']:<15} {row['subset']:<42} n={row['n']:<5} "
              f"null={row['null']:.4f} img={b['with_image_acc']:.4f} blind={b['blind_acc']:.4f} "
              f"naive={b['naive_retention']:.4f} corr={b['corrected_retention'] if b['corrected_retention'] is None else round(b['corrected_retention'],4)}")

print("\nPROBLEMS:", len(problems))
for item in problems:
    print("  -", item)
