#!/usr/bin/env python3
"""Correct the Deviations Log row that cites the cleaned first-attempt run ids,
and mark the stray aborted arm-1 run dir instead of deleting it."""
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")

# --- 1. fix the run-id citation in the amendment's Deviations Log ------------
p = ROOT / "docs/registered_m7_amendment_v1.md"
t = p.read_text()
old = "experiments/runs/m7_step0_heldout_{real,gray,none,caption}_an29_gpu{4,5,6,7}_20260730T151724Z"
new = ("experiments/runs/m7_step0_heldout_base_{real,gray,none,caption}_an29_20260730T1544*Z "
       "(correction 2026-07-30T17:20Z: the row originally cited "
       "m7_step0_heldout_*_20260730T151724Z, a first launch attempt that failed "
       "before any decoding because the harness requires a pre-existing run "
       "manifest carrying the prompt contract; those four dirs produced 0 rows "
       "and were removed. The live runs were relaunched through the extended "
       "launch_virl39k_blind_v1_condition.sh, which writes the manifest "
       "correctly)")
assert t.count(old) == 1, f"anchor count {t.count(old)}"
p.write_text(t.replace(old, new, 1))
print("deviations log run-id citation corrected")

# --- 2. mark the stray aborted arm-1 dir (keep: its logs are failure evidence)
d = ROOT / "experiments/runs/m7_virl_a1_real_seed1_an12_20260728T094310Z"
marker = d / "SUPERSEDED.md"
marker.write_text(
    "# Superseded run directory\n\n"
    "This is the ABORTED first launch attempt of M7 arm 1 (a1_real seed 1).\n"
    "It never trained: config materialised, then the run failed at init in the\n"
    "`limit_images: 8` / vLLM multimodal-profiling failure documented in\n"
    "`docs/registered_m7_single_image_v2.md`. Its logs are retained as the\n"
    "evidence for that registered failure narrative.\n\n"
    "The real arm-1 run is `m7_virl_a1_real_seed1_an12_20260728T102036Z`\n"
    "(complete, step 100/100, manifest closed). Exhaustive sweep 2026-07-30\n"
    "confirmed no manifest, config or report references this directory.\n"
    "Do not count this directory in any run inventory.\n"
)
print("SUPERSEDED.md written into the stray dir")
