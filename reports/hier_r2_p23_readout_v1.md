# HB P2.3 readout — attacker gates, blind floors, leak verification

Criterion: folded gate statistic <= 0.55 point AND folded CI upper <= 0.62, per attacker, pooled and per template.

## Attacker gate — `hier_coord_v1`

Gate status: **False** — checks `{"all_attackers_available": true, "all_point_estimates_at_most_0_55": false, "no_ci_upper_above_0_62": true}`; point failures: ['dinov2:hier_coord_v1_n12'].

| attacker | scope | folded stat | folded CI95 | unfolded AUC | unfolded CI95 | n pairs | flags |
|---|---|---|---|---|---|---|---|
| dinov2 | hier_coord_v1_n12 | 0.5569 | [0.5252, 0.5954] | 0.5569 | [0.5252, 0.5954] | 100 | point>0.55 |
| dinov2 | hier_coord_v1_n20 | 0.5474 | [0.5207, 0.5762] | 0.5474 | [0.5207, 0.5762] | 100 | — |
| dinov2 | hier_coord_v1_n8 | 0.5258 | [0.5012, 0.5663] | 0.4742 | [0.4337, 0.5127] | 100 | — |
| dinov2 | pooled | 0.5159 | [0.5012, 0.5348] | 0.5159 | [0.4970, 0.5348] | 300 | — |
| file_size | hier_coord_v1_n12 | 0.5329 | [0.5135, 0.5561] | 0.5329 | [0.5135, 0.5561] | 100 | — |
| file_size | hier_coord_v1_n20 | 0.5362 | [0.5119, 0.5613] | 0.5362 | [0.5119, 0.5613] | 100 | — |
| file_size | hier_coord_v1_n8 | 0.5097 | [0.5004, 0.5342] | 0.5097 | [0.4891, 0.5342] | 100 | — |
| file_size | pooled | 0.5092 | [0.5054, 0.5146] | 0.5092 | [0.5054, 0.5146] | 300 | — |
| frequency_stat | hier_coord_v1_n12 | 0.5325 | [0.5045, 0.5665] | 0.5325 | [0.5023, 0.5665] | 100 | — |
| frequency_stat | hier_coord_v1_n20 | 0.5091 | [0.5006, 0.5415] | 0.5091 | [0.4803, 0.5415] | 100 | — |
| frequency_stat | hier_coord_v1_n8 | 0.5039 | [0.5004, 0.5274] | 0.5039 | [0.4806, 0.5273] | 100 | — |
| frequency_stat | pooled | 0.5103 | [0.5008, 0.5250] | 0.5103 | [0.4944, 0.5250] | 300 | — |
| metadata | hier_coord_v1_n12 | 0.5310 | [0.5109, 0.5552] | 0.5310 | [0.5109, 0.5552] | 100 | — |
| metadata | hier_coord_v1_n20 | 0.5362 | [0.5149, 0.5614] | 0.5362 | [0.5149, 0.5614] | 100 | — |
| metadata | hier_coord_v1_n8 | 0.5063 | [0.5005, 0.5299] | 0.5063 | [0.4860, 0.5298] | 100 | — |
| metadata | pooled | 0.5136 | [0.5072, 0.5210] | 0.5136 | [0.5072, 0.5210] | 300 | — |

## Blind floors (member accuracy, base 3B)

| cell | gray | no_image |
|---|---|---|
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
