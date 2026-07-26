# D2 test-time image-access ablation results (v1)

Registered: `docs/registered_d2_testtime_ablation_v1.md`. Layer: open-form
realization on the frozen 601-row Geometry3K pilot evaluation set, decoding
contract identical to the registered pilot evaluations. Base cells are the
pinned registered arm step-0 evaluations, not re-measured.

## Reproduction check (A1 real vs published step-100)

| model | published | measured | delta | within +/-0.01 |
|---|---|---|---|---|
| a1_seed1_step100 | 0.4276 | 0.4276 | +0.0000 | True |
| a1_seed2_step100 | 0.4210 | 0.4210 | -0.0000 | True |

## Registered primary: retained gain without test-time image access

| seed | Acc(A1,real) | Acc(A1,none) | gain real | gain blind | RetainedGainBlind | band |
|---|---|---|---|---|---|---|
| seed1 | 0.4276 | 0.1082 | +0.2529 | +0.0400 | 0.1580 | a_image_mediated_at_test_time |
| seed2 | 0.4210 | 0.0982 | +0.2463 | +0.0300 | 0.1217 | a_image_mediated_at_test_time |

**Registered verdict: a_image_mediated_at_test_time**

## Registered secondary

| seed | RetainedGain(gray) | drop real-none | A2b real | A2b published none | A2b test-time image benefit |
|---|---|---|---|---|---|
| seed1 | 0.0656 | +0.3195 | 0.3195 | 0.0982 | +0.2213 |
| seed2 | 0.0876 | +0.3228 | 0.2962 | 0.1231 | +0.1731 |

## All cells

| cell | n | Acc_final | 95% CI | Acc_strict |
|---|---|---|---|---|
| a1_seed1_step100|gray | 601 | 0.1065 | [0.0815, 0.1314] | 0.1065 |
| a1_seed1_step100|none | 601 | 0.1082 | [0.0849, 0.1331] | 0.1065 |
| a1_seed1_step100|real | 601 | 0.4276 | [0.3894, 0.4692] | 0.4276 |
| a1_seed2_step100|gray | 601 | 0.1115 | [0.0882, 0.1348] | 0.1115 |
| a1_seed2_step100|none | 601 | 0.0982 | [0.0749, 0.1198] | 0.0982 |
| a1_seed2_step100|real | 601 | 0.4210 | [0.3844, 0.4642] | 0.4210 |
| a2b_seed1_step100|real | 601 | 0.3195 | [0.2845, 0.3611] | 0.3195 |
| a2b_seed2_step100|real | 601 | 0.2962 | [0.2612, 0.3344] | 0.2962 |

No interpretation beyond the registered bands.
