# 16-GPU Health Monitor Result V1

Status:
- The one-hour, read-only process-health monitor completed operationally with exit code 0 and all expected artifacts present.
- All four tracked pilot runs had 66 healthy observations plus one initial `observing` baseline; none had an unhealthy observation.
- This is an operations result, not a scientific gate decision.

Evidence:
- Run: `experiments/runs/gpu_health_16x60m_login_20260713T144444Z`.
- Window: `2026-07-13T14:45:08Z` through `2026-07-13T15:45:04Z` (3,596 seconds between first and last observations).
- Coverage: 67 complete samples, all 16 GPUs, and 87 unique node/PID/GPU/process-name identities across process turnover.
- Raw sample SHA256: `ef2e78e3bd906acf783297e9bf0373ce2180fd29a5cbad476796097bb2f7dc63`.
- Summary JSON SHA256: `6f3cb8dae8a2d6bdde29f300dbfcd3d295254328adac823364f61a3762ffdf7c`.
- Summary Markdown SHA256: `974281b4acf5d1bdcf584d79578bb2cfa4e4c118639aa2d86b0eab5bd547c5f4`.

| Arm | Node/GPUs | First observed step | Last observed step | Step advanced | Health observations | Final run state |
|---|---|---:|---:|---|---|---|
| A1 real | an12:0-3 | 29 | 31 | yes | 66 healthy, 1 baseline | running |
| A2 gray | an12:4-7 | 28 | 30 | yes | 66 healthy, 1 baseline | running |
| A2b no-image | an29:0-3 | 10 | 14 | yes | 66 healthy, 1 baseline | running |
| A3 caption resume | an29:4-7 | startup | 22 | yes | 66 healthy, 1 baseline | running |

GPU envelope:
- an12 GPUs 0-7: mean utilization 86.0%-89.8%; maximum temperature 48-51 C; maximum observed allocation 53,188-55,890 MiB; 3-6 samples per GPU below 5% utilization.
- an29 GPUs 0-3 (A2b): mean utilization 96.4%-97.5%; maximum temperature 68-76 C; maximum allocation 72,978-77,456 MiB; 0-1 samples per GPU below 5%.
- an29 GPUs 4-7 (A3): mean utilization 82.9%-85.2%; maximum temperature 71-72 C; maximum allocation 68,372-74,390 MiB; 8-9 samples per GPU below 5%, concentrated in the recorded checkpoint-load/startup phase.
- Low utilization was never treated as failure by itself. Process survival, log/step movement, and fatal signatures remained decisive.

Problems:
- The requested interval was configured as 30 seconds, but V1 slept after each approximately 24-second SSH collection. Median start-to-start interval was therefore 54 seconds (range 51-67), yielding 67 rather than approximately 121 samples.
- The evidence still spans the full requested hour and every sample has complete 16-GPU/process coverage. The cadence discrepancy does not change the observed health classifications.

Decision:
- Accept V1 as the completed one-hour health observation with the cadence deviation disclosed.
- Fix future scheduling to subtract collection time from the interval. `tests/test_gpu_health_monitor.py::test_cadence_does_not_add_collection_time_to_interval` is the adversarial fixture for the old behavior.
- Continue the separate M2 completion watchdog; no automatic chat injection is possible from a background process.

Next actions:
- Keep all four pilot arms unchanged.
- Read `experiments/runs/m2_pilot_completion_watchdog_login_20260713T144354Z/terminal_notification.md` after the four manifests become terminal.
