#!/usr/bin/env python3
from pathlib import Path

p = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/reports/main_progress.md")
t = p.read_text()
lines = t.splitlines()
i = next(i for i, l in enumerate(lines) if l.startswith("| A5 |"))
lines[i] = ("| A5 | Mini-A5 CP vs matched same-data GRPO | running | **CP arm complete at 120/120** "
            "(`mini_a5_cp_main_an29_20260727T064527Z`, status complete, `global_step_120` written). "
            "**Matched member arm launched** on the now-free an29 0–7 "
            "(`mini_a5_member_main_an29_20260728T023715Z`); member config sha256 verified against the "
            "registration, storage guard pass. The two arms differ only in `pair_group_mode` and the "
            "reward callback. Readout on held-out-template pair accuracy, not margins; the "
            "advantage-tensor equivalence test must pass first. Gate-1 four-arm registration already "
            "merged behind it. |")
j = next(j for j, l in enumerate(lines) if l.startswith("| M5 |"))
lines[j] = ("| M5 | Long-horizon to step 400 | running | Step 393/400 on an12:0–3. Terminal readout "
            "**tooling built and armed** (`scripts/build_m5_terminal_readout.py`) implementing "
            "MAIN_PHASE_RULING R1 exactly: Delta on R19 **geometry** pair accuracy, 400 vs 100, "
            "item-paired bootstrap CI, FLAT/RISING/FALLING/INDETERMINATE. Steps 150/200/300 are "
            "descriptive and cannot select the endpoint. Step-100 endpoint resolved and verified at "
            "600 geometry rows. **Step 400 is terminal — no extension or rerun under any outcome.** |")
p.write_text("\n".join(lines) + "\n")
print("ledger updated")
