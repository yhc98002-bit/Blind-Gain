# ViRL39K Blind-Solvability Sample V1

Status:
- Complete for the frozen 4,096-item stratified sample under all five conditions.
- Machine status JSON: `reports/blind_solvability_virl39k_sample_v1_audited.json`.
- This is a base-model corpus audit, not a pilot-arm result or PI gate decision.

Evidence:
- Decoding: greedy plus n=16 at temperature 1.0, 2,048 maximum tokens, G=5.
- Symbolic grading: `posix-itimer-v1` at `5.0` seconds per bounded call.
- Frozen source SHA256: `ffbad6eaff57f6dd11f136b066e4d4206e43381281a3cb24cc677241c360e6d5`.
- Multi-image distribution: `{'1': 3856, '2': 137, '3': 43, '4': 39, '5': 19, '6': 1, '8': 1}`; maximum 8 images.

Overall results with item-bootstrap 95% CIs:
| Condition | Pilot greedy accuracy | Canonical greedy accuracy | Mean p_i | Mean q_i | Mean pilot reward | Format rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| real | 0.2947 [0.2808, 0.3086] | 0.2720 [0.2583, 0.2852] | 0.2438 [0.2361, 0.2512] | 0.5115 [0.5028, 0.5205] | 0.2505 [0.2458, 0.2553] | 0.2732 [0.2654, 0.2815] |
| gray | 0.2102 [0.1980, 0.2229] | 0.1960 [0.1836, 0.2080] | 0.1849 [0.1781, 0.1920] | 0.4188 [0.4093, 0.4278] | 0.1863 [0.1818, 0.1906] | 0.2074 [0.2007, 0.2145] |
| noise | 0.2126 [0.2007, 0.2253] | 0.1970 [0.1851, 0.2092] | 0.1860 [0.1790, 0.1929] | 0.4251 [0.4159, 0.4344] | 0.1997 [0.1954, 0.2041] | 0.2330 [0.2257, 0.2396] |
| none | 0.1624 [0.1511, 0.1731] | 0.1548 [0.1438, 0.1667] | 0.1814 [0.1748, 0.1884] | 0.4151 [0.4065, 0.4237] | 0.1701 [0.1656, 0.1744] | 0.1787 [0.1725, 0.1849] |
| caption | 0.1868 [0.1750, 0.1990] | 0.1729 [0.1616, 0.1853] | 0.1811 [0.1749, 0.1873] | 0.4355 [0.4267, 0.4443] | 0.2396 [0.2353, 0.2441] | 0.3180 [0.3105, 0.3256] |

Per-category pilot greedy accuracy and mean q_i:
| Condition | Category | n | Greedy accuracy | Mean q_i |
| --- | --- | ---: | ---: | ---: |
| real | (GradeSchool) Geometric | 1123 | 0.2805 [0.2547, 0.3063] | 0.5280 [0.5116, 0.5446] |
| real | (GradeSchool) Non-Geo Math | 1574 | 0.3323 [0.3100, 0.3551] | 0.5261 [0.5115, 0.5405] |
| real | (GradeSchool) Science | 365 | 0.2466 [0.2000, 0.2904] | 0.4488 [0.4183, 0.4807] |
| real | Broader STEM Topics | 99 | 0.4848 [0.3939, 0.5859] | 0.5687 [0.5094, 0.6263] |
| real | Commonsense | 12 | 0.0000 [0.0000, 0.0000] | 0.3226 [0.2350, 0.4058] |
| real | Social Science | 68 | 0.0147 [0.0000, 0.0441] | 0.2204 [0.1901, 0.2559] |
| real | Spatial Reasoning | 205 | 0.1854 [0.1317, 0.2390] | 0.4076 [0.3699, 0.4466] |
| real | Tables/Diagrams/Charts | 650 | 0.2954 [0.2615, 0.3323] | 0.5411 [0.5189, 0.5639] |
| gray | (GradeSchool) Geometric | 1123 | 0.2654 [0.2386, 0.2921] | 0.4843 [0.4670, 0.5017] |
| gray | (GradeSchool) Non-Geo Math | 1574 | 0.2510 [0.2300, 0.2726] | 0.4546 [0.4402, 0.4688] |
| gray | (GradeSchool) Science | 365 | 0.1890 [0.1507, 0.2275] | 0.4281 [0.3968, 0.4585] |
| gray | Broader STEM Topics | 99 | 0.2020 [0.1212, 0.2828] | 0.4273 [0.3684, 0.4878] |
| gray | Commonsense | 12 | 0.0000 [0.0000, 0.0000] | 0.2262 [0.1387, 0.3287] |
| gray | Social Science | 68 | 0.0000 [0.0000, 0.0000] | 0.2043 [0.1760, 0.2331] |
| gray | Spatial Reasoning | 205 | 0.1317 [0.0878, 0.1806] | 0.3149 [0.2806, 0.3523] |
| gray | Tables/Diagrams/Charts | 650 | 0.0800 [0.0600, 0.1015] | 0.2714 [0.2542, 0.2900] |
| noise | (GradeSchool) Geometric | 1123 | 0.2538 [0.2289, 0.2796] | 0.5001 [0.4830, 0.5169] |
| noise | (GradeSchool) Non-Geo Math | 1574 | 0.2535 [0.2332, 0.2745] | 0.4523 [0.4383, 0.4668] |
| noise | (GradeSchool) Science | 365 | 0.1890 [0.1507, 0.2275] | 0.4321 [0.4018, 0.4631] |
| noise | Broader STEM Topics | 99 | 0.2222 [0.1414, 0.3030] | 0.4199 [0.3651, 0.4761] |
| noise | Commonsense | 12 | 0.0833 [0.0000, 0.2500] | 0.2114 [0.1579, 0.2989] |
| noise | Social Science | 68 | 0.0000 [0.0000, 0.0000] | 0.1961 [0.1685, 0.2246] |
| noise | Spatial Reasoning | 205 | 0.1415 [0.0927, 0.1902] | 0.3192 [0.2879, 0.3527] |
| noise | Tables/Diagrams/Charts | 650 | 0.1015 [0.0785, 0.1262] | 0.2880 [0.2715, 0.3066] |
| none | (GradeSchool) Geometric | 1123 | 0.1897 [0.1665, 0.2137] | 0.4796 [0.4624, 0.4975] |
| none | (GradeSchool) Non-Geo Math | 1574 | 0.1976 [0.1779, 0.2166] | 0.4625 [0.4480, 0.4774] |
| none | (GradeSchool) Science | 365 | 0.1726 [0.1342, 0.2137] | 0.4043 [0.3715, 0.4348] |
| none | Broader STEM Topics | 99 | 0.2121 [0.1313, 0.3030] | 0.4012 [0.3454, 0.4565] |
| none | Commonsense | 12 | 0.0000 [0.0000, 0.0000] | 0.1965 [0.1387, 0.2543] |
| none | Social Science | 68 | 0.0000 [0.0000, 0.0000] | 0.1693 [0.1523, 0.1897] |
| none | Spatial Reasoning | 205 | 0.0683 [0.0341, 0.1024] | 0.3078 [0.2732, 0.3440] |
| none | Tables/Diagrams/Charts | 650 | 0.0662 [0.0477, 0.0846] | 0.2609 [0.2448, 0.2769] |
| caption | (GradeSchool) Geometric | 1123 | 0.1906 [0.1665, 0.2137] | 0.4564 [0.4392, 0.4727] |
| caption | (GradeSchool) Non-Geo Math | 1574 | 0.2090 [0.1887, 0.2300] | 0.4767 [0.4622, 0.4916] |
| caption | (GradeSchool) Science | 365 | 0.1397 [0.1041, 0.1753] | 0.3483 [0.3205, 0.3747] |
| caption | Broader STEM Topics | 99 | 0.3939 [0.3030, 0.4949] | 0.5832 [0.5226, 0.6390] |
| caption | Commonsense | 12 | 0.0000 [0.0000, 0.0000] | 0.2114 [0.1387, 0.2989] |
| caption | Social Science | 68 | 0.0000 [0.0000, 0.0000] | 0.1745 [0.1523, 0.1986] |
| caption | Spatial Reasoning | 205 | 0.1024 [0.0634, 0.1463] | 0.3446 [0.3105, 0.3792] |
| caption | Tables/Diagrams/Charts | 650 | 0.1708 [0.1431, 0.2000] | 0.3860 [0.3641, 0.4071] |

Problems:
- Item-bootstrap intervals quantify sample uncertainty, not run-to-run RL variance.
- Question-blind captions measure caption-channel solvability; they are not claims about all possible captioners.

Decision:
- Retain these audited p_i and q_i values as corpus diagnostics. No gate decision is made here.

Next actions:
- Compare the ViRL39K pattern with filtered Geometry3K v2 and use discrepancies to scope corpus-specific sensitivity analyses.
