# Registered Mini-A5 Plumbing Smoke V1

Status:
- This document registers two one-step engineering training units: CP and
  matched member-level standard GRPO.
- It authorizes at most one optimizer step per smoke mode after this document
  is committed and a later immutable marker binds that commit at `HEAD`.
- It authorizes zero optimizer steps for either 120-step M6 main arm. A
  separate post-smoke registration marker is mandatory for those runs.
- Merge is sign-off; no signature round or scientific gate decision is
  asserted here.

## Purpose

The smoke must traverse real Qwen2.5-VL-3B generation, paired metadata
propagation, the registered reward callback, GRPO advantage construction, an
actor update, and a model-only checkpoint in the isolated EasyR1 overlay. It
is an engineering audit, not an efficacy measurement.

## Immutable Inputs

| Input | Registered value | SHA256 |
| --- | --- | --- |
| CP config | `configs/train/mini_a5_cp_plumbing_smoke_v1.yaml` | `3dfcd9d8f2a9f654d51a0441166820d7b06ca4cf083bff97f781a065c00e4014` |
| Member config | `configs/train/mini_a5_member_plumbing_smoke_v1.yaml` | `f94f8b4426d11f9eb8f183640bfeeca8c6258801125477f759b46e488ef2e118` |
| Fixed 24-pair plumbing data | `data/mini_a5_plumbing_val_v1.jsonl` | `1ed1413f6ca92d67fdd9ea2f8bf9072d9126c97403ffcd9fef0f97d9cbb74475` |
| Pair grouping implementation | `src/train/cp_grouping.py` | `6cb21c0a199d049780aa427aad1f51cd995db553433c1d2627431f0c1c1076e0` |
| Reward implementation | `src/rewards/cp_grpo_reward.py` | `e8dea3e49c03c44a050881fba6e9bec5c8120977659f5a786f2bf4526b6213f0` |
| EasyR1 overlay | `docs/easyr1_mini_a5_pair_grouping_patch.diff` | `03a46cd00626b58d5a4e56c0c7d450330801ef5b05cb3e11e7243bff15614b86` |
| Step-0 audit | `reports/mini_a5_step0_reward_audit_v1.json` | `debc84d4ae0c22f44f43345fb3510033aea6b8bfee09ed71f6f768bbbe97107f` |
| Catch audit | `reports/mini_a5_catch_audit_v1.json` | `37b9662c1f873c6b6cb7ee04a87a954dadef54ea974933c0e50e5ab8c60c2317` |
| Combined advantage/config audit | `reports/mini_a5_advantage_equivalence_v2.json` | `fc49b672828075e4456f89e47a7a12511bb2f2c1863ac599a20f4e699b99c45a` |

Model: ModelScope `Qwen/Qwen2.5-VL-3B-Instruct`, revision `master`, registered
tree digest
`84c656fb6d6a5f4ef3ccbf47c3880c3a3d22c63eb8736a88fa7a0ddb542e3568`.
EasyR1 base revision:
`dd71bbd252694f5f850213eec15795b6b88d9fea`. The shared base checkout is not
mutated; all eight recovery patches are applied in
`artifacts/repos/EasyR1-mini-a5`.

## Matched Smoke Design

- One node, all eight GPUs, TP1, eight colocated workers; no cross-node
  placement or rollout/training disaggregation.
- One optimizer step, 16 source prompts = eight adjacent A/B pairs, `G=5`,
  temperature 1, top-p 1, max response 2,048, real images, frozen vision
  tower, KL as loss, and no online filtering.
- CP uses `pair_group_mode=joint` and exact product reward
  `acc(a_i) * acc(b_i)`, broadcast to both members before normalization over
  the five unique pair outcomes.
- Member uses `pair_group_mode=member`, member accuracy, and ordinary
  per-source-prompt GRPO over five rollouts.
- The configs differ only in pair-group mode, reward callback, experiment
  name, and isolated checkpoint path.
- `save_model_only=true` is permitted because neither smoke is a resume source.
  Smoke checkpoints are retention-expired after their independent audit and a
  pre-deletion size/hash inventory.

Exact launch commands:

```bash
bash scripts/launch_mini_a5_plumbing_smoke.sh cp <node> 0,1,2,3,4,5,6,7
bash scripts/launch_mini_a5_plumbing_smoke.sh member <node> 0,1,2,3,4,5,6,7
```

The modes run sequentially on one fully available node. The launcher refuses
dirty registered inputs, a non-ancestor registration commit, occupied GPUs,
checkpoint overwrite, EasyR1 revision/patch drift, or shared-storage guard
failure.

## Mechanical Acceptance Conditions

All conditions are conjunctive:

1. Both immutable run manifests finish with exit code 0 and exactly one
   optimizer step.
2. Effective configs, data, source, model, registration, placement, and
   EasyR1 hashes match this registration and its later marker.
3. The CP log contains one structured
   `BLIND_GAINS_CP_ADVANTAGE_AUDIT` event for the training batch with 80 rows,
   eight pair groups, rollout counts `[5]`, and finite advantages.
4. The member run does not enter the joint-advantage branch.
5. Each file log contains finite expected reward metrics and finite actor
   update metrics at step 1; no NaN, traceback, OOM, or fatal NCCL signature is
   present.
6. Each model-only `global_step_1` checkpoint exists and its files are hashed
   before retention cleanup.
7. An independent versioned report records every check. A failed smoke does
   not authorize a retry or either main arm; a fix requires a new registered
   version with an adversarial fixture.

No model performance endpoint is read or interpreted from this smoke. The
step-0 reward statistics were frozen before this registration and no example
is selected, removed, regenerated, or reweighted from smoke output.
