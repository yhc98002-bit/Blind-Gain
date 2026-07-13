# M11 Generalization Execution Queue Status V4

Status:
- M11 remains `blocked` and no capacity queue is currently active while the
  isolated runtime is prepared.
- V3 launched four smoke cells only after A2b unexpectedly released an29 GPUs 0-3.
  All four failed; the two remaining smoke cells and all 18 full cells stayed
  pending.
- No model-performance result or final M11 output was produced.

Retained queue:
- Queue: `experiments/runs/m11_generalization_queue_login_20260713T054030Z`.
- End: `2026-07-13T09:26:32Z`; status: `fail`; exit code: 1.
- Last state: 4 failed smoke cells, 2 pending smoke cells, 18 pending full cells.
- Full-phase authorization never opened.

Root cause and repair:
- InternVL smoke failed on a null nested generation config.
- Gemma real-image smoke failed because Torch 2.5.1 lacks the required mask
  combinators.
- Tracked repair and isolated-runtime design are in
  `reports/m11_runtime_recovery_v1.md`.

Scheduling decision:
- A2b retry 1 now owns an29 GPUs 0-3 and A3 owns GPUs 4-7. This is the intended
  pilot-first placement.
- After the isolated runtime machine audit passes, a fresh immutable queue will
  resume the original two-poll capacity policy and six-cell smoke barrier.
- The queue must wait; it does not preempt, kill, or classify neighboring jobs as
  anomalies.

Next actions:
- Complete the CPU/network-only isolated environment setup.
- Start a new queue pinned to the repaired commit and environment audit.
- Preserve all failed smoke manifests as negative engineering evidence.
