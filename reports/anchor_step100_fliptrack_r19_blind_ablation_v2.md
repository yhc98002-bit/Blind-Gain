# Anchor Step-100 FlipTrack R19 Blind Ablation V2

Status:
- Complete as an engineering-anchor real-versus-gray/noise endpoint on the R19-selected instrument. This is not a four-arm pilot result, a PI gate, or a certified FlipTrack claim.
- V1 is preserved. V2 adds the completed noise condition and retains the same fixed real/gray response sets.
- Machine summary: `reports/anchor_step100_fliptrack_r19_blind_ablation_v2.json`; all 18 enumerated integrity checks are true.
- The frozen R19 human contact-sheet audit remains pending. R20 downgraded geometry and chart to R19-selected under frozen generator-level criteria.

Evidence:
- All endpoint evaluations use the same 1,200 R19 pair identities, Qwen2.5-VL-3B architecture, answer-tags-v1 contract, canonical-v2 scoring, greedy decoding, and 32 output tokens.
- Step-100 real, gray, and noise use the same merged checkpoint SHA256 `0653b7a428b19d99b1be9f1efece0cbcaf8156cacb49c44e6238f7c65b28d004`.
- Noise evaluation: `experiments/runs/fliptrack_v02r19_anchor_step100_noise_an12_20260712T094200Z`; one TP1 replica on an12 GPU5, exactly 1,200 pairs.
- Step-100 noise aggregate: `experiments/runs/fliptrack_aggregate_anchor_step100_noise_20260712T100845Z`, metrics SHA256 `db8c0787a92ed49455189b9f3ae96aea843a162e55d6b3a650b6861d655d309d`.
- Base noise aggregate: `experiments/runs/fliptrack_aggregate_base3b_noise_canonicalv2_20260712T100845Z`, metrics SHA256 `c2f837e85c17ed16b3fd333af91d054b64c550506ee4fc150db410411a81a154`.
- Paired noise comparisons: `experiments/runs/fliptrack_compare_base_vs_anchor_noise_r19_v1_20260712T100845Z` and `experiments/runs/fliptrack_compare_anchor_noise_vs_real_r19_v1_20260712T100845Z`.
- Intervals use 2,000 paired-item bootstrap draws. They quantify item uncertainty, not run-to-run RL variance.

Endpoint table:

| Endpoint | Pair accuracy | Strict pair accuracy | Member accuracy | Collapse Rate | Contract valid |
| --- | ---: | ---: | ---: | ---: | ---: |
| Base 3B, gray | 0.0000 | 0.0000 | 0.0854 | 1.0000 | 1.0000 |
| Step 100, gray | 0.0000 | 0.0000 | 0.0417 | 1.0000 | 1.0000 |
| Base 3B, noise | 0.0000 | 0.0000 | 0.0900 | 1.0000 | 1.0000 |
| Step 100, noise | 0.0000 | 0.0000 | 0.0163 | 1.0000 | 1.0000 |
| Step 100, real | 0.5633 | 0.3700 | 0.7192 | 0.0833 | 0.8200 |

Paired contrasts:

| Contrast | Pair delta | 95% CI | Strict-pair delta | 95% CI |
| --- | ---: | ---: | ---: | ---: |
| Base gray to step-100 gray | 0.0000 | [0.0000, 0.0000] | 0.0000 | [0.0000, 0.0000] |
| Base noise to step-100 noise | 0.0000 | [0.0000, 0.0000] | 0.0000 | [0.0000, 0.0000] |
| Step-100 gray to step-100 real | +0.5633 | [+0.5358, +0.5917] | +0.3700 | [+0.3433, +0.3967] |
| Step-100 noise to step-100 real | +0.5633 | [+0.5358, +0.5917] | +0.3700 | [+0.3433, +0.3967] |

Problems:
- The two blind conditions saturate the pair-accuracy floor. Their zero-width empirical intervals do not prove identical latent policies or provide a useful between-model discrimination test.
- This comparison contains one trained checkpoint and one selected instrument. It cannot estimate training-run variance or establish a general training effect.
- Gray/noise inputs remove the queried visual fact but also induce distribution shift. The matched no-image and caption training arms remain necessary.
- The noise run used the registered deterministic default seed `0`; this was made explicit in its manifest after launch without changing the running command. The hardened launcher now stamps seed/model provenance before launch.
- Human R19 acceptance is unresolved; no report should call this result certified.

Decision:
- Preserve the real-versus-blind gap as engineering calibration that the step-100 R19 endpoint depends on pixels available at evaluation time.
- Do not infer that GRPO increased visual dependence: the step-100 real endpoint itself was unchanged from base within paired uncertainty, and the matched four-arm pilot has not launched.
- Use the newly launched guarded Geometry3K gray/noise evaluations to characterize checkpoint behavior under the exact pilot contract.

Next actions:
- Complete the guarded step-100 Geometry3K gray/noise evaluations on an12 GPUs6/7.
- Complete the five active ViRL39K conditions and L10 audit.
- Keep L12 and every pilot optimizer step blocked until the human R19 audit and both PI signatures are recorded.
