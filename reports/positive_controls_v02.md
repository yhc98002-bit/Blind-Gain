# FlipTrack V0.2 Positive Controls

Status:
- Control A passes for all three retained templates under the registered final-answer pair metric.
- Control B real-image scale direction passes; the 3B caption-only side is still running, so P1.7 remains blocked.

Evidence:
- Original, mild, medium, severe, and gray transforms are deterministic and preserve image dimensions.
- Transform implementation: `src/eval/image_conditions.py`.
- R3 degradation runs: `experiments/runs/fliptrack_v02r3_qwen25vl3b_{mild,medium,severe}_20260709T233438Z`.
- R4 degradation runs: `experiments/runs/fliptrack_v02r4_qwen25vl3b_{mild,medium,severe}_20260709T234315Z` and `...T234448Z`.
- Gray runs: `experiments/runs/fliptrack_v02r3_qwen25vl3b_gray_20260709T232817Z` and `experiments/runs/fliptrack_v02r4_qwen25vl3b_gray_20260709T233957Z`.

Control A, 3B pair accuracy:
| Template | Original | Mild | Medium | Severe | Gray | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `starred_series_value_v02` | 0.46 | 0.15 | 0.14 | 0.00 | 0.00 | pass: non-increasing |
| `header_cued_table_code_v02` | 0.85 | 0.67 | 0.65 | 0.18 | 0.00 | pass: non-increasing |
| `coordinate_register_random_target_v02` | 0.42 | 0.41 | 0.25 | 0.00 | 0.00 | pass: non-increasing |

Control B, scale direction:
| Template | 3B real | 7B real | 7B caption | Real scale result |
| --- | ---: | ---: | ---: | --- |
| `starred_series_value_v02` | 0.46 | 0.67 | 0.01 | pass |
| `header_cued_table_code_v02` | 0.85 | 0.99 | 0.03 | pass |
| `coordinate_register_random_target_v02` | 0.42 | 0.75 | 0.06 | pass |

Problems:
- A 3B question-blind 384-token caption pass is still running at `experiments/runs/fliptrack_v02r3_qwen25vl3b_captions384_20260709T234315Z`; R4 3B captions must also be scored before caption scale is complete.
- Header-table's 3B strict-format pair accuracy is much lower than final-answer accuracy; this is reported separately in `reports/fliptrack_v02_hardness.md`.

Decision:
- Control A is sufficient to reject an instrument-deadness interpretation for these templates at base scale.
- Do not mark Control B complete until 3B caption-only values are available; low 7B caption values alone do not establish the scale trend.

Next actions:
- Finish 3B captions and caption QA for R3 and R4 retained templates.
- Add the 3B caption column and script-computed per-template pass/fail.
