# Anchor Step-100 FlipTrack R19 Endpoint V2

Status:
- Complete as an engineering-anchor endpoint on the R19-selected instrument; this is not a PI gate or a certified FlipTrack result.
- V1 remains preserved as `fail` because it mixed an unstamped historical base aggregate with a canonical-v2 step-100 aggregate. V2 reaggregates both fixed response sets with canonical-v2/answer-tags-v1.
- The frozen R19 human contact-sheet audit remains pending. R20 downgraded geometry and chart to R19-selected under the pre-frozen generator criteria.
- Machine summary: `reports/anchor_step100_fliptrack_r19_v2.json`; all ten integrity checks true.

Evidence:
- Base canonical-v2 reaggregate: `experiments/runs/fliptrack_aggregate_base3b_real_canonicalv2_20260712T092214Z`, metrics SHA256 `d1f1d421a99af2c5898197bd1ca86ba1af4321d8f7df85d96558f1112ea33f92`.
- Step-100 evaluation: `experiments/runs/fliptrack_v02r19_anchor_step100_real_an12_20260712T085144Z`; one TP1 replica on an12 GPU5, exactly 1,200 pairs.
- Step-100 canonical-v2 aggregate: `experiments/runs/fliptrack_aggregate_anchor_step100_real_20260712T091312Z`, metrics SHA256 `4fe2d566a4bd512209c2b70b726f4a35b9d5efd6a0462e21b7ef300c3fa32db3`.
- V2 paired comparison: `experiments/runs/fliptrack_compare_anchor_step100_r19_v2_20260712T092541Z`, SHA256 `f29d395bf06e4000f18267c1e770587c7ce922beff3d7e246439eb0ae7e26612`.
- Both endpoints use real images, identical prompt text, greedy decoding, 32 output tokens, the same R19 pairs, canonical-v2, and answer-tags-v1.
- Intervals are 2,000-draw paired item-bootstrap 95% intervals and do not estimate run-to-run RL variance.

Final-answer pair accuracy:

| R19 scope | n | Base | Step 100 | Paired delta | 95% CI | McNemar p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Overall | 1,200 | 0.5617 | 0.5633 | +0.0017 | [-0.0183, +0.0209] | 0.9362 |
| Geometry: coordinate register | 600 | 0.4717 | 0.4800 | +0.0083 | [-0.0183, +0.0367] | 0.6445 |
| Document: header-cued table | 300 | 0.8667 | 0.8567 | -0.0100 | [-0.0400, +0.0167] | 0.6476 |
| Chart: starred series | 300 | 0.4367 | 0.4367 | 0.0000 | [-0.0500, +0.0500] | 1.0000 |

Strict pair accuracy:

| R19 scope | Base | Step 100 | Paired delta | 95% CI | McNemar p |
| --- | ---: | ---: | ---: | ---: | ---: |
| Overall | 0.3717 | 0.3700 | -0.0017 | [-0.0242, +0.0208] | 0.9413 |
| Geometry: coordinate register | 0.4433 | 0.4800 | +0.0367 | [+0.0083, +0.0667] | 0.0263 |
| Document: header-cued table | 0.1800 | 0.0900 | -0.0900 | [-0.1233, -0.0567] | 1.12e-7 |
| Chart: starred series | 0.4200 | 0.4300 | +0.0100 | [-0.0433, +0.0600] | 0.8043 |

Other diagnostics:
- Overall Collapse Rate: base `0.0958`, step 100 `0.0833`.
- Overall contract-valid rate: base `0.8475`, step 100 `0.8200`.
- Geometry reaches 100% contract validity at step 100, while document contract validity falls from `0.4483` to `0.2833`. These format shifts explain the opposing strict-category movements without a corresponding final-answer pair gain.

Problems:
- This is one training run and one selected instrument. Item-paired intervals do not estimate run-to-run RL variance.
- The overall and geometry final-answer intervals lie inside the preregistration’s later +/-0.05 SESOI, but that rule was not registered for this engineering anchor; this is descriptive, not a formal equivalence result.
- Geometry3K training and the held-out geometry renderer share a broad domain, although rows, images, and generator sources are disjoint.
- Human R19 acceptance is unresolved; no claim should use the word certified for this endpoint.

Decision:
- Record the endpoint without interpreting it as improved visual dependence.
- The large Geometry3K test gain and near-zero R19 final-answer pair delta justify the planned four-arm decomposition; they do not substitute for it.
- Use the active gray/noise R19 ablations to measure whether residual step-100 pair accuracy depends on pixels.

Next actions:
- Complete and aggregate step-100 gray/noise R19 conditions.
- Complete the R19 human contact-sheet audit before promoting FlipTrack claims.
- Keep the four-arm pilot and its preregistered RQ2 analyses separate from this engineering calibration.
