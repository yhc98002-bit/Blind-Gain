# C5 R4 Readout V1 (7B access pair) - PARTIAL (verify-only)

Status: `partial-verify-only`.

Scope:
- Seed scope: one seed (data.seed 1) and a single 7B training pair; every accuracy, gain, and recovery below is a one-seed number and no between-seed variance claim is made (docs/registered_c5_7b_access_pair_v1.md).
- Both scoring contracts (I7) are computed separately and never merged: canonical = greedy_canonical_correct, strict = greedy_acc_strict.
- This report contains numbers, checks, and provenance only; interpretation is reserved to the PIs.

Machine artifact: `reports/c5_r4_readout_v1_partial.json`.

## PARTIAL MODE (verify-only)

- This output verifies schema, pairing, manifests, and registered hashes only; it is NOT the registered R4 result.
- No accuracy or performance value appears in this output (registered inspection discipline: no evaluation performance value is inspected before both arms complete).
- Refused estimands: cell_accuracy, matched_gain_a1_real, matched_gain_a2_gray, crossed_gain_a2_gray, descriptive_a1_tested_gray, crossed_recovery_trainshare_a2_gray, bootstrap_intervals.

## Checks

| Check | Value |
|---|---|
| bootstrap_draws_registered_5000 | true |
| bootstrap_seed_registered_20260730 | true |
| conditions_match_cells | true |
| content_identity_exact | true |
| contract_fields_boolean | true |
| contracts_never_merged | true |
| decoding_seed_registered_20260710 | true |
| expected_test_rows | 601 |
| format_prompt_sha256_registered | true |
| greedy_temperature_zero_n1 | true |
| item_identity_exact | true |
| manifests_complete | true |
| model_identity_verified | true |
| partial_refuses_all_estimands | true |
| prompt_contract_sha256_registered | true |
| row_field_consistency_across_cells | true |
| source_manifest_sha256_registered | true |
| test_rows_per_cell | base:gray=601, base:real=601 |
| train_filter_sha256_registered | true |

## Provenance

- Analysis git head: `d8f0eae3c850e6fefa830a79b5b2d1f069d7c36e`.
- Bootstrap: 5000 draws, seed 20260730; deterministic statistic/cell labels hashed into independent streams via src.analysis.pilot_fourarm.deterministic_seed.
- split == 'train' rows are never used in any estimand and are counted here only; the pairing identity is row_index within the test split.
- Registered documents: `docs/registered_c5_7b_access_pair_v1.md`, `docs/registered_extensions_v1.md`.

| Cell | Run dir | Test rows | Train rows | per_item sha256 |
|---|---|---:|---:|---|
| base:real | `experiments/runs/blind_solvability_v2_c5_7b_base_real_an29_20260731T123739Z` | 601 | 1288 | `6ffc7d5500fbc270490e79c21ba4275c72e00c198917c1d33774d84099a8dbac` |
| base:gray | `experiments/runs/blind_solvability_v2_c5_7b_base_gray_an29_20260731T123835Z` | 601 | 1288 | `a1457d0a5319e13d91159472df05e26973502daad1d17f9f78f09b160cf12659` |
