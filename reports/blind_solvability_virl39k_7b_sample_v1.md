# ViRL39K Blind-Solvability Sample V1

Status:
- Complete for the frozen 4,096-item stratified sample under all five conditions.
- Machine status JSON: `reports/blind_solvability_virl39k_7b_sample_v1_audited.json`.
- This is a base-model corpus audit, not a pilot-arm result or PI gate decision.

Evidence:
- Model revision: `Qwen/Qwen2.5-VL-7B-Instruct@cc594898137f460bfe9f0759e9844b3ce807cfb5`.
- Decoding: greedy plus n=16 at temperature 1.0, 2,048 maximum tokens, G=5.
- Symbolic grading: `posix-itimer-v1` at `5.0` seconds per bounded call.
- Frozen source SHA256: `ffbad6eaff57f6dd11f136b066e4d4206e43381281a3cb24cc677241c360e6d5`.
- Multi-image distribution: `{'1': 3856, '2': 137, '3': 43, '4': 39, '5': 19, '6': 1, '8': 1}`; maximum 8 images.

Overall results with item-bootstrap 95% CIs:
| Condition | Pilot greedy accuracy | Canonical greedy accuracy | Mean p_i | Mean q_i | Mean pilot reward | Format rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| real | 0.3579 [0.3435, 0.3726] | 0.3286 [0.3147, 0.3430] | 0.3058 [0.2971, 0.3143] | 0.5356 [0.5267, 0.5451] | 0.4201 [0.4140, 0.4263] | 0.5464 [0.5357, 0.5570] |
| gray | 0.2456 [0.2327, 0.2595] | 0.2268 [0.2134, 0.2395] | 0.2267 [0.2186, 0.2347] | 0.4424 [0.4329, 0.4514] | 0.3688 [0.3630, 0.3744] | 0.5280 [0.5170, 0.5389] |
| noise | 0.2483 [0.2351, 0.2617] | 0.2314 [0.2192, 0.2444] | 0.2259 [0.2177, 0.2339] | 0.4439 [0.4345, 0.4533] | 0.3764 [0.3711, 0.3820] | 0.5441 [0.5334, 0.5545] |
| none | 0.1824 [0.1702, 0.1939] | 0.1711 [0.1594, 0.1826] | 0.2109 [0.2027, 0.2190] | 0.4144 [0.4055, 0.4237] | 0.3243 [0.3188, 0.3299] | 0.4558 [0.4458, 0.4655] |
| caption | 0.1624 [0.1504, 0.1733] | 0.1536 [0.1423, 0.1650] | 0.2016 [0.1945, 0.2086] | 0.4458 [0.4367, 0.4553] | 0.4199 [0.4148, 0.4251] | 0.6567 [0.6482, 0.6656] |

Per-category pilot greedy accuracy and mean q_i:
| Condition | Category | n | Greedy accuracy | Mean q_i |
| --- | --- | ---: | ---: | ---: |
| real | (GradeSchool) Geometric | 1123 | 0.3749 [0.3464, 0.4025] | 0.5683 [0.5518, 0.5854] |
| real | (GradeSchool) Non-Geo Math | 1574 | 0.4206 [0.3977, 0.4447] | 0.5795 [0.5653, 0.5935] |
| real | (GradeSchool) Science | 365 | 0.1534 [0.1178, 0.1890] | 0.3393 [0.3117, 0.3676] |
| real | Broader STEM Topics | 99 | 0.5152 [0.4242, 0.6061] | 0.4806 [0.4154, 0.5448] |
| real | Commonsense | 12 | 0.0833 [0.0000, 0.2500] | 0.4981 [0.3364, 0.6642] |
| real | Social Science | 68 | 0.0147 [0.0000, 0.0441] | 0.1923 [0.1567, 0.2322] |
| real | Spatial Reasoning | 205 | 0.2585 [0.2000, 0.3171] | 0.4821 [0.4371, 0.5281] |
| real | Tables/Diagrams/Charts | 650 | 0.3400 [0.3031, 0.3769] | 0.5446 [0.5201, 0.5678] |
| gray | (GradeSchool) Geometric | 1123 | 0.3090 [0.2805, 0.3375] | 0.5392 [0.5224, 0.5558] |
| gray | (GradeSchool) Non-Geo Math | 1574 | 0.3183 [0.2961, 0.3424] | 0.4914 [0.4760, 0.5059] |
| gray | (GradeSchool) Science | 365 | 0.1616 [0.1260, 0.1973] | 0.3578 [0.3281, 0.3881] |
| gray | Broader STEM Topics | 99 | 0.3131 [0.2222, 0.4040] | 0.3725 [0.3145, 0.4335] |
| gray | Commonsense | 12 | 0.0000 [0.0000, 0.0000] | 0.2840 [0.1965, 0.3716] |
| gray | Social Science | 68 | 0.0147 [0.0000, 0.0441] | 0.1583 [0.1421, 0.1779] |
| gray | Spatial Reasoning | 205 | 0.1415 [0.0976, 0.1902] | 0.3359 [0.2972, 0.3743] |
| gray | Tables/Diagrams/Charts | 650 | 0.0585 [0.0415, 0.0769] | 0.2805 [0.2618, 0.3004] |
| noise | (GradeSchool) Geometric | 1123 | 0.3108 [0.2832, 0.3375] | 0.5253 [0.5082, 0.5421] |
| noise | (GradeSchool) Non-Geo Math | 1574 | 0.3208 [0.2980, 0.3425] | 0.4977 [0.4829, 0.5123] |
| noise | (GradeSchool) Science | 365 | 0.1178 [0.0849, 0.1507] | 0.3548 [0.3254, 0.3859] |
| noise | Broader STEM Topics | 99 | 0.3030 [0.2121, 0.3939] | 0.3678 [0.3120, 0.4245] |
| noise | Commonsense | 12 | 0.0000 [0.0000, 0.0000] | 0.2375 [0.1387, 0.3512] |
| noise | Social Science | 68 | 0.0000 [0.0000, 0.0000] | 0.1515 [0.1387, 0.1677] |
| noise | Spatial Reasoning | 205 | 0.1707 [0.1171, 0.2244] | 0.3540 [0.3160, 0.3920] |
| noise | Tables/Diagrams/Charts | 650 | 0.0846 [0.0646, 0.1062] | 0.2971 [0.2785, 0.3175] |
| none | (GradeSchool) Geometric | 1123 | 0.2315 [0.2075, 0.2565] | 0.5021 [0.4852, 0.5199] |
| none | (GradeSchool) Non-Geo Math | 1574 | 0.2344 [0.2128, 0.2554] | 0.4691 [0.4546, 0.4842] |
| none | (GradeSchool) Science | 365 | 0.1151 [0.0822, 0.1507] | 0.3351 [0.3075, 0.3637] |
| none | Broader STEM Topics | 99 | 0.2121 [0.1412, 0.2929] | 0.3662 [0.3078, 0.4245] |
| none | Commonsense | 12 | 0.0000 [0.0000, 0.0000] | 0.1579 [0.1387, 0.1965] |
| none | Social Science | 68 | 0.0000 [0.0000, 0.0000] | 0.1387 [0.1387, 0.1387] |
| none | Spatial Reasoning | 205 | 0.0878 [0.0537, 0.1268] | 0.3074 [0.2695, 0.3445] |
| none | Tables/Diagrams/Charts | 650 | 0.0569 [0.0400, 0.0754] | 0.2493 [0.2333, 0.2660] |
| caption | (GradeSchool) Geometric | 1123 | 0.1371 [0.1175, 0.1576] | 0.4778 [0.4598, 0.4946] |
| caption | (GradeSchool) Non-Geo Math | 1574 | 0.2014 [0.1823, 0.2205] | 0.5122 [0.4971, 0.5264] |
| caption | (GradeSchool) Science | 365 | 0.0822 [0.0548, 0.1123] | 0.2832 [0.2594, 0.3079] |
| caption | Broader STEM Topics | 99 | 0.4242 [0.3333, 0.5253] | 0.5079 [0.4435, 0.5712] |
| caption | Commonsense | 12 | 0.0000 [0.0000, 0.0000] | 0.2182 [0.1387, 0.3320] |
| caption | Social Science | 68 | 0.0147 [0.0000, 0.0441] | 0.1708 [0.1455, 0.2020] |
| caption | Spatial Reasoning | 205 | 0.0927 [0.0585, 0.1366] | 0.3534 [0.3161, 0.3938] |
| caption | Tables/Diagrams/Charts | 650 | 0.1569 [0.1277, 0.1862] | 0.3740 [0.3531, 0.3947] |

Problems:
- Item-bootstrap intervals quantify sample uncertainty, not run-to-run RL variance.
- Question-blind captions measure caption-channel solvability; they are not claims about all possible captioners.

Decision:
- Retain these audited p_i and q_i values as corpus diagnostics. No gate decision is made here.

Next actions:
- Compare the ViRL39K pattern with filtered Geometry3K v2 and use discrepancies to scope corpus-specific sensitivity analyses.
