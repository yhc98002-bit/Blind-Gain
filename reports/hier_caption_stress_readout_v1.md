# HB P2.3 caption-stress readout (72B captions -> base-3B QA)

Caption run: `experiments/runs/strong_caption_store_hier_v1_l3_an29_20260817T021703Z` · QA run: `experiments/runs/hier_caption_qa_base3b_an29_gpu0_20260817T003723Z`.
No registered HB caption ceiling exists yet (P3-freeze prerequisite); numbers as measured.

## `hier_coord_v1` — caption member accuracy 0.2367 (300 pairs)

| cell/role | n members | caption member acc | blind gray L3 |
|---|---|---|---|
| n12/target_stable | 100 | 0.2400 | 0.1133 |
| n12/target_switch | 100 | 0.2500 | 0.1133 |
| n20/target_stable | 100 | 0.1700 | 0.1367 |
| n20/target_switch | 100 | 0.1100 | 0.1367 |
| n8/target_stable | 100 | 0.3700 | 0.1200 |
| n8/target_switch | 100 | 0.2800 | 0.1200 |

## `hier_chart_v1` — caption member accuracy 0.0413 (400 pairs)

| cell/role | n members | caption member acc | blind gray L3 |
|---|---|---|---|
| s5_high/target_stable | 100 | 0.0400 | 0.0000 |
| s5_high/target_switch | 100 | 0.0000 | 0.0000 |
| s5_low/target_stable | 100 | 0.0400 | 0.0000 |
| s5_low/target_switch | 100 | 0.0500 | 0.0000 |
| s9_high/target_stable | 100 | 0.0400 | 0.0000 |
| s9_high/target_switch | 100 | 0.0300 | 0.0000 |
| s9_low/target_stable | 100 | 0.0700 | 0.0000 |
| s9_low/target_switch | 100 | 0.0600 | 0.0000 |
