# M5 Restore-and-Resume Integrity

Status:
- Integrity precondition: `pass`.
- This is an engineering precondition and does not declare M5 or a PI gate passed.

Evidence:
- Machine artifact: `reports/m5_restore_resume_integrity.json`.
- Source raw checkpoint: `checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_100`.
- Step-101 run: `/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/experiments/runs/m5_anchor_resume_integrity_step101_an12_20260716T164403Z/run_manifest.json`.
- Checks: `8/8` true.
- Continuity bounds were committed before the step-101 run and are recorded in the machine artifact.

Problems:
- Failed checks: `[]`.

Decision:
- None. A passing integrity artifact authorizes the already registered fixed step-400 launch; it does not interpret scientific outcomes.

Next actions:
- Launch the step-400 continuation from the original verified step-100 state, not from the integrity checkpoint.
- Preserve the fixed terminal step and registered evaluation checkpoints.
