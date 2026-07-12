# Anchor Metric Continuity Audit V1

Status:
- `fail` for a continuous 0–100 machine-auditable reward/KL curve.
- The final step-100 checkpoint and its hashes remain valid; this failure concerns metric-log continuity, not checkpoint integrity or optimizer completion.

Evidence:
- Machine audit: `reports/anchor_metric_continuity_audit_v1.json` (`status=fail`), SHA256 `43969dd89a445f6f78b10fae77757acb7cb4bcd129aed3a888a6eb8bc4665176`.
- Surviving metric file: `checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/experiment_log.jsonl`, 21 rows, SHA256 `79503502a03f0cc94a49505f96d12ea00ab27807b5cb73561338e719fbdbe98b`.
- Surviving training rows are exactly steps 81–100; surviving validation rows are steps 80, 90, and 100.
- Missing machine rows are training steps 1–80 and validation steps 0–70 at cadence 10.
- All 20 surviving training rows contain reward, accuracy/format components, KL loss, PPO KL, performance, and response-length fields.
- EasyR1 revision `dd71bbd252694f5f850213eec15795b6b88d9fea` opens `experiment_log.jsonl` and `generations.log` with mode `w` in `verl/utils/logger/logger.py:72` and `:75` every time `FileLogger` initializes.
- The step-80 continuation reused the original checkpoint output directory, so logger initialization deterministically truncated the pre-resume files before appending step-80 validation and steps 81–100.
- The 1.46 GiB parent stdout/stderr log remains at `experiments/runs/anchor_a0_recipe_3b_geo3k_20260709T224852Z/logs/an12.log`, SHA256 `17e29bd4852c9e8c56ca3d8ee127905a92091ac591e8555c108bd9168edf5e76`; it records process/checkpoint activity but does not contain the structured per-step metric payloads needed to reconstruct the missing curve.

Problems:
- `reports/anchor_recipe_report.md` preserves selected step-0 through step-40 values in prose, but those values no longer have their original machine JSONL source and cannot substitute for a continuous audit artifact.
- Steps 50–80 have no surviving structured metric records.
- This prevents calling the run a complete published reproduction with an auditable full reward/KL curve, even though it is a valid 100-step engineering anchor.

Decision:
- Do not infer, interpolate, or copy missing per-step values from narrative reports.
- Keep proposal Stage 0 conditional with respect to published-reproduction tolerance and full metric provenance.
- Add resume-safe FileLogger handling before any future EasyR1 resume: existing logs must be preserved or segmented, never silently truncated.
- Use `scripts/audit_training_metric_continuity.py` on future completed and resumed runs; a pass requires every training step exactly once and every registered validation cadence point.

Next actions:
- Preserve the logger fix as an explicit EasyR1 patch and stamp its patch hash into future run manifests.
- Complete the independent base-versus-step-100 fixed evaluation; report it separately from the incomplete native training curve.
