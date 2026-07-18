# Generalization Audits V1

Status:
- M11 evidence conjunction: `pass`.
- These are inference-only audits; they do not establish a training-effect claim.
- Caption results measure caption-mediated accessibility using fixed 3B question-blind captions.

Checks:
| Check | Result |
| --- | --- |
| `both_model_backends_staged` | `true` |
| `all_run_placements_have_verified_stage` | `true` |
| `complete_fliptrack_2x2x3_matrix` | `true` |
| `all_fliptrack_cells_audited` | `true` |
| `complete_blind_sample_2x3_matrix` | `true` |
| `all_blind_sample_cells_audited` | `true` |

FlipTrack:
| Backend | Split | Condition | Pair accuracy | 95% item-bootstrap CI | Collapse | Per-template pair accuracy |
| --- | --- | --- | ---: | --- | ---: | --- |
| gemma3 | R19 | caption | 0.0058 | [0.0017, 0.0100] | 0.4183 | coordinate_register_twenty_point_x_v02=0.0100, header_cued_table_code_v02=0.0033, starred_series_value_nine_v07=0.0000 |
| gemma3 | R19 | none | 0.0000 | [0.0000, 0.0000] | 1.0000 | coordinate_register_twenty_point_x_v02=0.0000, header_cued_table_code_v02=0.0000, starred_series_value_nine_v07=0.0000 |
| gemma3 | R19 | real | 0.3333 | [0.3067, 0.3600] | 0.0108 | coordinate_register_twenty_point_x_v02=0.1400, header_cued_table_code_v02=1.0000, starred_series_value_nine_v07=0.0533 |
| gemma3 | R20 | caption | 0.0067 | [0.0025, 0.0117] | 0.4367 | coordinate_register_twenty_point_x_v02=0.0050, header_cued_table_code_v02=0.0167, starred_series_value_nine_v07=0.0000 |
| gemma3 | R20 | none | 0.0000 | [0.0000, 0.0000] | 1.0000 | coordinate_register_twenty_point_x_v02=0.0000, header_cued_table_code_v02=0.0000, starred_series_value_nine_v07=0.0000 |
| gemma3 | R20 | real | 0.3283 | [0.3017, 0.3558] | 0.0208 | coordinate_register_twenty_point_x_v02=0.1300, header_cued_table_code_v02=0.9967, starred_series_value_nine_v07=0.0567 |
| internvl3 | R19 | caption | 0.0067 | [0.0025, 0.0117] | 0.4575 | coordinate_register_twenty_point_x_v02=0.0083, header_cued_table_code_v02=0.0100, starred_series_value_nine_v07=0.0000 |
| internvl3 | R19 | none | 0.0000 | [0.0000, 0.0000] | 1.0000 | coordinate_register_twenty_point_x_v02=0.0000, header_cued_table_code_v02=0.0000, starred_series_value_nine_v07=0.0000 |
| internvl3 | R19 | real | 0.6808 | [0.6542, 0.7067] | 0.0117 | coordinate_register_twenty_point_x_v02=0.4850, header_cued_table_code_v02=0.9733, starred_series_value_nine_v07=0.7800 |
| internvl3 | R20 | caption | 0.0133 | [0.0075, 0.0200] | 0.4533 | coordinate_register_twenty_point_x_v02=0.0133, header_cued_table_code_v02=0.0267, starred_series_value_nine_v07=0.0000 |
| internvl3 | R20 | none | 0.0000 | [0.0000, 0.0000] | 1.0000 | coordinate_register_twenty_point_x_v02=0.0000, header_cued_table_code_v02=0.0000, starred_series_value_nine_v07=0.0000 |
| internvl3 | R20 | real | 0.6783 | [0.6525, 0.7033] | 0.0167 | coordinate_register_twenty_point_x_v02=0.4600, header_cued_table_code_v02=0.9833, starred_series_value_nine_v07=0.8100 |

ViRL39K Blind-Solvability Sample:
| Backend | Condition | Acc_final | 95% item-bootstrap CI | Acc_strict | Contract-valid rate |
| --- | --- | ---: | --- | ---: | ---: |
| gemma3 | caption | 0.3091 | [0.2949, 0.3237] | 0.0000 | 0.0002 |
| gemma3 | none | 0.2424 | [0.2297, 0.2556] | 0.0000 | 0.0000 |
| gemma3 | real | 0.3418 | [0.3279, 0.3572] | 0.0000 | 0.0000 |
| internvl3 | caption | 0.1951 | [0.1833, 0.2073] | 0.1860 | 0.9387 |
| internvl3 | none | 0.1538 | [0.1426, 0.1653] | 0.1431 | 0.9229 |
| internvl3 | real | 0.2805 | [0.2664, 0.2944] | 0.2793 | 0.9846 |

Evidence:
- Machine artifact: `reports/generalization_audits_v1.json`.
- Every cell links its immutable metric path and SHA256 in the machine artifact.
- Decoding is greedy with temperature 0, top-p 1, n=1; prompt and parser versions are fixed.

Decision:
- Report the two model families separately; no architecture-pooled estimate is computed.
- Source/category and template strata are preserved in the machine artifact.
