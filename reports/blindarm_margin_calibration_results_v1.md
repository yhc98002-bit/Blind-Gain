# Blind-arm margin calibration results (v1)

Registered: `docs/registered_blindarm_margin_calibration_v1.md`. Inference-only calibration of the seed-1 visual-evidence ranking margin against blind-trained seed-1 checkpoints. Terminology: visual-evidence ranking / candidate-answer ranking.

- Scorer: `visual-evidence-ranking-v1`
- Primary template: `coordinate_register_twenty_point_x_v02`
- Bootstrap: 10000 resamples, seed 20260717, paired over FlipTrack pairs

## Registered verdict

**intermediate_pattern** — Blind-arm effects neither overlap the A1 effect nor all fall below half of it; the registered rule assigns no clean label and the pattern is reported descriptively.

## Real-input paired-margin effects vs frozen base (primary template)

| model | mean | 95% CI | below half of A1 | CI overlaps A1 |
|---|---|---|---|---|
| a1_step100 (reference) | +0.1501 | [+0.1448, +0.1554] | — | — |
| a2_step100 | +0.0356 | [+0.0337, +0.0375] | True | False |
| a2b_step100 | +0.0348 | [+0.0327, +0.0369] | True | False |
| a3_step100 | +0.0900 | [+0.0866, +0.0934] | False | False |

A1 step-100 seed-1 published DiD (real minus no-image, identical up to the structurally-zero blind margins): +0.1501 [+0.1448, +0.1554]

## Integrity controls (blind-condition margins, must be structurally zero)

| cell | mean margin | max abs margin | structurally zero |
|---|---|---|---|
| a1_step100|gray|coordinate_register_twenty_point_x_v02 | 0.00e+00 | 0.00e+00 | True |
| a1_step100|gray|header_cued_table_code_v02 | 0.00e+00 | 0.00e+00 | True |
| a1_step100|gray|starred_series_value_nine_v07 | 0.00e+00 | 0.00e+00 | True |
| a1_step100|no_image|coordinate_register_twenty_point_x_v02 | 0.00e+00 | 0.00e+00 | True |
| a1_step100|no_image|header_cued_table_code_v02 | 0.00e+00 | 0.00e+00 | True |
| a1_step100|no_image|starred_series_value_nine_v07 | 0.00e+00 | 0.00e+00 | True |
| a1_step60|gray|coordinate_register_twenty_point_x_v02 | 0.00e+00 | 0.00e+00 | True |
| a1_step60|gray|header_cued_table_code_v02 | 0.00e+00 | 0.00e+00 | True |
| a1_step60|gray|starred_series_value_nine_v07 | 0.00e+00 | 0.00e+00 | True |
| a1_step60|no_image|coordinate_register_twenty_point_x_v02 | 0.00e+00 | 0.00e+00 | True |
| a1_step60|no_image|header_cued_table_code_v02 | 0.00e+00 | 0.00e+00 | True |
| a1_step60|no_image|starred_series_value_nine_v07 | 0.00e+00 | 0.00e+00 | True |
| a2_step100|gray|coordinate_register_twenty_point_x_v02 | 0.00e+00 | 0.00e+00 | True |
| a2_step100|gray|header_cued_table_code_v02 | 0.00e+00 | 0.00e+00 | True |
| a2_step100|gray|starred_series_value_nine_v07 | 0.00e+00 | 0.00e+00 | True |
| a2_step100|no_image|coordinate_register_twenty_point_x_v02 | 0.00e+00 | 0.00e+00 | True |
| a2_step100|no_image|header_cued_table_code_v02 | 0.00e+00 | 0.00e+00 | True |
| a2_step100|no_image|starred_series_value_nine_v07 | 0.00e+00 | 0.00e+00 | True |
| a2b_step100|gray|coordinate_register_twenty_point_x_v02 | 0.00e+00 | 0.00e+00 | True |
| a2b_step100|gray|header_cued_table_code_v02 | 0.00e+00 | 0.00e+00 | True |
| a2b_step100|gray|starred_series_value_nine_v07 | 0.00e+00 | 0.00e+00 | True |
| a2b_step100|no_image|coordinate_register_twenty_point_x_v02 | 0.00e+00 | 0.00e+00 | True |
| a2b_step100|no_image|header_cued_table_code_v02 | 0.00e+00 | 0.00e+00 | True |
| a2b_step100|no_image|starred_series_value_nine_v07 | 0.00e+00 | 0.00e+00 | True |
| a3_step100|gray|coordinate_register_twenty_point_x_v02 | 0.00e+00 | 0.00e+00 | True |
| a3_step100|gray|header_cued_table_code_v02 | 0.00e+00 | 0.00e+00 | True |
| a3_step100|gray|starred_series_value_nine_v07 | 0.00e+00 | 0.00e+00 | True |
| a3_step100|no_image|coordinate_register_twenty_point_x_v02 | 0.00e+00 | 0.00e+00 | True |
| a3_step100|no_image|header_cued_table_code_v02 | 0.00e+00 | 0.00e+00 | True |
| a3_step100|no_image|starred_series_value_nine_v07 | 0.00e+00 | 0.00e+00 | True |
| base|gray|coordinate_register_twenty_point_x_v02 | 0.00e+00 | 0.00e+00 | True |
| base|gray|header_cued_table_code_v02 | 0.00e+00 | 0.00e+00 | True |
| base|gray|starred_series_value_nine_v07 | 0.00e+00 | 0.00e+00 | True |
| base|no_image|coordinate_register_twenty_point_x_v02 | 0.00e+00 | 0.00e+00 | True |
| base|no_image|header_cued_table_code_v02 | 0.00e+00 | 0.00e+00 | True |
| base|no_image|starred_series_value_nine_v07 | 0.00e+00 | 0.00e+00 | True |

## Condition-independent sharpening statistics (all cells, all templates)

| cell | n | margin mean | pair success | top-1 | MRR | norm. entropy | top1−top2 gap |
|---|---|---|---|---|---|---|---|
| a1_step100|gray|coordinate_register_twenty_point_x_v02 | 600 | +0.0000 | 0.0000 | 0.0000 | 0.2186 | 0.9980 | 0.0153 |
| a1_step100|gray|header_cued_table_code_v02 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.2175 | 0.9968 | 0.0629 |
| a1_step100|gray|starred_series_value_nine_v07 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.3057 | 0.9977 | 0.0623 |
| a1_step100|no_image|coordinate_register_twenty_point_x_v02 | 600 | +0.0000 | 0.0000 | 0.0000 | 0.2142 | 0.9981 | 0.0113 |
| a1_step100|no_image|header_cued_table_code_v02 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.2110 | 0.9961 | 0.0688 |
| a1_step100|no_image|starred_series_value_nine_v07 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.3053 | 0.9974 | 0.0683 |
| a1_step100|real|coordinate_register_twenty_point_x_v02 | 600 | +0.8235 | 0.9067 | 0.4767 | 0.7839 | 0.9728 | 0.2395 |
| a1_step100|real|header_cued_table_code_v02 | 300 | +2.1763 | 1.0000 | 1.0000 | 1.0000 | 0.8437 | 1.4461 |
| a1_step100|real|starred_series_value_nine_v07 | 300 | +0.4192 | 0.8767 | 0.5667 | 0.8448 | 0.9910 | 0.2277 |
| a1_step60|gray|coordinate_register_twenty_point_x_v02 | 600 | +0.0000 | 0.0000 | 0.0000 | 0.2184 | 0.9985 | 0.0154 |
| a1_step60|gray|header_cued_table_code_v02 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.2227 | 0.9969 | 0.0624 |
| a1_step60|gray|starred_series_value_nine_v07 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.3049 | 0.9979 | 0.0493 |
| a1_step60|no_image|coordinate_register_twenty_point_x_v02 | 600 | +0.0000 | 0.0000 | 0.0000 | 0.2162 | 0.9986 | 0.0108 |
| a1_step60|no_image|header_cued_table_code_v02 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.2143 | 0.9963 | 0.0661 |
| a1_step60|no_image|starred_series_value_nine_v07 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.3056 | 0.9976 | 0.0721 |
| a1_step60|real|coordinate_register_twenty_point_x_v02 | 600 | +0.7624 | 0.9067 | 0.4817 | 0.7818 | 0.9764 | 0.2177 |
| a1_step60|real|header_cued_table_code_v02 | 300 | +2.0966 | 1.0000 | 1.0000 | 1.0000 | 0.8574 | 1.3902 |
| a1_step60|real|starred_series_value_nine_v07 | 300 | +0.3896 | 0.8600 | 0.5233 | 0.8295 | 0.9920 | 0.2071 |
| a2_step100|gray|coordinate_register_twenty_point_x_v02 | 600 | +0.0000 | 0.0000 | 0.0000 | 0.2102 | 0.9973 | 0.0109 |
| a2_step100|gray|header_cued_table_code_v02 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.2168 | 0.9970 | 0.0614 |
| a2_step100|gray|starred_series_value_nine_v07 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.3055 | 0.9979 | 0.0464 |
| a2_step100|no_image|coordinate_register_twenty_point_x_v02 | 600 | +0.0000 | 0.0000 | 0.0000 | 0.2125 | 0.9978 | 0.0186 |
| a2_step100|no_image|header_cued_table_code_v02 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.2121 | 0.9964 | 0.0661 |
| a2_step100|no_image|starred_series_value_nine_v07 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.3057 | 0.9975 | 0.0497 |
| a2_step100|real|coordinate_register_twenty_point_x_v02 | 600 | +0.7089 | 0.9050 | 0.4583 | 0.7721 | 0.9791 | 0.1875 |
| a2_step100|real|header_cued_table_code_v02 | 300 | +2.0831 | 1.0000 | 1.0000 | 1.0000 | 0.8599 | 1.3785 |
| a2_step100|real|starred_series_value_nine_v07 | 300 | +0.3645 | 0.8600 | 0.5267 | 0.8253 | 0.9929 | 0.1912 |
| a2b_step100|gray|coordinate_register_twenty_point_x_v02 | 600 | +0.0000 | 0.0000 | 0.0000 | 0.2201 | 0.9966 | 0.0121 |
| a2b_step100|gray|header_cued_table_code_v02 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.2135 | 0.9971 | 0.0601 |
| a2b_step100|gray|starred_series_value_nine_v07 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.3038 | 0.9979 | 0.0451 |
| a2b_step100|no_image|coordinate_register_twenty_point_x_v02 | 600 | +0.0000 | 0.0000 | 0.0000 | 0.2143 | 0.9978 | 0.0093 |
| a2b_step100|no_image|header_cued_table_code_v02 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.2116 | 0.9965 | 0.0641 |
| a2b_step100|no_image|starred_series_value_nine_v07 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.3060 | 0.9974 | 0.0674 |
| a2b_step100|real|coordinate_register_twenty_point_x_v02 | 600 | +0.7081 | 0.8967 | 0.4583 | 0.7693 | 0.9789 | 0.1873 |
| a2b_step100|real|header_cued_table_code_v02 | 300 | +2.0799 | 1.0000 | 1.0000 | 1.0000 | 0.8604 | 1.3745 |
| a2b_step100|real|starred_series_value_nine_v07 | 300 | +0.3668 | 0.8567 | 0.5100 | 0.8141 | 0.9925 | 0.1869 |
| a3_step100|gray|coordinate_register_twenty_point_x_v02 | 600 | +0.0000 | 0.0000 | 0.0000 | 0.2174 | 0.9980 | 0.0168 |
| a3_step100|gray|header_cued_table_code_v02 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.2194 | 0.9969 | 0.0631 |
| a3_step100|gray|starred_series_value_nine_v07 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.3053 | 0.9978 | 0.0495 |
| a3_step100|no_image|coordinate_register_twenty_point_x_v02 | 600 | +0.0000 | 0.0000 | 0.0000 | 0.2223 | 0.9984 | 0.0122 |
| a3_step100|no_image|header_cued_table_code_v02 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.2145 | 0.9963 | 0.0691 |
| a3_step100|no_image|starred_series_value_nine_v07 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.3063 | 0.9972 | 0.0620 |
| a3_step100|real|coordinate_register_twenty_point_x_v02 | 600 | +0.7633 | 0.9067 | 0.4867 | 0.7832 | 0.9762 | 0.2123 |
| a3_step100|real|header_cued_table_code_v02 | 300 | +2.1177 | 1.0000 | 1.0000 | 1.0000 | 0.8535 | 1.4040 |
| a3_step100|real|starred_series_value_nine_v07 | 300 | +0.3893 | 0.8433 | 0.5000 | 0.8151 | 0.9917 | 0.2042 |
| base|gray|coordinate_register_twenty_point_x_v02 | 600 | +0.0000 | 0.0000 | 0.0000 | 0.2184 | 0.9987 | 0.0150 |
| base|gray|header_cued_table_code_v02 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.2213 | 0.9968 | 0.0630 |
| base|gray|starred_series_value_nine_v07 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.3064 | 0.9980 | 0.0434 |
| base|no_image|coordinate_register_twenty_point_x_v02 | 600 | +0.0000 | 0.0000 | 0.0000 | 0.2131 | 0.9987 | 0.0089 |
| base|no_image|header_cued_table_code_v02 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.2081 | 0.9963 | 0.0669 |
| base|no_image|starred_series_value_nine_v07 | 300 | +0.0000 | 0.0000 | 0.0000 | 0.3057 | 0.9974 | 0.0630 |
| base|real|coordinate_register_twenty_point_x_v02 | 600 | +0.6733 | 0.9067 | 0.4683 | 0.7751 | 0.9811 | 0.1780 |
| base|real|header_cued_table_code_v02 | 300 | +1.9756 | 1.0000 | 1.0000 | 1.0000 | 0.8770 | 1.3012 |
| base|real|starred_series_value_nine_v07 | 300 | +0.3470 | 0.8667 | 0.5067 | 0.8140 | 0.9934 | 0.1763 |

## Secondary real-vs-base effects (all templates)

| effect | margin | pair success | top-1 | MRR | raw-sum robustness |
|---|---|---|---|---|---|
| a1_step100|real_vs_base|coordinate_register_twenty_point_x_v02 | +0.1501 | +0.0000 | +0.0083 | +0.0088 | +1.0510 |
| a1_step100|real_vs_base|header_cued_table_code_v02 | +0.2007 | +0.0000 | +0.0000 | +0.0000 | +1.4657 |
| a1_step100|real_vs_base|starred_series_value_nine_v07 | +0.0722 | +0.0100 | +0.0600 | +0.0308 | +0.5773 |
| a1_step60|real_vs_base|coordinate_register_twenty_point_x_v02 | +0.0891 | +0.0000 | +0.0133 | +0.0067 | +0.6240 |
| a1_step60|real_vs_base|header_cued_table_code_v02 | +0.1210 | +0.0000 | +0.0000 | +0.0000 | +0.8832 |
| a1_step60|real_vs_base|starred_series_value_nine_v07 | +0.0426 | -0.0067 | +0.0167 | +0.0155 | +0.3407 |
| a2_step100|real_vs_base|coordinate_register_twenty_point_x_v02 | +0.0356 | -0.0017 | -0.0100 | -0.0030 | +0.2493 |
| a2_step100|real_vs_base|header_cued_table_code_v02 | +0.1075 | +0.0000 | +0.0000 | +0.0000 | +0.7871 |
| a2_step100|real_vs_base|starred_series_value_nine_v07 | +0.0174 | -0.0067 | +0.0200 | +0.0113 | +0.1395 |
| a2b_step100|real_vs_base|coordinate_register_twenty_point_x_v02 | +0.0348 | -0.0100 | -0.0100 | -0.0058 | +0.2437 |
| a2b_step100|real_vs_base|header_cued_table_code_v02 | +0.1043 | +0.0000 | +0.0000 | +0.0000 | +0.7558 |
| a2b_step100|real_vs_base|starred_series_value_nine_v07 | +0.0197 | -0.0100 | +0.0033 | +0.0001 | +0.1579 |
| a3_step100|real_vs_base|coordinate_register_twenty_point_x_v02 | +0.0900 | +0.0000 | +0.0183 | +0.0081 | +0.6300 |
| a3_step100|real_vs_base|header_cued_table_code_v02 | +0.1420 | +0.0000 | +0.0000 | +0.0000 | +1.0447 |
| a3_step100|real_vs_base|starred_series_value_nine_v07 | +0.0422 | -0.0233 | -0.0067 | +0.0011 | +0.3377 |

No margin-scale SESOI was registered; this calibration is descriptive and assigns no B1/B2/B3 gate decision.
