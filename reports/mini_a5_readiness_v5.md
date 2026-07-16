# Mini-A5 Readiness V5

Status:
- `blocked`. The exact CP/member one-step smoke registration is committed,
  machine-bound, and queued behind the active seed-2 and M11 priorities.
- No Mini-A5 optimizer step has run. The queue is GPU-inert while dependencies
  remain active and authorizes zero main-arm steps.
- A separate post-smoke registration marker remains mandatory before either
  120-step M6 arm.
- No PI gate decision is made.

Evidence:
- Registration document: `docs/registered_mini_a5_smoke_v1.md`, SHA256
  `c93bcb3e41e9a2ec4ac1df738e6b7fa025991f9038dfdab45ed073f430fec155`.
- Registration commit:
  `5e429b335dc4bf10e885bc1907d731d9e0a503f3`.
- Commit-binding marker:
  `reports/mini_a5_smoke_registration_marker_v1.json`, SHA256
  `5cd71846882c1b0d8d94d0d2dc46e3a9d5efabcbcfa2567b6e20ab225626a0e6`.
  All 11 checks pass; one step per smoke mode and zero main steps are the
  explicit authorization bounds.
- The isolated EasyR1 worktree remains at
  `dd71bbd252694f5f850213eec15795b6b88d9fea`; its eight-patch diff SHA256 is
  `c12ca1eaddf11d13b5206834490d71179596af89c58d37741cc2f8624602766a`.
- Queue run:
  `experiments/runs/mini_a5_smoke_queue_login_20260716T192243Z` at Git commit
  `8304808a6011228a2c2cab4bb44200bb47afbccb`.
- Queue state at launch: seed 2 `running`, M11 `running`, M5 `running`, CP
  `pending`, member `pending`, `performance_values_opened=false`, and
  `main_optimizer_steps_authorized=0`.
- Scheduling rule: seed 2 and M11 must complete without failure; M5 must remain
  running or complete. A node must report all GPUs below 1,024 MiB for two
  consecutive polls. CP and member then run sequentially on that same node.
- The independent auditor is committed before launch and checks 15 conditions
  per run plus five combined conditions, including the exact 80-row/eight-pair/
  `G=5` CP runtime event, finite reward/actor metrics, and checkpoint hashes.

Problems:
- Higher-priority GPU work currently occupies both nodes, so no full-node
  smoke placement exists.
- The two smoke outputs and independent audit do not yet exist.
- Main M6 launch remains unauthorized even if both smokes later complete.

Decision:
- Keep the queue GPU-inert until its structural dependencies and full-node
  checks pass. Do not preempt M5, seed 2, M11, or foreign work.
- Stop automatically after the smoke audit. Review and commit that audit before
  creating the post-smoke main-arm registration marker.

Next actions:
- Monitor dependency and queue health without opening active scientific
  metrics.
- On a smoke-audit pass, inventory retention-expired smoke checkpoints and
  bind the exact audit/config/data hashes into a new main-arm marker.
