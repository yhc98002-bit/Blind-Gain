#!/usr/bin/env python3
"""Extend the D2 runner and finalizer to the registered seed-3 models."""
from pathlib import Path
import sys

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")

# --- runner: add seed-3 model specs and cells -------------------------------
r = ROOT / "scripts/run_d2_testtime_ablation.py"
t = r.read_text()
if "a1_seed3_step100" not in t:
    old_models = '''    "a2b_seed2_step100": {
        "checkpoint": "checkpoints/pilot/mech_a2b_noimage_seed2_resume20/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a2b_noimage_seed2_resume20_an29_20260719T125447Z",
        "arm": "a2b_noimage",
    },
}'''
    new_models = '''    "a2b_seed2_step100": {
        "checkpoint": "checkpoints/pilot/mech_a2b_noimage_seed2_resume20/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a2b_noimage_seed2_resume20_an29_20260719T125447Z",
        "arm": "a2b_noimage",
    },
    "a1_seed3_step100": {
        "checkpoint": "checkpoints/pilot/mech_a1_real_seed3/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a1_real_seed3_an29_20260722T050330Z",
        "arm": "a1_real",
    },
    "a2b_seed3_step100": {
        "checkpoint": "checkpoints/pilot/mech_a2b_noimage_seed3/global_step_100/actor/huggingface",
        "training_run": "experiments/runs/mech_a2b_noimage_seed3_an29_20260724T033754Z",
        "arm": "a2b_noimage",
    },
}'''
    assert t.count(old_models) == 1, "runner model table anchor"
    t = t.replace(old_models, new_models)

    old_cells = '''] + [("a2b_seed1_step100", "real"), ("a2b_seed2_step100", "real")]'''
    new_cells = '''] + [
    (model, condition)
    for model in ("a1_seed3_step100",)
    for condition in ("real", "gray", "none")
] + [
    ("a2b_seed1_step100", "real"),
    ("a2b_seed2_step100", "real"),
    ("a2b_seed3_step100", "real"),
]'''
    assert t.count(old_cells) == 1, "runner cell list anchor"
    t = t.replace(old_cells, new_cells)
    r.write_text(t)
    print("runner patched")
else:
    print("runner already patched")

# --- finalizer: add seed-3 to models, published values, and cells -----------
f = ROOT / "scripts/finalize_d2_testtime_ablation.py"
t = f.read_text()
if "a1_seed3_step100" not in t:
    t = t.replace(
        'PUBLISHED_A1_REAL = {"a1_seed1_step100": 0.4276, "a1_seed2_step100": 0.4210}',
        'PUBLISHED_A1_REAL = {"a1_seed1_step100": 0.4276, "a1_seed2_step100": 0.4210, "a1_seed3_step100": 0.4060}',
        1,
    )
    t = t.replace(
        'PUBLISHED_A2B_NONE = {"a2b_seed1_step100": 0.0982, "a2b_seed2_step100": 0.1231}',
        'PUBLISHED_A2B_NONE = {"a2b_seed1_step100": 0.0982, "a2b_seed2_step100": 0.1231, "a2b_seed3_step100": 0.1215}',
        1,
    )
    old = '''CELLS = [("a1_seed1_step100", c) for c in ("real", "gray", "none")] + \\
        [("a1_seed2_step100", c) for c in ("real", "gray", "none")] + \\
        [("a2b_seed1_step100", "real"), ("a2b_seed2_step100", "real")]'''
    new = '''CELLS = [("a1_seed1_step100", c) for c in ("real", "gray", "none")] + \\
        [("a1_seed2_step100", c) for c in ("real", "gray", "none")] + \\
        [("a1_seed3_step100", c) for c in ("real", "gray", "none")] + \\
        [("a2b_seed1_step100", "real"), ("a2b_seed2_step100", "real"),
         ("a2b_seed3_step100", "real")]'''
    assert t.count(old) == 1, "finalizer cell anchor"
    t = t.replace(old, new)
    t = t.replace(
        '''    for seed, model_key in (("seed1", "a1_seed1_step100"), ("seed2", "a1_seed2_step100")):''',
        '''    for seed, model_key in (("seed1", "a1_seed1_step100"), ("seed2", "a1_seed2_step100"), ("seed3", "a1_seed3_step100")):''',
        1,
    )
    t = t.replace(
        '''    for seed, model_key in (("seed1", "a2b_seed1_step100"), ("seed2", "a2b_seed2_step100")):''',
        '''    for seed, model_key in (("seed1", "a2b_seed1_step100"), ("seed2", "a2b_seed2_step100"), ("seed3", "a2b_seed3_step100")):''',
        1,
    )
    t = t.replace(
        '''    elif bands["seed1"] == bands["seed2"]:
        verdict = bands["seed1"]''',
        '''    elif len(set(bands.values())) == 1:
        verdict = bands["seed1"]''',
        1,
    )
    f.write_text(t)
    print("finalizer patched")
else:
    print("finalizer already patched")
