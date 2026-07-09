# FlipTrack V0.2 Hardness Calibration

Status:
- P1.6 remains open. The first 600-pair batch has complete 3B real/gray/noise and 7B real/caption-only results.
- R2 has complete 3B real and 7B caption-only results. Chart is the only provisional candidate in the target visual/caption bands; its blind controls remain to be run.
- No template is frozen. R3 adds coordinate-point reading and header-cued document indexing and is being scored.

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

Problems:
- Triangle labels are captured well enough by generic captions to solve 71% of pairs, so its apparent visual success is not certified.
- Chart/grid/parallel/coordinate variants overshot hardness at 3B.
- The first parallel template assigned alternate-interior semantics to A and same-side semantics to B on every pair, producing frequency/statistical side AUC 1.0. This is fixed in R2 by random semantic side assignment for every generator.

Decision:
- Do not retain any first-batch template yet under the strict rule.
- Keep dense table as the deliberate pop-out contrast while calibrating its difficulty.
- Carry R2 chart forward as a provisional candidate; run gray/noise before retention.
- R3 tests two less caption-compressible operations: exact coordinate localization and row/column header intersection. Semantic A/B assignment is randomized by construction.

Next actions:
- Complete R3 3B/7B real and 7B caption scoring.
- Run gray/noise on chart and any R3 template whose 3B real score reaches `[0.4, 0.9]` and whose caption score is at most 0.15.
- Repackage and rerun attackers only after the retained template set is identified.
