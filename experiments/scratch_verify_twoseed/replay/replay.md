# M7 R3 Readout V1

Status: `complete`.

Scope:
- Seed scope: seed 1 only for all four arms; every gain, recovery, and correlation below is a per-seed (one seed) number and no between-seed variance claim is made (docs/registered_m7_seed_scope_v1.md).
- Single-image restriction: M7 is restricted to single-image rows (worker.rollout.limit_images=1); retained 23,542/25,255 train rows (93.2%) and 4,239/4,501 held-out rows (94.2%) (docs/registered_m7_single_image_v2.md).
- Pooled-only readout is prohibited; corpus aggregate, every joint stratum, and source-only/category-only descriptive tables are all published; A2/A2b/A3 are never pooled into one generic blind arm (docs/registered_extensions_v1.md Extension 3, docs/registered_m7_amendment_v1.md).
- This report contains numbers and provenance only; interpretation is reserved to the PIs.

Machine artifact: `experiments/scratch_verify_twoseed/replay/replay.json`.

## Strata accounting

- Joint (source, category) strata recounted from `data/virl39k_m7_heldout_v3.jsonl`: 60 total, 22 eligible (>= 30 held-out items), 38 descriptive-small-n.
- Eligibility depends only on sample count, never on a model outcome; descriptive-small-n strata are published, not merged or discarded, and enter no rank statistic.

## Corpus aggregate (one seed (seed 1))

| Arm | n | q_bar | Acc_final step 0 | Acc_final step 100 | Gain (95% CI) |
|---|---:|---:|---:|---:|---:|
| A1 real | 4239 | 0.5122 | 0.2744 | 0.4805 | 0.2062 [0.1901, 0.2220] |
| A2 gray | 4239 | 0.4235 | 0.1894 | 0.3373 | 0.1479 [0.1338, 0.1623] |
| A2b no-image | 4239 | 0.4154 | 0.1538 | 0.3074 | 0.1536 [0.1396, 0.1680] |
| A3 caption | 4239 | 0.4458 | 0.1849 | 0.3668 | 0.1819 [0.1665, 0.1967] |

Corpus A1 denominator: estimate 0.2062, paired SE 0.0083, stable `true` (rule: gain[A1] > 0 and gain[A1] >= 2 * paired_se).

| Blind arm | Aggregate recovery (95% CI) | Status | Undefined draws | Interval label |
|---|---:|---|---:|---|
| A2 gray | 0.7174 [NA] | stable | 0/5000 | stable |
| A2b no-image | 0.7449 [NA] | stable | 0/5000 | stable |
| A3 caption | 0.8822 [NA] | stable | 0/5000 | stable |

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

## Registered joint strata: gains (one seed (seed 1))

| Source | Category | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) | A1 stable |
|---|---|---:|---:|---:|---:|---:|---|
| K12 | (GradeSchool) Non-Geo Math | 147 | 0.0680 [-0.0136, 0.1565] | 0.0476 [-0.0204, 0.1156] | 0.1293 [0.0612, 0.1974] | 0.0340 [-0.0544, 0.1224] | false |
| M3CoT | (GradeSchool) Science | 65 | 0.5231 [0.4000, 0.6462] | 0.2308 [0.1385, 0.3385] | 0.3077 [0.2000, 0.4308] | 0.3538 [0.2462, 0.4769] | true |
| M3CoT | Social Science | 53 | 0.4906 [0.3585, 0.6226] | 0.3774 [0.2453, 0.5094] | 0.2830 [0.1509, 0.4151] | 0.5094 [0.3774, 0.6415] | true |
| MMK12 | (GradeSchool) Geometric | 653 | 0.1424 [0.1041, 0.1822] | 0.1087 [0.0720, 0.1440] | 0.1240 [0.0873, 0.1593] | 0.0919 [0.0536, 0.1286] | true |
| MMK12 | (GradeSchool) Non-Geo Math | 456 | 0.0241 [-0.0132, 0.0614] | 0.0417 [0.0066, 0.0746] | 0.0680 [0.0351, 0.0987] | 0.0943 [0.0570, 0.1316] | false |
| MMK12 | (GradeSchool) Science | 203 | 0.1281 [0.0590, 0.2020] | 0.1084 [0.0296, 0.1872] | 0.0788 [0.0000, 0.1576] | 0.2365 [0.1626, 0.3103] | true |
| MMK12 | Broader STEM Topics | 60 | 0.1333 [-0.0167, 0.3000] | 0.0500 [-0.0500, 0.1667] | 0.0833 [0.0167, 0.1667] | 0.0833 [-0.0333, 0.2000] | false |
| MMK12 | Spatial Reasoning | 113 | 0.0531 [-0.0354, 0.1416] | 0.0265 [-0.0531, 0.1062] | 0.0177 [-0.0531, 0.0885] | 0.0088 [-0.0619, 0.0799] | false |
| MMK12 | Tables/Diagrams/Charts | 239 | 0.0711 [0.0209, 0.1213] | 0.0167 [-0.0209, 0.0544] | 0.0167 [-0.0126, 0.0460] | 0.0753 [0.0293, 0.1213] | true |
| MMMath | (GradeSchool) Non-Geo Math | 428 | 0.0818 [0.0397, 0.1238] | 0.0514 [0.0093, 0.0935] | 0.0561 [0.0164, 0.0958] | 0.0514 [0.0140, 0.0911] | true |
| Processed | (GradeSchool) Geometric | 340 | 0.2882 [0.2294, 0.3471] | 0.2265 [0.1735, 0.2794] | 0.2471 [0.1912, 0.3029] | 0.2382 [0.1765, 0.2971] | true |
| Processed | (GradeSchool) Non-Geo Math | 457 | 0.3720 [0.3217, 0.4223] | 0.2998 [0.2516, 0.3479] | 0.2407 [0.1947, 0.2867] | 0.2888 [0.2407, 0.3370] | true |
| Processed | (GradeSchool) Science | 74 | 0.3919 [0.2703, 0.5270] | 0.3514 [0.2297, 0.4730] | 0.3108 [0.1892, 0.4324] | 0.4054 [0.2973, 0.5270] | true |
| Processed | Broader STEM Topics | 66 | 0.1515 [0.0152, 0.2879] | 0.1364 [0.0152, 0.2576] | 0.1515 [0.0000, 0.3030] | 0.1818 [0.0606, 0.3030] | true |
| Processed | Spatial Reasoning | 86 | 0.3140 [0.1977, 0.4302] | 0.1047 [0.0233, 0.1860] | 0.1628 [0.0814, 0.2442] | 0.2674 [0.1628, 0.3721] | true |
| Processed | Tables/Diagrams/Charts | 173 | 0.3526 [0.2659, 0.4393] | 0.2023 [0.1329, 0.2775] | 0.2081 [0.1272, 0.2834] | 0.3642 [0.2775, 0.4509] | true |
| R1OneVision | (GradeSchool) Science | 50 | 0.3000 [0.1400, 0.4400] | 0.3200 [0.1600, 0.4800] | 0.2600 [0.1200, 0.4000] | 0.3000 [0.1800, 0.4200] | true |
| ScienceQA | (GradeSchool) Science | 34 | 0.7059 [0.5588, 0.8529] | 0.6471 [0.4706, 0.8235] | 0.6176 [0.4412, 0.7647] | 0.7059 [0.5588, 0.8529] | true |
| ai2d | Tables/Diagrams/Charts | 107 | 0.1682 [0.0561, 0.2804] | 0.1121 [0.0187, 0.2056] | 0.1589 [0.0561, 0.2617] | 0.0935 [0.0000, 0.1869] | true |
| dvqa | Tables/Diagrams/Charts | 69 | 0.5652 [0.4203, 0.6957] | 0.0580 [0.0145, 0.1159] | 0.0580 [0.0145, 0.1159] | 0.4058 [0.2899, 0.5217] | true |
| geoqa_plus | (GradeSchool) Geometric | 118 | 0.3814 [0.2797, 0.4831] | 0.3475 [0.2458, 0.4492] | 0.3220 [0.2203, 0.4237] | 0.3814 [0.2966, 0.4746] | true |
| geoqa_plusConverted | (GradeSchool) Geometric | 34 | 0.2941 [0.0882, 0.5000] | 0.0294 [-0.1765, 0.2353] | 0.2941 [0.1176, 0.4706] | 0.2059 [0.0000, 0.4118] | true |

## Registered joint strata: recovery (one seed (seed 1))

Recovery is `gain[b,s] / gain[A1,s]` only when the A1 denominator is stable (gain[A1,s] > 0 and >= 2 paired SE); otherwise `undefined-unstable-denominator`. Unstable strata stay in the gain analysis and are omitted from the recovery rank statistic.

| Source | Category | A2 recovery (95% CI) | A2b recovery (95% CI) | A3 recovery (95% CI) |
|---|---|---:|---:|---:|
| K12 | (GradeSchool) Non-Geo Math | undefined-unstable-denominator | undefined-unstable-denominator | undefined-unstable-denominator |
| M3CoT | (GradeSchool) Science | 0.4412 [0.2632, 0.6581] | 0.5882 [0.3793, 0.8438] | 0.6765 [0.4571, 0.9355] |
| M3CoT | Social Science | 0.7692 [0.5000, 1.1500] | 0.5769 [0.3158, 0.8697] | 1.0385 [0.7200, 1.4737] |
| MMK12 | (GradeSchool) Geometric | 0.7634 [0.5043, 1.1205] | 0.8710 [0.5889, 1.2609] | 0.6452 [0.3736, 1.0125] |
| MMK12 | (GradeSchool) Non-Geo Math | undefined-unstable-denominator | undefined-unstable-denominator | undefined-unstable-denominator |
| MMK12 | (GradeSchool) Science | 0.8462 [0.2667, 2.0531] | 0.6154 [0.0322, 1.7827] | 1.8462 [1.0625, 4.3850] |
| MMK12 | Broader STEM Topics | undefined-unstable-denominator | undefined-unstable-denominator | undefined-unstable-denominator |
| MMK12 | Spatial Reasoning | undefined-unstable-denominator | undefined-unstable-denominator | undefined-unstable-denominator |
| MMK12 | Tables/Diagrams/Charts | 0.2353 [-0.4545, 1.1250] | 0.2353 [-0.1818, 1.1667] | 1.0588 [0.3333, 4.0000] |
| MMMath | (GradeSchool) Non-Geo Math | 0.6286 [0.0937, 1.5807] | 0.6857 [0.1951, 1.5909] | 0.6286 [0.1429, 1.6475] |
| Processed | (GradeSchool) Geometric | 0.7857 [0.6000, 1.0105] | 0.8571 [0.6404, 1.1290] | 0.8265 [0.6060, 1.1042] |
| Processed | (GradeSchool) Non-Geo Math | 0.8059 [0.6726, 0.9583] | 0.6471 [0.5326, 0.7733] | 0.7765 [0.6478, 0.9216] |
| Processed | (GradeSchool) Science | 0.8966 [0.6286, 1.2500] | 0.7931 [0.5000, 1.1667] | 1.0345 [0.7436, 1.4762] |
| Processed | Broader STEM Topics | 0.9000 [0.0000, 3.4175] | 1.0000 [-0.1111, 5.5000] | 1.2000 [0.2500, 5.0000] |
| Processed | Spatial Reasoning | 0.3333 [0.0968, 0.6334] | 0.5185 [0.2777, 0.8929] | 0.8519 [0.5200, 1.3636] |
| Processed | Tables/Diagrams/Charts | 0.5738 [0.3728, 0.8149] | 0.5902 [0.3768, 0.8364] | 1.0328 [0.8000, 1.3448] |
| R1OneVision | (GradeSchool) Science | 1.0667 [0.6250, 1.8000] | 0.8667 [0.4615, 1.4167] | 1.0000 [0.5789, 2.0000] |
| ScienceQA | (GradeSchool) Science | 0.9167 [0.6800, 1.1429] | 0.8750 [0.6667, 1.0952] | 1.0000 [0.7500, 1.3333] |
| ai2d | Tables/Diagrams/Charts | 0.6667 [0.1071, 2.3333] | 0.9444 [0.3333, 2.7179] | 0.5556 [-0.0500, 2.0000] |
| dvqa | Tables/Diagrams/Charts | 0.1026 [0.0233, 0.2069] | 0.1026 [0.0233, 0.2069] | 0.7179 [0.4792, 1.0938] |
| geoqa_plus | (GradeSchool) Geometric | 0.9111 [0.6327, 1.3125] | 0.8444 [0.5610, 1.2500] | 1.0000 [0.7377, 1.3824] |
| geoqa_plusConverted | (GradeSchool) Geometric | 0.1000 [-0.7500, 1.0000] | 1.0000 [0.3636, 3.2500] | 0.7000 [0.0000, 2.5000] |

## Descriptive small-n strata (38)

Published per registration; not merged, not discarded, not in any rank statistic.

| Source | Category | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) |
|---|---|---:|---:|---:|---:|---:|
| M3CoT | (GradeSchool) Geometric | 6 | -0.3333 [-0.6667, 0.0000] | 0.3333 [-0.3333, 0.8333] | 0.5000 [0.1667, 0.8333] | 0.3333 [0.0000, 0.6667] |
| M3CoT | (GradeSchool) Non-Geo Math | 11 | -0.1818 [-0.4545, 0.0000] | 0.1818 [0.0000, 0.4545] | 0.2727 [0.0000, 0.5455] | 0.0909 [0.0000, 0.2727] |
| M3CoT | Broader STEM Topics | 1 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| M3CoT | Commonsense | 12 | 0.5000 [0.2500, 0.7500] | 0.5000 [0.2500, 0.7500] | 0.3333 [0.0833, 0.5833] | 0.5833 [0.3333, 0.8333] |
| M3CoT | Spatial Reasoning | 20 | 0.3000 [0.1000, 0.5000] | 0.4000 [0.2000, 0.6000] | 0.3500 [0.1500, 0.5500] | 0.1500 [0.0000, 0.3000] |
| M3CoT | Tables/Diagrams/Charts | 7 | 0.1429 [0.0000, 0.4286] | 0.1429 [0.0000, 0.4286] | 0.1429 [0.0000, 0.4286] | 0.4286 [0.1429, 0.8571] |
| M3CoTConverted | (GradeSchool) Science | 6 | 0.1667 [0.0000, 0.5000] | 0.0000 [0.0000, 0.0000] | 0.1667 [0.0000, 0.5000] | 0.0000 [0.0000, 0.0000] |
| M3CoTConverted | Social Science | 5 | 0.4000 [0.0000, 0.8000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| M3CoTConverted | Spatial Reasoning | 2 | 0.0000 [0.0000, 0.0000] | 0.5000 [0.0000, 1.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| M3CoTConverted | Tables/Diagrams/Charts | 3 | -0.3333 [-1.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.3333 [0.0000, 1.0000] |
| MMK12 | Social Science | 3 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| MMK12Converted | (GradeSchool) Geometric | 13 | 0.3077 [0.0000, 0.6154] | 0.2308 [0.0000, 0.4615] | 0.1538 [-0.0769, 0.4615] | 0.1538 [-0.2308, 0.5385] |
| MMK12Converted | (GradeSchool) Non-Geo Math | 2 | 1.0000 [1.0000, 1.0000] | 0.0000 [0.0000, 0.0000] | 0.5000 [0.0000, 1.0000] | 0.5000 [0.0000, 1.0000] |
| MMK12Converted | (GradeSchool) Science | 8 | 0.0000 [-0.3750, 0.3750] | 0.2500 [-0.2500, 0.6250] | 0.2500 [0.0000, 0.6250] | 0.2500 [0.0000, 0.6250] |
| MMK12Converted | Broader STEM Topics | 1 | 0.0000 [0.0000, 0.0000] | 1.0000 [1.0000, 1.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| MMK12Converted | Spatial Reasoning | 1 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| MMK12Converted | Tables/Diagrams/Charts | 2 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| Processed | Commonsense | 1 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| Processed | Social Science | 4 | 0.5000 [0.0000, 1.0000] | 0.2500 [0.0000, 0.7500] | 0.2500 [0.0000, 0.7500] | 0.0000 [0.0000, 0.0000] |
| R1OneVision | (GradeSchool) Geometric | 12 | 0.0833 [-0.2500, 0.4167] | 0.1667 [0.0000, 0.4167] | 0.6667 [0.4167, 0.9167] | 0.1667 [-0.1667, 0.5000] |
| R1OneVision | (GradeSchool) Non-Geo Math | 5 | 0.4000 [0.0000, 0.8000] | 0.4000 [0.0000, 0.8000] | 0.0000 [0.0000, 0.0000] | 0.2000 [0.0000, 0.6000] |
| R1OneVision | Broader STEM Topics | 14 | 0.2857 [0.0714, 0.5000] | 0.3571 [0.1429, 0.6429] | 0.2143 [0.0000, 0.4286] | 0.1429 [0.0000, 0.3571] |
| R1OneVision | Spatial Reasoning | 18 | 0.3889 [0.1111, 0.6667] | 0.0000 [-0.1667, 0.1667] | 0.1667 [-0.0556, 0.3889] | 0.2222 [0.0556, 0.4444] |
| R1OneVision | Tables/Diagrams/Charts | 6 | 0.3333 [0.0000, 0.6667] | 0.3333 [0.0000, 0.6667] | 0.3333 [0.0000, 0.6667] | 0.5000 [0.1667, 0.8333] |
| R1OneVisionConverted | (GradeSchool) Geometric | 2 | 0.0000 [0.0000, 0.0000] | 0.0000 [-1.0000, 1.0000] | 0.5000 [0.0000, 1.0000] | 0.0000 [0.0000, 0.0000] |
| R1OneVisionConverted | (GradeSchool) Non-Geo Math | 2 | 0.5000 [0.0000, 1.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.5000 [0.0000, 1.0000] |
| R1OneVisionConverted | (GradeSchool) Science | 9 | 0.2222 [0.0000, 0.5556] | 0.2222 [0.0000, 0.5556] | 0.2222 [0.0000, 0.5556] | 0.1111 [0.0000, 0.3333] |
| R1OneVisionConverted | Spatial Reasoning | 2 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.5000 [0.0000, 1.0000] | 0.0000 [0.0000, 0.0000] |
| R1OneVisionConverted | Tables/Diagrams/Charts | 2 | 0.5000 [0.0000, 1.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| ScienceQA | Broader STEM Topics | 3 | 0.6667 [0.0000, 1.0000] | 1.0000 [1.0000, 1.0000] | 0.3333 [0.0000, 1.0000] | 0.3333 [0.0000, 1.0000] |
| ScienceQA | Social Science | 3 | 0.3333 [-1.0000, 1.0000] | 0.3333 [0.0000, 1.0000] | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] |
| ScienceQA | Spatial Reasoning | 9 | 0.8889 [0.6667, 1.0000] | 0.4444 [0.1111, 0.7778] | 0.3333 [0.0000, 0.6667] | 0.5556 [0.2222, 0.8889] |
| ScienceQA | Tables/Diagrams/Charts | 4 | 1.0000 [1.0000, 1.0000] | 0.7500 [0.2500, 1.0000] | 0.5000 [0.0000, 1.0000] | 0.5000 [0.0000, 1.0000] |
| chartqa | Tables/Diagrams/Charts | 9 | 0.5556 [0.2222, 0.8889] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.3333 [0.0000, 0.6667] |
| dvqa | Broader STEM Topics | 1 | 1.0000 [1.0000, 1.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| dvqa | Social Science | 1 | 1.0000 [1.0000, 1.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | -1.0000 [-1.0000, -1.0000] |
| geoqa_plusConverted | (GradeSchool) Non-Geo Math | 2 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| geoqa_plusConverted | Spatial Reasoning | 2 | 0.5000 [0.0000, 1.0000] | 0.5000 [0.0000, 1.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |

## Rank statistics (one seed (seed 1))

Tie-corrected Spearman across eligible strata; undefined bootstrap draws are counted, never replaced with zero; an interval with more than 5% undefined draws is labeled unstable.

| Blind arm | rho_gain (95% CI) | Undefined | Label | Direction > 0 holds | rho_recovery (95% CI) | Recovery strata | Undefined | Label | Direction > 0 holds |
|---|---:|---:|---|---|---:|---:|---:|---|---|
| A2 gray | -0.2592 [-0.4455, -0.1191] | 0/5000 | stable | false | 0.2095 [-0.1386, 0.4778] | 18/22 | 0/5000 | stable | true |
| A2b no-image | -0.2648 [-0.4365, -0.1022] | 0/5000 | stable | false | 0.5039 [-0.0361, 0.6593] | 18/22 | 0/5000 | stable | true |
| A3 caption | -0.7335 [-0.8091, -0.5539] | 0/5000 | stable | false | -0.1148 [-0.5521, 0.1985] | 18/22 | 0/5000 | stable | false |

## Source-only descriptive table

Role: descriptive robustness view; does not replace the registered joint-stratum analysis.

| Group | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) |
|---|---:|---:|---:|---:|---:|
| K12 | 147 | 0.0680 [-0.0136, 0.1497] | 0.0476 [-0.0204, 0.1156] | 0.1293 [0.0612, 0.2041] | 0.0340 [-0.0544, 0.1224] |
| M3CoT | 175 | 0.3943 [0.3143, 0.4743] | 0.3086 [0.2400, 0.3771] | 0.3029 [0.2343, 0.3714] | 0.3771 [0.3086, 0.4514] |
| M3CoTConverted | 16 | 0.1250 [-0.1250, 0.3750] | 0.0625 [0.0000, 0.1875] | 0.0625 [0.0000, 0.1875] | 0.0625 [0.0000, 0.1875] |
| MMK12 | 1727 | 0.0932 [0.0712, 0.1158] | 0.0706 [0.0498, 0.0903] | 0.0805 [0.0614, 0.0996] | 0.1013 [0.0805, 0.1228] |
| MMK12Converted | 27 | 0.2222 [0.0000, 0.4444] | 0.2222 [0.0370, 0.4074] | 0.1852 [0.0000, 0.3704] | 0.1852 [0.0000, 0.4074] |
| MMMath | 428 | 0.0818 [0.0374, 0.1238] | 0.0514 [0.0093, 0.0935] | 0.0561 [0.0164, 0.0981] | 0.0514 [0.0117, 0.0911] |
| Processed | 1201 | 0.3306 [0.2989, 0.3614] | 0.2448 [0.2157, 0.2739] | 0.2315 [0.2032, 0.2598] | 0.2839 [0.2548, 0.3156] |
| R1OneVision | 105 | 0.2952 [0.1905, 0.4000] | 0.2571 [0.1619, 0.3524] | 0.2762 [0.1810, 0.3810] | 0.2571 [0.1714, 0.3429] |
| R1OneVisionConverted | 17 | 0.2353 [0.0588, 0.4706] | 0.1176 [-0.1176, 0.3529] | 0.2353 [0.0588, 0.4706] | 0.1176 [0.0000, 0.2941] |
| ScienceQA | 53 | 0.7358 [0.6038, 0.8491] | 0.6226 [0.4717, 0.7547] | 0.5660 [0.4340, 0.6981] | 0.6604 [0.5283, 0.7925] |
| ai2d | 107 | 0.1682 [0.0561, 0.2804] | 0.1121 [0.0187, 0.2150] | 0.1589 [0.0561, 0.2617] | 0.0935 [0.0000, 0.1869] |
| chartqa | 9 | 0.5556 [0.2222, 0.8889] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.3333 [0.1111, 0.6667] |
| dvqa | 71 | 0.5775 [0.4366, 0.7183] | 0.0563 [0.0141, 0.1127] | 0.0563 [0.0141, 0.1127] | 0.3803 [0.2676, 0.4930] |
| geoqa_plus | 118 | 0.3814 [0.2712, 0.4915] | 0.3475 [0.2458, 0.4492] | 0.3220 [0.2203, 0.4237] | 0.3814 [0.2881, 0.4746] |
| geoqa_plusConverted | 38 | 0.2895 [0.1053, 0.4737] | 0.0526 [-0.1316, 0.2368] | 0.2632 [0.1053, 0.4211] | 0.1842 [0.0000, 0.3684] |

## Category-only descriptive table

Role: descriptive robustness view; does not replace the registered joint-stratum analysis.

| Group | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) |
|---|---:|---:|---:|---:|---:|
| (GradeSchool) Geometric | 1178 | 0.2114 [0.1791, 0.2428] | 0.1672 [0.1392, 0.1952] | 0.1927 [0.1638, 0.2216] | 0.1689 [0.1401, 0.1978] |
| (GradeSchool) Non-Geo Math | 1510 | 0.1517 [0.1258, 0.1775] | 0.1252 [0.1020, 0.1490] | 0.1245 [0.1026, 0.1464] | 0.1364 [0.1119, 0.1596] |
| (GradeSchool) Science | 449 | 0.2918 [0.2361, 0.3452] | 0.2339 [0.1826, 0.2851] | 0.2183 [0.1693, 0.2673] | 0.3185 [0.2673, 0.3675] |
| Broader STEM Topics | 146 | 0.1712 [0.0753, 0.2603] | 0.1438 [0.0616, 0.2260] | 0.1301 [0.0548, 0.2055] | 0.1370 [0.0616, 0.2192] |
| Commonsense | 13 | 0.4615 [0.2308, 0.7692] | 0.4615 [0.2308, 0.6923] | 0.3077 [0.0769, 0.5385] | 0.5385 [0.2308, 0.7692] |
| Social Science | 69 | 0.4638 [0.3333, 0.5797] | 0.3188 [0.2174, 0.4348] | 0.2754 [0.1739, 0.3913] | 0.4203 [0.2899, 0.5362] |
| Spatial Reasoning | 253 | 0.2174 [0.1542, 0.2846] | 0.1028 [0.0474, 0.1542] | 0.1186 [0.0672, 0.1700] | 0.1423 [0.0830, 0.1976] |
| Tables/Diagrams/Charts | 621 | 0.2367 [0.1932, 0.2802] | 0.0982 [0.0660, 0.1304] | 0.1063 [0.0725, 0.1385] | 0.2110 [0.1723, 0.2512] |

## Geometry3K anchor comparison (one seed (seed 1); informed comparison)

This comparison is informed, not fully prospective: the anchors are the completed Geometry3K seed-1 recovery readout (Informed-Prediction Disclosure, docs/registered_m7_amendment_v1.md).

| Blind arm | Geometry3K anchor | ViRL recovery (95% CI) | Difference (95% CI) | Direction (> anchor) holds | Interval label |
|---|---:|---:|---:|---|---|
| A2 gray | 0.0789 | 0.7174 | 0.6385 [0.5627, 0.7193] | true | stable |
| A2b no-image | 0.1184 | 0.7449 | 0.6265 [0.5522, 0.7058] | true | stable |
| A3 caption | no registered anchor | 0.8822 [NA] | NA | NA | stable |

## M10 support-sharpening candidates

Rule: base 0/16 under the arm's own condition, step-0 greedy wrong, step-100 greedy correct; 64-sample frozen-base follow-up is reported separately under M10.

| Arm | Candidates | Artifact |
|---|---:|---|
| A1 real | 302 | `experiments/scratch_verify_twoseed/replay/arts/support_candidates_a1_real.jsonl` |
| A2 gray | 278 | `experiments/scratch_verify_twoseed/replay/arts/support_candidates_a2_gray.jsonl` |
| A2b no-image | 292 | `experiments/scratch_verify_twoseed/replay/arts/support_candidates_a2b_noimage.jsonl` |
| A3 caption | 317 | `experiments/scratch_verify_twoseed/replay/arts/support_candidates_a3_caption.jsonl` |

Candidate selection does not claim that RL created or taught a capability; M10 language remains non-causal.

## Provenance

- Held-out manifest: `data/virl39k_m7_heldout_v3.jsonl` (sha256 `50f3b85c11c4046ef2512c544faec04286648688bb6d47548995f18cab40716c`, 4239 rows).
- Analysis git head: `d5848c37e10e04472961640e28c9e4eb4ad8af5e`.
- Bootstrap: 5000 draws, seed 20260716; deterministic statistic/arm labels hashed into independent streams via src.analysis.pilot_fourarm.deterministic_seed.
- data/virl39k_m7_split_manifest_v2.json n_strata_rank_eligible=21 counts component labels, not items, and was not used; eligibility was recounted directly from the held-out jsonl.
- Registered documents: `docs/registered_m7_amendment_v1.md`, `docs/registered_m7_seed_scope_v1.md`, `docs/registered_m7_single_image_v2.md`, `docs/registered_extensions_v1.md`.

| Arm | Step | Run dir | per_item sha256 |
|---|---|---|---|
| A1 real | step0 | `experiments/runs/m7_step0_heldout_base_real_an29_20260730T154447Z` | `50c0cda2fdaf6d2ae1bfcfb17b216f0658a72879a0f3c28f48c08592719fb7c3` |
| A1 real | step100 | `experiments/runs/m7_step100_heldout_a1_real_an29_20260731T161352Z` | `b3a304a3d446b7a415ae5b58f924dd10b07369011ff44629bd49242a5f5869b4` |
| A2 gray | step0 | `experiments/runs/m7_step0_heldout_base_gray_an29_20260730T154458Z` | `c168b70cd7b53f50f7de3d3b771533d32362ed5d99bc8cfabf99e1998b834c9e` |
| A2 gray | step100 | `experiments/runs/m7_step100_heldout_a2_gray_gray_an12_20260803T151508Z` | `1b161a71cf4184518c871c4d414863f681ac39a2d9b1481f0b46b3cde007f172` |
| A2b no-image | step0 | `experiments/runs/m7_step0_heldout_base_none_an29_20260730T154501Z` | `825c92ff2d51bf5bcd10ca0a3d6995d386b19ce526fa4fe11435d2a3a8bd3ac7` |
| A2b no-image | step100 | `experiments/runs/m7_step100_heldout_a2b_none_an29_20260801T014325Z` | `d95a34d2e9bbc7b9a6dd0130a76a78f936d5ad9c6fc76ca7aeec3912ac03e319` |
| A3 caption | step0 | `experiments/runs/m7_step0_heldout_base_caption_an29_20260730T154503Z` | `ac04a4e2740a4838f7358b38d8af1b47ca8e21b93e8c67f00c83d1e23059a207` |
| A3 caption | step100 | `experiments/runs/m7_step100_heldout_a3_caption_caption_an12_20260803T151440Z` | `a60640a0fd0169b4c0fbfe20e54b1f04c2dbbd678bc026ad382eef85b283493a` |
