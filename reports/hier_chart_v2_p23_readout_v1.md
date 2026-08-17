# HB P2.3 readout — attacker gates, blind floors, leak verification

Criterion: folded gate statistic <= 0.55 point AND folded CI upper <= 0.62, per attacker, pooled and per template.

## Attacker gate — `hier_chart_v2`

Gate status: **False** — checks `{"all_attackers_available": true, "all_point_estimates_at_most_0_55": false, "no_ci_upper_above_0_62": false}`; point failures: ['file_size:pooled', 'file_size:hier_chart_v2_s5_low', 'file_size:hier_chart_v2_s9_low', 'frequency_stat:pooled', 'frequency_stat:hier_chart_v2_s5_low', 'frequency_stat:hier_chart_v2_s9_low', 'metadata:pooled', 'metadata:hier_chart_v2_s5_low', 'metadata:hier_chart_v2_s9_low', 'dinov2:pooled', 'dinov2:hier_chart_v2_s5_low', 'dinov2:hier_chart_v2_s9_low'].

| attacker | scope | folded stat | folded CI95 | unfolded AUC | unfolded CI95 | n pairs | flags |
|---|---|---|---|---|---|---|---|
| dinov2 | hier_chart_v2_s5_high | 0.5084 | [0.5005, 0.5410] | 0.5084 | [0.4781, 0.5409] | 100 | — |
| dinov2 | hier_chart_v2_s5_low | 0.9999 | [0.9994, 1.0000] | 0.9999 | [0.9994, 1.0000] | 100 | point>0.55 ci_up>0.62 |
| dinov2 | hier_chart_v2_s9_high | 0.5056 | [0.5007, 0.5416] | 0.5056 | [0.4727, 0.5404] | 100 | — |
| dinov2 | hier_chart_v2_s9_low | 0.7596 | [0.7223, 0.8038] | 0.7596 | [0.7223, 0.8038] | 100 | point>0.55 ci_up>0.62 |
| dinov2 | pooled | 0.6758 | [0.6510, 0.7031] | 0.6758 | [0.6510, 0.7031] | 400 | point>0.55 ci_up>0.62 |
| file_size | hier_chart_v2_s5_high | 0.5230 | [0.5065, 0.5399] | 0.4770 | [0.4601, 0.4935] | 100 | — |
| file_size | hier_chart_v2_s5_low | 0.9813 | [0.9693, 0.9914] | 0.9813 | [0.9693, 0.9914] | 100 | point>0.55 ci_up>0.62 |
| file_size | hier_chart_v2_s9_high | 0.5032 | [0.5003, 0.5233] | 0.5032 | [0.4819, 0.5224] | 100 | — |
| file_size | hier_chart_v2_s9_low | 0.8637 | [0.8277, 0.9049] | 0.8637 | [0.8277, 0.9049] | 100 | point>0.55 ci_up>0.62 |
| file_size | pooled | 0.5603 | [0.5502, 0.5735] | 0.5603 | [0.5502, 0.5735] | 400 | point>0.55 |
| frequency_stat | hier_chart_v2_s5_high | 0.5269 | [0.5013, 0.5708] | 0.4731 | [0.4292, 0.5154] | 100 | — |
| frequency_stat | hier_chart_v2_s5_low | 1.0000 | [1.0000, 1.0000] | 1.0000 | [1.0000, 1.0000] | 100 | point>0.55 ci_up>0.62 |
| frequency_stat | hier_chart_v2_s9_high | 0.5361 | [0.5032, 0.5748] | 0.4639 | [0.4252, 0.5012] | 100 | — |
| frequency_stat | hier_chart_v2_s9_low | 0.8181 | [0.7737, 0.8614] | 0.8181 | [0.7737, 0.8614] | 100 | point>0.55 ci_up>0.62 |
| frequency_stat | pooled | 0.7262 | [0.6988, 0.7561] | 0.7262 | [0.6988, 0.7561] | 400 | point>0.55 ci_up>0.62 |
| metadata | hier_chart_v2_s5_high | 0.5278 | [0.5108, 0.5477] | 0.4722 | [0.4523, 0.4892] | 100 | — |
| metadata | hier_chart_v2_s5_low | 0.9771 | [0.9628, 0.9887] | 0.9771 | [0.9628, 0.9887] | 100 | point>0.55 ci_up>0.62 |
| metadata | hier_chart_v2_s9_high | 0.5017 | [0.5003, 0.5197] | 0.4983 | [0.4804, 0.5143] | 100 | — |
| metadata | hier_chart_v2_s9_low | 0.8823 | [0.8483, 0.9161] | 0.8823 | [0.8483, 0.9161] | 100 | point>0.55 ci_up>0.62 |
| metadata | pooled | 0.6003 | [0.5877, 0.6157] | 0.6003 | [0.5877, 0.6157] | 400 | point>0.55 |

## Blind floors (member accuracy, base 3B)

| cell | gray | no_image |
|---|---|---|
| hier_chart_v2_s5_high_l1 | 0.0000 | 0.0000 |
| hier_chart_v2_s5_high_l2 | 0.0000 | 0.0000 |
| hier_chart_v2_s5_high_l3 | 0.0000 | 0.0000 |
| hier_chart_v2_s5_high_probe | 0.0000 | 0.0000 |
| hier_chart_v2_s5_low_l1 | 0.0000 | 0.0000 |
| hier_chart_v2_s5_low_l2 | 0.0000 | 0.0000 |
| hier_chart_v2_s5_low_l3 | 0.0000 | 0.0000 |
| hier_chart_v2_s5_low_probe | 0.0000 | 0.0000 |
| hier_chart_v2_s9_high_l1 | 0.0000 | 0.0000 |
| hier_chart_v2_s9_high_l2 | 0.0000 | 0.0000 |
| hier_chart_v2_s9_high_l3 | 0.0000 | 0.0000 |
| hier_chart_v2_s9_high_probe | 0.0000 | 0.0000 |
| hier_chart_v2_s9_low_l1 | 0.0000 | 0.0000 |
| hier_chart_v2_s9_low_l2 | 0.0000 | 0.0000 |
| hier_chart_v2_s9_low_l3 | 0.0000 | 0.0000 |
| hier_chart_v2_s9_low_probe | 0.0000 | 0.0000 |
