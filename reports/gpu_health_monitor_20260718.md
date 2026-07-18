# GPU Health Monitor — 2026-07-18

Status:
- The read-only one-hour monitor completed normally. This is an operational health report, not a scientific gate decision.
- Both observed seed-2 training arms remained alive and advanced by three optimizer steps during the window.

Evidence:
- Run: `experiments/runs/gpu_health_16x60m_login_20260718T032119Z`.
- Window: `2026-07-18T03:22:35Z` through `2026-07-18T04:22:14Z`; 44 samples at 30-second cadence across all 16 GPUs.
- A1 real, seed 2: `an29` GPUs `2,5,6,7`; structural step advanced `72 -> 75`; 43 healthy observations and one startup observation.
- A2 gray, seed 2: `an12` GPUs `0,1,2,3`; structural step advanced `6 -> 9`; 43 healthy observations and one startup observation.
- Host-memory minimum: `610.162 GiB` available on `an12` and `253.281 GiB` on `an29`; swap use remained `0` on both nodes.
- Summary SHA256: `572e42b617a4ecb3a078a103b7a6cbeb610bd01808a815ec5823ee5a60a35490`.
- Samples SHA256: `16e046ae1e0cebb016f5b58b7ed8e892800e7b68492afedecf7f6a428c9befa9`.

Problems:
- None detected by the registered structural health checks.
- Idle GPUs were reported, not treated as a violation. They were subsequently admitted to the M5 step-150 evaluation after a separate host-memory check.

Decision:
- Leave both training arms untouched.
- Permit M5 step-150 inference on the four disjoint `an12` GPUs while maintaining the 450-GiB evaluation admission floor.

Next actions:
- Continue immutable structural monitoring through the existing run manifests and evaluation watcher.
- Do not inspect scientific values before the registered readout stage.
