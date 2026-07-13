# M2 Seed-1 Launch Status V3

Status:
- M2 remains `blocked`; the registered result report does not yet exist.
- A2b no-image failed at its first checkpoint boundary because an operational
  quota probe timed out. Its clean retry is prepared but has not launched at the
  time of this version.
- A1 real, A2 gray, and A3 caption remain active. This report records process and
  artifact state only and contains no pilot performance result.

Incident:
- Failed run: `mech_a2b_noimage_an29_20260713T031525Z`, an29 GPUs 0-3.
- End: `2026-07-13T09:16:36Z`; exit code 1.
- Root cause: a recursive quota-root `du` in the checkpoint callback exceeded
  600 seconds before the first checkpoint was written.
- No raw or merged A2b checkpoint exists. The failed run, log, shadow rows, and
  manifest are retained and will not be reused as training state.
- No training or validation performance metric was inspected during diagnosis.

Recovery:
- Full implementation and tests are recorded in
  `reports/pilot_checkpoint_guard_recovery_v1.md`.
- The guard now consumes a fresh quota-aware snapshot rather than recursively
  scanning the quota root from a distributed worker.
- Retry 1 will start from the registered base model under a new immutable run and
  checkpoint namespace. Only operational output identity differs from the
  registered A2b config; the deviation is machine-recorded.

M11 interaction:
- A2b's failure temporarily released an29 GPUs 0-3. The capacity queue launched
  four required smoke cells, all of which failed before full-matrix authorization.
- No M11 full-matrix cell ran. M11 remains queued behind pilot ownership and must
  not consume these GPUs after the A2b recovery starts.

Evidence:
- A2b run manifest and log:
  `experiments/runs/mech_a2b_noimage_an29_20260713T031525Z/`.
- Closed watcher:
  `experiments/runs/pilot_checkpoint_watch_mech_a2b_noimage_login_20260713T031557Z/`.
- Failed M11 capacity queue:
  `experiments/runs/m11_generalization_queue_login_20260713T054030Z/`.
- Current quota snapshot: `reports/storage_usage_snapshot.json`, measured at
  `2026-07-13T09:49:37Z`.

Next actions:
- Commit the recovery implementation.
- Relaunch A2b on an29 GPUs 0-3 and publish a versioned mechanical launch update.
- Leave M11 queued until the blind arms release an29 after completing pilot work.
