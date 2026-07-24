# X1 image-condition matrix results (v1)

Registered: `docs/registered_x1_matrix_v1.md`. Layers: candidate-evidence
ranking and open-form realization. All open-form cells use the locked
32-token greedy contract (truncation guard: 0/250 sampled rows truncated).
Statistics below are the registered readings and registered secondary only.

- Ratio definition: inflation_correct.mean / inflation_mismatched.mean, where inflation_X = per-pair (arm margin - base margin) under condition X; paired bootstrap 10000 resamples seed 20260717
- Primary template: `coordinate_register_twenty_point_x_v02`

## Registered readings (a)/(b): margin-inflation ratio, primary template

| arm | inflation correct | inflation mismatched | ratio (correct/mismatched) | ratio 95% CI | registered reading |
|---|---|---|---|---|---|
| a1_step100 | +0.1501 [+0.1448, +0.1554] | -0.0000 [-0.0013, +0.0012] | -3936.625 | [-3693.474, 3530.161] | outside_registered_readings |
| a2_step100 | +0.0356 [+0.0337, +0.0375] | +0.0004 [-0.0005, +0.0013] | 82.809 | [-683.810, 850.950] | b_content_specific_evidence_sharpening |
| a2b_step100 | +0.0348 [+0.0327, +0.0369] | +0.0001 [-0.0009, +0.0010] | 661.101 | [-1175.582, 1218.338] | b_content_specific_evidence_sharpening |
| a3_step100 | +0.0900 [+0.0866, +0.0934] | -0.0002 [-0.0013, +0.0008] | -377.408 | [-2524.921, 2579.335] | outside_registered_readings |

## Registered reading (c): twin-counterfactual condition, primary template

| model | twin-gold preferred rate | margin sign negative rate | flip rate given real-positive |
|---|---|---|---|
| base | 0.9533 | 0.9533 | 0.9510 |
| a1_step100 | 0.9533 | 0.9533 | 0.9510 |
| a2_step100 | 0.9525 | 0.9525 | 0.9501 |
| a2b_step100 | 0.9483 | 0.9483 | 0.9455 |
| a3_step100 | 0.9533 | 0.9533 | 0.9510 |

## Registered secondary: wrong-item vs right-item margin inflation (real condition, primary template)

| arm | right items | wrong items | inflation right | inflation wrong | ratio wrong/right |
|---|---|---|---|---|---|
| a1_step100 | 282 | 318 | +0.1842 | +0.1199 | 0.651 |
| a2_step100 | 256 | 344 | +0.0412 | +0.0315 | 0.764 |
| a2b_step100 | 269 | 331 | +0.0403 | +0.0304 | 0.755 |
| a3_step100 | 278 | 322 | +0.1085 | +0.0740 | 0.682 |

## Open-form realization: pair-correct by model x condition (all templates pooled)

| model | real | mismatched_real | twin_counterfactual | gray | no_image |
|---|---|---|---|---|---|
| base | 0.5617 | 0.0042 | 0.0000 | 0.0000 | 0.0000 |
| a1_step100 | 0.5900 | 0.0033 | 0.0000 | 0.0000 | 0.0000 |
| a2_step100 | 0.5617 | 0.0058 | 0.0000 | 0.0000 | 0.0000 |
| a2b_step100 | 0.5575 | 0.0017 | 0.0000 | 0.0000 | 0.0000 |
| a3_step100 | 0.5767 | 0.0050 | 0.0000 | 0.0000 | 0.0000 |

Per-template tables, all inflation effects, and full cell provenance are in
the machine JSON. No interpretation beyond the registered readings.
