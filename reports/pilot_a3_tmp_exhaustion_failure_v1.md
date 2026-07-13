# A3 Caption Temporary-Storage Failure V1

Status:
- The original A3 process was finalized `fail` at `2026-07-13T14:33:39Z` after a verified operational stall.
- No reward, loss, accuracy, or validation value was inspected while diagnosing or closing the run.

Evidence:
- Source run: `experiments/runs/mech_a3_caption_an29_20260713T033039Z`.
- Placement: an29 GPUs 4-7, TP1, four rollout replicas, seed 1.
- Last durable checkpoint: `checkpoints/pilot/mech_a3_caption/global_step_20`.
- The source metric log contained one row for every step 0-26. Steps 21-26 had no checkpoint and are excluded from the resumed trajectory.
- The training log stopped advancing at `2026-07-13T11:22:35Z`; the final pre-stop observation was `2026-07-13T14:33:08Z`.
- Log lines 1,351,408 and 1,373,896 report `OSError: [Errno 28] No space left on device` for `/tmp/pymp-*` directories.
- an29 `/tmp` had 20 KiB available and 157 free inodes; both block and inode use were 100%.
- The original process environment set only `RAY_TMPDIR=/dev/shm/bg-ray-bf656cf5076e`; `TMPDIR`, `TMP`, and `TEMP` were absent, allowing Python multiprocessing to fall back to `/tmp`.
- GPUs 4-7 retained approximately 51.8-52.0 GiB each at 0% utilization during the stall.
- The wrapper finalized with `status=fail`, `exit_code=-6`, and `artifacts_exist=true` after targeted `SIGTERM`.
- Four orphaned workers were identity-checked by PID, command, and exact A3 Ray root, then terminated. GPUs 4-7 returned to 2 MiB each. A2b and its separate Ray root were untouched.
- The obsolete A3 checkpoint watcher was separately finalized `fail` with exit `-15` because it could never receive step 40 from the failed parent.

Problems:
- `RAY_TMPDIR` controls Ray's own session tree but does not force Python `tempfile` or `multiprocessing.util` to use that tree.
- A live PID and allocated GPU memory concealed a terminal data-path failure; utilization alone was insufficient to establish health.

Decision:
- Resume only from hash-verified global step 20.
- Route `TMPDIR`, `TMP`, `TEMP`, and `RAY_TMPDIR` to one job-local `/dev/shm` root and verify both driver and Ray-worker multiprocessing paths before launch.
- Use a new immutable output namespace; do not append uncheckpointed source steps 21-26.

Next actions:
- Track the replacement in `reports/pilot_a3_resume20_recovery_v1.md`.
- Preserve this failed run, its logs, and the step-20 source lineage.
