# Blind Gains Main-Phase Registry

Source of authority: `docs/MAIN_PHASE_BRIEF.md`. A task is not complete merely because its implementation exists; the named evidence must exist and its enumerated checks must hold. PIs audit scientific gates, and the implementing agent does not declare them passed.

| ID | Task | Dependencies | Required evidence |
| --- | --- | --- | --- |
| M0 | Finalize pilot preregistration | none; blocks M2/M3 | `reports/m0_preregistration_finalization.md`; `reports/preregistration_pilot_v1.md`; `reports/pilot_reward_spec_v3.md`; `reports/fliptrack_v02r19_human_audit.md` |
| M1 | Finish ViRL39K 4,096 audit and fork ruling | audit can run with M0; ruling follows M0 | `reports/blind_solvability_virl39k_sample_v1.md`; `reports/blind_solvability_virl39k_sample_v1_audited.json`; `reports/virl_fork_ruling.md` |
| M2 | Four-arm pilot seed 1 | merged-at-HEAD M0 | `reports/pilot_4arm_seed1_results_v1.md`; `reports/pilot_4arm_seed1_r19_null_v1.md`; `reports/pilot_4arm_seed1_r19_null_v1.json`; `reports/pilot_4arm_seed1_r19_null_v1_audit.json`; `reports/pilot_4arm_seed1_r19_null_category_tables_v1.md` |
| M3 | Pilot seeds 2–3 | M0; follows M2 launch validation | `reports/pilot_3seed_summary_v1.md` |
| M4 | Register extensions | M1 fork resolved; M3/M7/M8-dependent fields remain `{computed-pending}`; flat/rising rule and exact merge marker block M5–M7/M9 | `docs/registered_extensions_v1.md`; `reports/registered_extensions_audit_v3.md`; `reports/registered_extensions_audit_v3.json` |
| M5 | Anchor long horizon to step 400 | M4; resume integrity | `reports/anchor_longhorizon_400_results_v1.md` |
| M6 | Mini-A5 matched control | M4; reward/grouping audits | `reports/mini_a5_control_results_v1.md` |
| M7 | ViRL 3B decomposition | M4 and M1 fork ruling; merged informed-prediction amendment before optimizer step 1 | `docs/registered_m7_amendment_v1.md`; `reports/virl_3b_decomposition_results_v1.md`; `reports/virl_3b_data_readiness_v1.md` |
| M8 | 7B caption and blind-solvability prep | parallel with M7; fields feed M4/M9 | `reports/flagship_7b_readiness_v1.md`; `reports/blind_solvability_virl39k_7b_sample_v1.md` |
| M9 | 7B flagship, seeds 1–3 | M4 and M8 | `reports/flagship_7b_results_v1.md`; `reports/flagship_7b_3seed_v1.md` |
| M10 | Support-sharpening resampling | folded into each applicable readout | `reports/support_sharpening_registry_v3.md`; `reports/support_sharpening_execution_status_v2.md`; `reports/support_sharpening_seed1_v2.md`; `reports/support_sharpening_seed1_v2.json` plus per-readout 64-sample artifacts |
| M11 | Non-Qwen inference audits | gap-filler; Gemma access may block | `reports/generalization_audits_v1.md` |
| M12 | Chart v08 two-subfamily instrument | gap-filler; R19 immutable | `reports/chart_v08_generation_status_v2.md`; `reports/chart_v08_mechanical_audit_v2.md`; `reports/chart_v08_calibration.md`; `reports/chart_v08_confirmatory.md` |
| M13 | Paper 1 pipeline | continuous | `docs/paper1/`; `reports/paper1_pipeline_status_v7.md`; `reports/paper1_pipeline_status_v7.json` |
| M14 | Merge-back readouts | M6 and M9 seed 1; registered M4 addendum | `reports/mergeback_gate_readouts_v1.md` |

Global completion checks:
- Every training unit has a registered document committed at `HEAD` before its first optimizer step.
- Every GPU run has immutable placement, model/config/data hashes, seed, command, times, and artifact paths.
- Every evaluation uses the locked prompt and greedy decoding contract unless a registered sampled analysis says otherwise.
- Every code fix includes an adversarial fixture, and every status is the conjunction of its enumerated checks.
- `docs/RESEARCH_DOC.md` sections 4–6 are maintained in the same commit as each ledger pass; sections 1–3 and 7 remain PI-owned.
