# X5 seed-2 image-condition matrix results (v1)

Identical registered readings to `docs/registered_x1_matrix_v1.md`, applied
to the seed-2 step-100 checkpoints. Frozen base cells pinned from the
audited seed-1/X1 matrices. Facts and registered readings only.

## Readings (a)/(b): margin-inflation ratio, primary template

| arm | inflation correct | inflation mismatched | registered reading |
|---|---|---|---|
| a1_seed2_step100 | +0.1293 [+0.1241, +0.1345] | -0.0004 [-0.0017, +0.0009] | outside_registered_readings |
| a2_seed2_step100 | +0.0373 [+0.0352, +0.0394] | -0.0003 [-0.0013, +0.0007] | outside_registered_readings |
| a2b_seed2_step100 | +0.0577 [+0.0553, +0.0601] | -0.0006 [-0.0016, +0.0003] | outside_registered_readings |
| a3_seed2_step100 | +0.0760 [+0.0732, +0.0788] | -0.0001 [-0.0012, +0.0010] | outside_registered_readings |

## Reading (c): twin condition, primary template

| model | twin-gold preferred rate | flip rate given real-positive |
|---|---|---|
| base | 0.9533 | 0.9510 |
| a1_seed2_step100 | 0.9550 | 0.9529 |
| a2_seed2_step100 | 0.9492 | 0.9464 |
| a2b_seed2_step100 | 0.9500 | 0.9474 |
| a3_seed2_step100 | 0.9542 | 0.9520 |

## Open-form realization pair-correct (all templates pooled)

| model | real | mismatched_real | twin_counterfactual | gray | no_image |
|---|---|---|---|---|---|
| base | 0.5617 | 0.0042 | 0.0000 | 0.0000 | 0.0000 |
| a1_seed2_step100 | 0.5825 | 0.0033 | 0.0000 | 0.0000 | 0.0000 |
| a2_seed2_step100 | 0.5567 | 0.0033 | 0.0000 | 0.0000 | 0.0000 |
| a2b_seed2_step100 | 0.5575 | 0.0025 | 0.0000 | 0.0000 | 0.0000 |
| a3_seed2_step100 | 0.5708 | 0.0067 | 0.0000 | 0.0000 | 0.0000 |

Full effects, secondary tables, and provenance are in the machine JSON.
