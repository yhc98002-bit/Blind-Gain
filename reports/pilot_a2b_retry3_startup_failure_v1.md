# A2b Retry-3 Startup Failure V1

Status:
- `mech_a2b_noimage_retry3` failed closed before the manifest runner, training
  process, log file, watcher, GPU allocation, checkpoint creation, or scientific
  step began.
- Final manifest status is `fail`; exit code `73`; end time
  `2026-07-13T11:34:46Z`.
- No pilot performance metric was produced or inspected.

Evidence:
- Run metadata:
  `experiments/runs/mech_a2b_noimage_retry3_an29_20260713T113319Z`.
- Authorization:
  `reports/pilot_launch_authorization_a2b_noimage_20260713T113319Z.json`;
  status `authorized`; SHA256
  `5cc1cbe8fbb51b72ad59c2dc2ba24d6668cd65a2b6f3a5c987dfdf95eb6185d0`.
- The immutable run manifest correctly records commit `71393d0`, the
  `/dev/shm` runtime-temp path, expandable CUDA segments, unchanged scientific
  config, TP1, four replicas, and an29 GPUs 0-3.
- The PID was gone at the launcher's 20-second startup check. No training log was
  created, no process matched the retry-3 run, all assigned GPUs remained at 2
  MiB, and no checkpoint namespace content exists.
- The launch command opened
  `/tmp/blind_gains_an29_mech_a2b_noimage_retry3.lock` with `flock` before
  invoking the manifest runner. The lock file is absent, and an explicit `/tmp`
  file-creation probe failed under the measured inode exhaustion.

Problems:
- Generic Python tempfiles were moved to `/dev/shm`, but the launch lock retained
  a final pre-process `/tmp` dependency. Its stderr was intentionally redirected
  to `/dev/null` by the detached launcher, explaining the absent log.

Decision:
- Move the stable per-arm lock to
  `/dev/shm/blind_gains_<node>_<arm-run-name>.lock`.
- Preserve the lock's duplicate-launch semantics; only its ephemeral filesystem
  changes.
- Retry 4 may use retry 3 as its failed source because retry 3 created no
  checkpoint or scientific state.

Next actions:
- Commit the lock-path fixture and failure record.
- Launch retry 4 from the registered base and read back allocator, tempfile, and
  lock placement before unattended execution.
