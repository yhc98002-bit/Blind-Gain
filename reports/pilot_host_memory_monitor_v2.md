# Three-Node Pilot Health Monitor

Status:
- A one-hour read-only 24-GPU health run is active; final summary is pending and no scientific gate is declared passed.

Evidence:
- Run: `experiments/runs/gpu_health_24x60m_login_20260714T150057Z`.
- Nodes: an12, an21, and an29; eight GPUs per node.
- Pinned arms: A1 recovery on an12, A2 recovery on an21, and A2b/A3 on an29.
- Each sample records GPU utilization/memory/temperature, GPU process identity and `ps` state, `/tmp`, `/dev/shm`, `MemAvailable`, swap, top user processes by RSS, wrapper survival, log movement, and maximum operational step observed.
- The first sample found all four wrappers alive. A2 was still in cold initialization on an21; this baseline is classified `observing`, not healthy or failed.
- Interim A2/an21 evidence through `2026-07-14T15:13:30Z`: 22 samples, nine healthy intervals, no fatal signature, minimum host `MemAvailable` about 845 GiB, and sampled GPU memory up to 50,986 MiB. Initialization-only warnings remain disclosed.
- The monitor sends no signals and does not read reward, accuracy, or validation metric values.

Problems:
- Final health aggregation remains unavailable until the one-hour run completes.
- Three-node SSH/process collection may exceed the nominal 30-second cadence; actual sample count and interval are reported rather than assumed.

Decision:
- Use lifecycle, host-memory, I/O, and process evidence to assess operational health. GPU idleness alone remains non-fatal.

Next actions:
- Review `experiments/runs/gpu_health_24x60m_login_20260714T150057Z/summary.md` after completion.
- Preserve and diagnose any unhealthy interval before scheduling another trainer on the affected node.
