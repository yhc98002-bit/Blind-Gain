# HB P2.2 — informativeness gates (base 3B; stable+invariance member accuracy)

| cell | L1 | L2 | L3 | monotone | L1 band | L2 band | L3≥0.05 | L3 switch (sep.) |
|---|---:|---:|---:|---|---|---|---|---:|
| hier_coord_v1/n12 | 0.6550 | 0.6150 | 0.3300 | PASS | PASS | PASS | PASS | 0.3900 |
| hier_coord_v1/n20 | 0.5300 | 0.5000 | 0.2800 | PASS | **FAIL** | PASS | PASS | 0.2000 |
| hier_coord_v1/n8 | 0.7050 | 0.6300 | 0.4250 | PASS | PASS | PASS | PASS | 0.3400 |

## Family-level L3 floor (≥ 0.05 in at least one cell)

- hier_coord_v1: PASS; cells passing every cell-level gate: ['n8', 'n12']

Per-model per-layer accuracies (descriptive) are in the JSON.
