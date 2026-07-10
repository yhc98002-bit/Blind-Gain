# FlipTrack Caption Leakage Audit

Status:
- Caption generation is question-blind: captions are generated from images with a fixed prompt before caption QA.
- Caption-only V0.1 pair accuracy is `0.1000`, below the recovery ceiling of `0.60`.
- On the exact 1,200-pair R19 package, caption-only pair accuracy is `0.0125` at 3B and `0.0208` at 7B; both are below the V0.2 ceiling of `0.15`.

Evidence:
- Caption prompt is fixed in `scripts/caption_fliptrack.py`.
- Caption run: `experiments/runs/fliptrack_v01_qwen25vl3b_captions_20260708T044623Z`
- Caption QA run: `experiments/runs/fliptrack_v01_qwen25vl3b_captionqa_20260708T045033Z`
- R19 exact 3B store: `experiments/runs/caption_store_merge_fliptrack_v02r19_qwen25vl3b_384_20260710T134825Z`.
- R19 keyed QA input: `experiments/runs/caption_qa_pair_build_fliptrack_v02r19_qwen25vl3b_384_20260710T140200Z`; all 2,400 release hashes map exactly and independent member-side audit found zero errors.
- R19 3B QA: `experiments/runs/fliptrack_v02r19_qwen25vl3b_captionqa384_an29_20260710T140850Z`.
- R19 aggregate: `experiments/runs/fliptrack_aggregate_v02r19_qwen25vl3b_caption384_20260710T142221Z`.
- R19 exact 7B store and keyed input: `experiments/runs/caption_store_merge_fliptrack_v02r19_qwen25vl7b_384_20260710T142844Z` and `experiments/runs/caption_qa_pair_build_fliptrack_v02r19_qwen25vl7b_384_20260710T142903Z`.
- R19 7B QA and aggregate: `experiments/runs/fliptrack_v02r19_qwen25vl7b_captionqa384_an12_20260710T142926Z` and `experiments/runs/fliptrack_aggregate_v02r19_qwen25vl7b_caption384_20260710T143606Z`.
- Paired scale comparison: `experiments/runs/fliptrack_compare_v02r19_caption_3b_vs_7b_20260710T150313Z`.

Per-template caption-only metrics:

| Template | n | Pair acc | Member acc | Collapse |
| --- | ---: | ---: | ---: | ---: |
| `dense_table_code_v01` | 100 | 0.0500 | 0.0700 | 0.5600 |
| `starred_legend_label_v01` | 100 | 0.1500 | 0.4150 | 0.1500 |
| `symbol_grid_v01` | 100 | 0.1000 | 0.3150 | 0.5800 |

R19 3B caption-only metrics:

| Template | n | Pair acc | Member acc | Collapse |
| --- | ---: | ---: | ---: | ---: |
| `header_cued_table_code_v02` | 300 | 0.0100 | 0.0133 | 0.5567 |
| `coordinate_register_twenty_point_x_v02` | 600 | 0.0200 | 0.1758 | 0.4183 |
| `starred_series_value_nine_v07` | 300 | 0.0000 | 0.0167 | 0.3633 |
| **Overall** | **1,200** | **0.0125** | **0.0954** | **0.4392** |

- Overall pair-accuracy bootstrap 95% CI is `[0.0067, 0.0192]`.
- The within-template key-shuffle null mean is `0.00681` with `p=0.01598`; captions retain a small measurable signal, concentrated in geometry, but remain far below the registered ceiling.
- Format-valid rate is `1.0`; ambiguous and extraction-fallback rates are both `0`.

R19 7B caption-only metrics:

| Template | n | Pair acc | Member acc | Collapse |
| --- | ---: | ---: | ---: | ---: |
| `header_cued_table_code_v02` | 300 | 0.0600 | 0.1067 | 0.4767 |
| `coordinate_register_twenty_point_x_v02` | 600 | 0.0083 | 0.0933 | 0.3767 |
| `starred_series_value_nine_v07` | 300 | 0.0067 | 0.0883 | 0.2967 |
| **Overall** | **1,200** | **0.0208** | **0.0954** | **0.3817** |

- Overall pair-accuracy bootstrap 95% CI is `[0.0133, 0.0292]`.
- Overall 3B-to-7B change is +0.0083 and is not significant by paired McNemar test (`p=0.1433`).
- Document captions rise from 0.0100 to 0.0600 (`p=0.000729`); report this as partial caption compressibility even though it remains below the 0.15 ceiling.

Decision:
- Caption leakage gate passes for V0.1 recovery.
- The legend template leaks more caption information than the table template but remains far below real-image accuracy.
- R19 passes the caption ceiling at both model sizes. Do not call caption information zero or claim that every template is scale-flat.

Next actions:
- Keep caption generation prompt fixed and question-blind for future versions.
- Carry the document-caption caveat into the paper and complete the pending human audit without changing R19 in response to model scores.
