# Gate 2 GPU Idle Audit

Status:
- Fail. The full recovery window contains 43 unexcused idle intervals longer than 30 minutes.
- A narrower corrective window from `2026-07-10T12:10:00Z` to `2026-07-10T15:58:27Z` has zero violations, but it does not replace the full-window result.

Evidence:
- Machine audit: `reports/gpu_idle_audit_gate2.json`.
- Audited window: `2026-07-09T22:48:53Z` through `2026-07-10T15:58:04Z`; 3,160 five-minute GPU samples.
- Idle definition: memory below 1,024 MiB and utilization at most 5%; an interval violates only when elapsed time between idle samples exceeds 30 minutes.
- Longest intervals were 285.1 minutes on `an29` GPUs 6 and 7, 280.1 minutes on `an29` GPU 5, and 245.1 minutes on `an12` GPU 6.
- `an12` GPUs 0-3 have no over-limit interval because the anchor occupied them continuously.
- Recent corrective audit is preserved at `/tmp/blind-gains/gpu_idle_recent.json`; 736 samples, zero violations.

Problems:
- The largest shared gap spans roughly `02:15Z-07:01Z` on multiple non-anchor GPUs. This is an operational failure, not a scientifically justified reservation.
- A second set of gaps appears around `09:00Z-12:05Z`, before the ViRL and final R19 job rotation was fully active.
- High-memory, low-utilization Qwen3-Omni workers on `an29` are classified as occupied, not idle; this audit therefore does not falsely charge their four GPUs as free.
- The audit does not infer justifications from prose or retroactively waive intervals.

Decision:
- Keep `gpu_idle_audit_no_violation=false` in `reports/gate2_machine_check.json`.
- Do not game Gate 2 by narrowing the official window. Use the recent zero-violation result only as evidence that the scheduling correction is working.

Next actions:
- Continue five-minute logging and proposal-critical backfills on every project-available slot.
- At the next PI gate, report both the historical failure and the current no-violation interval.
