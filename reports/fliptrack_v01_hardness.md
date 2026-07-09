# FlipTrack V0.1 Hardness

Status:
- Corrected FlipTrack V0.1 has 300 pairs: 100 chart, 100 document/OCR, 100 geometry/spatial.
- Qwen2.5-VL-3B real-image evaluation passes the recovery target.
- Gray and noise evaluations are at floor.
- Caption-only evaluation is far below the 0.60 leakage ceiling.

Evidence:
- Manifest: `data/fliptrack_v01_manifest.jsonl`
- Scored manifest: `data/fliptrack_v01_scored.jsonl`
- Real eval: `experiments/runs/fliptrack_v01_qwen25vl3b_real_20260708T044242Z/metrics/aggregate.json`
- Gray eval: `experiments/runs/fliptrack_v01_qwen25vl3b_gray_20260708T044242Z/metrics/aggregate.json`
- Noise eval: `experiments/runs/fliptrack_v01_qwen25vl3b_noise_20260708T044623Z/metrics/aggregate.json`
- Caption QA: `experiments/runs/fliptrack_v01_qwen25vl3b_captionqa_20260708T045033Z/metrics/aggregate.json`

Metrics:

| Mode | n | Pair acc | Member acc | Collapse |
| --- | ---: | ---: | ---: | ---: |
| 3B real | 300 | 0.8933 | 0.9300 | 0.0300 |
| 3B gray | 300 | 0.0000 | 0.0800 | 1.0000 |
| 3B noise | 300 | 0.0000 | 0.0800 | 0.8000 |
| 3B caption-only | 300 | 0.1000 | 0.2667 | 0.4300 |

Per-template real-image pair accuracy:

| Template | n | Pair acc | Member acc |
| --- | ---: | ---: | ---: |
| `starred_legend_label_v01` | 100 | 0.9500 | 0.9650 |
| `dense_table_code_v01` | 100 | 0.9100 | 0.9450 |
| `symbol_grid_v01` | 100 | 0.8200 | 0.8800 |

Decision:
- V0.1 passes the recovery hardness target for 3B: real-image pair accuracy is above 0.80 and caption-only pair accuracy is below 0.60.
- The first chart design failed and was replaced. The failed run is retained in `experiments/runs/fliptrack_v01_qwen25vl3b_real_20260708T043449Z`.

Problems:
- Artifact attacker gate found filename/path leakage; V0.1 should not be frozen for release until filenames are randomized and the attacker gate is rerun.
- Catch twins are not implemented yet.

Next actions:
- Randomize pair-member filenames and paths so `_a`/`_b` cannot be used by metadata attackers.
- Add catch twins before human audit.
