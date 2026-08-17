# HB P2.2 — informativeness gates (base 3B; stable+invariance member accuracy)

| cell | L1 | L2 | L3 | monotone | L1 band | L2 band | L3≥0.05 | L3 switch (sep.) |
|---|---:|---:|---:|---|---|---|---|---:|
| hier_chart_v2/s5_high | 0.4300 | 0.4500 | 0.1300 | **FAIL** | **FAIL** | PASS | PASS | 0.1200 |
| hier_chart_v2/s5_low | 0.9350 | 0.9100 | 0.3450 | PASS | PASS | **FAIL** | PASS | 0.3800 |
| hier_chart_v2/s9_high | 0.2850 | 0.2900 | 0.0650 | **FAIL** | **FAIL** | PASS | PASS | 0.0500 |
| hier_chart_v2/s9_low | 0.7700 | 0.7100 | 0.1050 | PASS | PASS | PASS | PASS | 0.3500 |

## Family-level L3 floor (≥ 0.05 in at least one cell)

- hier_chart_v2: PASS; cells passing every cell-level gate: ['s9_low']

Per-model per-layer accuracies (descriptive) are in the JSON.
