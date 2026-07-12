# Geometry3K Anchor Step-100 Pre/Post Evaluation V1

Status:
- Complete as a hash-pinned engineering-anchor evaluation; this is not a published-reproduction or PI gate verdict.
- Machine artifact: `reports/grpo_anchor_step100_prepost_v1.json`.

Evidence:
- Base run: `experiments/runs/blind_solvability_v2_guarded_rescore_geo3k_filtered_v2_retry_real_login_20260712T050905Z`.
- Step-100 run: `experiments/runs/blind_solvability_v2_guarded_rescore_anchor_step100_geo3k_real_login_20260712T082107Z`.
- Base/step-100 output SHA256: `021da42f00eab94bc431ed0e7924110c237f77454b23ded5a8f1064c48fd6aa3` / `22d93ad3f5510c49d9755d82dd0cdb148ea0818f75db77e7363b757b8ed0d8c4`.
- Every manifest lock, output hash, item identity, problem, answer, image hash, parser, prompt, and decoding check passed.
- Intervals are 2,000-draw paired item-bootstrap 95% intervals; they do not estimate run-to-run RL variance.

Test split (`n=601`):

| Metric | Base | Step 100 | Paired delta | 95% CI |
| --- | ---: | ---: | ---: | ---: |
| Greedy pilot accuracy | 0.1498 | 0.4359 | +0.2862 | [+0.2446, +0.3278] |
| Greedy canonical accuracy | 0.1747 | 0.4309 | +0.2562 | [+0.2163, +0.2995] |
| Greedy contract valid | 0.4393 | 0.9684 | +0.5291 | [+0.4875, +0.5707] |
| Greedy strict accuracy | 0.0599 | 0.4359 | +0.3760 | [+0.3344, +0.4160] |
| Sampled pilot accuracy | 0.0989 | 0.3990 | +0.3001 | [+0.2757, +0.3248] |
| Sampled training reward | 0.2343 | 0.6989 | +0.4646 | [+0.4502, +0.4778] |
| Sampled format reward | 0.3698 | 0.9989 | +0.6291 | [+0.6146, +0.6430] |

Pilot-accuracy transitions: `{'both_correct': 74, 'before_only': 16, 'after_only': 188, 'neither_correct': 323}`.

Train split (`n=1288`):

| Metric | Base | Step 100 | Paired delta | 95% CI |
| --- | ---: | ---: | ---: | ---: |
| Greedy pilot accuracy | 0.1553 | 0.4216 | +0.2663 | [+0.2399, +0.2927] |
| Greedy canonical accuracy | 0.1638 | 0.4169 | +0.2531 | [+0.2267, +0.2803] |
| Greedy contract valid | 0.4635 | 0.9744 | +0.5109 | [+0.4837, +0.5388] |
| Greedy strict accuracy | 0.0528 | 0.4216 | +0.3688 | [+0.3408, +0.3960] |
| Sampled pilot accuracy | 0.0872 | 0.3926 | +0.3054 | [+0.2882, +0.3223] |
| Sampled training reward | 0.2356 | 0.6958 | +0.4603 | [+0.4500, +0.4707] |
| Sampled format reward | 0.3839 | 0.9990 | +0.6151 | [+0.6050, +0.6256] |

Pilot-accuracy transitions: `{'both_correct': 174, 'before_only': 26, 'after_only': 369, 'neither_correct': 719}`.

Problems:
- The checkpoint was trained with the anchor's native EasyR1 `r1v` reward. Pilot-reward-v1 and canonical-v2 are used here only for a locked comparison.
- EasyR1 truncated the structured metric file when the anchor resumed; steps 1-80 of the native reward/KL curve cannot be reconstructed from that file.
- Geometry3K is both the anchor training source and evaluation family. The untouched test split avoids direct row reuse but does not establish external transfer.

Decision:
- Treat this as the missing deterministic pre/post engineering-anchor evaluation, not as a published-recipe reproduction claim.
- Use gray/noise step-100 evaluations to test whether the observed post-training gain still depends on image information.

Next actions:
- Run step-100 gray and noise ablations after the corrected L3 reward smoke closes its fail-closed dependency.
- Keep the four-arm pilot launch blocked until the final L12 preregistration has the required human audit and both PI approvals.
