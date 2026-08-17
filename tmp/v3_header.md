# X-series synthesis — Paper-1 evidence map (v3)

Supersedes `reports/x_series_synthesis_v2.md`. v3 adds the completed
**three-seed replication (Track C1)**, the **D2 test-time image-access**
readout, and the **B1 trained-checkpoint** scoring. Facts and registered
readings only; no interpretation beyond the registered documents. Layer names:
candidate-evidence ranking / open-form realization. "Already perceived/
understood" remains hypothesis language (X2 bottom branch,
`docs/registered_x2_ladder_v1.md`). Ordering follows RESEARCH_DOC §11.

Status at 2026-07-27: seeds 1–3 complete; M5 long-horizon at step 345/400;
Mini-A5 and M7 built and queued behind hardware availability (an29 blocked by a
full node root filesystem, admin request outstanding).

## 1. The replication rung (Track C1, NEW in v3)

Three seeds, four matched arms, 601 held-out Geometry3K items per seed, all
step-100 endpoints registered before measurement.

**Task gain (Acc_final, step 100 − step 0):**

| arm | seed 1 | seed 2 | seed 3 | mean |
|---|---|---|---|---|
| A1 real | +0.2529 | +0.2463 | +0.2313 | **+0.2435** |
| A3 caption | +0.1098 | +0.0832 | +0.1215 | +0.1048 |
| A2b no-image | +0.0300 | +0.0549 | +0.0532 | +0.0460 |
| A2 gray | +0.0200 | +0.0100 | +0.0183 | +0.0161 |

**Recovery of the A1 gain:** gray 7.9 / 4.1 / 7.9% (mean 6.6%); no-image
11.8 / 22.3 / 23.0% (19.1%); caption 43.4 / 33.8 / 52.5% (43.2%). The
preregistered 30–70% blind-recovery interval is falsified in every seed for
both zero-visual-bit arms.

**Registered geometry FlipTrack endpoint (pair accuracy, step 100 − step 0):**

| arm | seed 1 | seed 2 | seed 3 | mean | seed-level 95% CI | within ±0.05 |
|---|---|---|---|---|---|---|
| A1 real | −0.0017 | +0.0083 | +0.0100 | **+0.0056** | [−0.0016, +0.0127] | yes |
| A3 caption | −0.0083 | −0.0117 | +0.0050 | −0.0050 | [−0.0150, +0.0050] | yes |
| A2b no-image | −0.0233 | −0.0250 | −0.0333 | −0.0272 | [−0.0333, −0.0212] | yes |
| A2 gray | −0.0450 | −0.0450 | −0.0367 | −0.0422 | [−0.0477, −0.0368] | yes |

**A1 equivalence verdict: supported within the registered band.** The caption
inversion (A3 starts above A1 at step 0 and ends below it at step 100)
replicates in all three seeds. Source: `reports/three_seed_summary_v1.{md,json}`,
built from the three registered four-arm readouts.

Defect caught and corrected before it propagated: the first seed-3 readout
inherited `geo_audits` from the seed-2 template and returned values
byte-identical to seed 2. The plan's verification rule (seed 3 must not
reproduce seed 2 exactly) surfaced it; the builder now resolves the seed-3
audits itself and fails closed. Recorded in commit `ac3f362`.

## 2. Test-time image access (D2, NEW in v3)

Registered before inference (`docs/registered_d2_testtime_ablation_v1.md`),
eight cells on the frozen 601-row set, decoding contract identical to the
registered pilot evaluations; base cells pinned from the registered arm step-0
evaluations rather than re-measured.

| seed | Acc(A1, real) | Acc(A1, none) | RetainedGainBlind | band |
|---|---|---|---|---|
| 1 | 0.4276 | 0.1082 | 0.158 | (a) image-mediated |
| 2 | 0.4210 | 0.0982 | 0.122 | (a) image-mediated |

**Registered verdict: `a_image_mediated_at_test_time`,** both seeds agreeing.
The reproduction check reproduced the published step-100 values exactly.

Registered secondary, and the result most likely to bear on the canonical
claim: **A2b — trained with no images at all — reaches 0.3195 / 0.2962 when
evaluated *with* images**, against its published blind 0.0982 / 0.1231, a
test-time image benefit of **+0.221 / +0.173**. Source:
`reports/d2_testtime_ablation_v1.{md,json}`.

