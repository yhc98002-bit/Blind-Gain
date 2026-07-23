# Registered Mini-A5 Main Comparison V1

## Status and scope

This document is the post-smoke main-run registration required by
`docs/registered_mini_a5_smoke_v1.md` ("A separate post-smoke registration marker is
mandatory for those runs"). It authorizes exactly two 120-step M6 training arms —
CP-GRPO and matched same-data member-level standard GRPO — after a later immutable
marker (`reports/mini_a5_main_registration_marker_v1.json`) binds this document's
commit as an ancestor of `HEAD`. Merge is sign-off under the M4 ruling
(`docs/MAIN_PHASE_RULING_20260716.md`); M6 carries no additional signature round.

It changes no frozen design value: both training configurations, the corpus, the
catch set, the reward implementations, and the EasyR1 overlay are registered
byte-identical to the versions validated by the completed plumbing smokes and their
combined audit.

## Immutable inputs

| Input | Registered value | SHA256 |
| --- | --- | --- |
| CP main config | `configs/train/mini_a5_cp_3b_v1.yaml` | `8d7736f5364bd8bfd5595584aa05917a71306888282eeb2a37682ebf02c325e8` |
| Member main config | `configs/train/mini_a5_same_data_3b_v1.yaml` | `358e6d7cd40c3748e9e5dbae6715310611fcb295bab107e1138b4071ea0fcd9b` |
| Frozen training corpus | `data/mini_a5_train_v1/train.parquet` | `0b0f0965987d1c340c3ebd78da742c9d99b319b61524b5cb42960519fd9c9b28` |
| Fixed subsets manifest | `data/mini_a5_fixed_subsets_v1_manifest.json` | `9d3ab38b639c7d9672404fd52c521abf040ca56c0cf0f297860b3a7ccf922b7d` |
| Monitoring val set | `data/mini_a5_plumbing_val_v1.jsonl` | `1ed1413f6ca92d67fdd9ea2f8bf9072d9126c97403ffcd9fef0f97d9cbb74475` |
| Pair grouping implementation | `src/train/cp_grouping.py` | `6cb21c0a199d049780aa427aad1f51cd995db553433c1d2627431f0c1c1076e0` |
| Reward implementation | `src/rewards/cp_grpo_reward.py` | `e8dea3e49c03c44a050881fba6e9bec5c8120977659f5a786f2bf4526b6213f0` |
| EasyR1 overlay | `docs/easyr1_mini_a5_pair_grouping_patch.diff` | `03a46cd00626b58d5a4e56c0c7d450330801ef5b05cb3e11e7243bff15614b86` |
| Step-0 reward audit | `reports/mini_a5_step0_reward_audit_v1.json` | `debc84d4ae0c22f44f43345fb3510033aea6b8bfee09ed71f6f768bbbe97107f` |
| Catch audit | `reports/mini_a5_catch_audit_v1.json` | `37b9662c1f873c6b6cb7ee04a87a954dadef54ea974933c0e50e5ab8c60c2317` |
| Advantage/config audit | `reports/mini_a5_advantage_equivalence_v2.json` | `fc49b672828075e4456f89e47a7a12511bb2f2c1863ac599a20f4e699b99c45a` |
| Combined smoke audit | `reports/mini_a5_plumbing_smoke_audit_v1.json` | `f3d4d6337ed05e616ba3ca342c7caac02a795dc2dbda60d4bafde45ca69fe884` |

Model: ModelScope `Qwen/Qwen2.5-VL-3B-Instruct`, revision `master`, registered tree
digest `84c656fb6d6a5f4ef3ccbf47c3880c3a3d22c63eb8736a88fa7a0ddb542e3568`.
EasyR1 base revision `dd71bbd252694f5f850213eec15795b6b88d9fea`; all patches are
applied only in the isolated worktree `artifacts/repos/EasyR1-mini-a5`, whose diff
SHA256 must match the marker at launch time.

## Registered main design (fixed by the two configurations)

- Each arm: one node, all eight GPUs, TP1, eight colocated workers, `nnodes=1`;
  no cross-node placement and no rollout/training disaggregation.
- `max_steps=120`, seed `20260716`, frozen vision tower, KL as loss, no online
  filtering, temperature 1, top-p 1.
- The two configurations differ only in `pair_group_mode` (`joint` vs `member`),
  the reward callback (`compute_score` vs `compute_member_score`), the experiment
  name, and the isolated checkpoint path. This matched-difference property is
  machine-checked by the advantage/config audit and re-verified at launch.
- CP reward: exact product `acc(a_i) * acc(b_i)` broadcast to both members before
  normalization over pair outcomes. Member reward: member accuracy with ordinary
  per-source-prompt GRPO. Both use the pilot extraction/mathruler precedence.
- The training corpus is the frozen counterfactual training-only corpus; its
  disjointness from every registered evaluation template and the catch set's
  integrity were audited in `reports/mini_a5_corpus_audit_v1.json` and
  `reports/mini_a5_catch_audit_v1.json`. Step-0 reward hit rates and variance were
  frozen before the smoke registration in
  `reports/mini_a5_step0_reward_audit_v1.json`.
- The product reward is registered as-is. Any shaped-reward substitution requires a
  separately documented feasibility failure and a new registered version; none is
  authorized here.

## Execution and placement

Exact launch commands (arms run on a fully free eight-GPU node; sequential on one
node, or concurrent only on two distinct nodes):

```bash
bash scripts/launch_mini_a5_main.sh cp <node> 0,1,2,3,4,5,6,7
bash scripts/launch_mini_a5_main.sh member <node> 0,1,2,3,4,5,6,7
```

The launcher refuses: dirty registered inputs; a marker whose registration commit
is absent or not an ancestor of `HEAD`; hash drift in any registered input; EasyR1
revision or patch-inventory drift; any GPU on the target node with ≥1 GiB
allocated; any other `verl.trainer.main` process on the target node; checkpoint
overwrite; and shared-storage guard failure.

Storage: with `save_freq=20`, `save_limit=-1`, `save_model_only=false`, each arm
writes six full raw checkpoints (approximately 50 GiB each). A checkpoint
merge/relocation watcher must accompany each arm so raw state is merged, archived,
and pruned behind the trainer; launch is refused unless the storage guard verifies
headroom for at least two concurrent raw checkpoints plus merge output.

## Registered endpoints (read only after both arms complete)

Primary: held-out FlipTrack counterfactual templates (never present in the
training corpus, per the corpus audit) — CP-GRPO versus same-data standard GRPO at
step 120, pair-level success with paired bootstrap.

Secondary: catch-trial stability; the registered task benchmark; free-generation
versus candidate-ranking diagnostics under the existing registered ranking
instrument.

No value from either arm is opened before both arms and their endpoint
evaluations are complete; partial readouts are prohibited.

## Acceptance conditions

1. Both run manifests finish with exit code 0 and exactly 120 optimizer steps.
2. Effective configs, data, model, registration, placement, and EasyR1 hashes
   match this registration and its marker.
3. CP training logs contain structured `BLIND_GAINS_CP_ADVANTAGE_AUDIT` events
   with pair-consistent grouping; the member run never enters the joint branch.
4. No NaN, traceback, OOM, or fatal NCCL signature in either log.
5. Every saved checkpoint is hash-inventoried before any retention action.
6. An independent versioned report records every check before any endpoint value
   is read.

A failed arm does not authorize an ad-hoc retry; a fix requires a new registered
version with an adversarial fixture.
