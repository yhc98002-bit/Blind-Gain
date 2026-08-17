#!/usr/bin/env python3
"""Completion verification for the R3 / M7 step-0 held-out base evaluations."""
import json
import sys
from pathlib import Path

EXPECTED_ROWS = 4239
REQUIRED = ["q_i", "p_i_jeffreys", "sample_correct_count", "greedy_canonical_correct"]
EXPECTED_SRC_SHA = "c0097102496b3d979f77fb1f19e4c277d0de6886f57683917613c4e03a898432"

ok_all = True
for run_dir in [l.strip() for l in Path("tmp/m7_step0_run_dirs.txt").read_text().splitlines() if l.strip()]:
    d = Path(run_dir)
    problems = []
    manifest = json.loads((d / "run_manifest.json").read_text())
    status = manifest.get("status")
    exit_code = manifest.get("exit_code")
    if status != "complete":
        problems.append(f"status={status}")
    if exit_code != 0:
        problems.append(f"exit_code={exit_code}")

    per_item = d / "per_item.jsonl"
    rows = []
    if per_item.exists():
        with per_item.open() as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
    else:
        problems.append("per_item.jsonl absent")

    if len(rows) != EXPECTED_ROWS:
        problems.append(f"rows={len(rows)} != {EXPECTED_ROWS}")
    if rows:
        missing_fields = sorted({f for r in rows for f in REQUIRED if f not in r})
        if missing_fields:
            problems.append(f"missing fields: {missing_fields}")
        qids = {r.get("qid") for r in rows}
        if len(qids) != len(rows):
            problems.append(f"duplicate qids: {len(rows) - len(qids)}")
        splits = {r.get("split") for r in rows}
        if splits != {"train"}:
            problems.append(f"splits={splits}")
        conds = {r.get("condition") for r in rows}
        if len(conds) != 1:
            problems.append(f"mixed conditions: {conds}")
        shas = {r.get("source_manifest_sha256") for r in rows}
        if shas != {EXPECTED_SRC_SHA}:
            problems.append(f"source_manifest_sha256={shas}")
        nulls = sum(1 for r in rows if any(r.get(f) is None for f in REQUIRED))
        if nulls:
            problems.append(f"{nulls} rows with a null required field")
        mean_q = sum(float(r["q_i"]) for r in rows) / len(rows)
        mean_acc = sum(1.0 for r in rows if r["greedy_canonical_correct"]) / len(rows)
    else:
        mean_q = mean_acc = float("nan")

    verdict = "PASS" if not problems else "FAIL"
    ok_all &= not problems
    print(f"{verdict} {d.name}")
    print(f"    condition={manifest.get('condition')} gpu={manifest.get('gpu_ids')} "
          f"status={status} exit={exit_code} rows={len(rows)}")
    print(f"    start={manifest.get('start_time_utc')} end={manifest.get('end_time_utc')}")
    print(f"    q_bar(mean q_i)={mean_q:.6f}  Acc_final(greedy_canonical_correct)={mean_acc:.6f}")
    for p in problems:
        print(f"    PROBLEM: {p}")

print("ALL FOUR VERIFIED" if ok_all else "VERIFICATION FAILED")
sys.exit(0 if ok_all else 1)
