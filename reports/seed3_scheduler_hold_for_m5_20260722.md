# Seed-3 Scheduler Hold for M5, 2026-07-22

Status:
- Operational hold applied. The outer seed-3 v5 scheduler is finalized as `fail` after a deliberate `SIGTERM`; the already-launched A1 and A2 trainers and their attached retention watchers remain running and were not signaled.
- A2b and A3 were not launched. This reserves `an12` for the registered M5 continuation after A2 reaches step 100 and its watcher completes merge and latest-raw retention.
- This is scheduling evidence, not a scientific result or a PI gate decision.

Evidence:
- Retired outer scheduler: `experiments/runs/pilot_seed3_queue_v5_login_20260722T051147Z/run_manifest.json` (`status=fail`, `exit_code=-15`, `end_time_utc=2026-07-22T15:17:50Z`).
- Its final queue state records A1 on `an29:0-3`, A2 on `an12:0-3`, and A2b/A3 as pending.
- A1 trainer: `experiments/runs/mech_a1_real_seed3_an29_20260722T050330Z`.
- A1 watcher: `experiments/runs/pilot_checkpoint_watch_mech_a1_real_seed3_login_20260722T050427Z`.
- A2 trainer: `experiments/runs/mech_a2_gray_seed3_an12_20260722T145916Z`.
- A2 watcher: `experiments/runs/pilot_checkpoint_watch_mech_a2_gray_seed3_login_20260722T150017Z`.
- Immediately after scheduler retirement, both trainer wrappers, both watcher manifests, and both four-GPU allocations remained live. No checkpoint namespace was changed.

Problems:
- V5 would otherwise launch A2b as soon as A2 released `an12`, racing the higher-priority M5 continuation for the node.
- A second EasyR1 trainer on GPUs 4-7 is unsafe even though those GPUs are free: the measured Ray/worker host-memory growth makes host RAM, not GPU memory, the limiting resource.

Decision:
- Preserve A1 and A2 exactly as launched.
- Give M5 first claim on `an12:0-3` after the exact A2 trainer and its exact retention watcher both complete successfully.
- Use a dedicated fail-closed M5 lifecycle queue. It has no pilot-arm launcher and no process-signal path.

Next actions:
- Continue read-only health monitoring of A1 and A2.
- Launch `scripts/launch_m5_after_seed3_a2_queue.sh` after its code and fixtures are committed.
- Resume A2b and A3 on available capacity without colocating a second synchronous RL trainer on a node.
