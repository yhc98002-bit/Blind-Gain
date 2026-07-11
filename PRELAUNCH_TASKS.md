# Blind Gains Prelaunch Task Registry

This file is the authoritative task and named-report registry for `reports/prelaunch_progress.md`. A task may be marked `pass` only when every report listed on its registry line exists under `reports/` and is non-empty. Generated data, code, configs, run directories, and non-report artifacts remain additional task requirements but are outside this ledger-evidence check.

## Registry

- `L0` reports: `reports/storage_preflight.md`
- `L1` reports: `reports/parser_agreement_audit_v2.md`
- `L2` reports: `reports/scorer_v2_spec.md`
- `L3` reports: `reports/pilot_reward_spec.md`
- `L4` reports: `reports/a3_caption_path.md`
- `L5` reports: `reports/decon_geo3k_train_vs_test.md`, `reports/geo3k_filtered_subset.md`
- `L6` reports: `reports/eval_harness_version.md`, `reports/mech_pilot_3arm_geo3k.md`, `reports/base_external_benchmarks.md`, `reports/gpu_hours_utilization.md`
- `L7` reports: `reports/blind_solvability_geo3k_v2.md`, `reports/blind_solvability_geo3k_v2_audited.md`, `reports/blind_solvability_geo3k_v2_audited.json`
- `L8` reports: `reports/fliptrack_r20_confirmatory.md`, `reports/fliptrack_r20_confirmatory.json`
- `L9` reports: `reports/strong_caption_stress.md`
- `L10` reports: `reports/base_external_benchmarks.md`, `reports/blind_solvability_virl39k_sample_v1.md`, `reports/blind_solvability_virl39k_sample_v1_audited.json`
- `L11` reports: `reports/document_v_next_calibration.md`
- `L12` reports: `reports/preregistration_pilot_v1.md`
- `L13` reports: `reports/pilot_4arm_results_v1.md`

## Dependency Invariant

`L13` cannot be `pass` unless `L12` is also `pass` and `reports/preregistration_pilot_v1.md` exists and is non-empty. This registry defines evidence names; it does not authorize an agent to declare a PI-controlled scientific gate passed.
