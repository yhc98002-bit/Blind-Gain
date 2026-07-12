# Deterministic Evaluation Audit V2

Status:
- `pass` for the implemented Geometry3K base-versus-step-100 engineering-anchor comparison and the existing FlipTrack baseline path.
- This is an implementation audit, not a published-reproduction or PI gate verdict.
- The predecessor `reports/deterministic_eval_audit.md` remains unchanged and is superseded by this version.

Evidence:
- Geometry3K machine comparison: `reports/grpo_anchor_step100_prepost_v1.json`, SHA256 `8ecc3a41f75bc335c73ac06a8762dce3c48c3e2d3c425bbcf9988dd142314435`; machine status `pass` and all nine sub-checks true.
- Geometry3K report: `reports/grpo_anchor_step100_prepost_v1.md`, SHA256 `d75f362a981d2774c8ee16b89c36eddfdd5263209a301b5c03eac1fcc90ea03e`.
- Both checkpoints use the same prompt contract, prompt hash, data/filter hashes, parser and reward versions, greedy decoding (`temperature=0`, `top_p=1`, `n=1`), sampled decoding, maximum-token limit, and item identities.
- The comparison independently rehashes both per-item outputs and verifies every problem, answer, image hash, split, and row index before computing paired statistics.
- Geometry3K test rows: `601`; base greedy pilot accuracy `0.1498`; step-100 `0.4359`; paired delta `+0.2862`, 95% item-bootstrap CI `[+0.2446, +0.3278]`.
- FlipTrack evaluator: `scripts/eval_qwen_vl_fliptrack.py`; aggregator: `scripts/aggregate_fliptrack_eval.py`; metric implementation: `src/eval/fliptrack_metrics.py`.
- Adversarial fixtures: `tests/test_compare_anchor_prepost.py` rejects content drift under an unchanged row identity and rejects output bytes that no longer match the manifest hash.

Problems:
- The step-100 checkpoint was optimized with native EasyR1 `r1v`; pilot-reward-v1 and canonical-v2 are locked evaluation contracts, not retrospective claims about the optimized reward.
- The anchor resume truncated structured metrics for steps 1-80. The deterministic endpoint comparison is valid, but it does not restore the missing continuous native reward/KL curve.
- The paired interval covers item uncertainty only, not run-to-run RL variance.

Decision:
- The missing deterministic base-versus-trained endpoint audit is closed for the engineering anchor.
- Keep the published-reproduction claim open because endpoint correctness does not supply a published target, tolerance, or the missing native metric history.

Next actions:
- Evaluate the same step-100 checkpoint under gray and noise image conditions after L3 closes.
- Use the four-arm preregistered evaluation contract for pilot checkpoints; do not infer pilot outcomes from the engineering anchor.
