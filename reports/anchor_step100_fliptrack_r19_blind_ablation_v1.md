# Anchor Step-100 FlipTrack R19 Blind Ablation V1

Status:
- Complete as an engineering-anchor real-versus-gray endpoint on the R19-selected instrument. This is not a four-arm pilot result, a PI gate, or a certified FlipTrack claim.
- The machine summary is `reports/anchor_step100_fliptrack_r19_blind_ablation_v1.json`; all 11 enumerated integrity checks are true.
- The frozen R19 human contact-sheet audit is still pending. R20 independently downgraded geometry and chart to R19-selected under the frozen generator-level criteria.

Evidence:
- Step-100 gray evaluation: `experiments/runs/fliptrack_v02r19_anchor_step100_gray_an12_20260712T091721Z`; one TP1 replica on an12 GPU5, greedy decoding, 32 output tokens, exactly 1,200 pairs.
- Step-100 gray canonical-v2 aggregate: `experiments/runs/fliptrack_aggregate_anchor_step100_gray_20260712T094005Z`, metrics SHA256 `20168087af7d6a4ec3cbdd057a7442b12feb997176b7ce0b81ecd9ff7bde0601`.
- Base gray canonical-v2 aggregate: `experiments/runs/fliptrack_aggregate_base3b_gray_canonicalv2_20260712T094005Z`, metrics SHA256 `b4f12b695445645f8813e7eb8ac0444b7e1912fbfe147081fd94fbeed1eca40e`.
- Paired base-gray comparison: `experiments/runs/fliptrack_compare_base_vs_anchor_gray_r19_v1_20260712T094021Z`.
- Paired step-100 gray-versus-real comparison: `experiments/runs/fliptrack_compare_anchor_gray_vs_real_r19_v1_20260712T094021Z`.
- Intervals use 2,000 paired-item bootstrap draws. They quantify evaluation-item uncertainty, not run-to-run RL variance.

Endpoint table:

| Endpoint | Pair accuracy | Strict pair accuracy | Member accuracy | Collapse Rate | Contract valid |
| --- | ---: | ---: | ---: | ---: | ---: |
| Base 3B, gray | 0.0000 | 0.0000 | 0.0854 | 1.0000 | 1.0000 |
| Step 100, gray | 0.0000 | 0.0000 | 0.0417 | 1.0000 | 1.0000 |
| Step 100, real | 0.5633 | 0.3700 | 0.7192 | 0.0833 | 0.8200 |

Paired contrasts:

| Contrast | Pair delta | 95% CI | Strict-pair delta | 95% CI |
| --- | ---: | ---: | ---: | ---: |
| Base gray to step-100 gray | 0.0000 | [0.0000, 0.0000] | 0.0000 | [0.0000, 0.0000] |
| Step-100 gray to step-100 real | +0.5633 | [+0.5358, +0.5917] | +0.3700 | [+0.3433, +0.3967] |

Real-minus-gray final-answer pair deltas by template:

| R19 scope | n | Delta | 95% CI |
| --- | ---: | ---: | ---: |
| Geometry: coordinate register | 600 | +0.4800 | [+0.4400, +0.5200] |
| Document: header-cued table | 300 | +0.8567 | [+0.8167, +0.8933] |
| Chart: starred series | 300 | +0.4367 | [+0.3833, +0.4933] |

Problems:
- This comparison contains one trained checkpoint and one selected instrument. It cannot estimate training-run variance or establish a general training effect.
- Gray input is a zero-visual-bit ablation for the queried fact, but it also changes the model's input distribution. The no-image and caption arms remain necessary.
- The base and step-100 gray endpoints both have zero paired successes, so the zero-width empirical paired interval is descriptive floor saturation, not proof that their latent behavior is identical.
- The launcher used implicit deterministic seed defaults for the completed real/gray jobs. The launcher is now hardened to stamp `seed`, `noise_seed`, and `model_revision` and to publish predictions and metrics by atomic rename.
- Human R19 acceptance is unresolved; no report should call this result certified.

Decision:
- Preserve this as engineering calibration evidence that the step-100 real-image score depends on available pixels at evaluation time.
- Do not infer from it whether GRPO increased visual dependence. The matched four-arm pilot and preregistered checkpoint deltas are required for that claim.
- Complete the active step-100 noise endpoint as a second blind-input check.

Next actions:
- Finish and aggregate the noise endpoint using the same 1,200 pair identities.
- Close L3 reward-plumbing audit and checkpoint cleanup before launching guarded Geometry3K blind evaluations.
- Keep L12 and all pilot optimizer steps blocked until the human R19 audit and both PI signatures are recorded.
