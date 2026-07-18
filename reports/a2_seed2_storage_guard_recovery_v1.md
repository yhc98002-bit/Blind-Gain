# A2 Seed-2 Storage-Guard Recovery V1

Status:
- A2-gray seed 2 reached its registered step-20 checkpoint boundary but the
  fail-closed storage guard refused the save because its quota snapshot was
  older than the configured six-hour maximum.
- A provenance-bound conservative snapshot was atomically published at
  `2026-07-18T14:33:39Z` without changing or restarting the training process.
- The next automatic save attempt passed at `2026-07-18T14:35:36Z`; step 20
  was recorded by the checkpoint tracker and all four GPUs resumed training.
- No training or validation performance value was opened.

Evidence:
- Training run:
  `experiments/runs/mech_a2_gray_seed2_an12_20260718T004316Z`.
- Recovery run:
  `experiments/runs/a2_seed2_storage_snapshot_refresh_login_20260718T143334Z`,
  status `complete`, exit code `0`.
- Exact source snapshot:
  `experiments/runs/storage_snapshot_refresh_loop_login_20260713T100116Z/snapshots/storage_usage_snapshot_20260717T053850Z.json`.
- Exact source SHA256:
  `421ec8020d058bd6a4407202fc63017b24887858beff43c1dbbbfd713da5eb92`.
- Conservative reserve: 429,496,729,600 bytes (400 GiB).
- Guarded write allowance: 55,000,000,000 bytes; floor:
  21,474,836,480 bytes (20 GiB).
- Conservative headroom before the write: 110,618,386,432 bytes; after the
  authorized write: 55,618,386,432 bytes.
- Guard event changed from `refused` at `2026-07-18T14:30:36Z` to `pass` at
  `2026-07-18T14:35:36Z`.
- Checkpoint tracker after recovery: `last_global_step=20`.
- A post-save sample observed GPU utilization `100,100,100,100` on `an12`
  GPUs 0-3.

Problems:
- The shared allocation was not shown to be full. The refusal was caused by
  snapshot freshness, not by a measured capacity breach.
- The exact background quota refresh is metadata-intensive and can exceed one
  component timeout; the conservative publication path remains the approved
  fail-closed fallback.

Decision:
- Preserve the refusal events and recovery lifecycle as operational evidence.
- Leave A2 running from its in-memory state; no reconstruction or retraining
  was needed.
- Continue the independent exact snapshot refresh loop so later checkpoint
  boundaries receive a fresh quota measurement.

Next actions:
- Let A2-gray seed 2 continue to step 100 under normal checkpoint retention.
- Keep the existing watcher responsible for merge, hash verification, and
  raw-state retention at subsequent checkpoint boundaries.
