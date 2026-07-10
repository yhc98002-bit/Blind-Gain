# FlipTrack V0.1 Re-scored With Final-Answer Scorer

Status:
- Cached V0.1 prediction shards were re-scored with the P0.1 final-answer-span scorer.
- Old scores below are recomputed from the previous full-text-scan semantics, not copied from stale aggregate files.
- Inflation is `old_pair_accuracy - new_pair_accuracy`; positive values indicate old full-text scanning inflated results.

Evidence:
- Source shards are under `experiments/runs/fliptrack_v01_*/*/shards/*.jsonl`.
- New scorer: `src/eval/fliptrack_metrics.py`.

## Aggregate Old vs New

| Model | Mode | N | Old pair | New pair | Inflation | New strict pair | Ambiguous rate | Full-text mentions both |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3B | real | 300 | 0.8933 | 0.8933 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 3B | gray | 300 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 3B | noise | 300 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 3B | caption | 300 | 0.1000 | 0.1000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 7B | real | 300 | 0.9333 | 0.9333 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 7B | gray | 300 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 7B | noise | 300 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 7B | caption | 300 | 0.5167 | 0.5133 | 0.0033 | 0.0000 | 0.0033 | 0.0033 |

## Per-template Old vs New Pair Accuracy

### 3B real

| Template | N | Old pair | New pair | Inflation | New member | New collapse | New ambiguous |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `dense_table_code_v01` | 100 | 0.9100 | 0.9100 | 0.0000 | 0.9450 | 0.0100 | 0.0000 |
| `starred_legend_label_v01` | 100 | 0.9500 | 0.9500 | 0.0000 | 0.9650 | 0.0000 | 0.0000 |
| `symbol_grid_v01` | 100 | 0.8200 | 0.8200 | 0.0000 | 0.8800 | 0.0800 | 0.0000 |

### 3B gray

| Template | N | Old pair | New pair | Inflation | New member | New collapse | New ambiguous |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `dense_table_code_v01` | 100 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| `starred_legend_label_v01` | 100 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| `symbol_grid_v01` | 100 | 0.0000 | 0.0000 | 0.0000 | 0.2400 | 1.0000 | 0.0000 |

### 3B noise

| Template | N | Old pair | New pair | Inflation | New member | New collapse | New ambiguous |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `dense_table_code_v01` | 100 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.7200 | 0.0000 |
| `starred_legend_label_v01` | 100 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.7400 | 0.0000 |
| `symbol_grid_v01` | 100 | 0.0000 | 0.0000 | 0.0000 | 0.2400 | 0.9400 | 0.0000 |

### 3B caption

| Template | N | Old pair | New pair | Inflation | New member | New collapse | New ambiguous |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `dense_table_code_v01` | 100 | 0.0500 | 0.0500 | 0.0000 | 0.0700 | 0.5600 | 0.0000 |
| `starred_legend_label_v01` | 100 | 0.1500 | 0.1500 | 0.0000 | 0.4150 | 0.1500 | 0.0000 |
| `symbol_grid_v01` | 100 | 0.1000 | 0.1000 | 0.0000 | 0.3150 | 0.5800 | 0.0000 |

### 7B real

| Template | N | Old pair | New pair | Inflation | New member | New collapse | New ambiguous |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `dense_table_code_v01` | 100 | 0.9900 | 0.9900 | 0.0000 | 0.9950 | 0.0000 | 0.0000 |
| `starred_legend_label_v01` | 100 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |
| `symbol_grid_v01` | 100 | 0.8100 | 0.8100 | 0.0000 | 0.9000 | 0.0400 | 0.0000 |

### 7B gray

| Template | N | Old pair | New pair | Inflation | New member | New collapse | New ambiguous |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `dense_table_code_v01` | 100 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| `starred_legend_label_v01` | 100 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| `symbol_grid_v01` | 100 | 0.0000 | 0.0000 | 0.0000 | 0.2400 | 1.0000 | 0.0000 |

### 7B noise

| Template | N | Old pair | New pair | Inflation | New member | New collapse | New ambiguous |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `dense_table_code_v01` | 100 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.6500 | 0.0000 |
| `starred_legend_label_v01` | 100 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.8300 | 0.0000 |
| `symbol_grid_v01` | 100 | 0.0000 | 0.0000 | 0.0000 | 0.2400 | 1.0000 | 0.0000 |

### 7B caption

| Template | N | Old pair | New pair | Inflation | New member | New collapse | New ambiguous |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `dense_table_code_v01` | 100 | 0.0900 | 0.0900 | 0.0000 | 0.2300 | 0.3700 | 0.0000 |
| `starred_legend_label_v01` | 100 | 0.8800 | 0.8800 | 0.0000 | 0.9350 | 0.0100 | 0.0000 |
| `symbol_grid_v01` | 100 | 0.5800 | 0.5700 | 0.0100 | 0.7400 | 0.1400 | 0.0100 |

Decision:
- Observed aggregate inflation range: 0.0000 to 0.0033.
- Any positive inflation should be treated as measurement repair, not model change.

Next actions:
- Use these new scorer outputs for V0.2 scoring and all future benchmark tables.
- Do not compare future P0.1-scored numbers against stale full-text-scan aggregates without labeling the scorer version.
