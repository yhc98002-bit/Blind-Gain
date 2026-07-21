# Mini-A5 Readiness V6

Status:
- `blocked`. The exact registered CP/member one-step smoke remains authorized, but no smoke optimizer step has run in this recovery cycle.
- The corrected v2 queue is active and GPU-inert. Main M6 arms remain unauthorized.
- No PI gate decision is made.

Evidence:
- Registration marker: `reports/mini_a5_smoke_registration_marker_v1.json`; main optimizer steps authorized = 0.
- Corrected priority queue: `experiments/runs/mini_a5_smoke_queue_v2_login_20260721T164001Z`, commit `53b2f9e`.
- Dependencies: seed-2 sealed evaluation lifecycle `running`; M11 reconciled final report `complete`; M5 recovery `running`.
- Placement contract: one fully free permanent node, eight GPUs, eight TP1 workers; CP and member smokes run sequentially. The scheduler prefers `an29`.
- The queue cannot consume four spare GPUs because the registered smoke requires all eight GPUs on one node.
- Focused Mini-A5 tests: `16 passed`.
- Seed-3 capacity queue: `experiments/runs/pilot_seed3_queue_v2_login_20260721T164446Z`; all arms remain `pending` until the smoke audit completes.
- Seed-3 configs retain the exact registered SHA256 values in `docs/registered_pilot_seed23_v1.md`; scheduler/checkpoint fixtures: `27 passed`.

Problems:
- Seed-2 evaluation must finish before the smoke queue may seek a full node.
- The CP/member smoke outputs and independent audit do not yet exist.
- A separate post-smoke main-arm marker is still required before any 120-step M6 arm.

Decision:
- Preserve the registered eight-GPU smoke placement; do not reinterpret four idle GPUs as sufficient capacity.
- Prefer `an29` after seed-2 releases it. Use `an12` only if it is fully free and passes the existing admission checks.
- Keep seed 3 queued behind a successful smoke audit and launch at most one four-GPU synchronous trainer per node.

Next actions:
- Run CP then member one-step smokes automatically when dependencies and full-node capacity are satisfied.
- Audit both runs; stop with main optimizer authorization still zero.
- After the smoke audit, release the seed-3 scheduler. Main M6 remains fail-closed pending its separate marker.
