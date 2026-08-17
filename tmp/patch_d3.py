#!/usr/bin/env python3
"""Extend the D2/D3 runner to the full registered D3 matrix.

Adds the A2 gray and A3 caption rows (seeds 1-3) and the missing A2b columns,
so the runner covers docs/registered_d3_condition_matrix_v1.md. Cells already
produced under D2 are skipped automatically by completed_cells().
"""
from pathlib import Path
import sys

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
r = ROOT / "scripts/run_d2_testtime_ablation.py"
t = r.read_text()

if "a2_seed1_step100" in t:
    print("already patched")
    sys.exit(0)

anchor = '''    "a2b_seed3_step100": {
        "checkpoint": "checkpoints/pilot/mech_a2b_noimage_seed3/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a2b_noimage_seed3_an29_20260724T033754Z",
        "arm": "a2b_noimage",
    },
}'''
addition = '''    "a2b_seed3_step100": {
        "checkpoint": "checkpoints/pilot/mech_a2b_noimage_seed3/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a2b_noimage_seed3_an29_20260724T033754Z",
        "arm": "a2b_noimage",
    },
    "a2_seed1_step100": {
        "checkpoint": "checkpoints/pilot/mech_a2_gray_resume60_retry2/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a2_gray_resume60_retry2_an12_20260715T165701Z",
        "arm": "a2_gray",
    },
    "a2_seed2_step100": {
        "checkpoint": "checkpoints/pilot/mech_a2_gray_seed2_resume20/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a2_gray_seed2_resume20_an12_20260719T125918Z",
        "arm": "a2_gray",
    },
    "a2_seed3_step100": {
        "checkpoint": "checkpoints/pilot/mech_a2_gray_seed3/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a2_gray_seed3_an12_20260722T145916Z",
        "arm": "a2_gray",
    },
    "a3_seed1_step100": {
        "checkpoint": "checkpoints/pilot/mech_a3_caption_resume20/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a3_caption_resume20_an29_20260713T144233Z",
        "arm": "a3_caption",
    },
    "a3_seed2_step100": {
        "checkpoint": "checkpoints/pilot/mech_a3_caption_seed2/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a3_caption_seed2_an29_20260720T125144Z",
        "arm": "a3_caption",
    },
    "a3_seed3_step100": {
        "checkpoint": "checkpoints/pilot/mech_a3_caption_seed3/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a3_caption_seed3_an29_20260725T092128Z",
        "arm": "a3_caption",
    },
}'''
assert t.count(anchor) == 1, f"model anchor count {t.count(anchor)}"
t = t.replace(anchor, addition)

# Replace the cell list with the full registered D3 matrix.
start = t.index("CELLS = [")
end = t.index("\n\n", start)
new_cells = '''CELLS = [
    (f"{arm}_seed{seed}_step100", condition)
    for arm in ("a1", "a2", "a2b", "a3")
    for seed in (1, 2, 3)
    for condition in ("real", "gray", "none")
]'''
t = t[:start] + new_cells + t[end:]
r.write_text(t)
print("runner patched for full D3 matrix (36 cells; completed D2 cells auto-skipped)")
