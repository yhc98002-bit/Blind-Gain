# C5 R4 Readout V1 (7B access pair)

Status: `complete`.

Scope:
- Seed scope: one seed (data.seed 1) and a single 7B training pair; every accuracy, gain, and recovery below is a one-seed number and no between-seed variance claim is made (docs/registered_c5_7b_access_pair_v1.md).
- Both scoring contracts (I7) are computed separately and never merged: canonical = greedy_canonical_correct, strict = greedy_acc_strict.
- This report contains numbers, checks, and provenance only; interpretation is reserved to the PIs.

Machine artifact: `reports/c5_r4_readout_v1.json`.

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
| prompt_contract_sha256_registered | true |
| row_field_consistency_across_cells | true |
| source_manifest_sha256_registered | true |
| test_rows_per_cell | a1_real:gray=601, a1_real:real=601, a2_gray:gray=601, a2_gray:real=601, base:gray=601, base:real=601 |
| train_filter_sha256_registered | true |

## Contract: canonical (`greedy_canonical_correct`) - one seed (data.seed 1; single 7B training pair)

### Cell accuracy (one seed (data.seed 1; single 7B training pair))

| Model | Test | n | Acc (95% CI) |
|---|---|---:|---:|
| 7B base | real | 601 | 0.2346 [0.2013, 0.2696] |
| 7B base | gray | 601 | 0.0799 [0.0582, 0.1032] |
| A1 real | real | 601 | 0.4825 [0.4426, 0.5208] |
| A1 real | gray | 601 | 0.1248 [0.0998, 0.1514] |
| A2 gray | real | 601 | 0.4276 [0.3877, 0.4659] |
| A2 gray | gray | 601 | 0.1314 [0.1032, 0.1597] |

### Gains (one seed (data.seed 1; single 7B training pair))

| Estimand | Definition | Estimate (95% CI) |
|---|---|---:|
| Matched gain A1 | Acc(A1, test real) - Acc(base, test real) | 0.2479 [0.2030, 0.2912] |
| Matched gain A2 | Acc(A2, test gray) - Acc(base, test gray) | 0.0516 [0.0266, 0.0782] |
| Crossed gain A2 | Acc(A2, test real) - Acc(base, test real) | 0.1930 [0.1531, 0.2346] |
| A1 tested gray (descriptive) | Acc(A1, test gray) - Acc(base, test gray) | 0.0449 [0.0183, 0.0715] |

### Crossed recovery TrainShare A2-gray (one seed (data.seed 1; single 7B training pair))

- Rule: gain[A1, test real] > 0 and gain[A1, test real] >= 2 * paired_se (M7 stability rule); otherwise undefined-unstable-denominator and the ratio is not computed.
- Denominator (matched gain A1 (test real)): estimate 0.2479, paired SE 0.0218, stable `true`.
- Status: `stable`.
- TrainShare: 0.7785 [0.6418, 0.9214] (retained bootstrap draws 5000/5000).

## Contract: strict (`greedy_acc_strict`) - one seed (data.seed 1; single 7B training pair)

### Cell accuracy (one seed (data.seed 1; single 7B training pair))

| Model | Test | n | Acc (95% CI) |
|---|---|---:|---:|
| 7B base | real | 601 | 0.1215 [0.0965, 0.1481] |
| 7B base | gray | 601 | 0.0233 [0.0116, 0.0366] |
| A1 real | real | 601 | 0.4859 [0.4459, 0.5258] |
| A1 real | gray | 601 | 0.1248 [0.0998, 0.1498] |
| A2 gray | real | 601 | 0.4276 [0.3894, 0.4692] |
| A2 gray | gray | 601 | 0.1348 [0.1082, 0.1631] |

### Gains (one seed (data.seed 1; single 7B training pair))

| Estimand | Definition | Estimate (95% CI) |
|---|---|---:|
| Matched gain A1 | Acc(A1, test real) - Acc(base, test real) | 0.3644 [0.3245, 0.4043] |
| Matched gain A2 | Acc(A2, test gray) - Acc(base, test gray) | 0.1115 [0.0832, 0.1398] |
| Crossed gain A2 | Acc(A2, test real) - Acc(base, test real) | 0.3062 [0.2645, 0.3461] |
| A1 tested gray (descriptive) | Acc(A1, test gray) - Acc(base, test gray) | 0.1015 [0.0732, 0.1281] |

### Crossed recovery TrainShare A2-gray (one seed (data.seed 1; single 7B training pair))

- Rule: gain[A1, test real] > 0 and gain[A1, test real] >= 2 * paired_se (M7 stability rule); otherwise undefined-unstable-denominator and the ratio is not computed.
- Denominator (matched gain A1 (test real)): estimate 0.3644, paired SE 0.0209, stable `true`.
- Status: `stable`.
- TrainShare: 0.8402 [0.7457, 0.9456] (retained bootstrap draws 5000/5000).

## Cross-scale descriptive anchor

- cross-scale descriptive anchor (3B pilot, three seeds pooled); not a 7B estimand; not recomputed.
- 3B pilot pooled crossed TrainShare A2-gray: 0.487 [0.383, 0.588] (`reports/d3_trainshare_v1.md`).
- scale comparisons against the 3B pilot are descriptive and labeled cross-scale; no cross-scale statistic is computed (docs/registered_c5_7b_access_pair_v1.md Registered Readout).

## Provenance

- Analysis git head: `9be9f9d0b99a4f67ad26d72c279f2aa6b2357865`.
- Bootstrap: 5000 draws, seed 20260730; deterministic statistic/cell labels hashed into independent streams via src.analysis.pilot_fourarm.deterministic_seed.
- split == 'train' rows are never used in any estimand and are counted here only; the pairing identity is row_index within the test split.
- Registered documents: `docs/registered_c5_7b_access_pair_v1.md`, `docs/registered_extensions_v1.md`.

| Cell | Run dir | Test rows | Train rows | per_item sha256 |
|---|---|---:|---:|---|
| base:real | `experiments/runs/blind_solvability_v2_c5_7b_base_real_an29_20260731T123739Z` | 601 | 1288 | `6ffc7d5500fbc270490e79c21ba4275c72e00c198917c1d33774d84099a8dbac` |
| base:gray | `experiments/runs/blind_solvability_v2_c5_7b_base_gray_an29_20260731T123835Z` | 601 | 1288 | `a1457d0a5319e13d91159472df05e26973502daad1d17f9f78f09b160cf12659` |
| a1_real:real | `experiments/runs/blind_solvability_v2_c5_7b_a1_real_real_an12_20260806T212352Z` | 601 | 1288 | `dbfa2bf8cb295f0811f2d688c769d6a1dff31938d2370424cab09220e2df083d` |
| a1_real:gray | `experiments/runs/blind_solvability_v2_c5_7b_a1_real_gray_an12_20260806T212430Z` | 601 | 1288 | `05a2d2655c4f3b4c2d6a06effab64c50cf80fa15a089bbbe1c8487557a939ff2` |
| a2_gray:real | `experiments/runs/blind_solvability_v2_c5_7b_a2_gray_real_an12_20260806T064621Z` | 601 | 1288 | `e09129d0c52da6811b54b700ab66914f248c97ead957d41ab92f46efd63f94e0` |
| a2_gray:gray | `experiments/runs/blind_solvability_v2_c5_7b_a2_gray_gray_an12_20260806T064655Z` | 601 | 1288 | `2f1e880316e0cb141930c6ab4379dcb3f36fa1c08279c1a1b9e9516f96624a53` |
