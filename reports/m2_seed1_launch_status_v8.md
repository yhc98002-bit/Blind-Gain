# M2 Seed-1 Launch Status V8

Status:
- M2 remains `blocked`.
- A1 real, A2 gray, and A3 caption remain active. A2b retry 3 failed before
  process startup; retry 4 awaits the committed lock-path fix.
- No pilot performance metric was inspected.

Evidence:
- Retry-3 record: `reports/pilot_a2b_retry3_startup_failure_v1.md`.
- The startup failure created no log, watcher, checkpoint, or GPU process.
- The new adversarial fixture requires all recovery tempfile and lock paths to
  avoid compute-node `/tmp`.

Decision:
- Commit before retrying so the run manifest pins the complete operational fix.
- Keep M11 at `waiting_pilot_release`; the failed startup does not release the
  blind arm scientifically.

Next actions:
- Launch A2b retry 4 on an29 GPUs 0-3.
- Verify its `/dev/shm` lock and runtime-temp paths plus its exact config diff.
