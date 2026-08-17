# M7 R3 Readout V1 - PARTIAL (step-0 only)

Status: `partial-step0-only`.

Scope:
- Seed scope: seed 1 only for all four arms; every gain, recovery, and correlation below is a per-seed (one seed) number and no between-seed variance claim is made (docs/registered_m7_seed_scope_v1.md).
- Single-image restriction: M7 is restricted to single-image rows (worker.rollout.limit_images=1); retained 23,542/25,255 train rows (93.2%) and 4,239/4,501 held-out rows (94.2%) (docs/registered_m7_single_image_v2.md).
- Pooled-only readout is prohibited; corpus aggregate, every joint stratum, and source-only/category-only descriptive tables are all published; A2/A2b/A3 are never pooled into one generic blind arm (docs/registered_extensions_v1.md Extension 3, docs/registered_m7_amendment_v1.md).
- This report contains numbers and provenance only; interpretation is reserved to the PIs.

Machine artifact: `reports/m7_r3_readout_v1_partial.json`.

## PARTIAL MODE

- This output is a step-0-only plumbing readout; it is NOT the registered R3 result.
- Refused estimands (require the step-100 side): gain, recovery, rho_gain, rho_recovery, aggregate_recovery, geometry3k_anchor_comparison, m10_support_sharpening.

## Strata accounting

- Joint (source, category) strata recounted from `data/virl39k_m7_heldout_v3.jsonl`: 60 total, 22 eligible (>= 30 held-out items), 38 descriptive-small-n.
- Eligibility depends only on sample count, never on a model outcome; descriptive-small-n strata are published, not merged or discarded, and enter no rank statistic.

## Corpus aggregate (one seed (seed 1))

| Arm | n | q_bar | Acc_final step 0 |
|---|---:|---:|---:|
| A1 real | 4239 | 0.5122 | 0.2744 |
| A2 gray | 4239 | 0.4235 | 0.1894 |
| A2b no-image | 4239 | 0.4154 | 0.1538 |
| A3 caption | 4239 | 0.4458 | 0.1849 |

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

## Descriptive small-n strata (38)

Published per registration; not merged, not discarded, not in any rank statistic.

| Source | Category | n | q_bar A1 | q_bar A2 | q_bar A2b | q_bar A3 |
|---|---|---:|---:|---:|---:|---:|
| M3CoT | (GradeSchool) Geometric | 6 | 0.4921 | 0.2455 | 0.1772 | 0.2847 |
| M3CoT | (GradeSchool) Non-Geo Math | 11 | 0.2390 | 0.2925 | 0.1597 | 0.3183 |
| M3CoT | Broader STEM Topics | 1 | 0.1387 | 0.1387 | 0.1387 | 0.1387 |
| M3CoT | Commonsense | 12 | 0.2804 | 0.2306 | 0.1772 | 0.2760 |
| M3CoT | Spatial Reasoning | 20 | 0.1618 | 0.1938 | 0.1618 | 0.1618 |
| M3CoT | Tables/Diagrams/Charts | 7 | 0.1717 | 0.3081 | 0.1387 | 0.1717 |
| M3CoTConverted | (GradeSchool) Science | 6 | 0.2840 | 0.1387 | 0.1387 | 0.2070 |
| M3CoTConverted | Social Science | 5 | 0.3026 | 0.1387 | 0.1387 | 0.1849 |
| M3CoTConverted | Spatial Reasoning | 2 | 0.1387 | 0.1387 | 0.1387 | 0.1387 |
| M3CoTConverted | Tables/Diagrams/Charts | 3 | 0.2928 | 0.1387 | 0.1387 | 0.2157 |
| MMK12 | Social Science | 3 | 0.2157 | 0.1387 | 0.1387 | 0.1387 |
| MMK12Converted | (GradeSchool) Geometric | 13 | 0.6105 | 0.5649 | 0.5863 | 0.5401 |
| MMK12Converted | (GradeSchool) Non-Geo Math | 2 | 0.7430 | 0.1387 | 0.1387 | 0.5768 |
| MMK12Converted | (GradeSchool) Science | 8 | 0.3814 | 0.2963 | 0.3252 | 0.3693 |
| MMK12Converted | Broader STEM Topics | 1 | 0.6838 | 0.8548 | 0.5485 | 0.3699 |
| MMK12Converted | Spatial Reasoning | 1 | 0.5485 | 0.5485 | 0.5485 | 0.8548 |
| MMK12Converted | Tables/Diagrams/Charts | 2 | 0.6123 | 0.3699 | 0.3699 | 0.3436 |
| Processed | Commonsense | 1 | 0.1387 | 0.1387 | 0.1387 | 0.1387 |
| Processed | Social Science | 4 | 0.6758 | 0.3755 | 0.2999 | 0.4540 |
| R1OneVision | (GradeSchool) Geometric | 12 | 0.2760 | 0.2989 | 0.3788 | 0.3658 |
| R1OneVision | (GradeSchool) Non-Geo Math | 5 | 0.2669 | 0.2774 | 0.2206 | 0.1849 |
| R1OneVision | Broader STEM Topics | 14 | 0.3318 | 0.2527 | 0.1882 | 0.3107 |
| R1OneVision | Spatial Reasoning | 18 | 0.4773 | 0.3597 | 0.3289 | 0.4386 |
| R1OneVision | Tables/Diagrams/Charts | 6 | 0.2840 | 0.2157 | 0.1772 | 0.2681 |
| R1OneVisionConverted | (GradeSchool) Geometric | 2 | 0.7693 | 0.7386 | 0.8429 | 0.7016 |
| R1OneVisionConverted | (GradeSchool) Non-Geo Math | 2 | 0.3436 | 0.1387 | 0.1387 | 0.3436 |
| R1OneVisionConverted | (GradeSchool) Science | 9 | 0.1644 | 0.1387 | 0.1387 | 0.2099 |
| R1OneVisionConverted | Spatial Reasoning | 2 | 0.2543 | 0.2543 | 0.2543 | 0.1387 |
| R1OneVisionConverted | Tables/Diagrams/Charts | 2 | 0.3699 | 0.1387 | 0.1387 | 0.1387 |
| ScienceQA | Broader STEM Topics | 3 | 0.2157 | 0.1387 | 0.1387 | 0.1387 |
| ScienceQA | Social Science | 3 | 0.2753 | 0.2157 | 0.2928 | 0.3523 |
| ScienceQA | Spatial Reasoning | 9 | 0.1644 | 0.2356 | 0.1900 | 0.2157 |
| ScienceQA | Tables/Diagrams/Charts | 4 | 0.1387 | 0.1387 | 0.1387 | 0.1387 |
| chartqa | Tables/Diagrams/Charts | 9 | 0.5134 | 0.1387 | 0.1387 | 0.2840 |
| dvqa | Broader STEM Topics | 1 | 0.9019 | 0.1387 | 0.1387 | 0.1387 |
| dvqa | Social Science | 1 | 0.8548 | 0.1387 | 0.1387 | 0.1387 |
| geoqa_plusConverted | (GradeSchool) Non-Geo Math | 2 | 0.3436 | 0.4112 | 0.2543 | 0.3436 |
| geoqa_plusConverted | Spatial Reasoning | 2 | 0.4612 | 0.2543 | 0.1387 | 0.4112 |

## Source-only descriptive table

Role: descriptive robustness view; does not replace the registered joint-stratum analysis.

| Group | n | q_bar A1 | q_bar A2 | q_bar A2b | q_bar A3 | Acc0 A1 | Acc0 A2 | Acc0 A2b | Acc0 A3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| K12 | 147 | 0.6598 | 0.5015 | 0.5027 | 0.5808 | 0.4490 | 0.3129 | 0.2177 | 0.3197 |
| M3CoT | 175 | 0.2280 | 0.2053 | 0.1762 | 0.1952 | 0.0400 | 0.0114 | 0.0057 | 0.0000 |
| M3CoTConverted | 16 | 0.2733 | 0.1387 | 0.1387 | 0.1932 | 0.0625 | 0.0000 | 0.0000 | 0.0000 |
| MMK12 | 1727 | 0.5697 | 0.4719 | 0.4658 | 0.4851 | 0.3289 | 0.2154 | 0.1795 | 0.2142 |
| MMK12Converted | 27 | 0.5530 | 0.4494 | 0.4570 | 0.4830 | 0.3333 | 0.1852 | 0.1481 | 0.1481 |
| MMMath | 428 | 0.5649 | 0.5441 | 0.5471 | 0.5436 | 0.3364 | 0.3271 | 0.2734 | 0.2500 |
| Processed | 1201 | 0.4374 | 0.3603 | 0.3517 | 0.3958 | 0.2040 | 0.1440 | 0.1232 | 0.1524 |
| R1OneVision | 105 | 0.3132 | 0.2666 | 0.2526 | 0.3156 | 0.0857 | 0.0571 | 0.0286 | 0.0381 |
| R1OneVisionConverted | 17 | 0.2914 | 0.2228 | 0.2351 | 0.2667 | 0.0588 | 0.0588 | 0.0000 | 0.0000 |
| ScienceQA | 53 | 0.1726 | 0.1726 | 0.1648 | 0.1978 | 0.0189 | 0.0189 | 0.0000 | 0.0000 |
| ai2d | 107 | 0.7360 | 0.5142 | 0.4588 | 0.5590 | 0.4673 | 0.1682 | 0.1308 | 0.2991 |
| chartqa | 9 | 0.5134 | 0.1387 | 0.1387 | 0.2840 | 0.1111 | 0.0000 | 0.0000 | 0.0000 |
| dvqa | 71 | 0.6629 | 0.1517 | 0.1452 | 0.4045 | 0.3239 | 0.0000 | 0.0000 | 0.1549 |
| geoqa_plus | 118 | 0.5632 | 0.5488 | 0.5522 | 0.4505 | 0.2542 | 0.2542 | 0.1610 | 0.1525 |
| geoqa_plusConverted | 38 | 0.5242 | 0.4765 | 0.4058 | 0.4131 | 0.2105 | 0.2368 | 0.1053 | 0.2105 |

## Category-only descriptive table

Role: descriptive robustness view; does not replace the registered joint-stratum analysis.

| Group | n | q_bar A1 | q_bar A2 | q_bar A2b | q_bar A3 | Acc0 A1 | Acc0 A2 | Acc0 A2b | Acc0 A3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| (GradeSchool) Geometric | 1178 | 0.5117 | 0.4790 | 0.4793 | 0.4533 | 0.2649 | 0.2284 | 0.1834 | 0.2037 |
| (GradeSchool) Non-Geo Math | 1510 | 0.5258 | 0.4388 | 0.4390 | 0.4854 | 0.2927 | 0.2086 | 0.1662 | 0.2000 |
| (GradeSchool) Science | 449 | 0.4690 | 0.4454 | 0.4295 | 0.3729 | 0.2294 | 0.2160 | 0.1849 | 0.1069 |
| Broader STEM Topics | 146 | 0.6058 | 0.4370 | 0.4151 | 0.5433 | 0.4110 | 0.1918 | 0.1986 | 0.2877 |
| Commonsense | 13 | 0.2695 | 0.2235 | 0.1742 | 0.2655 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Social Science | 69 | 0.2580 | 0.1956 | 0.1748 | 0.1923 | 0.0290 | 0.0145 | 0.0290 | 0.0435 |
| Spatial Reasoning | 253 | 0.4468 | 0.3605 | 0.3351 | 0.3583 | 0.1739 | 0.1383 | 0.0949 | 0.1265 |
| Tables/Diagrams/Charts | 621 | 0.5490 | 0.3175 | 0.2911 | 0.4324 | 0.3221 | 0.0934 | 0.0757 | 0.1884 |

## Provenance

- Held-out manifest: `data/virl39k_m7_heldout_v3.jsonl` (sha256 `50f3b85c11c4046ef2512c544faec04286648688bb6d47548995f18cab40716c`, 4239 rows).
- Analysis git head: `553221fc3b97c3259143973273c9e8841d053b3c`.
- Bootstrap: 5000 draws, seed 20260716; deterministic statistic/arm labels hashed into independent streams via src.analysis.pilot_fourarm.deterministic_seed.
- data/virl39k_m7_split_manifest_v2.json n_strata_rank_eligible=21 counts component labels, not items, and was not used; eligibility was recounted directly from the held-out jsonl.
- Registered documents: `docs/registered_m7_amendment_v1.md`, `docs/registered_m7_seed_scope_v1.md`, `docs/registered_m7_single_image_v2.md`, `docs/registered_extensions_v1.md`.

| Arm | Step | Run dir | per_item sha256 |
|---|---|---|---|
| A1 real | step0 | `experiments/runs/m7_step0_heldout_base_real_an29_20260730T154447Z` | `50c0cda2fdaf6d2ae1bfcfb17b216f0658a72879a0f3c28f48c08592719fb7c3` |
| A2 gray | step0 | `experiments/runs/m7_step0_heldout_base_gray_an29_20260730T154458Z` | `c168b70cd7b53f50f7de3d3b771533d32362ed5d99bc8cfabf99e1998b834c9e` |
| A2b no-image | step0 | `experiments/runs/m7_step0_heldout_base_none_an29_20260730T154501Z` | `825c92ff2d51bf5bcd10ca0a3d6995d386b19ce526fa4fe11435d2a3a8bd3ac7` |
| A3 caption | step0 | `experiments/runs/m7_step0_heldout_base_caption_an29_20260730T154503Z` | `ac04a4e2740a4838f7358b38d8af1b47ca8e21b93e8c67f00c83d1e23059a207` |
