# C6 mechanism at scale: does the readout/anchor dissociation hold at 7B? Frozen 7B base vs C5 A1-real and A2-gray on FlipTrack R19 and its private twin R20

schema_version `blind-gains.c6-mechanism-at-scale-readout.v1`

Machine-readable readout: `reports/c6_mechanism_at_scale_v1.json`.

**Seed scope.** Every number below carries `seed_tag`: one seed (data.seed 1; single 7B training pair).

**Both contracts are reported and never merged (I7). The three task roles are never aggregated (I13); pooled values appear only under keys labelled `NOT_AN_ENDPOINT` and are not C6 results.**

## Registration

- document: `docs/registered_c6_mechanism_at_scale_v1.md`
- sha256: `113dc544d93f259c69f0314905ebe39bbd6244f3f6ee27494c8811d6eb5dbbb9`
- every branch quotation below was verified present in that document.

- decision rule: **Decision rule.** **MOVED** iff the 95% paired-bootstrap CI excludes zero in the positive direction. A positive point estimate whose interval contains zero is **NOT MOVED** — not "a trend". **MOVED_NEGATIVE_DIRECTION** iff the CI lies entirely below zero. Identical to the Gate-1 rule (`reports/mini_a5_gate1_endpoint_readout_v1.json` → `instrument`).

## Cells

| cell | model | instrument | run dir | n pairs | data_manifest_hash | pointer |
| --- | --- | --- | --- | ---: | --- | --- |
| `r19:base` (r19_base7b) | frozen 7B base (Qwen2.5-VL-7B-Instruct) | R19 | `experiments/runs/c6_r19_7b_base_real_an12_20260811T120648Z` | 1200 | `e1dde98451e1…` | verified (logs/c6_cells/r19_base7b) |
| `r19:a1_real` (r19_a1real) | A1-real (C5 arm 1, real images, outcome reward), global_step_100 | R19 | `experiments/runs/c6_r19_a1real_an12_20260811T122252Z` | 1200 | `e1dde98451e1…` | verified (logs/c6_cells/r19_a1real) |
| `r19:a2_gray` (r19_a2gray) | A2-gray (C5 arm 2, blind-trained), global_step_100 | R19 | `experiments/runs/c6_r19_a2gray_an12_20260811T123109Z` | 1200 | `e1dde98451e1…` | verified (logs/c6_cells/r19_a2gray) |
| `r20:base` (r20_base7b) | frozen 7B base (Qwen2.5-VL-7B-Instruct) | R20 | `experiments/runs/c6_r20_base7b_an12_20260811T124023Z` | 1200 | `20222e60201b…` | verified (logs/c6_cells/r20_base7b) |
| `r20:a1_real` (r20_a1real) | A1-real (C5 arm 1, real images, outcome reward), global_step_100 | R20 | `experiments/runs/c6_r20_a1real_an12_20260811T124736Z` | 1200 | `20222e60201b…` | verified (logs/c6_cells/r20_a1real) |
| `r20:a2_gray` (r20_a2gray) | A2-gray (C5 arm 2, blind-trained), global_step_100 | R20 | `experiments/runs/c6_r20_a2gray_an12_20260811T125348Z` | 1200 | `20222e60201b…` | verified (logs/c6_cells/r20_a2gray) |

### Cell levels per task role (descriptive levels, not endpoints)

| cell | role | template_id | n | lenient pair acc | strict pair acc |
| --- | --- | --- | ---: | ---: | ---: |
| `r19:base` | primary visual anchor (search + binding + read) | `coordinate_register_twenty_point_x_v02` | 600 | 0.7850 | 0.7850 |
| `r19:base` | saturated positive control / retention canary -- a DROP signals damage | `header_cued_table_code_v02` | 300 | 0.9933 | 0.9800 |
| `r19:base` | oracle-localized readout control | `starred_series_value_nine_v07` | 300 | 0.6733 | 0.6733 |
| `r19:a1_real` | primary visual anchor (search + binding + read) | `coordinate_register_twenty_point_x_v02` | 600 | 0.8100 | 0.8100 |
| `r19:a1_real` | saturated positive control / retention canary -- a DROP signals damage | `header_cued_table_code_v02` | 300 | 0.9933 | 0.9800 |
| `r19:a1_real` | oracle-localized readout control | `starred_series_value_nine_v07` | 300 | 0.7033 | 0.7033 |
| `r19:a2_gray` | primary visual anchor (search + binding + read) | `coordinate_register_twenty_point_x_v02` | 600 | 0.7917 | 0.7917 |
| `r19:a2_gray` | saturated positive control / retention canary -- a DROP signals damage | `header_cued_table_code_v02` | 300 | 0.9900 | 0.9800 |
| `r19:a2_gray` | oracle-localized readout control | `starred_series_value_nine_v07` | 300 | 0.6900 | 0.6900 |
| `r20:base` | primary visual anchor (search + binding + read) | `coordinate_register_twenty_point_x_v02` | 600 | 0.7567 | 0.7567 |
| `r20:base` | saturated positive control / retention canary -- a DROP signals damage | `header_cued_table_code_v02` | 300 | 0.9967 | 0.9867 |
| `r20:base` | oracle-localized readout control | `starred_series_value_nine_v07` | 300 | 0.6233 | 0.6233 |
| `r20:a1_real` | primary visual anchor (search + binding + read) | `coordinate_register_twenty_point_x_v02` | 600 | 0.7800 | 0.7800 |
| `r20:a1_real` | saturated positive control / retention canary -- a DROP signals damage | `header_cued_table_code_v02` | 300 | 0.9967 | 0.9933 |
| `r20:a1_real` | oracle-localized readout control | `starred_series_value_nine_v07` | 300 | 0.6367 | 0.6367 |
| `r20:a2_gray` | primary visual anchor (search + binding + read) | `coordinate_register_twenty_point_x_v02` | 600 | 0.7567 | 0.7567 |
| `r20:a2_gray` | saturated positive control / retention canary -- a DROP signals damage | `header_cued_table_code_v02` | 300 | 0.9900 | 0.9900 |
| `r20:a2_gray` | oracle-localized readout control | `starred_series_value_nine_v07` | 300 | 0.6367 | 0.6367 |

## Registered contrasts — arm minus base, per role, both contracts

### `c6_1_a1real_minus_base_r19` — R19

- central C6 statement: A1-real is the arm whose training condition matches the 3B Mini-A5 recipes (registration section 2)
- orientation: left = 7B base cell, right = arm cell (delta = r19_a1real minus r19_base7b)
- n pairs: 1200

| role | template_id | n | contract | base | arm | arm−base | 95% CI | McNemar p | decision |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: | --- |
| primary visual anchor (search + binding + read) | `coordinate_register_twenty_point_x_v02` | 600 | lenient | 0.7850 | 0.8100 | +0.0250 | [+0.0033, +0.0467] | 0.0357 | **MOVED** |
| primary visual anchor (search + binding + read) | `coordinate_register_twenty_point_x_v02` | 600 | contract_strict | 0.7850 | 0.8100 | +0.0250 | [+0.0050, +0.0467] | 0.0357 | **MOVED** |
| saturated positive control / retention canary -- a DROP signals damage | `header_cued_table_code_v02` | 300 | lenient | 0.9933 | 0.9933 | +0.0000 | [-0.0100, +0.0100] | 1 | **NOT MOVED** |
| saturated positive control / retention canary -- a DROP signals damage | `header_cued_table_code_v02` | 300 | contract_strict | 0.9800 | 0.9800 | +0.0000 | [-0.0167, +0.0167] | 1 | **NOT MOVED** |
| oracle-localized readout control | `starred_series_value_nine_v07` | 300 | lenient | 0.6733 | 0.7033 | +0.0300 | [-0.0067, +0.0667] | 0.1628 | **NOT MOVED** |
| oracle-localized readout control | `starred_series_value_nine_v07` | 300 | contract_strict | 0.6733 | 0.7033 | +0.0300 | [-0.0067, +0.0667] | 0.1628 | **NOT MOVED** |

**Pre-committed reading.**

- **lenient** — branch fired: **(d) anchor MOVED, readout NOT MOVED**
  - registration text: **(d) anchor MOVED, readout NOT MOVED** → the remaining cell of the 2×2. It is not anticipated by any prior result and no interpretation is pre-committed for it; it is reported descriptively, with the raw numbers, and explicitly flagged as an unregistered outcome. Naming it here prevents it from being quietly folded into (a) or (b).
  - anchor `coordinate_register_twenty_point_x_v02`: +0.0250 [+0.0033, +0.0467] → MOVED
  - readout `starred_series_value_nine_v07`: +0.0300 [-0.0067, +0.0667] → NOT MOVED
  - canary `header_cued_table_code_v02`: +0.0000 [-0.0100, +0.0100] → NOT MOVED (damage: False)
- **contract_strict** — branch fired: **(d) anchor MOVED, readout NOT MOVED**
  - registration text: **(d) anchor MOVED, readout NOT MOVED** → the remaining cell of the 2×2. It is not anticipated by any prior result and no interpretation is pre-committed for it; it is reported descriptively, with the raw numbers, and explicitly flagged as an unregistered outcome. Naming it here prevents it from being quietly folded into (a) or (b).
  - anchor `coordinate_register_twenty_point_x_v02`: +0.0250 [+0.0050, +0.0467] → MOVED
  - readout `starred_series_value_nine_v07`: +0.0300 [-0.0067, +0.0667] → NOT MOVED
  - canary `header_cued_table_code_v02`: +0.0000 [-0.0167, +0.0167] → NOT MOVED (damage: False)

- contracts agree: **True** — both contracts fire the same branch

- registration on contract disagreement: **Contract disagreement (I7).** The branch is evaluated separately under lenient and under contract-strict. If the two contracts fire different branches, **both branches are reported**, the disagreement is named as the result, and neither contract is chosen as the tie-breaker. No merged or averaged contract exists.

### `c6_2_a2gray_minus_base_r19` — R19

- blind-trained arm: same shape, same branches, different question -- what a blind-trained 7B arm does to a visual instrument (registration section 2); never netted against A1-real
- orientation: left = 7B base cell, right = arm cell (delta = r19_a2gray minus r19_base7b)
- n pairs: 1200

| role | template_id | n | contract | base | arm | arm−base | 95% CI | McNemar p | decision |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: | --- |
| primary visual anchor (search + binding + read) | `coordinate_register_twenty_point_x_v02` | 600 | lenient | 0.7850 | 0.7917 | +0.0067 | [-0.0167, +0.0283] | 0.6516 | **NOT MOVED** |
| primary visual anchor (search + binding + read) | `coordinate_register_twenty_point_x_v02` | 600 | contract_strict | 0.7850 | 0.7917 | +0.0067 | [-0.0133, +0.0283] | 0.6516 | **NOT MOVED** |
| saturated positive control / retention canary -- a DROP signals damage | `header_cued_table_code_v02` | 300 | lenient | 0.9933 | 0.9900 | -0.0033 | [-0.0100, +0.0000] | 1 | **NOT MOVED** |
| saturated positive control / retention canary -- a DROP signals damage | `header_cued_table_code_v02` | 300 | contract_strict | 0.9800 | 0.9800 | +0.0000 | [-0.0100, +0.0100] | 1 | **NOT MOVED** |
| oracle-localized readout control | `starred_series_value_nine_v07` | 300 | lenient | 0.6733 | 0.6900 | +0.0167 | [-0.0133, +0.0467] | 0.3833 | **NOT MOVED** |
| oracle-localized readout control | `starred_series_value_nine_v07` | 300 | contract_strict | 0.6733 | 0.6900 | +0.0167 | [-0.0133, +0.0467] | 0.3833 | **NOT MOVED** |

**Pre-committed reading.**

- **lenient** — branch fired: **(c) neither MOVED**
  - registration text: **(c) neither MOVED** → reported **descriptively as 7B recipe transfer**: the C5 recipe transferred to 7B on its own training distribution (R4) without moving either FlipTrack layer. No dissociation claim is made in either direction from this branch.
  - anchor `coordinate_register_twenty_point_x_v02`: +0.0067 [-0.0167, +0.0283] → NOT MOVED
  - readout `starred_series_value_nine_v07`: +0.0167 [-0.0133, +0.0467] → NOT MOVED
  - canary `header_cued_table_code_v02`: -0.0033 [-0.0100, +0.0000] → NOT MOVED (damage: False)
- **contract_strict** — branch fired: **(c) neither MOVED**
  - registration text: **(c) neither MOVED** → reported **descriptively as 7B recipe transfer**: the C5 recipe transferred to 7B on its own training distribution (R4) without moving either FlipTrack layer. No dissociation claim is made in either direction from this branch.
  - anchor `coordinate_register_twenty_point_x_v02`: +0.0067 [-0.0133, +0.0283] → NOT MOVED
  - readout `starred_series_value_nine_v07`: +0.0167 [-0.0133, +0.0467] → NOT MOVED
  - canary `header_cued_table_code_v02`: +0.0000 [-0.0100, +0.0100] → NOT MOVED (damage: False)

- contracts agree: **True** — both contracts fire the same branch

- registration on contract disagreement: **Contract disagreement (I7).** The branch is evaluated separately under lenient and under contract-strict. If the two contracts fire different branches, **both branches are reported**, the disagreement is named as the result, and neither contract is chosen as the tie-breaker. No merged or averaged contract exists.

### `c6_3_a1real_minus_base_r20` — R20

- replication of c6_1 on the private twin, not a vote
- orientation: left = 7B base cell, right = arm cell (delta = r20_a1real minus r20_base7b)
- n pairs: 1200

| role | template_id | n | contract | base | arm | arm−base | 95% CI | McNemar p | decision |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: | --- |
| primary visual anchor (search + binding + read) | `coordinate_register_twenty_point_x_v02` | 600 | lenient | 0.7567 | 0.7800 | +0.0233 | [+0.0017, +0.0433] | 0.04877 | **MOVED** |
| primary visual anchor (search + binding + read) | `coordinate_register_twenty_point_x_v02` | 600 | contract_strict | 0.7567 | 0.7800 | +0.0233 | [+0.0033, +0.0450] | 0.04877 | **MOVED** |
| saturated positive control / retention canary -- a DROP signals damage | `header_cued_table_code_v02` | 300 | lenient | 0.9967 | 0.9967 | +0.0000 | [-0.0100, +0.0100] | 1 | **NOT MOVED** |
| saturated positive control / retention canary -- a DROP signals damage | `header_cued_table_code_v02` | 300 | contract_strict | 0.9867 | 0.9933 | +0.0067 | [-0.0067, +0.0200] | 0.625 | **NOT MOVED** |
| oracle-localized readout control | `starred_series_value_nine_v07` | 300 | lenient | 0.6233 | 0.6367 | +0.0133 | [-0.0300, +0.0600] | 0.6516 | **NOT MOVED** |
| oracle-localized readout control | `starred_series_value_nine_v07` | 300 | contract_strict | 0.6233 | 0.6367 | +0.0133 | [-0.0300, +0.0600] | 0.6516 | **NOT MOVED** |

**Pre-committed reading.**

- **lenient** — branch fired: **(d) anchor MOVED, readout NOT MOVED**
  - registration text: **(d) anchor MOVED, readout NOT MOVED** → the remaining cell of the 2×2. It is not anticipated by any prior result and no interpretation is pre-committed for it; it is reported descriptively, with the raw numbers, and explicitly flagged as an unregistered outcome. Naming it here prevents it from being quietly folded into (a) or (b).
  - anchor `coordinate_register_twenty_point_x_v02`: +0.0233 [+0.0017, +0.0433] → MOVED
  - readout `starred_series_value_nine_v07`: +0.0133 [-0.0300, +0.0600] → NOT MOVED
  - canary `header_cued_table_code_v02`: +0.0000 [-0.0100, +0.0100] → NOT MOVED (damage: False)
- **contract_strict** — branch fired: **(d) anchor MOVED, readout NOT MOVED**
  - registration text: **(d) anchor MOVED, readout NOT MOVED** → the remaining cell of the 2×2. It is not anticipated by any prior result and no interpretation is pre-committed for it; it is reported descriptively, with the raw numbers, and explicitly flagged as an unregistered outcome. Naming it here prevents it from being quietly folded into (a) or (b).
  - anchor `coordinate_register_twenty_point_x_v02`: +0.0233 [+0.0033, +0.0450] → MOVED
  - readout `starred_series_value_nine_v07`: +0.0133 [-0.0300, +0.0600] → NOT MOVED
  - canary `header_cued_table_code_v02`: +0.0067 [-0.0067, +0.0200] → NOT MOVED (damage: False)

- contracts agree: **True** — both contracts fire the same branch

- registration on contract disagreement: **Contract disagreement (I7).** The branch is evaluated separately under lenient and under contract-strict. If the two contracts fire different branches, **both branches are reported**, the disagreement is named as the result, and neither contract is chosen as the tie-breaker. No merged or averaged contract exists.

### `c6_4_a2gray_minus_base_r20` — R20

- replication of c6_2 on the private twin, not a vote
- orientation: left = 7B base cell, right = arm cell (delta = r20_a2gray minus r20_base7b)
- n pairs: 1200

| role | template_id | n | contract | base | arm | arm−base | 95% CI | McNemar p | decision |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: | --- |
| primary visual anchor (search + binding + read) | `coordinate_register_twenty_point_x_v02` | 600 | lenient | 0.7567 | 0.7567 | +0.0000 | [-0.0217, +0.0233] | 1 | **NOT MOVED** |
| primary visual anchor (search + binding + read) | `coordinate_register_twenty_point_x_v02` | 600 | contract_strict | 0.7567 | 0.7567 | +0.0000 | [-0.0233, +0.0217] | 1 | **NOT MOVED** |
| saturated positive control / retention canary -- a DROP signals damage | `header_cued_table_code_v02` | 300 | lenient | 0.9967 | 0.9900 | -0.0067 | [-0.0167, +0.0000] | 0.5 | **NOT MOVED** |
| saturated positive control / retention canary -- a DROP signals damage | `header_cued_table_code_v02` | 300 | contract_strict | 0.9867 | 0.9900 | +0.0033 | [-0.0067, +0.0167] | 1 | **NOT MOVED** |
| oracle-localized readout control | `starred_series_value_nine_v07` | 300 | lenient | 0.6233 | 0.6367 | +0.0133 | [-0.0233, +0.0500] | 0.5966 | **NOT MOVED** |
| oracle-localized readout control | `starred_series_value_nine_v07` | 300 | contract_strict | 0.6233 | 0.6367 | +0.0133 | [-0.0233, +0.0533] | 0.5966 | **NOT MOVED** |

**Pre-committed reading.**

- **lenient** — branch fired: **(c) neither MOVED**
  - registration text: **(c) neither MOVED** → reported **descriptively as 7B recipe transfer**: the C5 recipe transferred to 7B on its own training distribution (R4) without moving either FlipTrack layer. No dissociation claim is made in either direction from this branch.
  - anchor `coordinate_register_twenty_point_x_v02`: +0.0000 [-0.0217, +0.0233] → NOT MOVED
  - readout `starred_series_value_nine_v07`: +0.0133 [-0.0233, +0.0500] → NOT MOVED
  - canary `header_cued_table_code_v02`: -0.0067 [-0.0167, +0.0000] → NOT MOVED (damage: False)
- **contract_strict** — branch fired: **(c) neither MOVED**
  - registration text: **(c) neither MOVED** → reported **descriptively as 7B recipe transfer**: the C5 recipe transferred to 7B on its own training distribution (R4) without moving either FlipTrack layer. No dissociation claim is made in either direction from this branch.
  - anchor `coordinate_register_twenty_point_x_v02`: +0.0000 [-0.0233, +0.0217] → NOT MOVED
  - readout `starred_series_value_nine_v07`: +0.0133 [-0.0233, +0.0533] → NOT MOVED
  - canary `header_cued_table_code_v02`: +0.0033 [-0.0067, +0.0167] → NOT MOVED (damage: False)

- contracts agree: **True** — both contracts fire the same branch

- registration on contract disagreement: **Contract disagreement (I7).** The branch is evaluated separately under lenient and under contract-strict. If the two contracts fire different branches, **both branches are reported**, the disagreement is named as the result, and neither contract is chosen as the tie-breaker. No merged or averaged contract exists.

## Replication across instruments (R20 is a replication, not a vote)

**R20 is a replication, not a vote.** Its branch reading is reported next to R19's. If the two instruments fire different branches, that is reported as a replication failure of the branch on the twin — it is not resolved by pooling, averaging, or majority.

| arm | contract | R19 branch | R20 branch | agree | statement |
| --- | --- | --- | --- | --- | --- |
| a1_real | lenient | (d) anchor MOVED, readout NOT MOVED | (d) anchor MOVED, readout NOT MOVED | True | the branch replicates on the private twin |
| a1_real | contract_strict | (d) anchor MOVED, readout NOT MOVED | (d) anchor MOVED, readout NOT MOVED | True | the branch replicates on the private twin |
| a2_gray | lenient | (c) neither MOVED | (c) neither MOVED | True | the branch replicates on the private twin |
| a2_gray | contract_strict | (c) neither MOVED | (c) neither MOVED | True | the branch replicates on the private twin |

## Cross-scale (descriptive only)

- DESCRIPTIVE ONLY -- no cross-scale difference, ratio, interval or test is computed anywhere in this report
- 3B Gate 1 (descriptive): all four Mini-A5 recipes move the oracle-localized readout control +0.15-0.23 lenient while no axis buys held-out content on the primary anchor under any contrast or any role (reports/mini_a5_gate1_endpoint_readout_v1.json, docs/registered_mini_a5_endpoint_readout_v1.md)
- R4/C5 (descriptive): the blind-attainable share of the gain grows with scale -- crossed TrainShare for A2-gray 0.7785 [0.6418, 0.9214] canonical / 0.8402 [0.7457, 0.9456] strict at 7B against a 3B pooled 0.487 [0.383, 0.588] (reports/c5_r4_readout_v1.json, docs/registered_c5_7b_access_pair_v1.md)

## Scope limits

- one seed, one 7B training pair: every number is a one-seed number; C6 makes no between-seed variance claim
- two arms, not four: C6 tests whether the dissociation holds at 7B for the transferred recipe; it does not establish recipe-independence at 7B
- descriptive cross-scale only: nothing here licenses a tested claim that the dissociation is stronger, weaker, or equal at 7B vs 3B
- no re-decision: Gate 1 and R4 stand as filed

## Acceptance checks

| check | status |
| --- | --- |
| `check_01_six_cells_bound` | pass |
| `check_02_model_identity` | pass |
| `check_03_manifest_hash_pins` | pass (re-hashed on disk at readout time) |
| `check_04_complete_run_manifests` | pass |
| `check_05_locked_evaluation_contract` | pass |
| `check_06_canonical_contract_fields_on_every_row` | pass |
| `check_07_both_contracts_present` | pass |
| `check_08_item_set_identity_across_models` | pass |
| `check_09_instrument_separation` | pass (R19 x R20 pair_id intersection = 0) |
| `check_10_per_role_n_pairs` | pass |
| `check_11_bootstrap_parameters_as_registered` | pass |
| `check_12_orientation_base_left_arm_right` | pass |
| `check_13_i13_labelling` | pass (no pooled-across-roles quantity appears except under a NOT_AN_ENDPOINT key; no per-shard quantity is emitted at all) |
| `check_14_one_seed_tagging` | pass |
| `check_15_cross_scale_discipline` | pass (descriptive strings only) |
| `check_16_determinism_and_immutability` | output contains no timestamps; existing outputs are never overwritten |

## Provenance

- analysis git hash: `2ebf8c0dbd9753c272498f0e999fdabba369b9f3`
- registration sha256: `113dc544d93f259c69f0314905ebe39bbd6244f3f6ee27494c8811d6eb5dbbb9`

| cell | run_manifest | run_manifest sha256 | generation git hash |
| --- | --- | --- | --- |
| `r19:base` | `experiments/runs/c6_r19_7b_base_real_an12_20260811T120648Z/run_manifest.json` | `7e38be7e64e016c725aea857bbcb234085cc29a642e2d1df06cd6a5b4aa98352` | `ee7fd256f321c39bfd5f7ed47614093fdb337bbd` |
| `r19:a1_real` | `experiments/runs/c6_r19_a1real_an12_20260811T122252Z/run_manifest.json` | `1f4dacaec75af6875a9266341b2bbf5fb4f20ccb1b07b724f28c821e86ee12d5` | `ee7fd256f321c39bfd5f7ed47614093fdb337bbd` |
| `r19:a2_gray` | `experiments/runs/c6_r19_a2gray_an12_20260811T123109Z/run_manifest.json` | `252d210354c1b7967d641e848a5b3a015df708472e08ecf7345ca23fbe6237d6` | `ee7fd256f321c39bfd5f7ed47614093fdb337bbd` |
| `r20:base` | `experiments/runs/c6_r20_base7b_an12_20260811T124023Z/run_manifest.json` | `eb575fa83c528f4075067dea57b86ade45e96c3d9fb7369adde79581390adbb3` | `ee7fd256f321c39bfd5f7ed47614093fdb337bbd` |
| `r20:a1_real` | `experiments/runs/c6_r20_a1real_an12_20260811T124736Z/run_manifest.json` | `1d9864ab6ba9287fcec50abab9cf7ddc8a4c5f4c493749e3dd3fe30783445702` | `ee7fd256f321c39bfd5f7ed47614093fdb337bbd` |
| `r20:a2_gray` | `experiments/runs/c6_r20_a2gray_an12_20260811T125348Z/run_manifest.json` | `40edc7a8075dcbf2f9dd263fec286242b12aacc5d854e89263bccc220360d9b5` | `ee7fd256f321c39bfd5f7ed47614093fdb337bbd` |

