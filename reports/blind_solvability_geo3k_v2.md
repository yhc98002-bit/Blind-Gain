# Geometry3K Blind-Solvability Audit V2

Status:
- Complete for the frozen filtered train corpus and untouched test split under all five conditions.
- This v2 uses 2,048-token outputs, the exact pilot-reward-v1 scorer, canonical-v2 comparison scoring, and Jeffreys-smoothed p_i. The retained v1 tables used 512 tokens and the canonical-v1 scorer.
- Machine status JSON: `reports/blind_solvability_geo3k_v2_audited.json` (`status=pass`).

Evidence:
- Items: 1889 ({'test': 601, 'train': 1288}).
- Prompt contract SHA256: `7ac39f53a2a824490fc5ee22671a888d2d79d55e1d8351919006d7d71c7a8f3f`.
- Sampling: n=16, temperature=1.0, G=5; greedy decoding uses temperature=0, top_p=1.0, n=1.
- Symbolic grading: `posix-itimer-v1` at `5.0` seconds per bounded call.

Primary pilot-reward and canonical-v2 results:
| Condition | Split | Pilot greedy accuracy | Canonical greedy accuracy | Mean p_i | Mean q_i | Mean pilot reward | Format rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| real | all | 0.1535 [0.1361, 0.1710] | 0.1673 [0.1498, 0.1842] | 0.1150 [0.1092, 0.1208] | 0.3631 [0.3513, 0.3751] | 0.2352 [0.2306, 0.2397] | 0.3794 [0.3711, 0.3874] |
| real | train | 0.1553 [0.1351, 0.1747] | 0.1638 [0.1436, 0.1848] | 0.1115 [0.1045, 0.1186] | 0.3545 [0.3405, 0.3693] | 0.2356 [0.2298, 0.2417] | 0.3839 [0.3732, 0.3947] |
| real | test | 0.1498 [0.1215, 0.1797] | 0.1747 [0.1464, 0.2030] | 0.1225 [0.1124, 0.1341] | 0.3818 [0.3594, 0.4030] | 0.2343 [0.2255, 0.2434] | 0.3698 [0.3548, 0.3842] |
| gray | all | 0.0651 [0.0551, 0.0768] | 0.0683 [0.0572, 0.0794] | 0.0682 [0.0630, 0.0739] | 0.2201 [0.2109, 0.2294] | 0.0764 [0.0723, 0.0805] | 0.1116 [0.1067, 0.1165] |
| gray | train | 0.0567 [0.0443, 0.0683] | 0.0582 [0.0458, 0.0707] | 0.0640 [0.0582, 0.0702] | 0.2126 [0.2025, 0.2230] | 0.0735 [0.0689, 0.0782] | 0.1102 [0.1046, 0.1161] |
| gray | test | 0.0832 [0.0632, 0.1049] | 0.0899 [0.0682, 0.1131] | 0.0771 [0.0670, 0.0881] | 0.2364 [0.2190, 0.2539] | 0.0826 [0.0754, 0.0899] | 0.1145 [0.1052, 0.1238] |
| noise | all | 0.0588 [0.0482, 0.0699] | 0.0625 [0.0513, 0.0731] | 0.0687 [0.0637, 0.0742] | 0.2250 [0.2163, 0.2342] | 0.1310 [0.1267, 0.1355] | 0.2201 [0.2131, 0.2271] |
| noise | train | 0.0512 [0.0396, 0.0644] | 0.0536 [0.0411, 0.0668] | 0.0648 [0.0591, 0.0709] | 0.2181 [0.2075, 0.2284] | 0.1301 [0.1249, 0.1354] | 0.2227 [0.2140, 0.2316] |
| noise | test | 0.0749 [0.0549, 0.0965] | 0.0815 [0.0599, 0.1048] | 0.0773 [0.0671, 0.0882] | 0.2399 [0.2229, 0.2574] | 0.1327 [0.1250, 0.1408] | 0.2145 [0.2026, 0.2268] |
| none | all | 0.0503 [0.0408, 0.0603] | 0.0503 [0.0408, 0.0604] | 0.0728 [0.0667, 0.0791] | 0.2184 [0.2094, 0.2277] | 0.0545 [0.0505, 0.0584] | 0.0629 [0.0591, 0.0665] |
| none | train | 0.0419 [0.0311, 0.0536] | 0.0419 [0.0318, 0.0528] | 0.0681 [0.0613, 0.0756] | 0.2117 [0.2013, 0.2221] | 0.0507 [0.0463, 0.0554] | 0.0602 [0.0559, 0.0646] |
| none | test | 0.0682 [0.0483, 0.0882] | 0.0682 [0.0483, 0.0882] | 0.0827 [0.0710, 0.0948] | 0.2326 [0.2159, 0.2506] | 0.0626 [0.0551, 0.0701] | 0.0685 [0.0620, 0.0751] |
| caption | all | 0.1747 [0.1572, 0.1922] | 0.1826 [0.1657, 0.2006] | 0.1363 [0.1288, 0.1441] | 0.3742 [0.3620, 0.3880] | 0.1934 [0.1883, 0.1986] | 0.2731 [0.2663, 0.2795] |
| caption | train | 0.1646 [0.1452, 0.1863] | 0.1700 [0.1498, 0.1902] | 0.1302 [0.1210, 0.1396] | 0.3592 [0.3437, 0.3757] | 0.1899 [0.1834, 0.1962] | 0.2728 [0.2646, 0.2809] |
| caption | test | 0.1963 [0.1664, 0.2280] | 0.2097 [0.1780, 0.2429] | 0.1496 [0.1362, 0.1641] | 0.4064 [0.3834, 0.4288] | 0.2008 [0.1916, 0.2096] | 0.2738 [0.2620, 0.2863] |

Jeffreys p_i bands (all items):
| Condition | [0,0.2) | [0.2,0.4) | [0.4,0.6) | [0.6,0.8) | [0.8,1] |
| --- | ---: | ---: | ---: | ---: | ---: |
| real | 0.7930 | 0.1556 | 0.0376 | 0.0138 | 0.0000 |
| gray | 0.9164 | 0.0482 | 0.0201 | 0.0127 | 0.0026 |
| noise | 0.9121 | 0.0551 | 0.0159 | 0.0154 | 0.0016 |
| none | 0.9127 | 0.0429 | 0.0196 | 0.0196 | 0.0053 |
| caption | 0.7422 | 0.1652 | 0.0551 | 0.0334 | 0.0042 |

q_i distributions (all items):
| Condition | Min | Q25 | Median | Q75 | Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| real | 0.1387 | 0.1387 | 0.1387 | 0.5485 | 0.9375 |
| gray | 0.1387 | 0.1387 | 0.1387 | 0.1387 | 0.9375 |
| noise | 0.1387 | 0.1387 | 0.1387 | 0.1387 | 0.9375 |
| none | 0.1387 | 0.1387 | 0.1387 | 0.1387 | 0.9375 |
| caption | 0.1387 | 0.1387 | 0.1387 | 0.6838 | 0.9375 |

Greedy real-vs-blind quadrants:
| Blind condition | Split | Both | Real only | Blind only | Neither |
| --- | --- | ---: | ---: | ---: | ---: |
| gray | all | 60 | 230 | 63 | 1536 |
| gray | train | 39 | 161 | 34 | 1054 |
| gray | test | 21 | 69 | 29 | 482 |
| noise | all | 56 | 234 | 55 | 1544 |
| noise | train | 37 | 163 | 29 | 1059 |
| noise | test | 19 | 71 | 26 | 485 |
| none | all | 47 | 243 | 48 | 1551 |
| none | train | 28 | 172 | 26 | 1062 |
| none | test | 19 | 71 | 22 | 489 |
| caption | all | 127 | 163 | 203 | 1396 |
| caption | train | 83 | 117 | 129 | 959 |
| caption | test | 44 | 46 | 74 | 437 |

Problems:
- These are base-model corpus measurements, not pilot-arm outcomes.
- Item-bootstrap intervals quantify item uncertainty; they do not estimate run-to-run RL variance.

Decision:
- No gate decision is made here. These frozen q_i values are inputs to PI-reviewed preregistration.

Next actions:
- Fill the preregistration's computed q_i fields and submit the frozen document for PI review after the separate human R19 audit is recorded.
