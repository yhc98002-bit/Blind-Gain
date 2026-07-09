# FlipTrack V0.2 Hardness Calibration

Status:
- P1.6 is complete at the task level. The retained set has three 100-pair templates, including one geometry family, and all registered hardness conditions are filled.
- The PI Gate 2 decision remains separate and is not asserted here.

Evidence:
- First-batch source manifest: `data/fliptrack_v02_source_manifest.jsonl`, 100 pairs per template.
- 3B real run: `experiments/runs/fliptrack_v02_qwen25vl3b_real_20260709T221953Z`.
- 3B gray run: `experiments/runs/fliptrack_v02_qwen25vl3b_gray_20260709T223401Z`.
- 3B noise run: `experiments/runs/fliptrack_v02_qwen25vl3b_noise_20260709T223850Z`.
- 7B real run: `experiments/runs/fliptrack_v02_qwen25vl7b_real_20260709T224248Z`.
- 7B captions and caption QA: `experiments/runs/fliptrack_v02_qwen25vl7b_captions384_20260709T221956Z` and `experiments/runs/fliptrack_v02_qwen25vl7b_captionqa384_20260709T224252Z`.
- All conditions use greedy decoding and the shared `<answer>...</answer>` contract. Captions are question-blind, fixed before QA, and capped at 384 new tokens.

Pair accuracy:
| Template | 3B real | 3B gray | 3B noise | 7B real | 7B caption | First-batch decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `coordinate_slope_v02` | 0.00 | 0.00 | 0.00 | 0.12 | 0.25 | reject: 3B real too hard; caption exceeds real |
| `dense_table_code_v01` | 0.91 | 0.00 | 0.00 | 1.00 | 0.10 | revise/contrast only: 3B real is 0.01 above upper target |
| `indexed_symbol_grid_v02` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | reject: visually unsolved |
| `parallel_angle_marker_v02` | 0.05 | 0.00 | 0.00 | 0.13 | 0.00 | reject: visually too hard; side assignment also leaked |
| `starred_series_value_v02` | 0.07 | 0.00 | 0.00 | 0.07 | 0.00 | reject: visually too hard |
| `triangle_missing_angle_v02` | 0.85 | 0.00 | 0.00 | 0.94 | 0.71 | reject: caption-compressible |

Aggregate diagnostics:
| Condition | Pair accuracy | Collapse | Format valid |
| --- | ---: | ---: | ---: |
| 3B real | 0.3133 | 0.3567 | 0.8758 |
| 3B gray | 0.0000 | 1.0000 | 1.0000 |
| 3B noise | 0.0000 | 0.9750 | 1.0000 |
| 7B real | 0.3767 | 0.3450 | 1.0000 |
| 7B caption-only | 0.1767 | 0.4083 | 0.9983 |

R2 calibration:
- Source manifest: `data/fliptrack_v02r2_source_manifest.jsonl`, 600 pairs.
- 3B real run: `experiments/runs/fliptrack_v02r2_qwen25vl3b_real_20260709T224957Z`.
- 7B captions: `experiments/runs/fliptrack_v02r2_qwen25vl7b_captions384_20260709T225001Z`.
- Caption QA: `experiments/runs/fliptrack_v02r2_qwen25vl7b_captionqa384_20260709T230830Z`.
- The corrected R2 aggregate pair accuracies are 0.375 for 3B real and 0.180 for 7B caption-only.

| R2 template | 3B real | 7B caption | R2 decision |
| --- | ---: | ---: | --- |
| `coordinate_slope_v02` | 0.01 | 0.25 | reject: visually unsolved and caption-compressible |
| `dense_table_code_v01` | 0.91 | 0.11 | contrast only: visual score remains above the registered upper bound |
| `indexed_symbol_grid_v02` | 0.08 | 0.00 | reject: visually unsolved |
| `parallel_angle_marker_v02` | 0.01 | 0.02 | reject: visually unsolved after semantic-side randomization |
| `starred_series_value_v02` | 0.40 | 0.00 | provisional retain: exactly meets the visual lower bound; blind controls pending |
| `triangle_missing_angle_v02` | 0.84 | 0.70 | reject: strongly caption-compressible |

R2 caption diagnostics:
- Aggregate collapse rate: 0.415; format-valid rate: 1.000; ambiguous rate: 0.000.
- Within-template key-shuffle null mean: 0.0027, one-sided Monte Carlo `p=0.00498` with 200 permutations.
- The triangle family alone contributes 70 of the 108 caption-solved pairs, confirming that generic captions preserve its displayed labels.

Retained V0.2 set:
- Selection config: `configs/data/fliptrack_v02_retained.json`.
- Hash-locked selection record: `experiments/manifests/fliptrack_v02_retained.json`.
- Selected source manifest: `data/fliptrack_v02_retained_source_manifest.jsonl`, SHA256 `a2cc793795ca0e806922e78a6dedf27e55028cb111cc8fd92656b072264d1353`.
- R3 source SHA256: `bae79e619527125c19717c2953c4909839dc43fd0644bf8b664f825debc8232a`.
- R4 source SHA256: `47e9d5bb6deb52b0b5e3f01d93b290d442ad4a4b1d72043b53f52dd38b9c1850`.

| Retained template | 3B real final | 3B real strict | 3B gray | 3B pair-shared noise | 7B real final | 7B caption | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `starred_series_value_v02` | 0.46 | 0.46 | 0.00 | 0.00 | 0.67 | 0.01 | retain: chart two-hop read |
| `header_cued_table_code_v02` | 0.85 | 0.19 | 0.00 | 0.00 | 0.99 | 0.03 | retain on final-answer metric; format caveat below |
| `coordinate_register_random_target_v02` | 0.42 | 0.42 | 0.00 | 0.00 | 0.75 | 0.06 | retain: geometry keystone |

Blind-control diagnostics:
- Pair-shared noise run: `experiments/runs/fliptrack_v02_retained_qwen25vl3b_noise_shared_20260709T235057Z`.
- Pair-shared noise collapse is 1.00 for every retained template; gray collapse is also 1.00.
- Earlier R3/R4 `noise` runs used independent random pixels for A and B. They remain useful stress tests but are superseded for the registered collapse criterion because different nuisance images can induce different wrong outputs.

Format caveat:
- The shared prompt contract was unchanged across templates and models.
- The 3B model omitted `<answer>` tags frequently on header-table: format-valid rate 0.425 and strict pair accuracy 0.19, despite final-answer pair accuracy 0.85. The 7B model had format-valid rate 0.995 and strict pair accuracy 0.98.
- Retention uses the pre-specified final-answer pair metric; strict-format results remain visible and must not be conflated with it.

Contact sheets:
- `reports/contact_sheets/fliptrack_v02r3/header_cued_table_code_v02.png`
- `reports/contact_sheets/fliptrack_v02r3/starred_series_value_v02.png`
- `reports/contact_sheets/fliptrack_v02r4/coordinate_register_random_target_v02.png`

Problems:
- Triangle labels are captured well enough by generic captions to solve 71% of pairs, so its apparent visual success is not certified.
- Chart/grid/parallel/coordinate variants overshot hardness at 3B.
- The first parallel template assigned alternate-interior semantics to A and same-side semantics to B on every pair, producing frequency/statistical side AUC 1.0. This is fixed in R2 by random semantic side assignment for every generator.

Decision:
- Do not retain any first-batch template yet under the strict rule.
- Keep dense table as the deliberate pop-out contrast while calibrating its difficulty.
- Freeze chart, header-table, and randomized-target coordinate register as the retained 300-pair V0.2 instrument.
- Reject the four-point fixed-Q coordinate family: its 7B caption pair accuracy was 0.25 because generic captions sometimes transcribed Q's exact coordinate.

Next actions:
- Complete retained-set package/lint and corrected artifact attackers.
- Finish the 3B caption pass for the P1.7 scale control.
