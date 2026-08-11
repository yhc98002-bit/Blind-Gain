# C6 — does the readout/anchor dissociation hold at 7B?

Registration: `docs/registered_c6_mechanism_at_scale_v1.md` — schema `blind-gains.c6-mechanism-at-scale-readout.v1`.
Seed scope: one seed (data.seed 1; single 7B training pair).

Decision rule: **MOVED** iff the 95% paired-bootstrap CI excludes zero in the positive direction. Both contracts are reported and never merged (I7); the three task roles are never aggregated (I13).

## c6_1_a1real_minus_base_r19 — A1-real minus 7B base on R19

_recipe-matched arm (real images, outcome reward) -- the central reading_

| role | contract | base | arm | arm−base | 95% CI | decision |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `coordinate_register_twenty_point_x_v02` (600) | lenient | 0.7850 | 0.8100 | +0.0250 | [+0.0033, +0.0467] | **MOVED** |
| `coordinate_register_twenty_point_x_v02` (600) | strict | 0.7850 | 0.8100 | +0.0250 | [+0.0050, +0.0467] | **MOVED** |
| `header_cued_table_code_v02` (300) | lenient | 0.9933 | 0.9933 | +0.0000 | [-0.0100, +0.0100] | **NOT MOVED** |
| `header_cued_table_code_v02` (300) | strict | 0.9800 | 0.9800 | +0.0000 | [-0.0167, +0.0167] | **NOT MOVED** |
| `starred_series_value_nine_v07` (300) | lenient | 0.6733 | 0.7033 | +0.0300 | [-0.0067, +0.0667] | **NOT MOVED** |
| `starred_series_value_nine_v07` (300) | strict | 0.6733 | 0.7033 | +0.0300 | [-0.0067, +0.0667] | **NOT MOVED** |

- **lenient** → branch **(d)**: anchor MOVED, readout NOT MOVED -- the remaining cell of the 2x2.  Not anticipated by any prior result and no interpretation was pre-committed; reported descriptively and explicitly flagged as an UNREGISTERED OUTCOME
- **strict** → branch **(d)**: anchor MOVED, readout NOT MOVED -- the remaining cell of the 2x2.  Not anticipated by any prior result and no interpretation was pre-committed; reported descriptively and explicitly flagged as an UNREGISTERED OUTCOME

## c6_2_a2gray_minus_base_r19 — A2-gray minus 7B base on R19

_blind-trained arm (no visual information in training) -- read under its own label_

| role | contract | base | arm | arm−base | 95% CI | decision |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `coordinate_register_twenty_point_x_v02` (600) | lenient | 0.7850 | 0.7917 | +0.0067 | [-0.0167, +0.0283] | **NOT MOVED** |
| `coordinate_register_twenty_point_x_v02` (600) | strict | 0.7850 | 0.7917 | +0.0067 | [-0.0133, +0.0283] | **NOT MOVED** |
| `header_cued_table_code_v02` (300) | lenient | 0.9933 | 0.9900 | -0.0033 | [-0.0100, +0.0000] | **NOT MOVED** |
| `header_cued_table_code_v02` (300) | strict | 0.9800 | 0.9800 | +0.0000 | [-0.0100, +0.0100] | **NOT MOVED** |
| `starred_series_value_nine_v07` (300) | lenient | 0.6733 | 0.6900 | +0.0167 | [-0.0133, +0.0467] | **NOT MOVED** |
| `starred_series_value_nine_v07` (300) | strict | 0.6733 | 0.6900 | +0.0167 | [-0.0133, +0.0467] | **NOT MOVED** |

- **lenient** → branch **(c)**: neither MOVED -- reported descriptively as 7B recipe transfer: the C5 recipe transferred to 7B on its own training distribution (R4) without moving either FlipTrack layer; no dissociation claim is made in either direction
- **strict** → branch **(c)**: neither MOVED -- reported descriptively as 7B recipe transfer: the C5 recipe transferred to 7B on its own training distribution (R4) without moving either FlipTrack layer; no dissociation claim is made in either direction

## c6_3_a1real_minus_base_r20 — A1-real minus 7B base on R20

_recipe-matched arm, private-twin replication_

| role | contract | base | arm | arm−base | 95% CI | decision |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `coordinate_register_twenty_point_x_v02` (600) | lenient | 0.7567 | 0.7800 | +0.0233 | [+0.0017, +0.0433] | **MOVED** |
| `coordinate_register_twenty_point_x_v02` (600) | strict | 0.7567 | 0.7800 | +0.0233 | [+0.0033, +0.0450] | **MOVED** |
| `header_cued_table_code_v02` (300) | lenient | 0.9967 | 0.9967 | +0.0000 | [-0.0100, +0.0100] | **NOT MOVED** |
| `header_cued_table_code_v02` (300) | strict | 0.9867 | 0.9933 | +0.0067 | [-0.0067, +0.0200] | **NOT MOVED** |
| `starred_series_value_nine_v07` (300) | lenient | 0.6233 | 0.6367 | +0.0133 | [-0.0300, +0.0600] | **NOT MOVED** |
| `starred_series_value_nine_v07` (300) | strict | 0.6233 | 0.6367 | +0.0133 | [-0.0300, +0.0600] | **NOT MOVED** |

- **lenient** → branch **(d)**: anchor MOVED, readout NOT MOVED -- the remaining cell of the 2x2.  Not anticipated by any prior result and no interpretation was pre-committed; reported descriptively and explicitly flagged as an UNREGISTERED OUTCOME
- **strict** → branch **(d)**: anchor MOVED, readout NOT MOVED -- the remaining cell of the 2x2.  Not anticipated by any prior result and no interpretation was pre-committed; reported descriptively and explicitly flagged as an UNREGISTERED OUTCOME

## c6_4_a2gray_minus_base_r20 — A2-gray minus 7B base on R20

_blind-trained arm, private-twin replication_

| role | contract | base | arm | arm−base | 95% CI | decision |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `coordinate_register_twenty_point_x_v02` (600) | lenient | 0.7567 | 0.7567 | +0.0000 | [-0.0217, +0.0233] | **NOT MOVED** |
| `coordinate_register_twenty_point_x_v02` (600) | strict | 0.7567 | 0.7567 | +0.0000 | [-0.0233, +0.0217] | **NOT MOVED** |
| `header_cued_table_code_v02` (300) | lenient | 0.9967 | 0.9900 | -0.0067 | [-0.0167, +0.0000] | **NOT MOVED** |
| `header_cued_table_code_v02` (300) | strict | 0.9867 | 0.9900 | +0.0033 | [-0.0067, +0.0167] | **NOT MOVED** |
| `starred_series_value_nine_v07` (300) | lenient | 0.6233 | 0.6367 | +0.0133 | [-0.0233, +0.0500] | **NOT MOVED** |
| `starred_series_value_nine_v07` (300) | strict | 0.6233 | 0.6367 | +0.0133 | [-0.0233, +0.0533] | **NOT MOVED** |

- **lenient** → branch **(c)**: neither MOVED -- reported descriptively as 7B recipe transfer: the C5 recipe transferred to 7B on its own training distribution (R4) without moving either FlipTrack layer; no dissociation claim is made in either direction
- **strict** → branch **(c)**: neither MOVED -- reported descriptively as 7B recipe transfer: the C5 recipe transferred to 7B on its own training distribution (R4) without moving either FlipTrack layer; no dissociation claim is made in either direction

## Replication across the private twin

| arm | contract | R19 branch | R20 branch | replicates |
| --- | --- | --- | --- | --- |
| A1-real | lenient | (d) | (d) | yes |
| A1-real | strict | (d) | (d) | yes |
| A2-gray | lenient | (c) | (c) | yes |
| A2-gray | strict | (c) | (c) | yes |

## Scope

One seed and one 7B training pair; two arms, not four; no cross-scale statistic is computed anywhere. C6 neither confirms nor overturns Gate 1 or R4.
