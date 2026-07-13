# A3 Caption Step-20 Recovery V2

Status:
- The operational recovery is validated through two post-resume optimizer steps; A3 remains actively training.
- M2 remains `blocked` until the registered run and readouts complete. No scientific gate is declared.
- No reward, loss, accuracy, or validation value was inspected.

Evidence:
- Run: `experiments/runs/mech_a3_caption_resume20_an29_20260713T144233Z`.
- Log line 612 explicitly records `Load from checkpoint: .../mech_a3_caption/global_step_20`.
- The new immutable experiment log contains step indices 20, 21, and 22. Step 20 is the normal resume-time validation; steps 21 and 22 establish post-resume optimizer progress.
- Failed source-run steps 21-26 remain excluded because they were not checkpointed.
- The replacement log has no `No space left on device`, traceback, CUDA OOM, loss-NaN, or reward-NaN marker.
- The live worker audit found all four A3 workers using `/dev/shm/bg-ray-c58d9441255f` for `TMPDIR`, `TMP`, `TEMP`, and `RAY_TMPDIR`.
- The one-hour all-process result is `reports/gpu_health_monitor_16x60m_result_v1.md`: A3 moved from startup to step 22 with 66 healthy observations and no unhealthy observation.
- A3 GPUs 4-7 averaged 82.9%-85.2% utilization over the hour, including startup, and reached 71-72 C maximum temperature.
- Checkpoint watcher: `experiments/runs/pilot_resume_checkpoint_watch_mech_a3_caption_resume20_login_20260713T144302Z`; it is waiting for the registered step-40 save.
- Mechanical completion watchdog: `experiments/runs/m2_pilot_completion_watchdog_login_20260713T144354Z`; it is pinned to this replacement manifest.

Problems:
- an29 `/tmp` is still full, but neither blind arm uses it for Python/Ray runtime temp or locks.
- The next durable checkpoint is step 40; until then, global step 20 remains the restart point.

Decision:
- Continue A3 unchanged from the restored step-20 state.
- Preserve the old step-20 raw archive until step 40 is merged and hash-verified.
- Do not reinterpret the operational recovery as a scientific result.

Next actions:
- Let the step-40 watcher enforce shared guard, merge verification, and latest-raw retention.
- Continue completion monitoring for all four arms.
