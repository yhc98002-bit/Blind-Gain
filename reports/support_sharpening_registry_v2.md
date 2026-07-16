# Support-Sharpening Registry V2

Status:
- Candidate selection is frozen and audited from the registered M2 readout.
- M10 inference remains `blocked`: the registration fixes 64 additional samples but does not define a non-overlapping RNG/seed stream relative to the original 16 samples.
- No M10 follow-up inference has been launched.

Evidence:
| Arm | Condition | Candidates | Immutable candidate artifact | SHA256 |
| --- | --- | ---: | --- | --- |
| A1 | real | 47 | `experiments/runs/pilot_4arm_seed1_readout_retry_login_20260716T161914Z/artifacts/support_candidates_a1_real.jsonl` | `2f373e957e23a43cee381515ce31fb30ff7b45997f4b9b74b40105a816ace495` |
| A2 | gray | 8 | `experiments/runs/pilot_4arm_seed1_readout_retry_login_20260716T161914Z/artifacts/support_candidates_a2_gray.jsonl` | `38391899c09c1ad287d7da2c8b8e148b55c096778f492c7a0bed31e4bb9d3cfe` |
| A2b | no-image | 7 | `experiments/runs/pilot_4arm_seed1_readout_retry_login_20260716T161914Z/artifacts/support_candidates_a2b_noimage.jsonl` | `210730fd1deb09cf4ef235ce64e9ac68c075b8a4cd02c38065bf0f9874d10985` |
| A3 | caption | 18 | `experiments/runs/pilot_4arm_seed1_readout_retry_login_20260716T161914Z/artifacts/support_candidates_a3_caption.jsonl` | `6ddf02172b260f25cc335365b8fe04d4c818d6e6d1b3e98e59a2b599552e4775` |

- Source readout: `reports/pilot_4arm_seed1_results_v1.json`, SHA256 `56ce2b6372fd90212bdabe2ce4f78b0b0d8bab7c2e64d72aa8b35d803051c7f4`.
- Every candidate is a registered target-step success with step-0 greedy failure and zero successes in the arm's own 16-sample baseline condition.
- Every candidate pins 64 extra samples, 80 total samples, temperature 1.0, top-p 1.0, 2,048 maximum tokens, canonical-v2, pilot-reward-v1, and the fixed prompt-contract hash.

Problems:
- The candidate schema records the original sampled decoding parameters but not the original sampling seed or a follow-up seed schedule.
- Asking vLLM for `n=64` with the original seed may reproduce the original stream prefix. Such rows would not constitute 64 additional draws.

Decision:
- Do not infer a seed schedule after observing candidate outcomes.
- Keep the four candidate files immutable and preserve the registered 47/8/7/18 counts.
- Continue to use only the registered language `mass sharpening within observed support` and `not observed in the base K-sample set`; no capability-creation claim is permitted.

Blocked question:
- Register either (a) one fixed new seed for an `n=64` follow-up after verifying that the generated stream does not replay the original 16-response prefix, or (b) a fixed list of 64 per-draw seeds, preserving repeated responses as valid independent draws. Which scheme should govern M2 and all later M10 readouts?

Next actions:
- After the seed rule is merged, add it to the machine contract and candidate-run manifest.
- Implement a prefix-overlap adversarial fixture and exact 64-row/sample accounting.
- Run all 80 candidates under their own frozen base condition and publish posterior intervals without causal capability language.
