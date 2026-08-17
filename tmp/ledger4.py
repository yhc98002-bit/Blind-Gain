#!/usr/bin/env python3
from pathlib import Path
p = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/reports/main_progress.md")
t = p.read_text()
old = [l for l in t.splitlines() if l.startswith("| CL |")][0]
new = ("| CL | Cue ladder on existing checkpoints (F4b) | fail | Gate 1 pass (exact reproduces R19). "
       "Gate 2 **fails under both rung designs** (v1 0.4533/0.1367/0.6167; v2 0.3333/0.6100/0.6167), "
       "so branches (a)/(b) are void and the 12 arm cells were deliberately **not scored** — "
       "F2d's prediction is untested, not refuted. Cause: the on-point annotation is a cue *and* an "
       "occluder (+0.317 when it is the sole identifier, −0.277 when the series is named). "
       "Instrument findings stand: R19's nine-series marker occludes the datum it localizes; at 3B a "
       "correct or misleading visual cue adds ~nothing once text names the series. v3 redesign "
       "specified, not attempted this round. `reports/cue_ladder_readout_v1.*`. |")
p.write_text(t.replace(old, new, 1))
print("ledger updated")
