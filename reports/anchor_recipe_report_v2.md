# P1.1 Anchor Recipe Report V2

Status:
- `complete` as a 100-step Qwen2.5-VL-3B Geometry3K engineering anchor.
- `not complete` as a published reproduction because no published target/tolerance was registered and the native metric file lost steps 1-80 on resume.
- V1 remains unchanged; its step-40 active status and `5bed99b9...` config hash are superseded for the successful run by this version.

Evidence:
- Parent: `experiments/runs/anchor_a0_recipe_3b_geo3k_20260709T224852Z`.
- Completed continuation: `experiments/runs/anchor_a0_recipe_3b_geo3k_resume80_20260711T150633Z`.
- Successful-run base config SHA256: `fdd39cead00fa6932d03c3040d90e76b71599983623b7478d67a309ce4dc3862`; effective parent override hash `45a99272d8403c0ad7b0952b54c9b45e39b4cce20a5d3e4a99b99666a397dcd5`.
- Config/hash reconciliation: `reports/grpo_chat_template_provenance_v1.md`.
- Step-100 checkpoint, merge, and raw-retention evidence: `reports/anchor_step100_oom_recovery_v2.md`.
- Final merged digest: `0653b7a428b19d99b1be9f1efece0cbcaf8156cacb49c44e6238f7c65b28d004`.
- Hash-pinned base/step-100 comparison: `reports/grpo_anchor_step100_prepost_v1.md` and `.json`.
- Native continuity audit: `reports/anchor_metric_continuity_audit_v1.md` and `.json`, status `fail` for a complete 0-100 curve.

Untouched Geometry3K test endpoint (`n=601`):

| Metric | Base | Step 100 | Paired delta | 95% item-bootstrap CI |
| --- | ---: | ---: | ---: | ---: |
| Greedy pilot accuracy | 0.1498 | 0.4359 | +0.2862 | [+0.2446, +0.3278] |
| Greedy canonical accuracy | 0.1747 | 0.4309 | +0.2562 | [+0.2163, +0.2995] |
| Greedy contract valid | 0.4393 | 0.9684 | +0.5291 | [+0.4875, +0.5707] |
| Greedy strict accuracy | 0.0599 | 0.4359 | +0.3760 | [+0.3344, +0.4160] |

Problems:
- The resume-safe logger fix was added after this run. Steps 1-80 of the native structured reward/KL series cannot be reconstructed and are not inferred.
- The successful run’s launch commit predates tracking of its config file. Manifest hashes and the resolved EasyR1 config survive, but this is weaker than the immutable run-local snapshot now required for pilots.
- Geometry3K test is row-held-out but from the same benchmark family as training; external/counterfactual transfer requires separate evaluation.

Decision:
- Use this checkpoint for engineering throughput, endpoint, image-ablation, and external-counterfactual calibration.
- Do not use the favorable endpoint to define a post hoc published-reproduction tolerance.

Next actions:
- Complete the active R19 external counterfactual endpoint.
- After L3 closes, run step-100 gray/noise evaluations under the same locked Geometry3K contract.
