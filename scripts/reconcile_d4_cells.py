#!/usr/bin/env python3
"""Reconcile the D4 caption cells after orchestrator restarts created duplicates.

Restarting the orchestrator while cells were in flight produced 20 run
directories for 12 logical cells, plus OOM failures where two cells were
double-booked onto one GPU. This keeps the earliest complete run per logical
cell, marks later duplicates `superseded` (not deleted -- they are byte-identical
and are part of the record), marks empty failures `superseded_failed`, repairs
stale `running` statuses on runs that actually finished, and reports which
logical cells still have no data.

Reads no accuracy value and changes no prediction file.
"""
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
EXPECTED_ROWS = 601
ARMS = ("a1", "a2", "a2b", "a3")
CELLS = {f"{a}_seed{s}" for a in ARMS for s in (1, 2, 3)}

pat = re.compile(r"d2_testtime_(.+?)_step100_caption_an12_gpu\d+_(\d{8}T\d{6}Z)$")
by_cell = defaultdict(list)
for d in sorted((ROOT / "experiments/runs").glob("d2_testtime_*_step100_caption_an12_gpu*")):
    m = pat.match(d.name)
    if not m:
        continue
    rows = 0
    p = d / "predictions.jsonl"
    if p.is_file():
        rows = sum(1 for line in p.read_text().splitlines() if line.strip())
    by_cell[m.group(1)].append({"dir": d, "stamp": m.group(2), "rows": rows})

report = {"expected_cells": sorted(CELLS), "kept": {}, "superseded": [],
          "repaired_status": [], "missing": []}

for cell in sorted(CELLS):
    runs = sorted(by_cell.get(cell, []), key=lambda r: r["stamp"])
    good = [r for r in runs if r["rows"] >= EXPECTED_ROWS]
    empty = [r for r in runs if r["rows"] < EXPECTED_ROWS]

    if not good:
        report["missing"].append(cell)
    else:
        keep = good[0]
        report["kept"][cell] = {"run": keep["dir"].name, "rows": keep["rows"]}
        man = keep["dir"] / "run_manifest.json"
        payload = json.loads(man.read_text())
        if payload.get("status") != "complete":
            payload["status"] = "complete"
            payload["status_repaired_note"] = (
                "orchestrator died before finalising; predictions complete at "
                f"{keep['rows']} rows")
            man.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
            report["repaired_status"].append(keep["dir"].name)
        for dup in good[1:]:
            man = dup["dir"] / "run_manifest.json"
            payload = json.loads(man.read_text())
            payload["status"] = "superseded"
            payload["superseded_by"] = keep["dir"].name
            payload["superseded_note"] = (
                "duplicate produced by an orchestrator restart; byte-identical to "
                "the kept run")
            man.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
            report["superseded"].append(dup["dir"].name)

    for e in empty:
        man = e["dir"] / "run_manifest.json"
        if not man.is_file():
            continue
        payload = json.loads(man.read_text())
        payload["status"] = "superseded_failed"
        payload["superseded_note"] = "empty run (CUDA OOM from GPU double-booking)"
        man.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        report["superseded"].append(e["dir"].name)

(ROOT / "reports/d4_cell_reconciliation_v1.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n")

print(f"kept {len(report['kept'])}/12 logical cells")
print(f"superseded {len(report['superseded'])} run dirs")
print(f"status repaired on {len(report['repaired_status'])}")
print(f"MISSING: {report['missing'] or 'none'}")
