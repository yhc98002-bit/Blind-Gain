# Anchor Step-100 OOM Recovery

Status:
- `active recovery`. The original native-reward anchor attempt passed and archived step 80 but was killed by Ray's host-memory monitor before the step-100 checkpoint.
- No anchor config, chat template, image path, or reward implementation has been changed. The recovery target is the exact archived step-80 raw state.

Evidence:
- Attempt: `experiments/runs/anchor_a0_recipe_3b_geo3k_20260709T224852Z` on `an12` GPUs 0-3.
- Failure class: `ray.exceptions.OutOfMemoryError`; Ray observed `957.61 GB / 1007.52 GB` host memory, above its `0.95` kill threshold.
- The killed rank was one of four anchor workers using approximately 208.56-209.15 GB each.
- Concurrent project evaluators on disjoint GPUs contributed additional host memory: L10 MathVerse/MMMU processes and the L7 caption condition. GPU isolation alone did not provide safe host-RAM isolation.
- Last complete checkpoint: `global_step_80`.
- Raw source: `/tmp/blindgain_checkpoint_archive/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_80/actor`.
- Raw source checksum manifest: `/tmp/blindgain_checkpoint_archive/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_80/actor/raw_training_state.source.sha256`.
- Shared resume metadata remains at `checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_80`: four `extra_state` shards and `dataloader.pt`.
- The failed parent process remained traceback-stuck with no Ray workers and no GPU allocation after the exception; this report authorizes termination of that project-owned failed process only.

Problems:
- The original attempt's manifest did not self-finalize after the Ray exception because its launcher predates `scripts/run_manifest_job.py` wrapping.
- Resuming while other VLM evaluators remain on `an12` would repeat the host-RAM risk even though GPUs 0-3 are disjoint.

Decision:
- Finalize the original attempt as failed after terminating only its traceback-stuck parent PID.
- Wait for the active L10 MathVerse and L7 caption evaluators on `an12` to finish; do not kill them.
- Verify the step-80 checksum manifest, restore only the required model and optimizer shards to the existing shared step-80 checkpoint under the Tier-S guard, and resume with the original config and native reward.
- Record the resumed attempt in a new immutable run directory with TP1, one synchronous replica, GPUs 0-3, and an explicit host-memory exclusivity deviation.

Next actions:
- Complete failed-attempt finalization, restore the verified step-80 raw state, and launch the unchanged step-80-to-100 continuation when `an12` host memory has safe headroom.
