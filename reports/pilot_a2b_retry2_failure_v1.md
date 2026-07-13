# A2b Retry-2 Operational Failure V1

Status:
- `mech_a2b_noimage_retry2` was terminated before its first checkpoint after
  becoming operationally deadlocked on compute-node `/tmp` inode exhaustion.
- Final training-manifest status is `fail`; end time
  `2026-07-13T11:31:20Z`; exit code `-6`.
- M2 remains `blocked`. No reward, loss, accuracy, or validation metric was
  inspected.

Evidence:
- Run: `experiments/runs/mech_a2b_noimage_retry2_an29_20260713T111446Z`.
- Watcher:
  `experiments/runs/pilot_checkpoint_watch_mech_a2b_noimage_retry2_login_20260713T111524Z`;
  finalized `fail` at `2026-07-13T11:31:56Z` after finding no checkpoint.
- Git: `e940994953877f151494574de306c9e38fe7d6fd`; effective-config SHA256:
  `98fca37b1afa068a2b783ea44d5c62106c280b934e2e3925902f4ad78713a58b`;
  data-manifest SHA256:
  `f3d88dd1e52ccef833f266880e487eef252193f774c1076f7dfbccd180b450e6`.
- Final log SHA256:
  `eb619233b35205fe9d6db5fd684bf4b18e73c3136c0d23f1c8d292e9f6df002f`.
- Final run-manifest SHA256:
  `b92c5accbf5c0faf52908212922375b16ba20210cd7430f2941ba9cecd40991c`.
- The log contains two Python multiprocessing tracebacks attempting to create
  `/tmp/pymp-*`, both ending in `OSError: [Errno 28] No space left on device`.
- an29 `/tmp` measured 32 GiB, 100% blocks, and 100% inodes; `/dev/shm`
  measured 308 GiB free with more than 131 million free inodes.
- After the exceptions, the log stopped growing for more than seven minutes.
  Seven 10-second `nvidia-smi dmon` samples showed 0% compute and 0% memory
  activity on GPUs 0-3. The process remained alive and held about 51.6 GiB/GPU.
- `checkpoints/pilot/mech_a2b_noimage_retry2` contains no `global_step_*`
  directory. The four GPUs returned to 2 MiB each after termination.

Problems:
- Ray was correctly routed to `/dev/shm`, but Python's generic temporary-file
  variables were not. Multiprocessing listener creation therefore used the full
  shared `/tmp` filesystem and left the driver waiting on failed workers.

Decision:
- The liveness evidence is sufficient to classify retry 2 as an operational
  deadlock rather than useful GPU work.
- No neighboring file or process was removed or modified.
- Retry 3 must start from the registered base because no checkpoint exists.
- Retry 3 preserves the allocator fix and additionally routes `TMPDIR`, `TMP`,
  and `TEMP` to its job-specific `/dev/shm` namespace. These are operational
  environment changes; the registered YAML remains unchanged except immutable
  output identity.

Next actions:
- Commit the tempfile fixture and this failure record.
- Launch retry 3 on an29 GPUs 0-3 with reason
  `compute_node_tmp_inode_exhaustion_deadlock_before_first_checkpoint`.
- Verify the remote process environment and reject any `/tmp/pymp-*` use by the
  retry process tree.
