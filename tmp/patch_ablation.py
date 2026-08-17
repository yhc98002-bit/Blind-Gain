#!/usr/bin/env python3
"""Minimal, backward-compatible patch to the D2/D3 orchestrator.

Adds --conditions (default = the original three, so existing behaviour is
unchanged) and relaxes the GPU assertion from "exactly 4,5,6,7" to "a non-empty
subset of 4-7", so the caption column can run on two GPUs while the other two
stay free for the M5 step-400 evaluation. Trainer GPUs 0-3 remain forbidden.
"""
from pathlib import Path

p = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/scripts/run_d2_testtime_ablation.py")
t = p.read_text()

old_cells = '''CELLS = [
    (f"{arm}_seed{seed}_step100", condition)
    for arm in ("a1", "a2", "a2b", "a3")
    for seed in (1, 2, 3)
    for condition in ("real", "gray", "none")
]'''
new_cells = '''DEFAULT_CONDITIONS = ("real", "gray", "none")


def build_cells(conditions=DEFAULT_CONDITIONS):
    return [
        (f"{arm}_seed{seed}_step100", condition)
        for arm in ("a1", "a2", "a2b", "a3")
        for seed in (1, 2, 3)
        for condition in conditions
    ]


CELLS = build_cells()'''
assert t.count(old_cells) == 1, "CELLS anchor"
t = t.replace(old_cells, new_cells, 1)

old_arg = '''    parser.add_argument("--poll-seconds", type=int, default=60)
    args = parser.parse_args()
    if sorted(args.gpu_ids) != [4, 5, 6, 7]:
        raise ValueError("D2 cells run on GPUs 4-7 only")'''
new_arg = '''    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument(
        "--conditions", nargs="+", default=list(DEFAULT_CONDITIONS),
        help="test conditions to run; defaults to the original D3 three. "
             "'caption' is registered in docs/registered_d3_caption_column_v1.md.",
    )
    args = parser.parse_args()
    if not args.gpu_ids or not set(args.gpu_ids).issubset({4, 5, 6, 7}):
        raise ValueError("D2/D3 cells run on GPUs 4-7 only (trainer GPUs 0-3 are never used)")
    if "caption" in args.conditions and not (
        ROOT / "docs/registered_d3_caption_column_v1.md"
    ).is_file():
        raise RuntimeError("caption column registration is absent")'''
assert t.count(old_arg) == 1, "arg anchor"
t = t.replace(old_arg, new_arg, 1)

old_pending = "    pending = [cell for cell in CELLS if cell not in done and cell not in live]"
new_pending = ("    cells = build_cells(tuple(args.conditions))\n"
               "    pending = [cell for cell in cells if cell not in done and cell not in live]")
assert t.count(old_pending) == 1, "pending anchor"
t = t.replace(old_pending, new_pending, 1)

p.write_text(t)
print("patched run_d2_testtime_ablation.py: --conditions added, GPU set relaxed to a subset of 4-7")
