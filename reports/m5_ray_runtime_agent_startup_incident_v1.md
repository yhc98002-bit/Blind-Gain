# M5 Ray Runtime-Agent Startup Incident V1

Status:
- The first post-A1 M5 recovery launch failed before GPU allocation and before any optimizer step.
- The hash-verified step-150 restore remains unchanged and available for a fresh immutable retry.

Evidence:
- Failed run: `experiments/runs/m5_anchor_longhorizon_400_resume150_an29_20260718T161215Z`.
- Run interval: 2026-07-18 16:12:32 UTC to 16:17:05 UTC; exit code 1.
- Ray started a local instance, then the raylet could not connect to its runtime-environment agent within 30 seconds (`Connection refused`, port 58179). The runner actor never started.
- `artifacts_exist=false`; `checkpoints/m5_anchor_longhorizon_400_resume150` is absent. No partial checkpoint or optimizer state was produced.
- The admission check observed 765,610,612 KiB available host memory, above the registered 650-GiB floor. All assigned GPUs remained unallocated, so this event was not a CUDA OOM or a training failure.
- The failed run's checkpoint and relocation watchers were retired after exact PID/command verification. Their wrapper manifests record exit code -15 at 2026-07-18 16:38 UTC.

Problems:
- Ray's runtime-environment agent was unreachable during startup. The failure happened before scientific execution, so it gives no evidence about the registered long-horizon run.

Decision:
- Preserve the failed lifecycle and logs; do not reuse its run directory.
- Retry from the same audited step-150 source under a new immutable run root when a clean four-GPU placement is available. Keep the registered model, data, reward, checkpoint schedule, and terminal step unchanged.
- Run a fail-closed Ray startup preflight before the retry. Do not treat a startup-only retry as additional optimizer budget.

Next actions:
- Allow the active seed-2 A2-gray and A2b jobs to continue untouched.
- Launch the M5 startup preflight and fresh recovery lifecycle on the next compatible four-GPU placement, then attach new checkpoint/evaluation watchers only after the trainer is alive.
