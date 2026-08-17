# HB P2.3 readout — attacker gates, blind floors, leak verification

Criterion: folded gate statistic <= 0.55 point AND folded CI upper <= 0.62, per attacker, pooled and per template.

## Attacker gate — `hier_coord_v1`

Gate status: **False** — checks `{"all_attackers_available": true, "all_point_estimates_at_most_0_55": false, "no_ci_upper_above_0_62": true}`; point failures: ['dinov2:hier_coord_v1_n20'].

| attacker | scope | folded stat | folded CI95 | unfolded AUC | unfolded CI95 | n pairs | flags |
|---|---|---|---|---|---|---|---|
| dinov2 | hier_coord_v1_n12 | 0.5048 | [0.5005, 0.5313] | 0.4952 | [0.4703, 0.5224] | 100 | — |
| dinov2 | hier_coord_v1_n20 | 0.5577 | [0.5305, 0.5897] | 0.5577 | [0.5305, 0.5897] | 100 | point>0.55 |
| dinov2 | hier_coord_v1_n8 | 0.5237 | [0.5008, 0.5607] | 0.5237 | [0.4887, 0.5607] | 100 | — |
| dinov2 | pooled | 0.5096 | [0.5005, 0.5282] | 0.5096 | [0.4914, 0.5282] | 300 | — |
| frequency_stat | hier_coord_v1_n12 | 0.5198 | [0.5016, 0.5466] | 0.5198 | [0.4955, 0.5466] | 100 | — |
| frequency_stat | hier_coord_v1_n20 | 0.5138 | [0.5008, 0.5478] | 0.5138 | [0.4817, 0.5478] | 100 | — |
| frequency_stat | hier_coord_v1_n8 | 0.5081 | [0.5008, 0.5448] | 0.4919 | [0.4552, 0.5249] | 100 | — |
| frequency_stat | pooled | 0.5096 | [0.5006, 0.5255] | 0.5096 | [0.4928, 0.5255] | 300 | — |
| metadata | hier_coord_v1_n12 | 0.5334 | [0.5132, 0.5578] | 0.5334 | [0.5132, 0.5578] | 100 | — |
| metadata | hier_coord_v1_n20 | 0.5321 | [0.5103, 0.5569] | 0.5321 | [0.5103, 0.5569] | 100 | — |
| metadata | hier_coord_v1_n8 | 0.5058 | [0.5004, 0.5291] | 0.5058 | [0.4850, 0.5290] | 100 | — |
| metadata | pooled | 0.5137 | [0.5078, 0.5209] | 0.5137 | [0.5078, 0.5209] | 300 | — |

## Attacker gate — `hier_chart_v1`

Gate status: **False** — checks `{"all_attackers_available": true, "all_point_estimates_at_most_0_55": false, "no_ci_upper_above_0_62": false}`; point failures: ['frequency_stat:pooled', 'frequency_stat:hier_chart_v1_s5_low', 'frequency_stat:hier_chart_v1_s9_high', 'frequency_stat:hier_chart_v1_s9_low', 'metadata:pooled', 'metadata:hier_chart_v1_s5_low', 'metadata:hier_chart_v1_s9_low', 'dinov2:pooled', 'dinov2:hier_chart_v1_s5_high', 'dinov2:hier_chart_v1_s5_low', 'dinov2:hier_chart_v1_s9_high', 'dinov2:hier_chart_v1_s9_low'].

| attacker | scope | folded stat | folded CI95 | unfolded AUC | unfolded CI95 | n pairs | flags |
|---|---|---|---|---|---|---|---|
| dinov2 | hier_chart_v1_s5_high | 0.5629 | [0.5247, 0.5992] | 0.5629 | [0.5247, 0.5992] | 100 | point>0.55 |
| dinov2 | hier_chart_v1_s5_low | 0.9190 | [0.8867, 0.9489] | 0.9190 | [0.8867, 0.9489] | 100 | point>0.55 ci_up>0.62 |
| dinov2 | hier_chart_v1_s9_high | 0.5609 | [0.5285, 0.5958] | 0.5609 | [0.5285, 0.5958] | 100 | point>0.55 |
| dinov2 | hier_chart_v1_s9_low | 0.7831 | [0.7436, 0.8263] | 0.7831 | [0.7436, 0.8263] | 100 | point>0.55 ci_up>0.62 |
| dinov2 | pooled | 0.6711 | [0.6472, 0.6969] | 0.6711 | [0.6472, 0.6969] | 400 | point>0.55 ci_up>0.62 |
| frequency_stat | hier_chart_v1_s5_high | 0.5184 | [0.5009, 0.5569] | 0.5184 | [0.4798, 0.5569] | 100 | — |
| frequency_stat | hier_chart_v1_s5_low | 0.9819 | [0.9658, 0.9962] | 0.9819 | [0.9658, 0.9962] | 100 | point>0.55 ci_up>0.62 |
| frequency_stat | hier_chart_v1_s9_high | 0.5906 | [0.5493, 0.6370] | 0.4094 | [0.3630, 0.4507] | 100 | point>0.55 ci_up>0.62 |
| frequency_stat | hier_chart_v1_s9_low | 0.8637 | [0.8203, 0.9063] | 0.8637 | [0.8203, 0.9063] | 100 | point>0.55 ci_up>0.62 |
| frequency_stat | pooled | 0.6957 | [0.6661, 0.7241] | 0.6957 | [0.6661, 0.7241] | 400 | point>0.55 ci_up>0.62 |
| metadata | hier_chart_v1_s5_high | 0.5166 | [0.5007, 0.5449] | 0.5166 | [0.4875, 0.5449] | 100 | — |
| metadata | hier_chart_v1_s5_low | 0.9315 | [0.9001, 0.9604] | 0.9315 | [0.9001, 0.9604] | 100 | point>0.55 ci_up>0.62 |
| metadata | hier_chart_v1_s9_high | 0.5066 | [0.5005, 0.5267] | 0.5066 | [0.4872, 0.5267] | 100 | — |
| metadata | hier_chart_v1_s9_low | 0.8103 | [0.7767, 0.8519] | 0.8103 | [0.7767, 0.8519] | 100 | point>0.55 ci_up>0.62 |
| metadata | pooled | 0.5910 | [0.5807, 0.6034] | 0.5910 | [0.5807, 0.6034] | 400 | point>0.55 |

## Blind floors (member accuracy, base 3B)

| cell | gray | no_image |
|---|---|---|
| hier_chart_v1_s5_high_l1 | 0.0000 | 0.0000 |
| hier_chart_v1_s5_high_l2 | 0.0000 | 0.0000 |
| hier_chart_v1_s5_high_l3 | 0.0000 | 0.0000 |
| hier_chart_v1_s5_high_probe | 0.0000 | 0.0000 |
| hier_chart_v1_s5_low_l1 | 0.0000 | 0.0000 |
| hier_chart_v1_s5_low_l2 | 0.0000 | 0.0000 |
| hier_chart_v1_s5_low_l3 | 0.0000 | 0.0000 |
| hier_chart_v1_s5_low_probe | 0.0000 | 0.0000 |
| hier_chart_v1_s9_high_l1 | 0.0000 | 0.0000 |
| hier_chart_v1_s9_high_l2 | 0.0000 | 0.0000 |
| hier_chart_v1_s9_high_l3 | 0.0000 | 0.0000 |
| hier_chart_v1_s9_high_probe | 0.0000 | 0.0000 |
| hier_chart_v1_s9_low_l1 | 0.0000 | 0.0000 |
| hier_chart_v1_s9_low_l2 | 0.0000 | 0.0000 |
| hier_chart_v1_s9_low_l3 | 0.0000 | 0.0000 |
| hier_chart_v1_s9_low_probe | 0.0000 | 0.0000 |
| hier_coord_v1_n12_l1 | 0.0950 | 0.1000 |
| hier_coord_v1_n12_l2 | 0.0950 | 0.1000 |
| hier_coord_v1_n12_l3 | 0.1133 | 0.1133 |
| hier_coord_v1_n12_probe | 0.0000 | 0.0000 |
| hier_coord_v1_n20_l1 | 0.1200 | 0.1200 |
| hier_coord_v1_n20_l2 | 0.1200 | 0.1200 |
| hier_coord_v1_n20_l3 | 0.1367 | 0.1367 |
| hier_coord_v1_n20_probe | 0.0000 | 0.0000 |
| hier_coord_v1_n8_l1 | 0.1550 | 0.1350 |
| hier_coord_v1_n8_l2 | 0.1550 | 0.1350 |
| hier_coord_v1_n8_l3 | 0.1200 | 0.1200 |
| hier_coord_v1_n8_probe | 0.0000 | 0.0000 |

## Leak verification (edit direction + PNG size, causal pairs)

| family | cell | role | n | value-delta neg | pos | multi-field | png edited>base | edited<base | mean delta (B) |
|---|---|---|---|---|---|---|---|---|---|
| hier_chart_v1 | s5_high | target_stable | 50 | 25 | 25 | 0 | 45 | 5 | +424 |
| hier_chart_v1 | s5_high | target_switch | 50 | 50 | 0 | 0 | 13 | 37 | -250 |
| hier_chart_v1 | s5_low | target_stable | 50 | 50 | 0 | 0 | 49 | 1 | +1521 |
| hier_chart_v1 | s5_low | target_switch | 50 | 50 | 0 | 0 | 50 | 0 | +1412 |
| hier_chart_v1 | s9_high | target_stable | 50 | 20 | 30 | 0 | 41 | 9 | +425 |
| hier_chart_v1 | s9_high | target_switch | 50 | 50 | 0 | 0 | 14 | 36 | -238 |
| hier_chart_v1 | s9_low | target_stable | 50 | 49 | 1 | 0 | 49 | 1 | +1510 |
| hier_chart_v1 | s9_low | target_switch | 50 | 50 | 0 | 0 | 50 | 0 | +1053 |
| hier_coord_v1 | n12 | target_stable | 50 | 26 | 24 | 0 | 19 | 28 | -33 |
| hier_coord_v1 | n12 | target_switch | 50 | 1 | 1 | 48 | 6 | 44 | -109 |
| hier_coord_v1 | n20 | target_stable | 50 | 20 | 30 | 0 | 21 | 29 | -27 |
| hier_coord_v1 | n20 | target_switch | 50 | 0 | 2 | 48 | 12 | 38 | -148 |
| hier_coord_v1 | n8 | target_stable | 50 | 16 | 34 | 0 | 23 | 25 | +9 |
| hier_coord_v1 | n8 | target_switch | 50 | 2 | 1 | 47 | 18 | 32 | -53 |
