# M5 Storage Guard Recovery V1

Status:
- Operational recovery passed. M5 was waiting at the step-150 pre-save guard
  because its quota snapshot was stale, not because the shared allocation was
  exhausted.
- The guard accepted a documented conservative upper-bound snapshot at
  `2026-07-17T21:39:31Z`; M5 resumed on an12 GPUs 0-3 without termination or
  restart.
- M5 itself remains in progress and no scientific result or gate is declared.

Evidence:
- Stalled run: `experiments/runs/m5_anchor_longhorizon_400_an12_20260716T173030Z`.
- Repeated refusal reason: `storage usage snapshot is stale`; the last refusal was
  `2026-07-17T21:34:30Z`.
- Failed exact refresh:
  `experiments/runs/storage_usage_m5_step150_guard_retry_20260717T205734Z`;
  immutable status `failed`; `.uv_cache` exceeded the 1,800-second per-component
  `du` timeout. No snapshot was published by this run.
- Preserved exact source:
  `reports/storage_usage_snapshot_exact_20260717T054846Z.json`; SHA256
  `421ec8020d058bd6a4407202fc63017b24887858beff43c1dbbbfd713da5eb92`;
  exact used bytes `1,070,497,619,968` under the conservative 1,500-GiB quota.
- One-time conservative snapshot:
  `reports/storage_usage_snapshot_conservative_20260717T213613Z.json`; SHA256
  `b457b29029dbf854b7661cc6b7ac5414bbf99472ebf329e6fe1a582df2f9c6ae`.
- The upper bound adds 400 GiB (`429,496,729,600` bytes) of unmeasured growth to
  the exact source. It therefore assumes used bytes `1,499,994,349,568` and free
  bytes `110,618,386,432` before the step-150 write.
- After the registered 60,000,000,000-byte checkpoint budget, conservative free
  space is `50,618,386,432` bytes (47.14 GiB), above the 20-GiB guard floor.
- Acceptance is appended to the M5 guard log with status `pass`, used bytes
  `1,499,994,349,568`, and free-after bytes `50,618,386,432`.
- At the first post-recovery health sample, GPUs 0-3 were each at 100% utilization.
- Freshness watcher:
  `experiments/runs/m5_storage_freshness_watch_login_20260717T220109Z`, source
  commit `e1ea789e151e429e91784c57c26404e8eae836f8`, tmux
  `m5_storage_freshness_20260717T220109Z`. It checks every five minutes, republishes
  the same source-anchored upper bound at four hours, opens no performance values,
  and stops when the M5 run manifest becomes terminal.
- Fixtures: `4 passed in 11.80s`. They verify reserve/write/floor accounting,
  reject unsafe writes, reject future timestamps, and prohibit chaining one
  conservative snapshot from another.

Problems:
- The exact quota-root scan can exceed 30 minutes under shared-filesystem pressure.
  The default component timeout is now 7,200 seconds for future exact scans.
- The conservative artifact is an upper bound, not a claim that 400 GiB was
  actually consumed. Its purpose is fail-closed authorization under a deliberately
  pessimistic usage assumption.

Decision:
- Preserve both the failed exact-refresh run and its logs.
- Keep the M5 training process untouched. Use the freshness watcher until M5 is
  terminal, while allowing later exact snapshots to supersede the mutable current
  snapshot.
- Never derive a new conservative source from a prior conservative snapshot.

Next actions:
- Verify the step-150 checkpoint, merge, retention, and evaluation lifecycle.
- Continue the fixed M5 run to step 400 under the existing registration.
