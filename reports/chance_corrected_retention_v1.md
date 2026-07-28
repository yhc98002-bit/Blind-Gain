# Null-corrected blind retention — external benchmarks (v1)

Generated: `2026-07-28T13:00:34Z`  ·  machine-readable twin: `reports/chance_corrected_retention_v1.json`  ·  generator: `scripts/chance_corrected_retention_v1.py`

## Definitions

- `corrected retention = (mean(blind) - mean(null)) / (mean(with_image) - mean(null))`
- `naive retention = mean(blind) / mean(with_image)`
- Null rule (closed form, no empirical null): multiple-choice item -> `1/k` using that item's own presented option count `k`; free-form item -> `0`; multiple-choice item whose gold label is absent from the presented option labels -> `0`.
- Subset null = mean of the per-item nulls in that subset; recomputed inside every bootstrap replicate.
- CI: item-level paired bootstrap, 10000 replicates, seed 20260728, percentile 2.5/97.5. The ratio of differences is recomputed on each replicate.
- Two scoring contracts are carried throughout: lenient = `Acc_final`, contract-strict = `Acc_strict`.
- `den<=0` column: `true` when the corrected-retention denominator `mean(with_image) - null` is non-positive in the point estimate or changes sign across bootstrap replicates. Ratios in those rows are not on a 0-1 scale.

## 1. Headline rows — naive vs corrected (lenient `Acc_final`)

| Model | Benchmark | Subset | n | with-image | blind | null | naive ret. | corrected ret. | corrected 95% CI | den<=0 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| Qwen2.5-VL-3B | MMStar | all items (MC pooled, item-level null) | 1500 | 0.5540 | 0.2607 | 0.2688 | 0.4705 | -0.0286 | [-0.1084, 0.0486] | no |
| Qwen2.5-VL-7B | MMStar | all items (MC pooled, item-level null) | 1500 | 0.6320 | 0.2880 | 0.2688 | 0.4557 | 0.0528 | [-0.0098, 0.1166] | no |
| Qwen2.5-VL-3B | MathVista-testmini | MC pooled (item-level null) | 539 | 0.7254 | 0.5121 | 0.3316 | 0.7059 | 0.4582 | [0.3506, 0.5636] | no |
| Qwen2.5-VL-3B | MathVista-testmini | free-form | 460 | 0.5043 | 0.1152 | 0.0000 | 0.2284 | 0.2284 | [0.1736, 0.2870] | no |
| Qwen2.5-VL-7B | MathVista-testmini | MC pooled (item-level null) | 539 | 0.7607 | 0.5306 | 0.3316 | 0.6976 | 0.4638 | [0.3675, 0.5614] | no |
| Qwen2.5-VL-7B | MathVista-testmini | free-form | 460 | 0.5478 | 0.1152 | 0.0000 | 0.2103 | 0.2103 | [0.1595, 0.2646] | no |
| Gemma-3 | ViRL39K sample, blind=none | MC pooled, k determinable (item-level null) | 1215 | 0.1350 | 0.0856 | 0.2680 | 0.6341 | 1.3713 | [1.2178, 1.5736] | yes |
| Gemma-3 | ViRL39K sample, blind=none | free-form pooled (numeric+text_or_expression) | 2789 | 0.4295 | 0.3123 | 0.0000 | 0.7270 | 0.7270 | [0.6898, 0.7646] | no |
| InternVL3-9B | ViRL39K sample, blind=none | MC pooled, k determinable (item-level null) | 1215 | 0.2938 | 0.2049 | 0.2680 | 0.6975 | -2.4395 | [-17.9606, 6.5052] | yes |
| InternVL3-9B | ViRL39K sample, blind=none | free-form pooled (numeric+text_or_expression) | 2789 | 0.2686 | 0.1302 | 0.0000 | 0.4846 | 0.4846 | [0.4385, 0.5326] | no |

## 2. All subsets — lenient contract (`Acc_final`)

| Model | Benchmark | Subset | format | k | n | with-image | with-image 95% CI | blind | blind 95% CI | null | naive ret. | naive 95% CI | corrected ret. | corrected 95% CI | den<=0 | boot den<=0 frac |
| --- | --- | --- | --- | :---: | ---: | ---: | :---: | ---: | :---: | ---: | ---: | :---: | ---: | :---: | :---: | ---: |
| Qwen2.5-VL-3B | MMStar | MC k=2 | multiple_choice | 2 | 85 | 0.8235 | [0.7412, 0.8941] | 0.4471 | [0.3412, 0.5529] | 0.5000 | 0.5429 | [0.4079, 0.6875] | -0.1636 | [-0.5294, 0.1636] | no | 0.000 |
| Qwen2.5-VL-3B | MMStar | MC k=3 | multiple_choice | 3 | 90 | 0.5556 | [0.4556, 0.6556] | 0.3222 | [0.2333, 0.4222] | 0.3333 | 0.5800 | [0.3962, 0.8140] | -0.0500 | [-0.5455, 0.4444] | no | 0.000 |
| Qwen2.5-VL-3B | MMStar | MC k=4 | multiple_choice | 4 | 1323 | 0.5374 | [0.5110, 0.5639] | 0.2449 | [0.2215, 0.2683] | 0.2500 | 0.4557 | [0.4122, 0.5007] | -0.0178 | [-0.1006, 0.0646] | no | 0.000 |
| Qwen2.5-VL-3B | MMStar | MC gold-label absent from presented options | multiple_choice | n/a | 2 | 0.0000 | [0.0000, 0.0000] | 0.0000 | [0.0000, 0.0000] | 0.0000 | n/a | n/a | n/a | n/a | yes | 1.000 |
| Qwen2.5-VL-3B | MMStar | all items (MC pooled, item-level null) | multiple_choice | mixed(2,3,4) | 1500 | 0.5540 | [0.5293, 0.5787] | 0.2607 | [0.2387, 0.2833] | 0.2688 | 0.4705 | [0.4301, 0.5125] | -0.0286 | [-0.1084, 0.0486] | no | 0.000 |
| Qwen2.5-VL-7B | MMStar | MC k=2 | multiple_choice | 2 | 85 | 0.9059 | [0.8353, 0.9647] | 0.4118 | [0.3059, 0.5176] | 0.5000 | 0.4545 | [0.3377, 0.5753] | -0.2174 | [-0.4805, 0.0435] | no | 0.000 |
| Qwen2.5-VL-7B | MMStar | MC k=3 | multiple_choice | 3 | 90 | 0.6667 | [0.5667, 0.7667] | 0.3556 | [0.2556, 0.4556] | 0.3333 | 0.5333 | [0.3731, 0.7308] | 0.0667 | [-0.2333, 0.4074] | no | 0.000 |
| Qwen2.5-VL-7B | MMStar | MC k=4 | multiple_choice | 4 | 1323 | 0.6130 | [0.5858, 0.6387] | 0.2759 | [0.2517, 0.3001] | 0.2500 | 0.4501 | [0.4096, 0.4932] | 0.0713 | [0.0044, 0.1380] | no | 0.000 |
| Qwen2.5-VL-7B | MMStar | MC gold-label absent from presented options | multiple_choice | n/a | 2 | 0.0000 | [0.0000, 0.0000] | 0.0000 | [0.0000, 0.0000] | 0.0000 | n/a | n/a | n/a | n/a | yes | 1.000 |
| Qwen2.5-VL-7B | MMStar | all items (MC pooled, item-level null) | multiple_choice | mixed(2,3,4) | 1500 | 0.6320 | [0.6073, 0.6567] | 0.2880 | [0.2653, 0.3113] | 0.2688 | 0.4557 | [0.4184, 0.4952] | 0.0528 | [-0.0098, 0.1166] | no | 0.000 |
| Qwen2.5-VL-3B | MathVista-testmini | MC k=2 | multiple_choice | 2 | 185 | 0.8757 | [0.8270, 0.9189] | 0.5351 | [0.4649, 0.6054] | 0.5000 | 0.6111 | [0.5210, 0.7078] | 0.0935 | [-0.0963, 0.2925] | no | 0.000 |
| Qwen2.5-VL-3B | MathVista-testmini | MC k=3 | multiple_choice | 3 | 18 | 0.6667 | [0.4444, 0.8889] | 0.5000 | [0.2778, 0.7222] | 0.3333 | 0.7500 | [0.4375, 1.1111] | 0.5000 | [-0.3333, 1.3333] | yes | 0.001 |
| Qwen2.5-VL-3B | MathVista-testmini | MC k=4 | multiple_choice | 4 | 272 | 0.6728 | [0.6140, 0.7279] | 0.5551 | [0.4963, 0.6140] | 0.2500 | 0.8251 | [0.7460, 0.9064] | 0.7217 | [0.5981, 0.8487] | no | 0.000 |
| Qwen2.5-VL-3B | MathVista-testmini | MC k=5 | multiple_choice | 5 | 51 | 0.5490 | [0.4118, 0.6863] | 0.2549 | [0.1373, 0.3725] | 0.2000 | 0.4643 | [0.2571, 0.7241] | 0.1573 | [-0.2025, 0.5270] | no | 0.000 |
| Qwen2.5-VL-3B | MathVista-testmini | MC k=6 | multiple_choice | 6 | 9 | 0.4444 | [0.1111, 0.7778] | 0.1111 | [0.0000, 0.3333] | 0.1667 | 0.2500 | [0.0000, 1.5000] | -0.2000 | [-3.0000, 1.6667] | yes | 0.043 |
| Qwen2.5-VL-3B | MathVista-testmini | MC k=7 | multiple_choice | 7 | 3 | 0.6667 | [0.0000, 1.0000] | 1.0000 | [1.0000, 1.0000] | 0.1429 | 1.5000 | [1.0000, 3.0000] | 1.6364 | [-6.0000, 4.5000] | yes | 0.038 |
| Qwen2.5-VL-3B | MathVista-testmini | MC k=8 | multiple_choice | 8 | 1 | 0.0000 | [0.0000, 0.0000] | 0.0000 | [0.0000, 0.0000] | 0.1250 | n/a | n/a | 1.0000 | [1.0000, 1.0000] | yes | 1.000 |
| Qwen2.5-VL-3B | MathVista-testmini | MC pooled (item-level null) | multiple_choice | mixed(2-8) | 539 | 0.7254 | [0.6865, 0.7625] | 0.5121 | [0.4694, 0.5529] | 0.3316 | 0.7059 | [0.6463, 0.7655] | 0.4582 | [0.3506, 0.5636] | no | 0.000 |
| Qwen2.5-VL-3B | MathVista-testmini | free-form | free_form_numeric | n/a | 460 | 0.5043 | [0.4587, 0.5500] | 0.1152 | [0.0870, 0.1457] | 0.0000 | 0.2284 | [0.1736, 0.2870] | 0.2284 | [0.1736, 0.2870] | no | 0.000 |
| Qwen2.5-VL-7B | MathVista-testmini | MC k=2 | multiple_choice | 2 | 185 | 0.8865 | [0.8378, 0.9297] | 0.4757 | [0.4054, 0.5459] | 0.5000 | 0.5366 | [0.4551, 0.6220] | -0.0629 | [-0.2483, 0.1240] | no | 0.000 |
| Qwen2.5-VL-7B | MathVista-testmini | MC k=3 | multiple_choice | 3 | 18 | 0.7778 | [0.5556, 0.9444] | 0.5000 | [0.2778, 0.7222] | 0.3333 | 0.6429 | [0.3333, 1.0000] | 0.3750 | [-0.1429, 1.0000] | yes | 0.000 |
| Qwen2.5-VL-7B | MathVista-testmini | MC k=4 | multiple_choice | 4 | 272 | 0.7279 | [0.6765, 0.7794] | 0.6103 | [0.5515, 0.6691] | 0.2500 | 0.8384 | [0.7700, 0.9058] | 0.7538 | [0.6508, 0.8540] | no | 0.000 |
| Qwen2.5-VL-7B | MathVista-testmini | MC k=5 | multiple_choice | 5 | 51 | 0.5490 | [0.4118, 0.6863] | 0.3922 | [0.2549, 0.5294] | 0.2000 | 0.7143 | [0.5000, 1.0000] | 0.5506 | [0.2021, 1.0000] | no | 0.000 |
| Qwen2.5-VL-7B | MathVista-testmini | MC k=6 | multiple_choice | 6 | 9 | 0.5556 | [0.2222, 0.8889] | 0.1111 | [0.0000, 0.3333] | 0.1667 | 0.2000 | [0.0000, 0.6667] | -0.1429 | [-3.0000, 0.4286] | yes | 0.007 |
| Qwen2.5-VL-7B | MathVista-testmini | MC k=7 | multiple_choice | 7 | 3 | 0.3333 | [0.0000, 1.0000] | 0.6667 | [0.0000, 1.0000] | 0.1429 | 2.0000 | [0.0000, 2.0000] | 2.7500 | [-6.0000, 2.7500] | yes | 0.296 |
| Qwen2.5-VL-7B | MathVista-testmini | MC k=8 | multiple_choice | 8 | 1 | 0.0000 | [0.0000, 0.0000] | 0.0000 | [0.0000, 0.0000] | 0.1250 | n/a | n/a | 1.0000 | [1.0000, 1.0000] | yes | 1.000 |
| Qwen2.5-VL-7B | MathVista-testmini | MC pooled (item-level null) | multiple_choice | mixed(2-8) | 539 | 0.7607 | [0.7236, 0.7959] | 0.5306 | [0.4879, 0.5733] | 0.3316 | 0.6976 | [0.6434, 0.7531] | 0.4638 | [0.3675, 0.5614] | no | 0.000 |
| Qwen2.5-VL-7B | MathVista-testmini | free-form | free_form_numeric | n/a | 460 | 0.5478 | [0.5022, 0.5913] | 0.1152 | [0.0870, 0.1435] | 0.0000 | 0.2103 | [0.1595, 0.2646] | 0.2103 | [0.1595, 0.2646] | no | 0.000 |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=none] | MC k=2 | multiple_choice | 2 | 75 | 0.0000 | [0.0000, 0.0000] | 0.0000 | [0.0000, 0.0000] | 0.5000 | n/a | n/a | 1.0000 | [1.0000, 1.0000] | yes | 1.000 |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=none] | MC k=3 | multiple_choice | 3 | 72 | 0.0278 | [0.0000, 0.0694] | 0.0000 | [0.0000, 0.0000] | 0.3333 | 0.0000 | [0.0000, 0.0000] | 1.0909 | [1.0000, 1.2632] | yes | 1.000 |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=none] | MC k=4 | multiple_choice | 4 | 1010 | 0.1574 | [0.1347, 0.1802] | 0.1010 | [0.0832, 0.1198] | 0.2500 | 0.6415 | [0.5399, 0.7568] | 1.6096 | [1.3318, 2.0511] | yes | 1.000 |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=none] | MC k=5 | multiple_choice | 5 | 58 | 0.0517 | [0.0000, 0.1207] | 0.0345 | [0.0000, 0.0862] | 0.2000 | 0.6667 | [0.0000, 2.5000] | 1.1163 | [0.7674, 1.8696] | yes | 1.000 |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=none] | MC pooled, k determinable (item-level null) | multiple_choice | mixed(2-5) | 1215 | 0.1350 | [0.1160, 0.1547] | 0.0856 | [0.0700, 0.1012] | 0.2680 | 0.6341 | [0.5330, 0.7440] | 1.3713 | [1.2178, 1.5736] | yes | 1.000 |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=none] | free-form numeric | free_form_numeric | n/a | 1982 | 0.5030 | [0.4813, 0.5252] | 0.3567 | [0.3365, 0.3779] | 0.0000 | 0.7091 | [0.6703, 0.7505] | 0.7091 | [0.6703, 0.7505] | no | 0.000 |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=none] | free-form text_or_expression | free_form_text_or_expression | n/a | 807 | 0.2491 | [0.2193, 0.2788] | 0.2032 | [0.1760, 0.2305] | 0.0000 | 0.8159 | [0.7204, 0.9185] | 0.8159 | [0.7204, 0.9185] | no | 0.000 |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=none] | free-form pooled (numeric+text_or_expression) | free_form | n/a | 2789 | 0.4295 | [0.4109, 0.4478] | 0.3123 | [0.2954, 0.3295] | 0.0000 | 0.7270 | [0.6898, 0.7646] | 0.7270 | [0.6898, 0.7646] | no | 0.000 |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=caption] | MC k=2 | multiple_choice | 2 | 75 | 0.0000 | [0.0000, 0.0000] | 0.0400 | [0.0000, 0.0933] | 0.5000 | n/a | n/a | 0.9200 | [0.8133, 1.0000] | yes | 1.000 |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=caption] | MC k=3 | multiple_choice | 3 | 72 | 0.0278 | [0.0000, 0.0694] | 0.0278 | [0.0000, 0.0694] | 0.3333 | 1.0000 | [0.0000, 4.0000] | 1.0000 | [0.8332, 1.2105] | yes | 1.000 |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=caption] | MC k=4 | multiple_choice | 4 | 1010 | 0.1574 | [0.1347, 0.1802] | 0.1297 | [0.1099, 0.1515] | 0.2500 | 0.8239 | [0.7143, 0.9467] | 1.2995 | [1.0749, 1.6207] | yes | 1.000 |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=caption] | MC k=5 | multiple_choice | 5 | 58 | 0.0517 | [0.0000, 0.1207] | 0.0345 | [0.0000, 0.0862] | 0.2000 | 0.6667 | [0.0000, 2.7250] | 1.1163 | [0.7674, 1.8696] | yes | 1.000 |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=caption] | MC pooled, k determinable (item-level null) | multiple_choice | mixed(2-5) | 1215 | 0.1350 | [0.1160, 0.1539] | 0.1136 | [0.0963, 0.1317] | 0.2680 | 0.8415 | [0.7301, 0.9677] | 1.1609 | [1.0276, 1.3213] | yes | 1.000 |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=caption] | free-form numeric | free_form_numeric | n/a | 1982 | 0.5030 | [0.4808, 0.5252] | 0.4768 | [0.4546, 0.4990] | 0.0000 | 0.9478 | [0.9059, 0.9927] | 0.9478 | [0.9059, 0.9927] | no | 0.000 |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=caption] | free-form text_or_expression | free_form_text_or_expression | n/a | 807 | 0.2491 | [0.2193, 0.2788] | 0.1995 | [0.1722, 0.2280] | 0.0000 | 0.8010 | [0.7027, 0.9081] | 0.8010 | [0.7027, 0.9081] | no | 0.000 |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=caption] | free-form pooled (numeric+text_or_expression) | free_form | n/a | 2789 | 0.4295 | [0.4116, 0.4478] | 0.3966 | [0.3783, 0.4148] | 0.0000 | 0.9232 | [0.8848, 0.9639] | 0.9232 | [0.8848, 0.9639] | no | 0.000 |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=none] | MC k=2 | multiple_choice | 2 | 75 | 0.0133 | [0.0000, 0.0400] | 0.0000 | [0.0000, 0.0000] | 0.5000 | 0.0000 | [0.0000, 0.0000] | 1.0274 | [1.0000, 1.0870] | yes | 1.000 |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=none] | MC k=3 | multiple_choice | 3 | 72 | 0.2500 | [0.1528, 0.3472] | 0.0000 | [0.0000, 0.0000] | 0.3333 | 0.0000 | [0.0000, 0.0000] | 4.0000 | [-12.0000, 24.0000] | yes | 0.959 |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=none] | MC k=4 | multiple_choice | 4 | 1010 | 0.3277 | [0.2990, 0.3574] | 0.2465 | [0.2198, 0.2733] | 0.2500 | 0.7523 | [0.6695, 0.8411] | -0.0446 | [-0.4831, 0.2774] | no | 0.000 |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=none] | MC k=5 | multiple_choice | 5 | 58 | 0.1207 | [0.0345, 0.2069] | 0.0000 | [0.0000, 0.0000] | 0.2000 | 0.0000 | [0.0000, 0.0000] | 2.5217 | [-8.2857, 19.3333] | yes | 0.964 |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=none] | MC pooled, k determinable (item-level null) | multiple_choice | mixed(2-5) | 1215 | 0.2938 | [0.2683, 0.3202] | 0.2049 | [0.1819, 0.2280] | 0.2680 | 0.6975 | [0.6190, 0.7816] | -2.4395 | [-17.9606, 6.5052] | yes | 0.028 |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=none] | free-form numeric | free_form_numeric | n/a | 1982 | 0.3290 | [0.3083, 0.3496] | 0.1544 | [0.1387, 0.1705] | 0.0000 | 0.4693 | [0.4211, 0.5230] | 0.4693 | [0.4211, 0.5230] | no | 0.000 |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=none] | free-form text_or_expression | free_form_text_or_expression | n/a | 807 | 0.1202 | [0.0979, 0.1437] | 0.0706 | [0.0533, 0.0892] | 0.0000 | 0.5876 | [0.4495, 0.7447] | 0.5876 | [0.4495, 0.7447] | no | 0.000 |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=none] | free-form pooled (numeric+text_or_expression) | free_form | n/a | 2789 | 0.2686 | [0.2517, 0.2850] | 0.1302 | [0.1180, 0.1427] | 0.0000 | 0.4846 | [0.4385, 0.5326] | 0.4846 | [0.4385, 0.5326] | no | 0.000 |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=caption] | MC k=2 | multiple_choice | 2 | 75 | 0.0133 | [0.0000, 0.0400] | 0.0000 | [0.0000, 0.0000] | 0.5000 | 0.0000 | [0.0000, 0.0000] | 1.0274 | [1.0000, 1.0870] | yes | 1.000 |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=caption] | MC k=3 | multiple_choice | 3 | 72 | 0.2500 | [0.1528, 0.3472] | 0.0556 | [0.0139, 0.1111] | 0.3333 | 0.2222 | [0.0500, 0.4667] | 3.3333 | [-9.0000, 19.0000] | yes | 0.957 |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=caption] | MC k=4 | multiple_choice | 4 | 1010 | 0.3277 | [0.2990, 0.3564] | 0.2079 | [0.1832, 0.2337] | 0.2500 | 0.6344 | [0.5586, 0.7151] | -0.5414 | [-1.1460, -0.1855] | no | 0.000 |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=caption] | MC k=5 | multiple_choice | 5 | 58 | 0.1207 | [0.0517, 0.2069] | 0.0172 | [0.0000, 0.0517] | 0.2000 | 0.1429 | [0.0000, 0.7143] | 2.3043 | [-8.2857, 17.6667] | yes | 0.959 |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=caption] | MC pooled, k determinable (item-level null) | multiple_choice | mixed(2-5) | 1215 | 0.2938 | [0.2675, 0.3193] | 0.1770 | [0.1556, 0.1984] | 0.2680 | 0.6022 | [0.5301, 0.6775] | -3.5223 | [-25.9110, 8.8777] | yes | 0.028 |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=caption] | free-form numeric | free_form_numeric | n/a | 1982 | 0.3290 | [0.3083, 0.3496] | 0.2417 | [0.2230, 0.2603] | 0.0000 | 0.7347 | [0.6763, 0.7970] | 0.7347 | [0.6763, 0.7970] | no | 0.000 |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=caption] | free-form text_or_expression | free_form_text_or_expression | n/a | 807 | 0.1202 | [0.0979, 0.1437] | 0.1016 | [0.0818, 0.1227] | 0.0000 | 0.8454 | [0.6735, 1.0556] | 0.8454 | [0.6735, 1.0556] | no | 0.000 |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=caption] | free-form pooled (numeric+text_or_expression) | free_form | n/a | 2789 | 0.2686 | [0.2521, 0.2850] | 0.2011 | [0.1864, 0.2162] | 0.0000 | 0.7490 | [0.6929, 0.8112] | 0.7490 | [0.6929, 0.8112] | no | 0.000 |

## 3. All subsets — contract-strict (`Acc_strict`)

Same items, same nulls; `Acc_strict` additionally requires the `<answer>` wrapper.

| Model | Benchmark | Subset | n | null | with-image | blind | naive ret. | corrected ret. | corrected 95% CI | den<=0 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| Qwen2.5-VL-3B | MMStar | MC k=2 | 85 | 0.5000 | 0.0000 | 0.0000 | n/a | 1.0000 | [1.0000, 1.0000] | yes |
| Qwen2.5-VL-3B | MMStar | MC k=3 | 90 | 0.3333 | 0.0000 | 0.0111 | n/a | 0.9667 | [0.9000, 1.0000] | yes |
| Qwen2.5-VL-3B | MMStar | MC k=4 | 1323 | 0.2500 | 0.0015 | 0.0166 | 11.0000 | 0.9392 | [0.9093, 0.9664] | yes |
| Qwen2.5-VL-3B | MMStar | MC gold-label absent from presented options | 2 | 0.0000 | 0.0000 | 0.0000 | n/a | n/a | n/a | yes |
| Qwen2.5-VL-3B | MMStar | all items (MC pooled, item-level null) | 1500 | 0.2688 | 0.0013 | 0.0153 | 11.5000 | 0.9477 | [0.9225, 0.9701] | yes |
| Qwen2.5-VL-7B | MMStar | MC k=2 | 85 | 0.5000 | 0.0471 | 0.3882 | 8.2500 | 0.2468 | [0.0137, 0.4568] | yes |
| Qwen2.5-VL-7B | MMStar | MC k=3 | 90 | 0.3333 | 0.0000 | 0.2333 | n/a | 0.3000 | [0.0333, 0.5667] | yes |
| Qwen2.5-VL-7B | MMStar | MC k=4 | 1323 | 0.2500 | 0.0302 | 0.2018 | 6.6750 | 0.2193 | [0.1197, 0.3154] | yes |
| Qwen2.5-VL-7B | MMStar | MC gold-label absent from presented options | 2 | 0.0000 | 0.0000 | 0.0000 | n/a | n/a | n/a | yes |
| Qwen2.5-VL-7B | MMStar | all items (MC pooled, item-level null) | 1500 | 0.2688 | 0.0293 | 0.2140 | 7.2955 | 0.2289 | [0.1444, 0.3131] | yes |
| Qwen2.5-VL-3B | MathVista-testmini | MC k=2 | 185 | 0.5000 | 0.0000 | 0.0000 | n/a | 1.0000 | [1.0000, 1.0000] | yes |
| Qwen2.5-VL-3B | MathVista-testmini | MC k=3 | 18 | 0.3333 | 0.0000 | 0.0000 | n/a | 1.0000 | [1.0000, 1.0000] | yes |
| Qwen2.5-VL-3B | MathVista-testmini | MC k=4 | 272 | 0.2500 | 0.2022 | 0.2978 | 1.4727 | -1.0000 | [-7.6667, 0.5821] | yes |
| Qwen2.5-VL-3B | MathVista-testmini | MC k=5 | 51 | 0.2000 | 0.0784 | 0.1373 | 1.7500 | 0.5161 | [-0.3889, 1.4839] | yes |
| Qwen2.5-VL-3B | MathVista-testmini | MC k=6 | 9 | 0.1667 | 0.0000 | 0.1111 | n/a | 0.3333 | [-1.0000, 1.0000] | yes |
| Qwen2.5-VL-3B | MathVista-testmini | MC k=7 | 3 | 0.1429 | 0.0000 | 1.0000 | n/a | -6.0000 | [-6.0000, -6.0000] | yes |
| Qwen2.5-VL-3B | MathVista-testmini | MC k=8 | 1 | 0.1250 | 0.0000 | 0.0000 | n/a | 1.0000 | [1.0000, 1.0000] | yes |
| Qwen2.5-VL-3B | MathVista-testmini | MC pooled (item-level null) | 539 | 0.3316 | 0.1095 | 0.1707 | 1.5593 | 0.7244 | [0.5904, 0.8552] | yes |
| Qwen2.5-VL-3B | MathVista-testmini | free-form | 460 | 0.0000 | 0.2348 | 0.1022 | 0.4352 | 0.4352 | [0.3136, 0.5776] | no |
| Qwen2.5-VL-7B | MathVista-testmini | MC k=2 | 185 | 0.5000 | 0.1189 | 0.0000 | 0.0000 | 1.3121 | [1.1783, 1.5041] | yes |
| Qwen2.5-VL-7B | MathVista-testmini | MC k=3 | 18 | 0.3333 | 0.1667 | 0.0000 | 0.0000 | 2.0000 | [-6004799503160660.0000, 6.0000] | yes |
| Qwen2.5-VL-7B | MathVista-testmini | MC k=4 | 272 | 0.2500 | 0.4449 | 0.3529 | 0.7934 | 0.5283 | [0.2941, 0.7500] | no |
| Qwen2.5-VL-7B | MathVista-testmini | MC k=5 | 51 | 0.2000 | 0.0392 | 0.0588 | 1.5000 | 0.8780 | [0.4118, 1.6452] | yes |
| Qwen2.5-VL-7B | MathVista-testmini | MC k=6 | 9 | 0.1667 | 0.0000 | 0.0000 | n/a | 1.0000 | [1.0000, 1.0000] | yes |
| Qwen2.5-VL-7B | MathVista-testmini | MC k=7 | 3 | 0.1429 | 0.0000 | 0.3333 | n/a | -1.3333 | [-6.0000, 1.0000] | yes |
| Qwen2.5-VL-7B | MathVista-testmini | MC k=8 | 1 | 0.1250 | 0.0000 | 0.0000 | n/a | 1.0000 | [1.0000, 1.0000] | yes |
| Qwen2.5-VL-7B | MathVista-testmini | MC pooled (item-level null) | 539 | 0.3316 | 0.2746 | 0.1855 | 0.6757 | 2.5608 | [1.6487, 7.2170] | yes |
| Qwen2.5-VL-7B | MathVista-testmini | free-form | 460 | 0.0000 | 0.3804 | 0.0717 | 0.1886 | 0.1886 | [0.1278, 0.2611] | no |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=none] | MC k=2 | 75 | 0.5000 | 0.0000 | 0.0000 | n/a | 1.0000 | [1.0000, 1.0000] | yes |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=none] | MC k=3 | 72 | 0.3333 | 0.0000 | 0.0000 | n/a | 1.0000 | [1.0000, 1.0000] | yes |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=none] | MC k=4 | 1010 | 0.2500 | 0.0000 | 0.0000 | n/a | 1.0000 | [1.0000, 1.0000] | yes |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=none] | MC k=5 | 58 | 0.2000 | 0.0000 | 0.0000 | n/a | 1.0000 | [1.0000, 1.0000] | yes |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=none] | MC pooled, k determinable (item-level null) | 1215 | 0.2680 | 0.0000 | 0.0000 | n/a | 1.0000 | [1.0000, 1.0000] | yes |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=none] | free-form numeric | 1982 | 0.0000 | 0.0000 | 0.0000 | n/a | n/a | n/a | yes |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=none] | free-form text_or_expression | 807 | 0.0000 | 0.0000 | 0.0000 | n/a | n/a | n/a | yes |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=none] | free-form pooled (numeric+text_or_expression) | 2789 | 0.0000 | 0.0000 | 0.0000 | n/a | n/a | n/a | yes |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=caption] | MC k=2 | 75 | 0.5000 | 0.0000 | 0.0000 | n/a | 1.0000 | [1.0000, 1.0000] | yes |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=caption] | MC k=3 | 72 | 0.3333 | 0.0000 | 0.0000 | n/a | 1.0000 | [1.0000, 1.0000] | yes |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=caption] | MC k=4 | 1010 | 0.2500 | 0.0000 | 0.0000 | n/a | 1.0000 | [1.0000, 1.0000] | yes |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=caption] | MC k=5 | 58 | 0.2000 | 0.0000 | 0.0000 | n/a | 1.0000 | [1.0000, 1.0000] | yes |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=caption] | MC pooled, k determinable (item-level null) | 1215 | 0.2680 | 0.0000 | 0.0000 | n/a | 1.0000 | [1.0000, 1.0000] | yes |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=caption] | free-form numeric | 1982 | 0.0000 | 0.0000 | 0.0000 | n/a | n/a | n/a | yes |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=caption] | free-form text_or_expression | 807 | 0.0000 | 0.0000 | 0.0000 | n/a | n/a | n/a | yes |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=caption] | free-form pooled (numeric+text_or_expression) | 2789 | 0.0000 | 0.0000 | 0.0000 | n/a | n/a | n/a | yes |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=none] | MC k=2 | 75 | 0.5000 | 0.0133 | 0.0000 | 0.0000 | 1.0274 | [1.0000, 1.0870] | yes |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=none] | MC k=3 | 72 | 0.3333 | 0.2500 | 0.0000 | 0.0000 | 4.0000 | [-12.0000, 24.0000] | yes |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=none] | MC k=4 | 1010 | 0.2500 | 0.3257 | 0.2208 | 0.6778 | -0.3856 | [-0.9496, -0.0414] | no |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=none] | MC k=5 | 58 | 0.2000 | 0.1207 | 0.0000 | 0.0000 | 2.5217 | [-8.2857, 19.3333] | yes |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=none] | MC pooled, k determinable (item-level null) | 1215 | 0.2680 | 0.2922 | 0.1835 | 0.6282 | -3.4898 | [-25.5357, 14.1362] | yes |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=none] | free-form numeric | 1982 | 0.0000 | 0.3285 | 0.1483 | 0.4516 | 0.4516 | [0.4026, 0.5016] | no |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=none] | free-form text_or_expression | 807 | 0.0000 | 0.1177 | 0.0644 | 0.5474 | 0.5474 | [0.4124, 0.7041] | no |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=none] | free-form pooled (numeric+text_or_expression) | 2789 | 0.0000 | 0.2675 | 0.1241 | 0.4638 | 0.4638 | [0.4184, 0.5127] | no |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=caption] | MC k=2 | 75 | 0.5000 | 0.0133 | 0.0000 | 0.0000 | 1.0274 | [1.0000, 1.0870] | yes |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=caption] | MC k=3 | 72 | 0.3333 | 0.2500 | 0.0556 | 0.2222 | 3.3333 | [-9.5000, 19.0000] | yes |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=caption] | MC k=4 | 1010 | 0.2500 | 0.3257 | 0.1871 | 0.5745 | -0.8301 | [-1.6263, -0.4213] | no |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=caption] | MC k=5 | 58 | 0.2000 | 0.1207 | 0.0000 | 0.0000 | 2.5217 | [-8.2857, 19.3333] | yes |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=caption] | MC pooled, k determinable (item-level null) | 1215 | 0.2680 | 0.2922 | 0.1588 | 0.5437 | -4.5102 | [-32.9370, 19.6956] | yes |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=caption] | free-form numeric | 1982 | 0.0000 | 0.3285 | 0.2366 | 0.7204 | 0.7204 | [0.6608, 0.7831] | no |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=caption] | free-form text_or_expression | 807 | 0.0000 | 0.1177 | 0.0954 | 0.8105 | 0.8105 | [0.6355, 1.0263] | no |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=caption] | free-form pooled (numeric+text_or_expression) | 2789 | 0.0000 | 0.2675 | 0.1958 | 0.7319 | 0.7319 | [0.6770, 0.7922] | no |

## 4. Whole-benchmark naive retention (reference; reproduces the currently published figures)

No corrected value is given at this level for mixed benchmarks.

| Model | Benchmark | n | with-image `Acc_final` | blind `Acc_final` | naive ret. (lenient) | naive 95% CI | with-image `Acc_strict` | blind `Acc_strict` | naive ret. (strict) | naive strict 95% CI |
| --- | --- | ---: | ---: | ---: | ---: | :---: | ---: | ---: | ---: | :---: |
| Qwen2.5-VL-3B | MMStar | 1500 | 0.5540 | 0.2607 | 0.4705 | [0.4302, 0.5132] | 0.0013 | 0.0153 | 11.5000 | [3.8000, 29.0000] |
| Qwen2.5-VL-7B | MMStar | 1500 | 0.6320 | 0.2880 | 0.4557 | [0.4178, 0.4947] | 0.0293 | 0.2140 | 7.2955 | [5.5614, 10.2424] |
| Qwen2.5-VL-3B | MathVista-testmini | 999 | 0.6236 | 0.3293 | 0.5281 | [0.4826, 0.5740] | 0.1672 | 0.1391 | 0.8323 | [0.6949, 0.9890] |
| Qwen2.5-VL-7B | MathVista-testmini | 999 | 0.6627 | 0.3393 | 0.5121 | [0.4697, 0.5550] | 0.3233 | 0.1331 | 0.4118 | [0.3516, 0.4762] |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=none] | 4096 | 0.3418 | 0.2424 | 0.7093 | [0.6748, 0.7448] | 0.0000 | 0.0000 | n/a | n/a |
| Gemma-3 | ViRL39K audit sample (4096) [blind condition=caption] | 4096 | 0.3418 | 0.3091 | 0.9043 | [0.8671, 0.9428] | 0.0000 | 0.0000 | n/a | n/a |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=none] | 4096 | 0.2805 | 0.1538 | 0.5483 | [0.5085, 0.5897] | 0.2793 | 0.1431 | 0.5122 | [0.4739, 0.5519] |
| InternVL3-9B | ViRL39K audit sample (4096) [blind condition=caption] | 4096 | 0.2805 | 0.1951 | 0.6954 | [0.6514, 0.7421] | 0.2793 | 0.1860 | 0.6661 | [0.6239, 0.7112] |

## 5. Not computed

| Benchmark | Model | Subset | n | reason |
| --- | --- | --- | ---: | --- |
| MathVista-testmini | Qwen2.5-VL-3B | whole benchmark (single global null) | n/a | Mixed benchmark: 539 MC items and 460 free-form items. Per the null rule a single global null is not permitted, so no whole-benchmark corrected retention is reported. |
| MathVista-testmini | Qwen2.5-VL-7B | whole benchmark (single global null) | n/a | Mixed benchmark: 539 MC items and 460 free-form items. Per the null rule a single global null is not permitted, so no whole-benchmark corrected retention is reported. |
| ViRL39K audit sample (4096) [blind condition=none] | Gemma-3 | MC, k indeterminable | 92 | answer_type=multiple_choice but the option list is not present in the stored prompt text (options appear only in the image); k cannot be determined per item, so no null is assigned. |
| ViRL39K audit sample (4096) [blind condition=none] | Gemma-3 | whole 4096-row sample (single global null) | n/a | Mixed sample (MC + free-form); a single global null is not permitted by the null rule. |
| ViRL39K audit sample (4096) [blind condition=caption] | Gemma-3 | MC, k indeterminable | 92 | answer_type=multiple_choice but the option list is not present in the stored prompt text (options appear only in the image); k cannot be determined per item, so no null is assigned. |
| ViRL39K audit sample (4096) [blind condition=caption] | Gemma-3 | whole 4096-row sample (single global null) | n/a | Mixed sample (MC + free-form); a single global null is not permitted by the null rule. |
| ViRL39K audit sample (4096) [blind condition=none] | InternVL3-9B | MC, k indeterminable | 92 | answer_type=multiple_choice but the option list is not present in the stored prompt text (options appear only in the image); k cannot be determined per item, so no null is assigned. |
| ViRL39K audit sample (4096) [blind condition=none] | InternVL3-9B | whole 4096-row sample (single global null) | n/a | Mixed sample (MC + free-form); a single global null is not permitted by the null rule. |
| ViRL39K audit sample (4096) [blind condition=caption] | InternVL3-9B | MC, k indeterminable | 92 | answer_type=multiple_choice but the option list is not present in the stored prompt text (options appear only in the image); k cannot be determined per item, so no null is assigned. |
| ViRL39K audit sample (4096) [blind condition=caption] | InternVL3-9B | whole 4096-row sample (single global null) | n/a | Mixed sample (MC + free-form); a single global null is not permitted by the null rule. |
| BLINK | Qwen2.5-VL-3B and 7B | all | n/a | No image-removed (blind) run exists under experiments/runs; blind accuracy is not available, so retention (naive or corrected) cannot be computed. |
| HallusionBench | Qwen2.5-VL-3B and 7B | all | n/a | No image-removed (blind) run exists under experiments/runs; blind accuracy is not available, so retention (naive or corrected) cannot be computed. |
| MMVP | Qwen2.5-VL-3B and 7B | all | n/a | No image-removed (blind) run exists under experiments/runs; blind accuracy is not available, so retention (naive or corrected) cannot be computed. |
| MathVerse | Qwen2.5-VL-3B and 7B | all | n/a | No image-removed (blind) run exists under experiments/runs; blind accuracy is not available, so retention (naive or corrected) cannot be computed. |
| MMMU dev+validation | Qwen2.5-VL-3B and 7B | all | n/a | No image-removed (blind) run exists under experiments/runs; blind accuracy is not available, so retention (naive or corrected) cannot be computed. |

### With-image `k` availability for the five benchmarks that have no blind arm

| Benchmark | with-image postprocessed run | n | k distribution (option-label count -> rows) |
| --- | --- | ---: | --- |
| BLINK | `experiments/runs/vlmevalkit_postprocess_l10_blink3b_canonicalv2_final_20260711T132325Z` | 1901 | k=2:924, k=3:134, k=4:843 |
| BLINK | `experiments/runs/vlmevalkit_postprocess_l10_blink7b_canonicalv2_final_20260711T132325Z` | 1901 | k=2:924, k=3:134, k=4:843 |
| HallusionBench | `experiments/runs/vlmevalkit_postprocess_l10_hallusion3b_canonicalv2_final_20260711T132325Z` | 1129 | k=0:1129 |
| HallusionBench | `experiments/runs/vlmevalkit_postprocess_l10_hallusion7b_canonicalv2_final_20260711T132325Z` | 1129 | k=0:1129 |
| MMVP | `experiments/runs/vlmevalkit_postprocess_l10_mmvp3b_canonicalv2_final_20260711T132326Z` | 300 | k=2:300 |
| MMVP | `experiments/runs/vlmevalkit_postprocess_l10_mmvp7b_canonicalv2_final_20260711T132326Z` | 300 | k=2:300 |
| MathVerse | `experiments/runs/vlmevalkit_postprocess_l10_mathverse3b_canonicalv2_v2_20260711T143923Z` | 3940 | k=0:1760, k=2:105, k=3:60, k=4:1835, k=5:150, k=6:30 |
| MathVerse | `experiments/runs/vlmevalkit_postprocess_l10_mathverse7b_canonicalv2_v2_20260711T143943Z` | 3940 | k=0:1760, k=2:105, k=3:60, k=4:1835, k=5:150, k=6:30 |
| MMMU dev+validation | `experiments/runs/vlmevalkit_postprocess_l10_mmmu3b_v2_canonicalv2_20260711T145554Z` | 1050 | k=0:62, k=2:35, k=3:133, k=4:699, k=5:108, k=6:6, k=7:2, k=9:5 |
| MMMU dev+validation | `experiments/runs/vlmevalkit_postprocess_l10_mmmu7b_v2_canonicalv2_20260711T145711Z` | 1050 | k=0:62, k=2:35, k=3:133, k=4:699, k=5:108, k=6:6, k=7:2, k=9:5 |

## 6. Answer-format census

MathVista-testmini (`question_type` x option-label count):

| Model | mc=False/True | k | rows |
| --- | :---: | ---: | ---: |
| Qwen2.5-VL-3B | False | 0 | 460 |
| Qwen2.5-VL-3B | True | 2 | 185 |
| Qwen2.5-VL-3B | True | 3 | 18 |
| Qwen2.5-VL-3B | True | 4 | 272 |
| Qwen2.5-VL-3B | True | 5 | 51 |
| Qwen2.5-VL-3B | True | 6 | 9 |
| Qwen2.5-VL-3B | True | 7 | 3 |
| Qwen2.5-VL-3B | True | 8 | 1 |
| Qwen2.5-VL-7B | False | 0 | 460 |
| Qwen2.5-VL-7B | True | 2 | 185 |
| Qwen2.5-VL-7B | True | 3 | 18 |
| Qwen2.5-VL-7B | True | 4 | 272 |
| Qwen2.5-VL-7B | True | 5 | 51 |
| Qwen2.5-VL-7B | True | 6 | 9 |
| Qwen2.5-VL-7B | True | 7 | 3 |
| Qwen2.5-VL-7B | True | 8 | 1 |

ViRL39K audit sample, 4096 rows (`source_metadata.answer_type` x parsed k; `k=None` = option list absent from the stored prompt):

| answer_type | k | rows |
| --- | :---: | ---: |
| multiple_choice | 2 | 75 |
| multiple_choice | 3 | 72 |
| multiple_choice | 4 | 1010 |
| multiple_choice | 5 | 58 |
| multiple_choice | None | 92 |
| numeric | 0 | 1982 |
| text_or_expression | 0 | 807 |

## 7. Checks

| Check | Result |
| --- | --- |
| MMStar: with-image and blind item id sets identical | 1500 / 1500 for 3B and 7B |
| MMStar: `option_labels` length identical between with-image and blind rows | 1500 / 1500 for 3B and 7B |
| MMStar: `k` cross-checked against `data/vlmevalkit/MMStar_VLMEVAL.tsv` option columns | option-presence patterns ABCD:1321, AB:85, ABC:90, ABD:1, ACD:1, BCD:2 |
| MathVista: with-image and blind item id sets identical | 999 / 999 for 3B and 7B |
| MathVista: `question_type == multi_choice` agrees with non-empty `option_labels` | 999 / 999 rows |
| ViRL sample: all six run files carry the same 4096 `qid` set | true |
| ViRL sample: parsed ground-truth label lies inside the parsed option list | 1215 / 1215 parsed MC items |
| ViRL sample: MC items whose option list is absent from the stored prompt | 92 of 1307 |

## 8. Provenance — input artifacts

| File | bytes | sha256 |
| --- | ---: | --- |
| `experiments/runs/vlmevalkit_mmstar3b_adapted_an29_20260710T004416Z/postprocessed_v2/rows.jsonl` | 649385 | `0c1eade940b039ab3ea4c09d9ab03f48cf09d7bed8e473a03a1d721696bf3908` |
| `experiments/runs/layer1_blind_mmstar3b_an29_20260710T023019Z/predictions.jsonl` | 892064 | `26e7cd871eda9bb0b810a4a93ad6ca10d4b672d39bc40f696dfff49a0f364314` |
| `experiments/runs/vlmevalkit_mmstar7b_adapted_an29_20260710T005355Z/postprocessed_v2/rows.jsonl` | 655643 | `332ca35761923ddd002da65c88adb7113c5a2bc88e91361655551850052baedd` |
| `experiments/runs/layer1_blind_mmstar7b_an29_20260710T023019Z/predictions.jsonl` | 908238 | `4e3283bb0e472762d91abca7b2b1731eeaf724d20d7b39cf1297086ed747bd90` |
| `experiments/runs/vlmevalkit_postprocess_mathvista3b_20260710T022024Z/rows.jsonl` | 517583 | `ce0ff9741d1c277bedfbde3ff4f6e8b4d891561f9cba72339f118089fbea1fc6` |
| `experiments/runs/layer1_blind_mathvista3b_an29_20260710T023019Z/predictions.jsonl` | 575820 | `3cd25ded8d18c654aab9365950c4cb56f8b90c60d69d009e8eb210ca4ea6065d` |
| `experiments/runs/vlmevalkit_postprocess_mathvista7b_20260710T022024Z/rows.jsonl` | 534080 | `a24aca43f3b40e1a3a45085484138d8933fbeeae90f79d0a694f8edc8885e4dd` |
| `experiments/runs/layer1_blind_mathvista7b_an29_20260710T023019Z/predictions.jsonl` | 576195 | `15b974068cb43fa7a27fb3e9d9f3879a4cba3d50d1201fb3d11d3a7a81b5eb3a` |
| `experiments/runs/m11_blind_gemma3_virl4096_none_gemma3_none_s0of1_an29_20260716T200132Z/per_item.jsonl` | 14896208 | `3095957aa0be20edd3a7c636f2acb98b09f74ed2ff58d95ca9ed31b0a3420168` |
| `experiments/runs/m11_blind_gemma3_virl4096_real_gemma3_real_s0of1_an29_20260716T191637Z/per_item.jsonl` | 14173307 | `014ad99a06ccb8d22b95128c6b916e314df9b2a293b18217d4bc2759cd7317f3` |
| `experiments/runs/m11_blind_gemma3_virl4096_caption_gemma3_caption_s0of1_an29_20260716T231512Z/per_item.jsonl` | 15253975 | `48754b6c64fc4967467e8e1efbd2d83d754919f426a85d51c355d2335900e0c6` |
| `experiments/runs/m11_virl4096_retry1_internvl3_none_s0of1_an12_20260716T170739Z/per_item.jsonl` | 14784695 | `1042ced5178e16dd54f9eef4ded36b9c6cf4862fac872469e897876ad6304bc2` |
| `experiments/runs/m11_virl4096_patchbudgetv2_internvl3_real_s0of1_an29_20260717T072527Z/per_item.jsonl` | 13623437 | `101d395645602726ef53dd12c4659da52f8c648ad799c9d620cf5dcf030f7964` |
| `experiments/runs/m11_virl4096_retry1_internvl3_caption_s0of1_an12_20260716T170744Z/per_item.jsonl` | 14675851 | `cc5661bc3cb38bd5875c42992ee2d0ef0f1c058b0566f421a7bfe9540bcc6928` |

Cross-family run keys are the `path` fields of `reports/generalization_audits_v2.json` under `blind_sample.{gemma3,internvl3}|{real,none,caption}`.

