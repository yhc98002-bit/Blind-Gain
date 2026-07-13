# M11 Generalization Execution Queue Status V3

Status:
- M11 remains `blocked`: no GPU smoke, prediction, metric, or model-performance
  result exists yet.
- The heartbeat-enabled capacity queue is running with 24/24 cells pending and no
  GPU allocation.

Correction from V2:
- V2's capacity logic was correct, but no-capacity polls changed only in-memory
  streak counters. Its state timestamp therefore could not distinguish normal
  polling from a stalled scheduler while all GPUs remained occupied.
- V2 run `experiments/runs/m11_generalization_queue_login_20260713T050649Z`
  was stopped before any child started and is preserved with status `fail`, exit
  code 143, and end time `2026-07-13T05:40:13Z`.
- V1 and V2 produced zero scientific artifacts and observed no model outputs.

V3 evidence:
- Queue run: `experiments/runs/m11_generalization_queue_login_20260713T054030Z`.
- Scheduler commit: `60b0d635cf97c0a755b22ac667fdb7f17a0d93b8`.
- Config SHA256:
  `4619c1d673b4e0b9e4b4d30651c0d9e752c9608d5727798d96ac120486090fe6`.
- Run status: `running`; phase: `smoke`; GPU allocation: none.
- First persisted poll: `2026-07-13T05:40:31Z`; observed free GPUs: none;
  stable free GPUs: none; all per-GPU streaks: zero.
- Second persisted poll: `2026-07-13T05:45:32Z`; poll count: 2; observed
  free GPUs: none; stable free GPUs: none; all 24 cells remained pending.
- Each subsequent poll atomically updates `capacity_poll_count`,
  `last_capacity_poll_utc`, observed/stable GPU lists, and the state timestamp.
  Polls do not append repetitive events, so long waits remain bounded in size.

Capacity and execution contract:
- A child requires memory used at most 1,024 MiB and utilization at most 10% on
  the same an29 GPU for two consecutive 300-second polls.
- Foreign and M2 jobs are normal neighbors. A busy or briefly free GPU is not
  reserved, interrupted, or treated as an error.
- Six one-pair smoke cells still fail closed before the 18 full cells.
- Child runs pin the Git revision active at child launch. Current HEAD includes
  pinned `timm==0.9.12`, explicit Gemma slow processing, tracked InternVL
  `GenerationMixin` repair, and runtime metadata audited in every result cell.

Verification:
- Heartbeat fixture proves two polls update counters/timestamps and do not grow
  the event list; focused queue suite passed 6/6.
- Literal `python -m pytest tests/`: 540/540 passed in 305.66 seconds.
- Main-objective audit has exactly one error: required task M11 is not pass. Every
  other ledger/report/dependency/audited-file invariant passes.

Decision:
- Keep V3 active and preserve M2 training placement.
- Keep M11 blocked until the complete registered matrix and
  `reports/generalization_audits_v1.{md,json}` pass.

Next actions:
- Confirm a second persisted no-capacity heartbeat.
- Allow smoke launch only after the registered two-poll stability condition.
- On complete matrix evidence, update M11 to `pass`, rerun the literal test suite
  and objective audit, and commit the final reports.
