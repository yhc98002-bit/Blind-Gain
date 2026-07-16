# Mini-A5 Plumbing Audit V2

Status:
- `blocked`. The corpus, corrected CP/control grouping, matched configs, and
  immutable advantage artifact are ready. Step-0 sampled reward statistics, a
  registered EasyR1 GPU smoke, catch-trial inputs, and the final merged M6
  registration marker remain required.
- This report authorizes zero optimizer steps and makes no PI gate decision.

Correction to V1:
- Self-review found that the V1 draft overlay assigned the shared pair uid to
  both A and B in `member` mode. That would have normalized the standard
  control over a mixed `2G` group instead of normalizing each source prompt
  over its own `G` rollouts.
- No M6 optimizer step used the V1 overlay. V2 gives only the CP arm a shared
  pair uid. The same-data control receives collision-safe member-specific uids
  and therefore executes ordinary per-prompt GRPO.
- The adversarial fixture measures a maximum absolute advantage error of
  `0.0664496422` under the retired shared-`2G` behavior, so the old behavior
  cannot pass silently.

Evidence:
- Grouping implementation: `src/train/cp_grouping.py`, SHA256
  `6cb21c0a199d049780aa427aad1f51cd995db553433c1d2627431f0c1c1076e0`.
- Exact joint/member rewards: `src/rewards/cp_grpo_reward.py`, SHA256
  `e8dea3e49c03c44a050881fba6e9bec5c8120977659f5a786f2bf4526b6213f0`.
- Reproducible EasyR1 overlay:
  `docs/easyr1_mini_a5_pair_grouping_patch.diff`, SHA256
  `45dc05840e3bf442538baeaf5b0aad94c0452d57900de9e30bf97e2ed61cd153`.
  It applies cleanly after the seven pinned recovery patches in a detached
  worktree; the shared EasyR1 checkout remains unchanged at `dd71bbd`.
- CP config: `configs/train/mini_a5_cp_3b_v1.yaml`, SHA256
  `8d7736f5364bd8bfd5595584aa05917a71306888282eeb2a37682ebf02c325e8`.
- Same-data config: `configs/train/mini_a5_same_data_3b_v1.yaml`, SHA256
  `358e6d7cd40c3748e9e5dbae6715310611fcb295bab107e1138b4071ea0fcd9b`.
- Machine audit: `reports/mini_a5_advantage_equivalence_v1.json`, SHA256
  `a0000403d13255343ff6e039be3619e0caeba4f7278c50c9fac1ad1f5220fc1a`;
  all 28 checks pass.
- Both configs were independently materialized through EasyR1's structured
  `PPOConfig` and `deep_post_init`: `joint/member`, `shuffle=false`, rollout
  batch `400`, `G=5`, TP1, eight GPUs, and `120` steps resolved as expected.

Matched design:
- The configs differ only in four registered arm-specific fields: pair-group
  mode, reward callback, experiment name, and checkpoint path.
- Both use the exact 6,000-row corpus, Qwen2.5-VL-3B, real images, frozen vision
  tower, pilot prompt contract, 2,048 response tokens, `G=5`, identical KL and
  optimizer settings, 400 source prompts per step, and 120 optimizer steps.
- Because 6,000 is divisible by 400, each pass has 15 batches and 120 steps are
  exactly eight complete corpus passes. No deterministic tail is dropped.
- The matched maximum generated-token envelope is `491,520,000` per arm. This
  is a budget ceiling, not a claim that every response reaches 2,048 tokens.

Fixed diagnostics:
- Step-0 sample: `data/mini_a5_step0_sample_v1.jsonl`, 192 pairs, exactly 64
  per template, SHA256
  `254558f2ab274ae95cd900412d56203e7bf6eaa94ddc95c8707641266da643c2`.
- Plumbing validation: `data/mini_a5_plumbing_val_v1.jsonl`, 24 pairs/48 rows,
  SHA256
  `1ed1413f6ca92d67fdd9ea2f8bf9072d9126c97403ffcd9fef0f97d9cbb74475`.
- Selection manifest: `data/mini_a5_fixed_subsets_v1_manifest.json`, SHA256
  `9d3ab38b639c7d9672404fd52c521abf040ca56c0cf0f297860b3a7ccf922b7d`.
  Step-0 and plumbing-validation pair overlap is zero.
- `scripts/run_mini_a5_step0.py` is inference-only and pins the training
  sampling contract (`temperature=1`, `top_p=1`, `n=5`, 2,048 tokens). Its
  launcher records one TP1 replica and `optimizer_steps=0`.

Validation:
- Thirty focused tests pass across pair grouping, reward callbacks, old-UID
  failure detection, patch application, exact corpus masks/identity,
  deterministic subset selection, resume-prefix rejection, and config drift.
- Constant all-zero and all-one reward vectors remain finite zero advantages.
- CP equals an independent GRPO reference over the five unique joint outcomes.
- CP and standard-member paths are exactly equal when their assigned reward
  vectors are held equal (`max_abs_diff=0.0`), isolating reward assignment as
  the intended treatment difference.

Problems:
- Step-0 sampled reward hit rates and variances have not yet been produced.
- The EasyR1 overlay has not yet traversed generation, batch reward, advantage,
  and update code on a real GPU batch.
- Catch-trial stability inputs and the exact registration commit have not yet
  been frozen.

Decision:
- V2 supersedes only the V1 control-grouping behavior; V1 remains in the repo
  as the audit trail.
- Keep M6 fail-closed. Run the no-optimizer step-0 diagnostic next, then freeze
  its statistics and complete the registration/smoke sequence before either
  main arm takes an optimizer step.
