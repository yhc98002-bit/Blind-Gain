# Three-seed Geometry3K summary (Track C1)

Seeds 1-3, four matched arms, step-100 endpoints, 601 held-out items per
seed. Each seed's numbers are read verbatim from its registered readout.
Scope tags stay attached: Geometry3K corpus, 3B scale, three seeds.

## Task gain (Acc_final, step 100 minus step 0)

| arm | seed 1 | seed 2 | seed 3 | mean |
|---|---|---|---|---|
| a1_real | +0.2529 | +0.2463 | +0.2313 | +0.2435 |
| a2_gray | +0.0200 | +0.0100 | +0.0183 | +0.0161 |
| a2b_noimage | +0.0300 | +0.0549 | +0.0532 | +0.0460 |
| a3_caption | +0.1098 | +0.0832 | +0.1215 | +0.1048 |

## Recovery of the A1 gain

| arm | seed 1 | seed 2 | seed 3 | mean |
|---|---|---|---|---|
| a2_gray | 7.9% | 4.1% | 7.9% | 6.6% |
| a2b_noimage | 11.8% | 22.3% | 23.0% | 19.1% |
| a3_caption | 43.4% | 33.8% | 52.5% | 43.2% |

The preregistered 30-70% blind-recovery interval is falsified in every seed for gray and no-image: True.

## Registered geometry FlipTrack endpoint (pair accuracy, step 100 minus step 0)

| arm | seed 1 | seed 2 | seed 3 | mean | seed-level 95% CI | within +/-0.05 |
|---|---|---|---|---|---|---|
| a1_real | -0.0017 | +0.0083 | +0.0100 | +0.0056 | [-0.0016, +0.0127] | True |
| a2_gray | -0.0450 | -0.0450 | -0.0367 | -0.0422 | [-0.0477, -0.0368] | True |
| a2b_noimage | -0.0233 | -0.0250 | -0.0333 | -0.0272 | [-0.0333, -0.0212] | True |
| a3_caption | -0.0083 | -0.0117 | +0.0050 | -0.0050 | [-0.0150, +0.0050] | True |

**A1 equivalence verdict: equivalence_supported_within_registered_band**

## Caption inversion (A3 starts above A1 and ends below it)

| seed 1 | seed 2 | seed 3 |
|---|---|---|
| True | True | True |

No interpretation beyond the registered statistics; the pooled verdict uses
the registered +/-0.05 band on seed-level variation with three seeds.

> **CORRECTION (2026-07-27):** the A1 FlipTrack equivalence statement in this file is superseded by `reports/correction_three_seed_fliptrack_v1.md`. The null does not survive contract-strict scoring (A1 strict deltas -0.1267 / +0.0333 / -0.0267), the seed-level CI should have been the preregistered item-level paired CI, and the +/-0.05 margin was registered for the A2gray-A2b contrast rather than for A1. The +0.2435 task gain is unaffected.
