# Anchor Step-100 OOM Recovery

Status:
- `active recovery`. The original native-reward anchor attempt passed and archived step 80 but was killed by Ray's host-memory monitor before the step-100 checkpoint.
- No anchor config, chat template, image path, or reward implementation has been changed. The recovery target is the exact archived step-80 raw state.
- The original attempt is finalized `fail`; the archived state has been independently reverified and restored. Resume launch is waiting for the deliberate host-memory isolation window.

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
- The stuck parent was terminated and the original manifest finalized with exit 1 at `2026-07-11T14:34:47Z`.
- Independent archive verification: `experiments/runs/anchor_step80_verify_login_20260711T143511Z`; all eight source shards passed SHA256.
- Guarded restore: `experiments/runs/anchor_step80_restore_login_20260711T144238Z`; exactly `46,304,794,904` bytes were restored and reverified.
- Restore marker: `checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_80/actor/RAW_STATE_RESTORED_FOR_RESUME.json`; checksum-manifest SHA256 `aa2dbf8f77b7a1a4cfbc924521d6516302331e52ca450c26dbad9932ad59fd1e`.
- The 39G L3 smoke checkpoint was separately checksum-verified and removed, restoring enough shared headroom for the eventual step-100 save.

Problems:
- The original attempt's manifest did not self-finalize after the Ray exception because its launcher predates `scripts/run_manifest_job.py` wrapping.
- Resuming while other VLM evaluators remain on `an12` would repeat the host-RAM risk even though GPUs 0-3 are disjoint.

Decision:
- The original attempt was finalized as failed after terminating only its traceback-stuck parent PID.
- The step-80 checksum manifest was verified and only the required model and optimizer shards were restored under the Tier-S guard.
- Pause the project-owned L7 caption evaluator at its durable per-item prefix, record the pause, and resume it later through the launcher's validated `--resume-from` path. Do not terminate or alter foreign processes.
- Resume with the original config and native reward after the project evaluators have left `an12` host memory.
- Record the resumed attempt in a new immutable run directory with TP1, one synchronous replica, GPUs 0-3, and an explicit host-memory exclusivity deviation.
- Use `scripts/launch_anchor_step80_resume.sh`; it refuses cross-node placement, a missing restore marker, incomplete raw ranks, a duplicate anchor, or concurrent project VLM evaluators on `an12`.

Next actions:
- Pause and register the L7 caption prefix, then launch the unchanged step-80-to-100 continuation on `an12` GPUs 0-3.
