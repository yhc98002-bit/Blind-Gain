# HB P2.2 — informativeness gates (base 3B; stable+invariance member accuracy)

| cell | L1 | L2 | L3 | monotone | L1 band | L2 band | L3≥0.05 | L3 switch (sep.) |
|---|---:|---:|---:|---|---|---|---|---:|
| hier_chart_v1/s5_high | 0.4950 | 0.5350 | 0.0950 | **FAIL** | **FAIL** | PASS | PASS | 0.0400 |
| hier_chart_v1/s5_low | 0.9050 | 0.8800 | 0.4250 | PASS | PASS | **FAIL** | PASS | 0.3000 |
| hier_chart_v1/s9_high | 0.4500 | 0.4450 | 0.0750 | PASS | **FAIL** | PASS | PASS | 0.0700 |
| hier_chart_v1/s9_low | 0.7950 | 0.7450 | 0.2000 | PASS | PASS | PASS | PASS | 0.2600 |
| hier_coord_v1/n12 | 0.6750 | 0.5950 | 0.3250 | PASS | PASS | PASS | PASS | 0.3700 |
| hier_coord_v1/n20 | 0.5750 | 0.5100 | 0.3150 | PASS | **FAIL** | PASS | PASS | 0.2100 |
| hier_coord_v1/n8 | 0.7250 | 0.6400 | 0.4250 | PASS | PASS | PASS | PASS | 0.3300 |

## Family-level L3 floor (≥ 0.05 in at least one cell)

- hier_coord_v1: PASS; cells passing every cell-level gate: ['n8', 'n12']
- hier_chart_v1: PASS; cells passing every cell-level gate: ['s9_low']

Per-model per-layer accuracies (descriptive) are in the JSON.
