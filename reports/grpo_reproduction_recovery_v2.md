# GRPO Reproduction Recovery V2

Status:
- `complete` as a 100-step Qwen2.5-VL-3B Geometry3K engineering anchor.
- `not complete` as a published reproduction: no published target/tolerance is registered, and the continuous native reward/KL history is incomplete.
- The predecessor `reports/grpo_reproduction_recovery.md` remains unchanged and records the earlier 30-step recovery state.

Evidence:
- Parent run: `experiments/runs/anchor_a0_recipe_3b_geo3k_20260709T224852Z`.
- Verified continuation from step 80: `experiments/runs/anchor_a0_recipe_3b_geo3k_resume80_20260711T150633Z`; `status=complete`, `exit_code=0`.
- Final checkpoint and retention audit: `reports/anchor_step100_oom_recovery_v2.md`.
- Final merged model: `checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_100/actor/huggingface`; merged digest `0653b7a428b19d99b1be9f1efece0cbcaf8156cacb49c44e6238f7c65b28d004`.
- Exact recipe diff: `reports/anchor_a0_recipe_config_diff.md` and `.json`; machine diff SHA256 `3fcb0ce5c96549127bf1ff83ef4353821c2753dda5240e478886e73194afd475`.
- Locked endpoint evaluation: `reports/grpo_anchor_step100_prepost_v1.md` and `.json`; all manifest, output, item-identity, prompt, data, decoding, and scoring checks pass.

Untouched Geometry3K test endpoint (`n=601`):

| Metric | Base | Step 100 | Paired delta | 95% item-bootstrap CI |
| --- | ---: | ---: | ---: | ---: |
| Greedy pilot accuracy | 0.1498 | 0.4359 | +0.2862 | [+0.2446, +0.3278] |
| Greedy canonical accuracy | 0.1747 | 0.4309 | +0.2562 | [+0.2163, +0.2995] |
| Greedy contract valid | 0.4393 | 0.9684 | +0.5291 | [+0.4875, +0.5707] |
| Greedy strict accuracy | 0.0599 | 0.4359 | +0.3760 | [+0.3344, +0.4160] |

Problems:
- `reports/anchor_metric_continuity_audit_v1.json` is `fail`: the structured file retains training steps 81-100 and validation points 80/90/100, but not steps 1-80 or validation 0-70.
- EasyR1 opened its file logger in truncate mode when the run resumed. The explicit resume-safe logger patch now prevents recurrence, but it cannot reconstruct old metrics.
- The run has documented recipe deviations in validation batch size/decoding/cadence, SDPA padding mode, GPU count, save cadence, and finite 100-step budget.
- Geometry3K test is held out by row but belongs to the same benchmark family as training; this endpoint is not evidence of external transfer.

Decision:
- Use the checkpoint as an engineering baseline and throughput anchor.
- Do not label it a published reproduction or define a tolerance post hoc from its favorable endpoint.
- Preserve the failed continuity audit beside the valid checkpoint and endpoint artifacts.

Next actions:
- Complete step-100 gray/noise image ablations after the corrected L3 smoke.
- Keep proposal Stage 0 conditional until a published target and tolerance are defined or the work is explicitly framed only as an engineering anchor.
