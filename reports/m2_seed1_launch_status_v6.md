# M2 Seed-1 Launch Status V6

Status:
- M2 remains `blocked`; all four registered arm processes are active.
- A2b retry 2 remains alive with no checkpoint and resumed rollout work after two
  Python multiprocessing temporary-directory exceptions.
- This report contains operational evidence only. No reward, loss, accuracy, or
  validation metric was inspected.

Evidence:
- Run: `experiments/runs/mech_a2b_noimage_retry2_an29_20260713T111446Z`.
- The launch/config/placement evidence remains as recorded in
  `reports/m2_seed1_launch_status_v5.md`.
- At the exception time, an29 `/tmp` was a 32-GiB loop filesystem at 100% blocks
  and 100% inodes, with 127 inodes free. `/dev/shm` had about 308 GiB free and
  more than 131 million free inodes.
- The two tracebacks are `OSError: [Errno 28] No space left on device` while
  Python attempted to create `/tmp/pymp-*` listener directories.
- The run remained `running`, its Ray workers remained resident, and subsequent
  rollout activity appeared in the log. No `global_step_*` checkpoint exists at
  this status boundary.
- No file belonging to another process or project was removed.
- Repository verification after the allocator/release-gate changes: 562 tests
  passed in 438.58 seconds.

Problems:
- The process inherited Python's default `/tmp` despite Ray itself being routed
  to a job-specific `/dev/shm` directory.
- Compute-node `/tmp` is shared with unrelated work and cannot be treated as
  safely reclaimable capacity.

Decision:
- Do not terminate retry 2 while it continues useful work; monitor for a manifest
  failure or checkpoint progress.
- For every future pilot recovery, set `TMPDIR`, `TMP`, and `TEMP` to
  `<ray_tmp_dir>/tmp` under `/dev/shm`, and record that path in the run manifest.
- Preserve `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` cumulatively for
  every retry, independent of the newest recovery reason.
- Do not alter any registered YAML field.

Next actions:
- If retry 2 fails before a checkpoint, launch retry 3 from the registered base
  only after the `/dev/shm` tempfile fix is committed.
- If retry 2 reaches a checkpoint, retain it under the existing watcher and
  record the temporary-directory exceptions in the deviations log.
