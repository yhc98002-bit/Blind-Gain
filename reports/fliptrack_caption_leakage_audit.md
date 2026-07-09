# FlipTrack Caption Leakage Audit

Status:
- Caption generation is question-blind: captions are generated from images with a fixed prompt before caption QA.
- Caption-only V0.1 pair accuracy is `0.1000`, below the recovery ceiling of `0.60`.

Evidence:
- Caption prompt is fixed in `scripts/caption_fliptrack.py`.
- Caption run: `experiments/runs/fliptrack_v01_qwen25vl3b_captions_20260708T044623Z`
- Caption QA run: `experiments/runs/fliptrack_v01_qwen25vl3b_captionqa_20260708T045033Z`

Per-template caption-only metrics:

| Template | n | Pair acc | Member acc | Collapse |
| --- | ---: | ---: | ---: | ---: |
| `dense_table_code_v01` | 100 | 0.0500 | 0.0700 | 0.5600 |
| `starred_legend_label_v01` | 100 | 0.1500 | 0.4150 | 0.1500 |
| `symbol_grid_v01` | 100 | 0.1000 | 0.3150 | 0.5800 |

Decision:
- Caption leakage gate passes for V0.1 recovery.
- The legend template leaks more caption information than the table template but remains far below real-image accuracy.

Next actions:
- Keep caption generation prompt fixed and question-blind for future versions.
- Add a report field that stores caption prompt hash in every caption run manifest.
