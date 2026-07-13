# Pilot Checkpoint Guard Recovery V1

Status:
- The checkpoint-guard root cause is fixed and covered by an adversarial fixture.
- The failed A2b process is retained as an immutable failed run. It has no raw or
  merged checkpoint and will be restarted from the registered base model in a new
  run namespace.
- This is an operational recovery record, not a pilot result. No training or
  validation performance metric was inspected.

Failure evidence:
- Failed run:
  `experiments/runs/mech_a2b_noimage_an29_20260713T031525Z`.
- The run ended at `2026-07-13T09:16:36Z` with exit code 1 while entering its
  first scheduled checkpoint save.
- The traceback terminates in `src/ops/storage_guard.py:allocated_bytes` after
  `du -sx --block-size=1 /XYFS02/HDD_POOL/paratera_xy/pxy1289` exceeded its
  600-second timeout.
- `checkpoints/pilot/mech_a2b_noimage` contains no `global_step_*` directory.
  There is therefore no scientifically defensible state from which to resume.
- Its login watcher was closed at `2026-07-13T09:52:29Z` with exit code 143 after
  the parent run had failed; that watcher produced no checkpoint artifact.

Fix:
- `src/ops/easyr1_checkpoint_guard.py` now reads a quota-aware usage snapshot
  through `allocated_bytes_from_snapshot`; it no longer performs a recursive
  shared-filesystem scan in the distributed checkpoint callback.
- `scripts/launch_mech_pilot_arm.sh` pins the snapshot path and a six-hour
  maximum age. A missing, stale, malformed, wrong-root, or low-headroom snapshot
  fails closed and follows the existing wait-and-retry policy.
- `scripts/run_storage_snapshot_refresh_loop.py` maintains immutable history
  snapshots from the login node every three hours. Its launcher delays the first
  scan by two hours because the current snapshot is fresh, avoiding an immediate
  filesystem scan during model loading.
- The latest snapshot was measured at `2026-07-13T09:49:37Z`: 567,062,717,952
  bytes used and 1,043,550,018,048 bytes available under the conservative
  1,500-GiB guard capacity.

Recovery discipline:
- `scripts/launch_mech_pilot_recovery.sh` accepts only a failed matching-arm
  manifest and refuses recovery if any raw checkpoint exists.
- The retry receives an immutable `retryN` run/checkpoint namespace.
- The generated effective config changes only `trainer.experiment_name`,
  `trainer.save_checkpoint_path`, and disables checkpoint discovery/loading.
  Registered data, reward, seed, optimizer, rollout, tower, prompt, and budget
  settings remain unchanged.
- The retry manifest records the source failed run, root cause, and exact
  operational deviation.

Verification:
- Focused unit tests: `10 passed`.
- The low-quota fixture presents a tiny local directory alongside a high-usage
  quota snapshot. The old direct-directory probe would pass; the fixed guard
  rejects it for insufficient quota headroom.
- A stale-snapshot fixture verifies that probe failure is logged as a refusal,
  waits, consumes a refreshed snapshot, and then permits the save.
- Recovery-config fixtures verify scientific sections remain byte-equivalent as
  parsed objects and that existing outputs cannot be overwritten.
- Shell syntax and Python bytecode compilation pass for all new launch/recovery
  paths.

Decision:
- Discard the failed partial A2b trajectory and start a clean, same-seed run from
  the registered base model after this fix is committed.
- Keep M11 subordinate to the pilot. The temporary vacancy allowed only failed
  M11 smoke attempts; no full M11 matrix cell launched.

Next actions:
- Commit the guard and recovery machinery before launch.
- Start A2b retry 1 on an29 GPUs 0-3 and attach a new checkpoint watcher.
- Verify run-manifest placement, config invariants, process health, and guard
  inputs without inspecting pilot performance metrics.
