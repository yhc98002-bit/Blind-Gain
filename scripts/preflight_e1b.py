#!/usr/bin/env python3
"""E1b preflight — NON-EVALUATIVE loader and resource check.

Runs before the E1b registration is merged. It deliberately does NOT load a
model, generate anything, or read any prediction file: it only checks that the
configs are well-formed, the checkpoints and inputs exist, the row counts match
the base rows E1b will be compared against, and that nothing would collide or
stray onto M7's GPUs.

Explicit non-goals, so this cannot become a back door to peeking at results:
  - no model is instantiated
  - no *.jsonl prediction or metrics file is opened
  - no accuracy is computed or printed
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
CFG = ROOT / "configs/eval/e1b"
FORBIDDEN_GPUS = {0, 1, 2, 3}

# base row counts from reports/base_external_benchmarks.md, so E1b is comparable
EXPECTED_ROWS = {"mmstar": 1500, "mathvista": 999}

problems, checked = [], 0
configs = sorted(CFG.glob("e1b_*.json"))
if not configs:
    sys.exit("no E1b configs found; run build_e1b_configs.py first")

seen_outputs = {}
for p in configs:
    checked += 1
    try:
        c = json.loads(p.read_text())
    except Exception as e:
        problems.append(f"{p.name}: unparseable ({e})")
        continue

    meta = c.get("_e1b")
    if not meta:
        problems.append(f"{p.name}: missing _e1b provenance block")
        continue

    # checkpoint present
    ck = Path(meta["checkpoint"])
    if not ck.is_dir():
        problems.append(f"{p.name}: checkpoint absent {ck}")
    elif not (ck / "config.json").is_file():
        problems.append(f"{p.name}: checkpoint has no config.json {ck}")

    # resource isolation declared and sane
    iso = meta.get("resource_isolation", {})
    if set(iso.get("allowed_gpus", [])) & FORBIDDEN_GPUS:
        problems.append(f"{p.name}: allowed_gpus overlaps M7's GPUs 0-3")
    if not set(iso.get("forbidden_gpus", [])) >= FORBIDDEN_GPUS:
        problems.append(f"{p.name}: does not declare GPUs 0-3 forbidden")

    # input present, and row count matches the base row it will be compared to
    if meta["condition"] == "blind":
        tsv = ROOT / c["input_tsv"]
        if not tsv.is_file():
            problems.append(f"{p.name}: input_tsv absent {tsv}")
        else:
            # TSV fields contain embedded newlines, so a line count is NOT a row
            # count: MMStar is 2106 lines / 1500 records, MathVista 4421 / 999.
            # Parse it properly or this check invents a comparability problem.
            import pandas as pd
            n = len(pd.read_csv(tsv, sep="	"))
            exp = EXPECTED_ROWS[meta["benchmark"]]
            if n != exp:
                problems.append(f"{p.name}: {n} rows, base used {exp}")
        if not c.get("model_path"):
            problems.append(f"{p.name}: blind config missing model_path")
    else:
        models = c.get("model", {})
        if len(models) != 1:
            problems.append(f"{p.name}: expected exactly one model entry")
        else:
            mp = next(iter(models.values())).get("model_path", "")
            if mp != meta["checkpoint"]:
                problems.append(f"{p.name}: model_path does not match _e1b.checkpoint")

    key = (meta["arm"], meta["seed"], meta["benchmark"], meta["condition"])
    if key in seen_outputs:
        problems.append(f"{p.name}: duplicate cell, collides with {seen_outputs[key]}")
    seen_outputs[key] = p.name

# full grid present
expected_cells = {(a, s, b, cond)
                  for a in ("a1_real", "a2_gray", "a2b_noimage", "a3_caption")
                  for s in (1, 2, 3) for b in EXPECTED_ROWS for cond in ("image", "blind")}
missing_cells = sorted(expected_cells - set(seen_outputs))
if missing_cells:
    problems.append(f"{len(missing_cells)} grid cells missing, e.g. {missing_cells[:3]}")

# M7 must still hold 0-3 and E1b's GPUs must be free
try:
    q = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=15", "an12",
         "nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits"],
        capture_output=True, text=True, timeout=40).stdout
    used = {int(l.split(",")[0]): int(l.split(",")[1]) for l in q.strip().splitlines() if l.strip()}
    busy_trainer = [g for g in (0, 1, 2, 3) if used.get(g, 0) > 5000]
    busy_e1b = [g for g in (4, 5, 6, 7) if used.get(g, 0) > 5000]
    print(f"an12 GPUs 0-3 in use by M7: {busy_trainer or 'NONE (M7 not running?)'}")
    print(f"an12 GPUs 4-7 free for E1b: {[g for g in (4,5,6,7) if g not in busy_e1b]}")
    if busy_e1b:
        problems.append(f"E1b GPUs already occupied: {busy_e1b}")
except Exception as e:
    print(f"(GPU probe skipped: {e})")

print(f"\nchecked {checked} configs, {len(seen_outputs)} distinct cells "
      f"of {len(expected_cells)} expected")
if problems:
    print(f"\nPREFLIGHT FAIL ({len(problems)}):")
    for p_ in problems:
        print("  - " + p_)
    sys.exit(1)
print("\nPREFLIGHT PASS — configs well-formed, checkpoints and inputs present, "
      "grid complete, resource isolation declared, no predictions read.")
