# Anchor Step-100 FlipTrack R19 Endpoint V1

Status:
- `fail` for publication as a fully matched table. The paired final-answer comparison recomputes both runs with canonical-v2, but the historical base aggregate predates parser/contract stamping and its strict-format columns are not matched to the step-100 aggregate.
- The fixed predictions are being reaggregated under canonical-v2; V2 will supersede this failed table without deleting it.
- The frozen R19 human contact-sheet audit remains pending. R20 downgraded geometry and chart to R19-selected under the pre-frozen generator criteria.
- Machine summary: `reports/anchor_step100_fliptrack_r19_v1.json`; two aggregate-contract checks are false.

Evidence:
- Base evaluation: `experiments/runs/fliptrack_v02r19_packaged_qwen25vl3b_real_an29_20260710T142716Z`.
- Step-100 evaluation: `experiments/runs/fliptrack_v02r19_anchor_step100_real_an12_20260712T085144Z`; one TP1 replica on an12 GPU5, exactly 1,200 pairs.
- Step-100 aggregate: `experiments/runs/fliptrack_aggregate_anchor_step100_real_20260712T091312Z`; pair accuracy 95% item-bootstrap CI `[0.5350, 0.5917]`.
- Paired comparison: `experiments/runs/fliptrack_compare_anchor_step100_r19_20260712T092004Z`, comparison SHA256 `4fd73e64a61abfa356f527773ab27bce0cd59449039f1c656423cf839b10b87e`.
- Both endpoints use real images, greedy decoding, 32 output tokens, the same R19 pairs, canonical-v2, and answer-tags-v1.

Results:

| R19 scope | n | Base pair acc. | Step 100 pair acc. | Paired delta | McNemar p |
| --- | ---: | ---: | ---: | ---: | ---: |
| Overall | 1,200 | 0.5617 | 0.5633 | +0.0017 | 0.9362 |
| Geometry: coordinate register | 600 | 0.4717 | 0.4800 | +0.0083 | 0.6445 |
| Document: header-cued table | 300 | 0.8667 | 0.8567 | -0.0100 | 0.6476 |
| Chart: starred series | 300 | 0.4367 | 0.4367 | 0.0000 | 1.0000 |

Untrusted V1 secondary diagnostics:
- Do not compare V1 strict-format or Collapse Rate values across endpoints. The old base aggregate has no parser/contract stamps, while the step-100 aggregate is canonical-v2/answer-tags-v1.
- The point estimates above come from `compare_fliptrack_runs.py`, which recomputes final-answer pair correctness for both fixed response sets with the current scorer; V2 will independently reaggregate both endpoints for all secondary columns.

Problems:
- This is one training run and one selected instrument. McNemar tests paired items but do not estimate run-to-run RL variance.
- The base evaluation prompt text is byte-equivalent to answer-tags-v1, but its stored scoring rows and aggregate predate canonical-v2 metadata.
- The result is not a formal equivalence claim: no paired delta confidence interval was registered for this engineering anchor.
- Geometry3K training and the held-out geometry renderer share a broad domain, although rows, images, and generator sources are disjoint.
- Human R19 acceptance is unresolved; no claim should use the word certified for this endpoint.

Decision:
- Do not publish V1 as a matched endpoint table.
- Preserve its paired final-answer output as debugging evidence while requiring the canonical-v2 base reaggregate for V2.
- Use the active gray/noise R19 ablations to determine whether the step-100 policy’s residual pair accuracy depends on pixels.
- Keep the four-arm pilot and its preregistered RQ2 analyses separate from this engineering calibration.

Next actions:
- Complete and aggregate the step-100 gray/noise R19 conditions.
- Complete the R19 human contact-sheet audit before promoting FlipTrack claims.
