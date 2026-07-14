# Pilot Host-Memory Monitor

Status:
- A one-hour read-only health run is active; final summary is pending and no gate is declared passed.

Evidence:
- Run: `experiments/runs/gpu_health_16x60m_login_20260714T081158Z`.
- Scope: all GPUs and reported GPU processes on an12 and an29; pinned pilot runs A1 recovery, A2b retry4, and A3 resume20.
- Cadence/duration: 30-second target interval for 3,600 seconds.
- Each node sample records GPU utilization/memory/temperature, GPU process identity and `ps` state, `/tmp` and `/dev/shm`, `MemAvailable`, total/swap memory, and the top 16 user processes by RSS.
- Host-memory summary reports minimum available GiB and percent, maximum swap use, and counts below 150/75 GiB.
- The observer sends no process signals and treats GPU idleness alone as non-fatal.

Problems:
- The final report does not exist until the one-hour run completes.
- A1's initial samples may be warnings while checkpoint/Ray initialization occurs; health requires later progress evidence.

Decision:
- Use this monitor to validate process health and host-memory headroom, not to inspect scientific outcomes.

Next actions:
- Read `experiments/runs/gpu_health_16x60m_login_20260714T081158Z/summary.md` after completion.
- If any node crosses the warning bands, preserve logs and diagnose before placing another pilot trainer there.
