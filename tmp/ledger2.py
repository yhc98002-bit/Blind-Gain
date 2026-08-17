#!/usr/bin/env python3
from pathlib import Path

p = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/reports/main_progress.md")
t = p.read_text()
subs = [
    ("| P0.3 | Freeze and version intervention-group schema + loader fixture | pending | I15. |",
     "| P0.3 | Freeze and version intervention-group schema + loader fixture | pass | `src/train/intervention_group_schema.py` pins v1 and fails closed on unknown versions; rejects causal members sharing the original answer, groups without an invariance member (I5), and stale `delta_q`. 13-case fixture. |"),
    ("| P0.4 | Fix task roles in all reports and text | pending | Primary visual anchor / saturated positive control + retention canary / oracle-localized readout control. No aggregate across roles (I13). |",
     "| P0.4 | Fix task roles in all reports and text | pass | `src/eval/task_roles.py` + 8-case I13 guard; unknown tasks fail closed. Registered primary endpoint already role-pure; only the `overall` key crosses roles and is now labelled an accounting identity. Registry records `SATURATION_CLAIM_IS_ACCURATE = False`. `reports/p04_task_roles_v1.md`. |"),
    ("| CL | Cue ladder on existing checkpoints (F4b) | pending | Generation CPU; scoring inference-only, fits 4-GPU gaps. Register before scoring; invariants I12, I13. |",
     "| CL | Cue ladder on existing checkpoints (F4b) | running | Registered `docs/registered_cue_ladder_v1.md` before any scoring. Four rungs replayed from the frozen R19 nine-series `pair_seed`s, so the ladder is item-paired with R19; replay integrity gate passes 300/300. Scoring next on free GPUs. |"),
]
for old, new in subs:
    if old not in t:
        raise SystemExit(f"anchor missing: {old[:70]}")
    t = t.replace(old, new, 1)
p.write_text(t)
print("ledger updated")
