# M7 R3 Readout V2 (registered two-seed estimator)

Status: `complete`.

Scope:
- Seed scope: the registered two-seed estimator over both fixed M7 seeds (1 and 2) for all four arms. gain[b,s] is the mean across the two seeds of Acc_final(step_final) - Acc_final(step_0) on paired held-out items, taken per item before any stratum mean, ratio, rank statistic or bootstrap draw (docs/registered_m7_amendment_v1.md:52-53). step_0 is the shared base model and is never checkpointed, so one step-0 cell per arm serves both seeds (docs/registered_m7_seed_scope_v1.md:62-64, docs/registered_pilot_seed23_v1.md:19).
- Between-seed dispersion: measured and reported descriptively in payload['seed_dispersion']; n_seeds = 2, so no seed-level interval, test, or replication claim is registered or made. Item-paired bootstrap uncertainty does not replace seed dispersion and seed dispersion does not replace it (docs/registered_m7_amendment_v1.md:81-82, docs/registered_extensions_v1.md:143).
- Seed mean is taken per item, before any stratum mean, ratio, rank statistic or bootstrap draw.
- Step-0 reuse: the four step-0 cells are seed-independent and one set serves both seeds (under a shared step_0, mean_over_seeds(Acc_100,seed - Acc_0) = mean_over_seeds(Acc_100,seed) - Acc_0 exactly; the step-0 term is shared, not averaged).
- PI sign-off flag: docs/registered_m7_seed_scope_v1.md:39-40 reads 'Every M7 readout must carry the scope tag "one seed" wherever a gain, recovery or correlation is reported.' That sentence was written for the seed-1-only regime it introduces at lines 23-26. This readout keeps a scope tag on every gain, recovery and correlation but sets its value to the true scope; it does not print the literal string 'one seed' on a two-seed number. That literal wording is the one line a two-seed readout contradicts and is flagged here rather than silently reinterpreted.
- Single-image restriction: M7 is restricted to single-image rows (worker.rollout.limit_images=1); retained 23,542/25,255 train rows (93.2%) and 4,239/4,501 held-out rows (94.2%) (docs/registered_m7_single_image_v2.md).
- Pooled-only readout is prohibited; corpus aggregate, every joint stratum, and source-only/category-only descriptive tables are all published; A2/A2b/A3 are never pooled into one generic blind arm (docs/registered_extensions_v1.md Extension 3, docs/registered_m7_amendment_v1.md).
- This report contains numbers and provenance only; interpretation is reserved to the PIs.

Machine artifact: `tmp/r3_md_refresh/out.json`.

## Strata accounting

- Joint (source, category) strata recounted from `data/virl39k_m7_heldout_v3.jsonl`: 60 total, 22 eligible (>= 30 held-out items), 38 descriptive-small-n.
- Eligibility depends only on sample count, never on a model outcome; descriptive-small-n strata are published, not merged or discarded, and enter no rank statistic.

## Corpus aggregate (two seeds (seeds 1, 2; registered two-seed mean))

| Arm | n | q_bar | Acc_final step 0 | Acc_final step 100 | Gain (95% CI) |
|---|---:|---:|---:|---:|---:|
| A1 real | 4239 | 0.5122 | 0.2744 | 0.4788 | 0.2044 [0.1898, 0.2189] |
| A2 gray | 4239 | 0.4235 | 0.1894 | 0.3379 | 0.1485 [0.1359, 0.1615] |
| A2b no-image | 4239 | 0.4154 | 0.1538 | 0.2996 | 0.1458 [0.1332, 0.1583] |
| A3 caption | 4239 | 0.4458 | 0.1849 | 0.3657 | 0.1807 [0.1673, 0.1939] |

Corpus A1 denominator: estimate 0.2044, paired SE 0.0075, stable `true` (rule: gain[A1] > 0 and gain[A1] >= 2 * paired_se).

| Blind arm | Aggregate recovery (95% CI) | Status | Undefined draws | Interval label |
|---|---:|---|---:|---|
| A2 gray | 0.7265 [0.6592, 0.7961] | stable | 0/5000 | stable |
| A2b no-image | 0.7132 [0.6483, 0.7844] | stable | 0/5000 | stable |
| A3 caption | 0.8840 [0.8091, 0.9632] | stable | 0/5000 | stable |

## Registered joint strata: q_bar (22 eligible)

| Source | Category | n | q_bar A1 | q_bar A2 | q_bar A2b | q_bar A3 |
|---|---|---:|---:|---:|---:|---:|
| K12 | (GradeSchool) Non-Geo Math | 147 | 0.6598 | 0.5015 | 0.5027 | 0.5808 |
| M3CoT | (GradeSchool) Science | 65 | 0.2325 | 0.1877 | 0.1972 | 0.1868 |
| M3CoT | Social Science | 53 | 0.2124 | 0.1906 | 0.1648 | 0.1682 |
| MMK12 | (GradeSchool) Geometric | 653 | 0.5573 | 0.5329 | 0.5325 | 0.4946 |
| MMK12 | (GradeSchool) Non-Geo Math | 456 | 0.5363 | 0.4105 | 0.4125 | 0.4830 |
| MMK12 | (GradeSchool) Science | 203 | 0.7115 | 0.6981 | 0.6646 | 0.5123 |
| MMK12 | Broader STEM Topics | 60 | 0.6298 | 0.2683 | 0.2751 | 0.5655 |
| MMK12 | Spatial Reasoning | 113 | 0.5662 | 0.4898 | 0.4780 | 0.4374 |
| MMK12 | Tables/Diagrams/Charts | 239 | 0.5379 | 0.2769 | 0.2624 | 0.4466 |
| MMMath | (GradeSchool) Non-Geo Math | 428 | 0.5649 | 0.5441 | 0.5471 | 0.5436 |
| Processed | (GradeSchool) Geometric | 340 | 0.4069 | 0.3554 | 0.3593 | 0.3798 |
| Processed | (GradeSchool) Non-Geo Math | 457 | 0.4459 | 0.3561 | 0.3562 | 0.4106 |
| Processed | (GradeSchool) Science | 74 | 0.3497 | 0.3311 | 0.3242 | 0.3338 |
| Processed | Broader STEM Topics | 66 | 0.6611 | 0.6457 | 0.6094 | 0.6057 |
| Processed | Spatial Reasoning | 86 | 0.3895 | 0.2505 | 0.2126 | 0.3015 |
| Processed | Tables/Diagrams/Charts | 173 | 0.4473 | 0.3399 | 0.3103 | 0.3817 |
| R1OneVision | (GradeSchool) Science | 50 | 0.2661 | 0.2344 | 0.2250 | 0.2795 |
| ScienceQA | (GradeSchool) Science | 34 | 0.1659 | 0.1591 | 0.1523 | 0.1915 |
| ai2d | Tables/Diagrams/Charts | 107 | 0.7360 | 0.5142 | 0.4588 | 0.5590 |
| dvqa | Tables/Diagrams/Charts | 69 | 0.6567 | 0.1521 | 0.1454 | 0.4122 |
| geoqa_plus | (GradeSchool) Geometric | 118 | 0.5632 | 0.5488 | 0.5522 | 0.4505 |
| geoqa_plusConverted | (GradeSchool) Geometric | 34 | 0.5386 | 0.4934 | 0.4304 | 0.4173 |

## Registered joint strata: gains (two seeds (seeds 1, 2; registered two-seed mean))

| Source | Category | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) | A1 stable |
|---|---|---:|---:|---:|---:|---:|---|
| K12 | (GradeSchool) Non-Geo Math | 147 | 0.0816 [0.0068, 0.1599] | 0.0442 [-0.0102, 0.0986] | 0.0850 [0.0238, 0.1463] | 0.0374 [-0.0374, 0.1122] | true |
| M3CoT | (GradeSchool) Science | 65 | 0.5692 [0.4538, 0.6769] | 0.2846 [0.2000, 0.3769] | 0.3000 [0.2000, 0.4000] | 0.3385 [0.2385, 0.4462] | true |
| M3CoT | Social Science | 53 | 0.5472 [0.4340, 0.6604] | 0.3113 [0.2075, 0.4245] | 0.3208 [0.1981, 0.4434] | 0.4811 [0.3585, 0.5943] | true |
| MMK12 | (GradeSchool) Geometric | 653 | 0.1470 [0.1141, 0.1807] | 0.1355 [0.1026, 0.1677] | 0.1210 [0.0888, 0.1547] | 0.0919 [0.0597, 0.1233] | true |
| MMK12 | (GradeSchool) Non-Geo Math | 456 | 0.0252 [-0.0099, 0.0592] | 0.0351 [0.0044, 0.0647] | 0.0548 [0.0274, 0.0811] | 0.0866 [0.0548, 0.1184] | false |
| MMK12 | (GradeSchool) Science | 203 | 0.1059 [0.0443, 0.1700] | 0.0911 [0.0222, 0.1601] | 0.0764 [0.0049, 0.1478] | 0.2463 [0.1798, 0.3128] | true |
| MMK12 | Broader STEM Topics | 60 | 0.0667 [-0.0583, 0.1917] | 0.0500 [-0.0500, 0.1500] | 0.0833 [0.0333, 0.1417] | 0.0750 [-0.0250, 0.1750] | false |
| MMK12 | Spatial Reasoning | 113 | 0.1018 [0.0265, 0.1770] | -0.0088 [-0.0796, 0.0619] | 0.0088 [-0.0487, 0.0664] | 0.0133 [-0.0531, 0.0841] | true |
| MMK12 | Tables/Diagrams/Charts | 239 | 0.0711 [0.0188, 0.1213] | 0.0105 [-0.0230, 0.0418] | 0.0126 [-0.0105, 0.0356] | 0.0774 [0.0356, 0.1192] | true |
| MMMath | (GradeSchool) Non-Geo Math | 428 | 0.0724 [0.0362, 0.1098] | 0.0572 [0.0187, 0.0947] | 0.0584 [0.0222, 0.0935] | 0.0526 [0.0175, 0.0876] | true |
| Processed | (GradeSchool) Geometric | 340 | 0.2632 [0.2103, 0.3147] | 0.2147 [0.1662, 0.2618] | 0.2176 [0.1691, 0.2662] | 0.2485 [0.1971, 0.3000] | true |
| Processed | (GradeSchool) Non-Geo Math | 457 | 0.3600 [0.3140, 0.4070] | 0.2932 [0.2516, 0.3359] | 0.2418 [0.2002, 0.2845] | 0.3009 [0.2560, 0.3457] | true |
| Processed | (GradeSchool) Science | 74 | 0.4189 [0.2973, 0.5338] | 0.3581 [0.2432, 0.4662] | 0.3378 [0.2365, 0.4459] | 0.4054 [0.2973, 0.5135] | true |
| Processed | Broader STEM Topics | 66 | 0.1667 [0.0303, 0.3030] | 0.1894 [0.0758, 0.3030] | 0.1061 [-0.0303, 0.2424] | 0.1894 [0.0682, 0.3106] | true |
| Processed | Spatial Reasoning | 86 | 0.3140 [0.2093, 0.4244] | 0.1453 [0.0756, 0.2151] | 0.1570 [0.0930, 0.2267] | 0.2267 [0.1279, 0.3256] | true |
| Processed | Tables/Diagrams/Charts | 173 | 0.3671 [0.2861, 0.4509] | 0.2168 [0.1474, 0.2862] | 0.1821 [0.1098, 0.2543] | 0.3410 [0.2601, 0.4220] | true |
| R1OneVision | (GradeSchool) Science | 50 | 0.3100 [0.1900, 0.4300] | 0.2800 [0.1300, 0.4200] | 0.2700 [0.1500, 0.4000] | 0.3500 [0.2400, 0.4600] | true |
| ScienceQA | (GradeSchool) Science | 34 | 0.6765 [0.5441, 0.7941] | 0.6029 [0.4265, 0.7647] | 0.5882 [0.4412, 0.7206] | 0.6618 [0.5294, 0.7941] | true |
| ai2d | Tables/Diagrams/Charts | 107 | 0.1262 [0.0187, 0.2336] | 0.1028 [0.0187, 0.1869] | 0.2103 [0.1215, 0.2991] | 0.0981 [0.0093, 0.1869] | true |
| dvqa | Tables/Diagrams/Charts | 69 | 0.5797 [0.4493, 0.7029] | 0.0362 [0.0072, 0.0725] | 0.0435 [0.0072, 0.0870] | 0.3841 [0.2754, 0.5000] | true |
| geoqa_plus | (GradeSchool) Geometric | 118 | 0.3602 [0.2712, 0.4492] | 0.3390 [0.2458, 0.4280] | 0.2924 [0.2034, 0.3814] | 0.3390 [0.2627, 0.4153] | true |
| geoqa_plusConverted | (GradeSchool) Geometric | 34 | 0.2647 [0.0735, 0.4559] | 0.1029 [-0.0882, 0.2794] | 0.2206 [0.0882, 0.3676] | 0.2500 [0.0735, 0.4118] | true |

## Registered joint strata: recovery (two seeds (seeds 1, 2; registered two-seed mean))

Recovery is `gain[b,s] / gain[A1,s]` only when the A1 denominator is stable (gain[A1,s] > 0 and >= 2 paired SE); otherwise `undefined-unstable-denominator`. Unstable strata stay in the gain analysis and are omitted from the recovery rank statistic.

| Source | Category | A2 recovery (95% CI) | A2b recovery (95% CI) | A3 recovery (95% CI) |
|---|---|---:|---:|---:|
| K12 | (GradeSchool) Non-Geo Math | 0.5417 [-0.2778, 3.6000] | 1.0417 [0.1297, 5.1667] | 0.4583 [-0.9019, 2.5647] |
| M3CoT | (GradeSchool) Science | 0.5000 [0.3506, 0.6622] | 0.5270 [0.3571, 0.7286] | 0.5946 [0.4353, 0.7662] |
| M3CoT | Social Science | 0.5690 [0.3750, 0.8070] | 0.5862 [0.3750, 0.8163] | 0.8793 [0.6508, 1.1667] |
| MMK12 | (GradeSchool) Geometric | 0.9219 [0.6784, 1.2357] | 0.8229 [0.5829, 1.1266] | 0.6250 [0.3957, 0.9054] |
| MMK12 | (GradeSchool) Non-Geo Math | undefined-unstable-denominator | undefined-unstable-denominator | undefined-unstable-denominator |
| MMK12 | (GradeSchool) Science | 0.8605 [0.2551, 2.1820] | 0.7209 [0.0417, 2.0626] | 2.3256 [1.3749, 5.5918] |
| MMK12 | Broader STEM Topics | undefined-unstable-denominator | undefined-unstable-denominator | undefined-unstable-denominator |
| MMK12 | Spatial Reasoning | -0.0870 [-1.1462, 0.8495] | 0.0870 [-0.6000, 1.0000] | 0.1304 [-0.7324, 1.1603] |
| MMK12 | Tables/Diagrams/Charts | 0.1471 [-0.4462, 0.8000] | 0.1765 [-0.1936, 0.8505] | 1.0882 [0.4000, 3.8025] |
| MMMath | (GradeSchool) Non-Geo Math | 0.7903 [0.2467, 1.8002] | 0.8065 [0.3000, 1.7805] | 0.7258 [0.2394, 1.6757] |
| Processed | (GradeSchool) Geometric | 0.8156 [0.6337, 1.0373] | 0.8268 [0.6324, 1.0719] | 0.9441 [0.7282, 1.2096] |
| Processed | (GradeSchool) Non-Geo Math | 0.8146 [0.6987, 0.9482] | 0.6717 [0.5592, 0.7960] | 0.8359 [0.7167, 0.9725] |
| Processed | (GradeSchool) Science | 0.8548 [0.6429, 1.1311] | 0.8065 [0.5775, 1.0980] | 0.9677 [0.7143, 1.3182] |
| Processed | Broader STEM Topics | 1.1364 [0.4368, 4.1250] | 0.6364 [-0.2857, 2.5000] | 1.1364 [0.3500, 4.4286] |
| Processed | Spatial Reasoning | 0.4630 [0.2545, 0.7297] | 0.5000 [0.3013, 0.8043] | 0.7222 [0.4081, 1.1702] |
| Processed | Tables/Diagrams/Charts | 0.5906 [0.4031, 0.8072] | 0.4961 [0.3103, 0.7064] | 0.9291 [0.7333, 1.1811] |
| R1OneVision | (GradeSchool) Science | 0.9032 [0.5000, 1.3913] | 0.8710 [0.5517, 1.2333] | 1.1290 [0.8214, 1.6522] |
| ScienceQA | (GradeSchool) Science | 0.8913 [0.6591, 1.0952] | 0.8696 [0.7083, 1.0526] | 0.9783 [0.7778, 1.2273] |
| ai2d | Tables/Diagrams/Charts | 0.8148 [0.0935, 3.6927] | 1.6667 [0.7550, 6.7143] | 0.7778 [-0.0307, 3.5208] |
| dvqa | Tables/Diagrams/Charts | 0.0625 [0.0139, 0.1163] | 0.0750 [0.0143, 0.1486] | 0.6625 [0.4471, 0.9726] |
| geoqa_plus | (GradeSchool) Geometric | 0.9412 [0.6896, 1.2931] | 0.8118 [0.5663, 1.1316] | 0.9412 [0.7179, 1.2381] |
| geoqa_plusConverted | (GradeSchool) Geometric | 0.3889 [-0.3546, 1.7867] | 0.8333 [0.2778, 2.7500] | 0.9444 [0.2593, 3.2100] |

## Descriptive small-n strata (38)

Published per registration; not merged, not discarded, not in any rank statistic.

| Source | Category | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) |
|---|---|---:|---:|---:|---:|---:|
| M3CoT | (GradeSchool) Geometric | 6 | -0.2500 [-0.5833, 0.0000] | 0.1667 [-0.3333, 0.6667] | 0.5000 [0.1667, 0.8333] | 0.1667 [0.0000, 0.3333] |
| M3CoT | (GradeSchool) Non-Geo Math | 11 | -0.1364 [-0.4091, 0.0909] | 0.1364 [0.0000, 0.2727] | 0.3182 [0.1364, 0.5000] | 0.0909 [0.0000, 0.2273] |
| M3CoT | Broader STEM Topics | 1 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| M3CoT | Commonsense | 12 | 0.4167 [0.2083, 0.6250] | 0.5417 [0.3333, 0.7500] | 0.2917 [0.0833, 0.5000] | 0.5417 [0.2917, 0.7917] |
| M3CoT | Spatial Reasoning | 20 | 0.3250 [0.1500, 0.5250] | 0.3500 [0.1750, 0.5250] | 0.3000 [0.1250, 0.4750] | 0.1750 [0.0500, 0.3250] |
| M3CoT | Tables/Diagrams/Charts | 7 | 0.2143 [0.0000, 0.5000] | 0.1429 [0.0000, 0.4286] | 0.2143 [0.0714, 0.4286] | 0.3571 [0.1429, 0.6429] |
| M3CoTConverted | (GradeSchool) Science | 6 | 0.1667 [0.0000, 0.3333] | 0.0000 [0.0000, 0.0000] | 0.0833 [0.0000, 0.2500] | 0.0833 [0.0000, 0.2500] |
| M3CoTConverted | Social Science | 5 | 0.4000 [0.1000, 0.7000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.1000 [0.0000, 0.3000] |
| M3CoTConverted | Spatial Reasoning | 2 | 0.0000 [0.0000, 0.0000] | 0.2500 [0.0000, 0.5000] | 0.2500 [0.0000, 0.5000] | 0.0000 [0.0000, 0.0000] |
| M3CoTConverted | Tables/Diagrams/Charts | 3 | -0.1667 [-0.5000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.3333 [0.0000, 1.0000] |
| MMK12 | Social Science | 3 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| MMK12Converted | (GradeSchool) Geometric | 13 | 0.2308 [-0.0769, 0.5000] | 0.1538 [-0.0385, 0.3462] | 0.2308 [-0.0385, 0.5000] | 0.0769 [-0.2308, 0.3846] |
| MMK12Converted | (GradeSchool) Non-Geo Math | 2 | 1.0000 [1.0000, 1.0000] | 0.2500 [0.0000, 0.5000] | 0.2500 [0.0000, 0.5000] | 0.5000 [0.5000, 0.5000] |
| MMK12Converted | (GradeSchool) Science | 8 | 0.0625 [-0.1875, 0.3750] | 0.3125 [-0.0625, 0.6875] | 0.2500 [0.0000, 0.6250] | 0.2500 [0.0000, 0.6250] |
| MMK12Converted | Broader STEM Topics | 1 | 0.0000 [0.0000, 0.0000] | 0.5000 [0.5000, 0.5000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| MMK12Converted | Spatial Reasoning | 1 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| MMK12Converted | Tables/Diagrams/Charts | 2 | 0.2500 [0.0000, 0.5000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.2500 [0.0000, 0.5000] |
| Processed | Commonsense | 1 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| Processed | Social Science | 4 | 0.5000 [0.0000, 1.0000] | 0.1250 [0.0000, 0.3750] | 0.1250 [0.0000, 0.3750] | 0.0000 [0.0000, 0.0000] |
| R1OneVision | (GradeSchool) Geometric | 12 | 0.1250 [-0.2083, 0.4583] | 0.3333 [0.1250, 0.5417] | 0.5833 [0.3333, 0.8333] | 0.1667 [-0.0417, 0.3750] |
| R1OneVision | (GradeSchool) Non-Geo Math | 5 | 0.4000 [0.1000, 0.7000] | 0.4000 [0.0000, 0.8000] | 0.2000 [0.0000, 0.4000] | 0.2000 [0.0000, 0.6000] |
| R1OneVision | Broader STEM Topics | 14 | 0.2857 [0.1071, 0.5000] | 0.3214 [0.1071, 0.5357] | 0.2143 [0.0357, 0.4286] | 0.1786 [0.0357, 0.3571] |
| R1OneVision | Spatial Reasoning | 18 | 0.3611 [0.1389, 0.5833] | 0.0000 [-0.1389, 0.1111] | 0.1667 [-0.0278, 0.3056] | 0.1944 [0.0000, 0.3889] |
| R1OneVision | Tables/Diagrams/Charts | 6 | 0.3333 [0.0000, 0.6667] | 0.3333 [0.0000, 0.6667] | 0.3333 [0.1667, 0.5000] | 0.5833 [0.3333, 0.8333] |
| R1OneVisionConverted | (GradeSchool) Geometric | 2 | 0.0000 [0.0000, 0.0000] | 0.2500 [-0.5000, 1.0000] | 0.5000 [0.0000, 1.0000] | 0.2500 [0.0000, 0.5000] |
| R1OneVisionConverted | (GradeSchool) Non-Geo Math | 2 | 0.5000 [0.0000, 1.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.2500 [0.0000, 0.5000] |
| R1OneVisionConverted | (GradeSchool) Science | 9 | 0.2778 [0.0000, 0.5556] | 0.1667 [0.0000, 0.3889] | 0.1667 [0.0000, 0.3889] | 0.1111 [0.0000, 0.3333] |
| R1OneVisionConverted | Spatial Reasoning | 2 | 0.2500 [0.0000, 0.5000] | 0.0000 [0.0000, 0.0000] | 0.2500 [0.0000, 0.5000] | 0.0000 [0.0000, 0.0000] |
| R1OneVisionConverted | Tables/Diagrams/Charts | 2 | 0.5000 [0.0000, 1.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| ScienceQA | Broader STEM Topics | 3 | 0.8333 [0.5000, 1.0000] | 0.6667 [0.5000, 1.0000] | 0.6667 [0.5000, 1.0000] | 0.3333 [0.0000, 1.0000] |
| ScienceQA | Social Science | 3 | 0.5000 [-0.5000, 1.0000] | 0.3333 [0.0000, 1.0000] | 0.8333 [0.5000, 1.0000] | 0.8333 [0.5000, 1.0000] |
| ScienceQA | Spatial Reasoning | 9 | 0.9444 [0.8333, 1.0000] | 0.5000 [0.2222, 0.7778] | 0.3333 [0.1111, 0.5556] | 0.5556 [0.3319, 0.7778] |
| ScienceQA | Tables/Diagrams/Charts | 4 | 1.0000 [1.0000, 1.0000] | 0.5000 [0.1250, 0.8750] | 0.5000 [0.1250, 0.8750] | 0.6250 [0.2500, 1.0000] |
| chartqa | Tables/Diagrams/Charts | 9 | 0.5556 [0.2778, 0.8333] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.2778 [0.0000, 0.5556] |
| dvqa | Broader STEM Topics | 1 | 1.0000 [1.0000, 1.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| dvqa | Social Science | 1 | 1.0000 [1.0000, 1.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | -1.0000 [-1.0000, -1.0000] |
| geoqa_plusConverted | (GradeSchool) Non-Geo Math | 2 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| geoqa_plusConverted | Spatial Reasoning | 2 | 0.5000 [0.0000, 1.0000] | 0.5000 [0.0000, 1.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |

## Rank statistics (two seeds (seeds 1, 2; registered two-seed mean))

Tie-corrected Spearman across eligible strata; undefined bootstrap draws are counted, never replaced with zero; an interval with more than 5% undefined draws is labeled unstable.

| Blind arm | rho_gain (95% CI) | Undefined | Label | Direction > 0 holds | rho_recovery (95% CI) | Recovery strata | Undefined | Label | Direction > 0 holds |
|---|---:|---:|---|---|---:|---:|---:|---|---|
| A2 gray | -0.2253 [-0.3924, -0.1078] | 0/5000 | stable | false | 0.4226 [-0.0030, 0.6079] | 20/22 | 0/5000 | stable | true |
| A2b no-image | -0.3077 [-0.4579, -0.1666] | 0/5000 | stable | false | 0.2917 [-0.0497, 0.6051] | 20/22 | 0/5000 | stable | true |
| A3 caption | -0.7403 [-0.8125, -0.5709] | 0/5000 | stable | false | -0.0346 [-0.4361, 0.3086] | 20/22 | 0/5000 | stable | false |

## Source-only descriptive table

Role: descriptive robustness view; does not replace the registered joint-stratum analysis.

| Group | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) |
|---|---:|---:|---:|---:|---:|
| K12 | 147 | 0.0816 [0.0068, 0.1565] | 0.0442 [-0.0102, 0.0986] | 0.0850 [0.0238, 0.1463] | 0.0374 [-0.0374, 0.1088] |
| M3CoT | 175 | 0.4343 [0.3629, 0.5086] | 0.2971 [0.2371, 0.3600] | 0.3086 [0.2486, 0.3714] | 0.3543 [0.2914, 0.4171] |
| M3CoTConverted | 16 | 0.1562 [0.0000, 0.3438] | 0.0312 [0.0000, 0.0938] | 0.0625 [0.0000, 0.1562] | 0.1250 [0.0000, 0.2812] |
| MMK12 | 1727 | 0.0935 [0.0735, 0.1138] | 0.0738 [0.0559, 0.0921] | 0.0744 [0.0573, 0.0915] | 0.1008 [0.0825, 0.1199] |
| MMK12Converted | 27 | 0.2222 [0.0370, 0.4074] | 0.2037 [0.0556, 0.3704] | 0.2037 [0.0370, 0.3704] | 0.1667 [-0.0185, 0.3519] |
| MMMath | 428 | 0.0724 [0.0350, 0.1098] | 0.0572 [0.0199, 0.0935] | 0.0584 [0.0222, 0.0946] | 0.0526 [0.0187, 0.0876] |
| Processed | 1201 | 0.3235 [0.2943, 0.3522] | 0.2469 [0.2202, 0.2727] | 0.2182 [0.1932, 0.2435] | 0.2856 [0.2590, 0.3139] |
| R1OneVision | 105 | 0.3000 [0.2143, 0.3857] | 0.2524 [0.1667, 0.3381] | 0.2810 [0.2000, 0.3619] | 0.2857 [0.2095, 0.3667] |
| R1OneVisionConverted | 17 | 0.2941 [0.1176, 0.5000] | 0.1176 [-0.0294, 0.3235] | 0.1765 [0.0294, 0.3529] | 0.1176 [0.0000, 0.2647] |
| ScienceQA | 53 | 0.7453 [0.6415, 0.8396] | 0.5660 [0.4340, 0.6887] | 0.5566 [0.4526, 0.6604] | 0.6321 [0.5189, 0.7358] |
| ai2d | 107 | 0.1262 [0.0187, 0.2290] | 0.1028 [0.0140, 0.1869] | 0.2103 [0.1168, 0.3037] | 0.0981 [0.0047, 0.1869] |
| chartqa | 9 | 0.5556 [0.2778, 0.8333] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.2778 [0.0556, 0.5556] |
| dvqa | 71 | 0.5915 [0.4648, 0.7183] | 0.0352 [0.0070, 0.0704] | 0.0423 [0.0070, 0.0845] | 0.3592 [0.2465, 0.4718] |
| geoqa_plus | 118 | 0.3602 [0.2712, 0.4492] | 0.3390 [0.2458, 0.4280] | 0.2924 [0.2034, 0.3814] | 0.3390 [0.2627, 0.4110] |
| geoqa_plusConverted | 38 | 0.2632 [0.0789, 0.4342] | 0.1184 [-0.0526, 0.2766] | 0.1974 [0.0789, 0.3289] | 0.2237 [0.0658, 0.3816] |

## Category-only descriptive table

Role: descriptive robustness view; does not replace the registered joint-stratum analysis.

| Group | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) |
|---|---:|---:|---:|---:|---:|
| (GradeSchool) Geometric | 1178 | 0.2037 [0.1761, 0.2309] | 0.1804 [0.1541, 0.2054] | 0.1774 [0.1524, 0.2025] | 0.1677 [0.1418, 0.1935] |
| (GradeSchool) Non-Geo Math | 1510 | 0.1474 [0.1242, 0.1705] | 0.1225 [0.1010, 0.1440] | 0.1179 [0.0980, 0.1371] | 0.1381 [0.1166, 0.1599] |
| (GradeSchool) Science | 449 | 0.2940 [0.2461, 0.3419] | 0.2272 [0.1804, 0.2728] | 0.2171 [0.1715, 0.2639] | 0.3241 [0.2795, 0.3675] |
| Broader STEM Topics | 146 | 0.1541 [0.0685, 0.2363] | 0.1541 [0.0856, 0.2260] | 0.1164 [0.0445, 0.1849] | 0.1404 [0.0685, 0.2124] |
| Commonsense | 13 | 0.3846 [0.1923, 0.6154] | 0.5000 [0.2692, 0.7308] | 0.2692 [0.0769, 0.4615] | 0.5000 [0.2692, 0.7308] |
| Social Science | 69 | 0.5145 [0.4058, 0.6159] | 0.2609 [0.1739, 0.3551] | 0.2899 [0.1884, 0.3986] | 0.3986 [0.2826, 0.5072] |
| Spatial Reasoning | 253 | 0.2431 [0.1877, 0.3024] | 0.0968 [0.0494, 0.1443] | 0.1087 [0.0672, 0.1502] | 0.1304 [0.0771, 0.1818] |
| Tables/Diagrams/Charts | 621 | 0.2375 [0.1957, 0.2794] | 0.0942 [0.0644, 0.1240] | 0.1055 [0.0765, 0.1345] | 0.2045 [0.1691, 0.2424] |

## Geometry3K anchor comparison (two seeds (seeds 1, 2; registered two-seed mean); informed comparison)

This comparison is informed, not fully prospective: the anchors are the completed Geometry3K seed-1 recovery readout (Informed-Prediction Disclosure, docs/registered_m7_amendment_v1.md).

| Blind arm | Geometry3K anchor | ViRL recovery (95% CI) | Difference (95% CI) | Direction (> anchor) holds | Interval label |
|---|---:|---:|---:|---|---|
| A2 gray | 0.0789 | 0.7265 | 0.6476 [0.5803, 0.7172] | true | stable |
| A2b no-image | 0.1184 | 0.7132 | 0.5948 [0.5299, 0.6660] | true | stable |
| A3 caption | no registered anchor | 0.8840 [0.8091, 0.9632] | NA | NA | stable |

## M10 support-sharpening candidates

Rule: base 0/16 under the arm's own condition, step-0 greedy wrong, step-100 greedy correct; 64-sample frozen-base follow-up is reported separately under M10.

Seed rule: candidate lists are computed per seed and published separately; no union/intersection/two-seed candidate rule is registered (docs/registered_extensions_v1.md:142), so they are not merged.

| Arm | Seed | Candidates | Artifact |
|---|---|---:|---|
| A1 real | seed1 | 302 | `tmp/r3_md_refresh/artifacts/support_candidates_a1_real_seed1.jsonl` |
| A1 real | seed2 | 311 | `tmp/r3_md_refresh/artifacts/support_candidates_a1_real_seed2.jsonl` |
| A2 gray | seed1 | 278 | `tmp/r3_md_refresh/artifacts/support_candidates_a2_gray_seed1.jsonl` |
| A2 gray | seed2 | 268 | `tmp/r3_md_refresh/artifacts/support_candidates_a2_gray_seed2.jsonl` |
| A2b no-image | seed1 | 292 | `tmp/r3_md_refresh/artifacts/support_candidates_a2b_noimage_seed1.jsonl` |
| A2b no-image | seed2 | 267 | `tmp/r3_md_refresh/artifacts/support_candidates_a2b_noimage_seed2.jsonl` |
| A3 caption | seed1 | 317 | `tmp/r3_md_refresh/artifacts/support_candidates_a3_caption_seed1.jsonl` |
| A3 caption | seed2 | 299 | `tmp/r3_md_refresh/artifacts/support_candidates_a3_caption_seed2.jsonl` |

Candidate selection does not claim that RL created or taught a capability; M10 language remains non-causal.

## Seed dispersion (descriptive only)

Role: descriptive only. 'Seed-to-seed dispersion is also reported descriptively and is not replaced by item-bootstrap uncertainty' (docs/registered_m7_amendment_v1.md:81-82); 'Use item-paired intervals; seed dispersion is separately descriptive' (docs/registered_extensions_v1.md:143). Two seeds is n=2: no seed-level confidence interval, significance test, or 'the effect replicates' claim is registered. No registered branch keys on seed disagreement; the direction verdict is read off the two-seed mean statistic in payload['rank_statistics'] and fires unchanged whatever the per-seed values do.

- q_bar[b,s] is the item mean of the frozen Jeffreys-smoothed base q_i under arm b's own information condition (docs/registered_m7_amendment_v1.md:49-51); it comes from the shared step-0 cells and is identical for both seeds.
- Registered direction verdict source: payload['rank_statistics'], computed on the two-seed mean; the per-seed values below fire no registered branch.
- Every number in this section is a point estimate. No interval, test, or replication claim is attached to a two-point seed spread.

| Arm | Gain seed1 | Gain seed2 | Gain difference | Two-seed mean gain (95% CI) |
|---|---:|---:|---:|---:|
| A1 real | 0.2062 | 0.2026 | 0.0035 | 0.2044 [0.1898, 0.2189] |
| A2 gray | 0.1479 | 0.1491 | -0.0012 | 0.1485 [0.1359, 0.1615] |
| A2b no-image | 0.1536 | 0.1380 | 0.0156 | 0.1458 [0.1332, 0.1583] |
| A3 caption | 0.1819 | 0.1795 | 0.0024 | 0.1807 [0.1673, 0.1939] |

| Blind arm | Statistic | seed1 | seed2 | Difference | Two-seed mean (registered) |
|---|---|---:|---:|---:|---:|
| A2 gray | aggregate_recovery | 0.7174 | 0.7357 | -0.0183 | 0.7265 |
| A2 gray | rho_gain | -0.2592 | -0.1948 | -0.0644 | -0.2253 |
| A2 gray | rho_recovery | 0.2095 | 0.6088 | -0.3993 | 0.4226 |
| A2b no-image | aggregate_recovery | 0.7449 | 0.6810 | 0.0638 | 0.7132 |
| A2b no-image | rho_gain | -0.2648 | -0.3552 | 0.0903 | -0.3077 |
| A2b no-image | rho_recovery | 0.5039 | 0.2193 | 0.2846 | 0.2917 |
| A3 caption | aggregate_recovery | 0.8822 | 0.8859 | -0.0038 | 0.8840 |
| A3 caption | rho_gain | -0.7335 | -0.7561 | 0.0226 | -0.7403 |
| A3 caption | rho_recovery | -0.1148 | 0.0500 | -0.1648 | -0.0346 |

## Provenance

- Held-out manifest: `data/virl39k_m7_heldout_v3.jsonl` (sha256 `50f3b85c11c4046ef2512c544faec04286648688bb6d47548995f18cab40716c`, 4239 rows).
- Analysis git head: `37a8932c91546a8db31e83226261ae541fed9ba9`.
- Bootstrap: 5000 draws, seed 20260716; deterministic statistic/arm labels hashed into independent streams via src.analysis.pilot_fourarm.deterministic_seed.
- data/virl39k_m7_split_manifest_v2.json n_strata_rank_eligible=21 counts component labels, not items, and was not used; eligibility was recounted directly from the held-out jsonl.
- Registered documents: `docs/registered_m7_amendment_v1.md`, `docs/registered_m7_seed_scope_v1.md`, `docs/registered_m7_single_image_v2.md`, `docs/registered_extensions_v1.md`.

| Arm | Step | Run dir | per_item sha256 |
|---|---|---|---|
| A1 real | step0 | `experiments/runs/m7_step0_heldout_base_real_an29_20260730T154447Z` | `50c0cda2fdaf6d2ae1bfcfb17b216f0658a72879a0f3c28f48c08592719fb7c3` |
| A1 real | step100_seed1 | `experiments/runs/m7_step100_heldout_a1_real_an29_20260731T161352Z` | `b3a304a3d446b7a415ae5b58f924dd10b07369011ff44629bd49242a5f5869b4` |
| A1 real | step100_seed2 | `experiments/runs/m7_step100_heldout_seed2_a1_real_seed2_real_an29_20260809T144439Z` | `a0723d380332dcb999f32d0e769c0195d7d4cb5b6dd7f983c6dcbf7f462a4081` |
| A2 gray | step0 | `experiments/runs/m7_step0_heldout_base_gray_an29_20260730T154458Z` | `c168b70cd7b53f50f7de3d3b771533d32362ed5d99bc8cfabf99e1998b834c9e` |
| A2 gray | step100_seed1 | `experiments/runs/m7_step100_heldout_a2_gray_gray_an12_20260803T151508Z` | `1b161a71cf4184518c871c4d414863f681ac39a2d9b1481f0b46b3cde007f172` |
| A2 gray | step100_seed2 | `experiments/runs/m7_step100_heldout_seed2_a2_gray_seed2_gray_an12_20260816T082503Z` | `167eed66ffd1cb1edc5d884ea33bf82df98d012e850bc472e62ed1c8c0b15776` |
| A2b no-image | step0 | `experiments/runs/m7_step0_heldout_base_none_an29_20260730T154501Z` | `825c92ff2d51bf5bcd10ca0a3d6995d386b19ce526fa4fe11435d2a3a8bd3ac7` |
| A2b no-image | step100_seed1 | `experiments/runs/m7_step100_heldout_a2b_none_an29_20260801T014325Z` | `d95a34d2e9bbc7b9a6dd0130a76a78f936d5ad9c6fc76ca7aeec3912ac03e319` |
| A2b no-image | step100_seed2 | `experiments/runs/m7_step100_heldout_seed2_a2b_noimage_seed2_none_an29_20260811T041120Z` | `666aae61106a968332fe4d6fa92f5328cb3e708ccedaab7d9468dd7f8fd0e8dd` |
| A3 caption | step0 | `experiments/runs/m7_step0_heldout_base_caption_an29_20260730T154503Z` | `ac04a4e2740a4838f7358b38d8af1b47ca8e21b93e8c67f00c83d1e23059a207` |
| A3 caption | step100_seed1 | `experiments/runs/m7_step100_heldout_a3_caption_caption_an12_20260803T151440Z` | `a60640a0fd0169b4c0fbfe20e54b1f04c2dbbd678bc026ad382eef85b283493a` |
| A3 caption | step100_seed2 | `experiments/runs/m7_step100_heldout_seed2_a3_caption_seed2_caption_an29_20260816T082631Z` | `8d4441fd3cb3200f7f551ec70f8b769c6521349f8febfb99166f677cf3301d52` |
