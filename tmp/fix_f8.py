#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
p = ROOT / "reports/RESULTS.md"
t = p.read_text()

step = "?"
log = ROOT / "checkpoints/mini_a5/mini_a5_same_data_seed1/experiment_log.jsonl"
if log.is_file():
    rows = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
    if rows:
        step = rows[-1].get("step")

old = """matched member arm at 17/120 on an29."""
new = f"""matched member arm at {step}/120 on an29."""
assert t.count(old) == 1
t = t.replace(old, new, 1)

old2 = "audit of all six conditions (`scripts/audit_mini_a5_acceptance.py`) must return"
new2 = ("audit of all six conditions (`scripts/audit_mini_a5_acceptance.py`, emitting\n"
        "`reports/mini_a5_acceptance_audit_v1.json`) must return")
assert t.count(old2) == 1
t = t.replace(old2, new2, 1)

p.write_text(t)
print(f"F8 section updated: member arm {step}/120, acceptance artifact cited")
