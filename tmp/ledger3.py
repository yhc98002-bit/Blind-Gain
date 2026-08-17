#!/usr/bin/env python3
from pathlib import Path

p = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/reports/main_progress.md")
t = p.read_text()

subs = [
    ('| M11 | Cross-family completion | blocked | State ambiguous in prior ledgers between "validity confirmed" and "full matrix pending"; must be resolved before any claim. |',
     "| M11 | Cross-family completion | blocked | **Ambiguity resolved 2026-07-27.** Both readings were partly right: six *smoke* cells validate the instrument cross-family (no-image collapse, caption ≤0.013) and are what PAPER1 §5's dossier cites; the **18-cell full matrix never ran**. Queue `m11_generalization_full_recovery_login_20260715T182317Z` has manifest status `fail` and its watcher (pid 177427) is dead, despite status report v10 describing it as running. No model performance may be reported from M11 until the full matrix and machine audit complete. Relaunch needs a node and is not scheduled. |"),
    ("| CL | Cue ladder on existing checkpoints (F4b) | running | Registered `docs/registered_cue_ladder_v1.md` before any scoring. Four rungs replayed from the frozen R19 nine-series `pair_seed`s, so the ladder is item-paired with R19; replay integrity gate passes 300/300. Scoring next on free GPUs. |",
     "| CL | Cue ladder on existing checkpoints (F4b) | running | v1 gate 1 **pass** (exact reproduces R19, paired delta +0.0167, CI covers zero); v1 gate 2 **FAIL** (base not monotone: exact 0.4533, region 0.1367, none 0.6167) → branches (a)/(b) void. Cause was a design fault — v1 varied question form *and* annotation. v2 amendment registered: all rungs share the named-series question, only annotation varies. `named_exact`/`named_region` built (300/300 replay integrity); base gate running. No third attempt this round if v2 also fails. |"),
]
for old, new in subs:
    if old not in t:
        raise SystemExit(f"anchor missing: {old[:70]}")
    t = t.replace(old, new, 1)

t = t.replace(
    "- The B1 premise probe's on-disk `metrics.json` files read 0.000 for every cell\n  under the pre-fix scorer and are void; cite the rescored readout instead.",
    "- The B1 premise probe's on-disk `metrics.json` files read 0.000 for every cell\n"
    "  under the pre-fix scorer and are void; cite the rescored readout instead.\n"
    "- `reports/m11_execution_queue_status_v10.md` describes its queue as `running`;\n"
    "  the run manifest says `fail` and the watcher is dead. Status reports are not\n"
    "  a substitute for checking the manifest.")
p.write_text(t)
print("ledger updated")
