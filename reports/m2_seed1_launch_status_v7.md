# M2 Seed-1 Launch Status V7

Status:
- M2 remains `blocked`.
- A1 real, A2 gray, and A3 caption remain active. A2b retry 2 is failed and
  retry 3 is prepared but not launched at this status boundary.
- No pilot performance metric was inspected.

Evidence:
- Retry-2 failure record: `reports/pilot_a2b_retry2_failure_v1.md`.
- Retry 2 has no checkpoint and cannot be resumed.
- The future-launch hardening is committed only after its adversarial fixture
  passes: all recovery runs retain expandable CUDA segments, and Python
  temporary sockets use `<ray_tmp_dir>/tmp` under `/dev/shm`.
- Focused launcher/recovery/queue verification: 16 tests passed.
- Full repository verification before the tempfile-only addition: 562 tests
  passed in 438.58 seconds.

Decision:
- Launch retry 3 only from a commit containing the tempfile hardening and this
  immutable failure record.
- Keep M11 queued; failed A2b capacity does not satisfy its release gate.

Next actions:
- Launch retry 3 on an29 GPUs 0-3.
- Verify process residency, exact source/effective YAML diff, allocator setting,
  and tempfile environment without reading scientific metrics.
