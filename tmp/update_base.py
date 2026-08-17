#!/usr/bin/env python3
from pathlib import Path

p = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/reports/RESULTS.md")
t = p.read_text()
old = ("Caveat carried: the step-0 minuend is a single pinned legacy run shared by all\n"
       "three seeds, so seed spread reflects step-100 variation only.")
new = ("**Baseline verified (2026-07-27).** The audit flagged that the step-0 minuend\n"
       "was a single pinned legacy run, shared across all three seeds and measured\n"
       "under a possibly different harness build. It has now been re-measured from\n"
       "scratch on the locked 1,200-pair R19 manifest with the current harness and\n"
       "reproduces **exactly**: geometry lenient 0.4717 and strict 0.4433, matching\n"
       "the pinned values to four decimals (run `fliptrack_base_remeasure_an12_20260727T124803Z`).\n"
       "The minuend is therefore verified rather than inherited. The residual caveat\n"
       "stands that it is still a single measurement, so seed-level spread reflects\n"
       "step-100 variation only.")
if new.split("\n")[0] in t:
    print("already updated")
    raise SystemExit(0)
assert t.count(old) == 1, f"anchor count {t.count(old)}"
p.write_text(t.replace(old, new, 1))
print("RESULTS.md: baseline caveat resolved")
