#!/usr/bin/env python3
"""Correct the stale C5 row in reports/main_progress.md.

The row claims C5 was re-scoped to A1 and A2b; the PI decision retained
A2-gray by the fired precommitted M8 fork rule (Extension 4). Exact-match
replacement so a concurrent edit anywhere else in the file is untouched.
"""
from pathlib import Path

PATH = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/reports/main_progress.md")
OLD = (
    "| C5 | 7B access pair | blocked | Re-scoped to A1 and A2b only, one seed. "
    "Awaiting a node. |"
)
NEW = (
    "| C5 | 7B access pair | blocked | Re-scoped to A1 and **A2-gray** only, one seed "
    "(not A2b: A2-gray is retained by the fired precommitted M8 fork rule, "
    "Extension 4 of `docs/registered_extensions_v1.md` — gray 0.2456 vs no-image "
    "0.1824, non-overlapping 95% intervals; a rule-citation, not preference). "
    "Authored + registered 2026-07-30: `docs/registered_c5_7b_access_pair_v1.md`, "
    "`reports/c5_arm_configs_v1.json`, `scripts/launch_c5_7b_arm.sh`. No 7B base "
    "geo3k eval exists yet; required before readout. Launch when M7 frees GPUs "
    "(~2026-08-02). |"
)

text = PATH.read_text(encoding="utf-8")
count = text.count(OLD)
if count != 1:
    raise SystemExit(f"expected exactly one stale C5 row, found {count}; aborting untouched")
PATH.write_text(text.replace(OLD, NEW), encoding="utf-8")
print("C5 row corrected")
