# P1.1 Anchor Recipe Report

Status:
- The canonical recipe-scale anchor is healthy through step 40/100 and remains active on `an12` GPUs 0-3.
- P1.1 is incomplete until the run reaches step 100 or terminates with a diagnosed failure.
- Step-0 through step-40 full-split greedy validation points at 10-step cadence are preserved.

Evidence:
- Active run: `experiments/runs/anchor_a0_recipe_3b_geo3k_20260709T224852Z`.
- Metrics: `checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/experiment_log.jsonl`.
- Config: `configs/train/anchor_a0_recipe_3b_geo3k.yaml`.
- Human-readable diff: `reports/anchor_a0_recipe_config_diff.md`; machine diff: `reports/anchor_a0_recipe_config_diff.json`.
- Node/GPU allocation: `an12`, GPUs `0,1,2,3`.
- Config hash: `5bed99b9ec8204e05f77c237d217ef3b6c509c2263c9e225599bf217889fed39`.
- Data hash: `f86c700640e1f72dea6ac8acb3004e74e38e1ffb262f36a994d54114d6d6cc56`.
- Step-20 merged checkpoint: `checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_20/actor/huggingface`.
- Step-20 merge run: `experiments/runs/easyr1_checkpoint_merge_anchor_a0_step20_an12_20260710T073637Z`.
- Raw step-20 FSDP/optimizer state was checksum-verified and relocated under login-node `/tmp/blindgain_checkpoint_archive`; the merged Hugging Face checkpoint remains on shared storage.
- Step-40 merged checkpoint: `checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_40/actor/huggingface`.
- Step-40 merge run: `experiments/runs/easyr1_checkpoint_merge_anchor_a0_step40_an12_20260710T161553Z`.
- Step-40 merged verification: `experiments/runs/easyr1_checkpoint_merge_anchor_a0_step40_an12_20260710T161553Z/merged_checkpoint_verification.json`; all 825 indexed tensors matched their safetensors files and every one of the 14 files has a recorded SHA256.
- Raw step-40 state was independently checksum-verified and relocated to `/tmp/blindgain_checkpoint_archive/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_40/actor`; no raw model/optimizer shard remains on shared storage.

Validation curve (full 601-item Geometry3K test split, greedy):

| Step | Overall reward | Format reward | Accuracy reward | Mean response length | Clip ratio |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.0774 | 0.1015 | 0.0532 | 378.64 | 0.0416 |
| 10 | 0.6231 | 0.9750 | 0.2712 | 292.44 | 0.0256 |
| 20 | 0.6398 | 0.9750 | 0.3045 | 312.08 | 0.0251 |
| 30 | 0.6581 | 0.9684 | 0.3478 | 340.18 | 0.0312 |
| 40 | 0.6697 | 0.9784 | 0.3611 | 322.38 | 0.0214 |

Training checkpoints:

| Step | Overall reward | Format reward | Accuracy reward | KL loss | PPO KL | Seconds/step |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 0.0311 | 0.0379 | 0.0242 | 0.00058 | 0.000122 | 1552.9 |
| 10 | 0.5850 | 0.9938 | 0.1762 | 0.02812 | 0.000031 | 1782.0 |
| 20 | 0.6301 | 0.9988 | 0.2613 | 0.03471 | 0.000098 | 1824.4 |
| 30 | 0.6441 | 0.9980 | 0.2902 | 0.02773 | 0.000019 | 1817.4 |
| 40 | 0.6615 | 0.9973 | 0.3258 | 0.03029 | 0.000050 | 1839.7 |

Locked recipe fields:
- `rollout_batch_size: 512`; actor global batch size `128`; rollout group size `5`.
- Maximum response length `2048`; vision tower unfrozen, matching the reference recipe.
- Validation before training and every 10 steps with `{temperature: 0.0, top_p: 1.0, n: 1}`.
- Checkpoints every 20 steps; all merged checkpoints are retained on shared storage.

Known deviations and failed attempts:
- Earlier immutable attempts are preserved under `experiments/runs/anchor_a0_recipe_3b_geo3k_*`; they exposed duplicate launch contention, an overlong Ray socket path, an SDPA padding-free dependency, and an oversized validation gather.
- The active launcher uses a hashed short Ray path, SDPA-compatible padded actor/reference execution, immutable checkpoint paths, a node lock, and validation batches of 32.
- Shared user quota cannot retain every raw FSDP and optimizer state. Each raw state is merged, checksum-verified, and relocated; the merged checkpoint and relocation manifest remain durable in the project tree.

Problems:
- At roughly 25-30 minutes per optimizer step, approximately 60 steps remain; completion requires another multi-day allocation window.
- Validation format reward is non-monotonic (0.9750 at step 20, 0.9684 at step 30, 0.9784 at step 40) while answer accuracy continues to increase. Both components must remain separate.
- Each future raw checkpoint temporarily consumes about 44 GB and must be merged and relocated promptly to avoid another quota failure.

Decision:
- Keep the active run unchanged. Its reward, KL, memory, and response-length traces are stable through step 40.
- Preserve the fixed validation contract and do not shorten the run after observing the favorable early curve.

Next actions:
- At step 60, merge the checkpoint, verify hashes, and rotate raw state with `scripts/relocate_easyr1_raw_checkpoint.py`.
- Continue validation at every 10 steps and checkpoint extraction at steps 60, 80, and 100 while other node GPUs run independent scientific jobs.
- Finalize P1.1 only after step 100 and publish the complete curves.
