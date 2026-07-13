# M2 Seed-1 Launch Status V4

Status:
- M2 remains `blocked` until all four registered runs and evaluations complete.
- A2b retry 1 is active on an29 GPUs 0-3. A1 real, A2 gray, and A3 caption
  remain active on their registered placements.
- This report contains process, authorization, and configuration evidence only.
  No reward, loss, accuracy, or validation metric was inspected.

A2b recovery launch:
- Run: `experiments/runs/mech_a2b_noimage_retry1_an29_20260713T100420Z`.
- Watcher:
  `experiments/runs/pilot_checkpoint_watch_mech_a2b_noimage_retry1_login_20260713T100501Z`.
- Start: `2026-07-13T10:04:38Z`; node: an29; GPUs: 0,1,2,3; TP: 1;
  replicas: 4; seed: 1.
- Git: `12b0817432e66cd2f387c704e384431a6e8a8b8e`.
- Effective config SHA256:
  `d00a8d710e159d87823d8a5beb0e0c1d8870791c326fb4ef1357af92a622137f`.
- Data manifest SHA256:
  `f3d88dd1e52ccef833f266880e487eef252193f774c1076f7dfbccd180b450e6`.
- Checkpoint namespace: `checkpoints/pilot/mech_a2b_noimage_retry1`.

Authorization and invariants:
- Recovery authorization passed every registered check, including canonical
  recovery-path validity and namespace absence.
- Parsed source-versus-effective config comparison found exactly two changes:
  `trainer.experiment_name` and `trainer.save_checkpoint_path`.
- Registered image condition, data, reward, prompt, model, seed, rollout,
  optimizer, tower, validation cadence, save cadence, and 100-step budget are
  unchanged.
- The manifest links the failed source run and records
  `scientific_config_change=false`.
- The retry wrapper, child process, and checkpoint watcher are live. Model and
  rollout workers are resident on all four assigned GPUs; no traceback or fatal
  exception is present.

Failed source retention:
- Source: `experiments/runs/mech_a2b_noimage_an29_20260713T031525Z`.
- The source has status `fail`, no `global_step_*` checkpoint, and is never used as
  recovery state.
- Root cause and guard fixtures are in
  `reports/pilot_checkpoint_guard_recovery_v1.md`.
- A first recovery authorization attempt was blocked before run-directory or GPU
  allocation because it correctly saw the old canonical namespace. The retained
  machine artifact is
  `reports/pilot_launch_authorization_a2b_noimage_20260713T100130Z.json`.
  Recovery-aware authorization was then narrowed to canonical `*_retryN` paths
  under `checkpoints/pilot`, with arbitrary-path and duplicate-path fixtures.

Storage:
- The login-node snapshot refresher is active in
  `experiments/runs/storage_snapshot_refresh_loop_login_20260713T100116Z`.
- Current quota snapshot was measured at `2026-07-13T10:01:10Z`: 517,970,045,440
  bytes used and 1,092,642,690,560 bytes available under the conservative
  1,500-GiB guard capacity.
- The checkpoint callback consumes this snapshot and waits on stale, unavailable,
  or low-headroom inputs instead of recursively scanning or terminating the arm.

M11 scheduling:
- All eight an29 GPUs are pilot-owned again. M11 remains behind the blind arms and
  cannot satisfy its two-poll free-capacity condition.
- The failed M11 smoke attempts did not open the full matrix.

Next actions:
- Continue operational monitoring and hash-verified checkpoint retention.
- Do not inspect or report pilot performance until the registered readout stage.
- Leave M11 capacity-queued after its isolated runtime audit is complete.
