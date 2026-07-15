# M11 Full-Only Queue Readiness V1

Status:
- The full-only M11 recovery queue is `prepared` but not yet launched.
- M11 remains `blocked`: all 18 registered full cells are pending.
- The queue cannot allocate a GPU until all four exact M2 step-100 FlipTrack
  completion markers exist and pass their internal checks.
- No smoke-item model-performance value was read or emitted by the preflight.

Evidence:
- Config: `configs/eval/m11_generalization_recovery_v2.json`.
- Runner: `scripts/run_m11_full_recovery_queue.py`.
- Launcher: `scripts/launch_m11_full_recovery_queue.sh`.
- Real-artifact preflight result: six smoke cells, 18 full cells, status `pass`.
- Focused queue/runtime/report-builder tests: `22 passed`.
- The config pins SHA256 values for each retained smoke run manifest, metrics
  artifact, and prediction artifact.
- The retained smoke matrix is exactly two backends by real/no-image/caption;
  identity, one-row limit, greedy decoding, parser, prompt contract, runtime,
  and expected-artifact registration are all revalidated.

Failure controls:
- Any post-registration mutation of a smoke artifact is a hard hash failure.
- A hash-valid manifest with the wrong backend/dataset/condition identity is a
  hard semantic failure.
- Missing M2 markers keep the queue waiting without GPU allocation; an existing
  malformed marker fails the queue instead of being treated as merely pending.
- The queue state contains only the 18 full cells, so successful smoke cells
  cannot be replayed accidentally.

Decision:
- Use a new recovery queue instead of mutating or relaunching the failed V1
  queue.
- Run the scheduler on the login node. Child jobs remain single-node TP1 on
  `an29` and begin only after two stable free-GPU polls.
- Preserve all prior failed queues and smoke generations as immutable evidence.

Next actions:
- Commit the exact runner, launcher, config, fixtures, and this report.
- Launch the login-only watcher from that committed HEAD.
- Keep M11 blocked until all 18 full cells and the machine audit complete.
