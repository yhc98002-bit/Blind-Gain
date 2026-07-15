# M8 7B Preparation Status V4

Status:
- M8 remains `blocked`: all five exact 7B conditions are active and a committed
  CPU-only completion/aggregation/audit queue now covers their downstream handoff.
- V4 supersedes the operational snapshot in V3 without modifying V1-V3 or any
  immutable condition run.
- No M8 performance value was opened or interpreted for this report.

Evidence:
- M8 audit/queue implementation: commit
  `3bf812051aa46d5b0df6b76438169d1c280993fe`.
- Validation: 12 focused tests passed, including backward compatibility with the
  3B/L10 audit and adversarial wrong-model, unpinned-revision, incomplete-source,
  foreign-config, and false-audit cases. Python compilation, Bash parsing,
  ShellCheck, JSON validation, `git diff --check`, and the main-objective audit pass.
- Active queue:
  `experiments/runs/m8_virl39k_7b_summary_queue_login_20260715T214703Z`.
  Its manifest is pinned to `3bf8120`, uses no GPU, and reports
  `waiting_source_runs` with `performance_values_inspected=false`.

Mechanical snapshot at `2026-07-15T21:47:59Z`:

| Condition | GPU | Rows present / 4,096 | Manifest state |
| --- | ---: | ---: | --- |
| real | `an29:0` | 570 | running |
| gray | `an29:1` | 610 | running |
| no-image | `an29:2` | 552 | running |
| own-caption | `an29:3` | 522 | running |
| noise | `an29:4` | 412 | running |

- GPUs 0-4 were active at 85-95% instantaneous utilization and 62-66 GiB
  allocated per card. GPUs 5-7 remain unallocated because no dependency-eligible
  registered job fits that fragment.
- The queue binds each condition to its exact run path, condition, `an29` GPU,
  TP1 placement, 7B revision, 4,096-row contract, n=16/2,048-token decoding, and
  seed. A source terminal failure or identity mismatch fails the queue.
- Only after all five runs complete with exactly 4,096 rows will the queue launch
  `reports/blind_solvability_virl39k_7b_sample_v1.{md,json}` and its distinct
  `_audited.{md,json}` artifacts.
- Terminal queue completion requires every audit sub-check true, zero recomputed
  score mismatches, the exact source-run map, and the exact immutable queue-config
  hash. Reports are never overwritten.

Problems:
- All five conditions remain partial; the current row counts are operational
  progress only and are not valid analysis inputs.
- Aggregation, bootstrap intervals, full row-identity checks, and independent score
  recomputation cannot run until every source reaches 4,096 rows.

Decision:
- Keep all five independent TP1 jobs on `an29:0-4` and let the login queue perform
  the exact completion handoff automatically.
- Do not inspect partial outputs or schedule M11 on the three free GPUs; M11 remains
  fail-closed on all four M2 R19 markers.
- Keep `an21` outside the scheduler; only `an12` and `an29` are permanent nodes.

Next actions:
- Monitor row advancement, process liveness, and GPU health mechanically.
- Let the queue aggregate and audit only after all five manifests finalize cleanly.
- Use the resulting audited 7B artifact to fill M8-dependent flagship fields.

Machine-readable companion:
- `reports/m8_7b_prep_launch_status_v4.json`.
