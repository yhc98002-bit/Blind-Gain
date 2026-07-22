# 16-GPU Health Monitor Failure, 2026-07-22

Status:
- Failed after 45 read-only samples. This is a monitor failure, not a training failure.

Evidence:
- Run: `experiments/runs/gpu_health_16x60m_login_20260722T054755Z`.
- The sampler recorded both `an12` and `an29` every 30 seconds and never sent a process signal.
- Final error: an12 SSH returned `memory allocation failed` while M5 host-memory use was near its mechanical handoff threshold.
- The old wrapper then failed to spawn its separate manifest-finalizer process, leaving a stale `running` field. The manifest is reconciled to `fail`, exit code 1, with `artifacts_exist=false`.

Problems:
- The monitor treated a transient SSH collection error as fatal.
- The old manifest runner required a second process spawn to finalize status, which is least reliable during host-memory pressure.

Decision:
- Do not describe this run as a completed one-hour health window.
- Finalize future jobs in-process; the spawn-OOM regression fixture now proves that a failed child launch cannot leave a false `running` status.
- Use shorter per-segment health windows and record individual collection failures without masking actual trainer state.

Next actions:
- Start a fresh bounded health monitor after the M5 200-to-250 segment reaches four-GPU startup readiness.
- Report M5 and seed-3 A1 process health separately from monitor health.
