# HB P2.2 — informativeness gates (base 3B; stable+invariance member accuracy)

| cell | L1 | L2 | L3 | monotone | L1 band | L2 band | L3≥0.05 | L3 switch (sep.) |
|---|---:|---:|---:|---|---|---|---|---:|
| hier_chart_v3/s9_high | 0.4500 | 0.4300 | 0.0750 | PASS | **FAIL** | PASS | PASS | 0.0600 |
| hier_chart_v3/s9_low | 0.7250 | 0.7000 | 0.1200 | PASS | PASS | PASS | PASS | 0.2600 |

## Family-level L3 floor (≥ 0.05 in at least one cell)

- hier_chart_v3: PASS; cells passing every cell-level gate: ['s9_low']

Per-model per-layer accuracies (descriptive) are in the JSON.
