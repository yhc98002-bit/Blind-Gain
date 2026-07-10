# Geometry3K Blind-Solvability Audit

Status:
- Complete over 2702 Geometry3K items under all five registered conditions.
- Metrics use the canonical answer parser; intervals are 2,000-draw item-bootstrap 95% confidence intervals.

Evidence:
- real: `experiments/runs/blind_solvability_geo3k_real_an12_20260710T074916Z`
- gray: `experiments/runs/blind_solvability_geo3k_gray_an12_20260710T074917Z`
- noise: `experiments/runs/blind_solvability_geo3k_noise_an12_20260710T074918Z`
- none: `experiments/runs/blind_solvability_geo3k_none_an12_20260710T074918Z`
- caption: `experiments/runs/blind_solvability_geo3k_v2limits_caption_an29_20260710T085325Z`

Aggregate results:
| Condition | Split | Greedy accuracy | Sample p | pass@G=5 | pass@K=16 | p in [0.2, 0.8] |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| real | all | 0.1088 [0.0973, 0.1207] | 0.0567 [0.0526, 0.0607] | 0.1897 [0.1789, 0.2006] | 0.3431 [0.3249, 0.3616] | 0.0788 [0.0688, 0.0896] |
| real | train | 0.1080 [0.0942, 0.1223] | 0.0549 [0.0503, 0.0596] | 0.1841 [0.1713, 0.1965] | 0.3351 [0.3151, 0.3551] | 0.0733 [0.0624, 0.0842] |
| real | test | 0.1115 [0.0882, 0.1381] | 0.0630 [0.0543, 0.0726] | 0.2092 [0.1849, 0.2348] | 0.3710 [0.3328, 0.4077] | 0.0982 [0.0749, 0.1215] |
| gray | all | 0.0463 [0.0385, 0.0544] | 0.0292 [0.0256, 0.0331] | 0.0845 [0.0761, 0.0935] | 0.1484 [0.1347, 0.1621] | 0.0403 [0.0326, 0.0477] |
| gray | train | 0.0438 [0.0352, 0.0519] | 0.0285 [0.0243, 0.0331] | 0.0826 [0.0733, 0.0925] | 0.1433 [0.1290, 0.1585] | 0.0405 [0.0324, 0.0490] |
| gray | test | 0.0549 [0.0382, 0.0732] | 0.0318 [0.0238, 0.0408] | 0.0908 [0.0735, 0.1100] | 0.1664 [0.1381, 0.1963] | 0.0399 [0.0250, 0.0566] |
| noise | all | 0.0455 [0.0377, 0.0533] | 0.0292 [0.0256, 0.0331] | 0.0866 [0.0783, 0.0951] | 0.1540 [0.1406, 0.1680] | 0.0418 [0.0344, 0.0496] |
| noise | train | 0.0452 [0.0362, 0.0543] | 0.0284 [0.0245, 0.0327] | 0.0852 [0.0755, 0.0952] | 0.1514 [0.1361, 0.1671] | 0.0414 [0.0333, 0.0505] |
| noise | test | 0.0466 [0.0316, 0.0632] | 0.0319 [0.0237, 0.0410] | 0.0914 [0.0741, 0.1113] | 0.1631 [0.1348, 0.1913] | 0.0433 [0.0283, 0.0599] |
| none | all | 0.0437 [0.0359, 0.0522] | 0.0317 [0.0276, 0.0361] | 0.0855 [0.0773, 0.0947] | 0.1406 [0.1277, 0.1540] | 0.0429 [0.0344, 0.0511] |
| none | train | 0.0409 [0.0328, 0.0490] | 0.0311 [0.0265, 0.0358] | 0.0848 [0.0748, 0.0950] | 0.1380 [0.1238, 0.1528] | 0.0443 [0.0362, 0.0528] |
| none | test | 0.0532 [0.0366, 0.0715] | 0.0338 [0.0245, 0.0434] | 0.0882 [0.0714, 0.1088] | 0.1498 [0.1231, 0.1764] | 0.0383 [0.0233, 0.0549] |
| caption | all | 0.1107 [0.0995, 0.1232] | 0.0631 [0.0578, 0.0683] | 0.1831 [0.1719, 0.1949] | 0.3050 [0.2876, 0.3220] | 0.0929 [0.0818, 0.1036] |
| caption | train | 0.1057 [0.0919, 0.1190] | 0.0608 [0.0549, 0.0666] | 0.1767 [0.1636, 0.1904] | 0.2941 [0.2741, 0.3137] | 0.0890 [0.0771, 0.1009] |
| caption | test | 0.1281 [0.1032, 0.1564] | 0.0713 [0.0598, 0.0842] | 0.2055 [0.1797, 0.2311] | 0.3428 [0.3045, 0.3794] | 0.1065 [0.0832, 0.1314] |

Sample-p distribution over all items:
| Condition | p=0 | 0<p<0.2 | 0.2<=p<=0.8 | 0.8<p<1 | p=1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| real | 0.6569 [0.6395, 0.6743] | 0.2639 [0.2472, 0.2798] | 0.0788 [0.0688, 0.0892] | 0.0004 [0.0000, 0.0011] | 0.0000 [0.0000, 0.0000] |
| gray | 0.8516 [0.8375, 0.8645] | 0.1058 [0.0947, 0.1173] | 0.0403 [0.0333, 0.0481] | 0.0019 [0.0004, 0.0037] | 0.0004 [0.0000, 0.0011] |
| noise | 0.8460 [0.8320, 0.8597] | 0.1107 [0.0988, 0.1225] | 0.0418 [0.0340, 0.0496] | 0.0015 [0.0004, 0.0030] | 0.0000 [0.0000, 0.0000] |
| none | 0.8594 [0.8457, 0.8727] | 0.0925 [0.0825, 0.1029] | 0.0429 [0.0352, 0.0511] | 0.0044 [0.0019, 0.0070] | 0.0007 [0.0000, 0.0019] |
| caption | 0.6950 [0.6780, 0.7117] | 0.2084 [0.1936, 0.2239] | 0.0929 [0.0814, 0.1040] | 0.0037 [0.0019, 0.0063] | 0.0000 [0.0000, 0.0000] |

Greedy real-vs-blind quadrants:
| Blind condition | Split | Both | Real only | Blind only | Neither |
| --- | --- | ---: | ---: | ---: | ---: |
| gray | all | 59 | 235 | 66 | 2342 |
| gray | train | 44 | 183 | 48 | 1826 |
| gray | test | 15 | 52 | 18 | 516 |
| noise | all | 60 | 234 | 63 | 2345 |
| noise | train | 45 | 182 | 50 | 1824 |
| noise | test | 15 | 52 | 13 | 521 |
| none | all | 59 | 235 | 59 | 2349 |
| none | train | 44 | 183 | 42 | 1832 |
| none | test | 15 | 52 | 17 | 517 |
| caption | all | 115 | 179 | 184 | 2224 |
| caption | train | 87 | 140 | 135 | 1739 |
| caption | test | 28 | 39 | 49 | 485 |

Problems:
- These are base-model dataset-property measurements, not training-arm outcomes.
- Caption results use the frozen question-blind 3B caption store; they do not estimate arbitrary question-conditioned descriptions.

Decision:
- Use per-item blind p and the [0.2, 0.8] band to stratify later mechanical-pilot analysis.
- Keep real, gray, noise, no-image, and caption results separate; do not collapse them into one generic blind score.

Next actions:
- Run the same registered harness on the stratified ViRL39K sample before the future scientific pilot.
