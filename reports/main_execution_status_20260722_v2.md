# Main-Phase Execution Status V2, 2026-07-22

Status:
- Seed 2 remains structurally complete. M3 remains open because seed 3 and the registered three-seed summary are pending.
- Seed-3 A1 is running on `an29` GPUs 0-3 and had reached logged step 25 at `2026-07-22T15:22Z`. Seed-3 A2-gray is running on `an12` GPUs 0-3; it was in its first rollout/optimizer cycle with logged step 0 at the same check. Both logs advanced and neither tail matched the registered fatal patterns.
- M5 step 200 is fully saved, merged, evaluated, hash-verified, and archived. The former process was deliberately handed off at that boundary without `SIGKILL`; M5 is now waiting for A2 to release `an12`, not failed at the checkpoint level.
- A2b and A3 are pending. No seed-3 performance value has been opened.

Evidence:
- A1 trainer/watcher: `experiments/runs/mech_a1_real_seed3_an29_20260722T050330Z` and `experiments/runs/pilot_checkpoint_watch_mech_a1_real_seed3_login_20260722T050427Z`.
- A2 trainer/watcher: `experiments/runs/mech_a2_gray_seed3_an12_20260722T145916Z` and `experiments/runs/pilot_checkpoint_watch_mech_a2_gray_seed3_login_20260722T150017Z`.
- Outer scheduler hold: `reports/seed3_scheduler_hold_for_m5_20260722.md`.
- M5 source: `experiments/runs/m5_anchor_longhorizon_400_resume150_an12_20260721T160431Z`.
- M5 step-200 evaluation marker: `experiments/runs/m5_anchor_longhorizon_400_resume150_an12_20260721T160431Z/evaluations/step200_evaluation_complete.json`.
- M5 boundary handoff: `experiments/runs/m5_step200_handoff_login_20260722T145418Z`.
- Segmented recovery design: `reports/m5_segmented_recovery_plan_v1.md`; focused segment/recovery tests pass.
- New M5-after-A2 lifecycle implementation: `scripts/run_m5_after_seed3_a2_queue.py`, `scripts/launch_m5_after_seed3_a2_queue.sh`, and `tests/test_m5_after_seed3_a2_queue.py`; 64 focused queue/segment/watcher/guard tests pass.
- Shared Lustre project-quota snapshot at `2026-07-22T15:22:52Z`: 1,358,143,307,776 bytes used and 252,469,428,224 bytes free under the conservative 1,500-GiB allocation.
- A2-node host memory at the same check: 705,972,724 KiB available. A1-node host memory: 463,862,164 KiB available.
- Seed-2 archive preservation: `experiments/runs/seed2_archive_preservation_execute_login_20260722T143937Z` and `reports/storage_preservation_seed2_20260722.md`.

Problems:
- M5 cannot safely share a node with another synchronous EasyR1 trainer. Its previous process showed approximately 7.25 GiB of host-memory growth per optimizer step, so GPU 4-7 availability alone is not sufficient placement evidence.
- The prior one-hour health monitor collected 45 read-only samples, then failed when low host memory on an12 prevented SSH allocation. It is reconciled as failed in `reports/gpu_health_16x60m_failure_20260722.md`; it is not cited as a completed hour-long monitor.
- `an29:/tmp` remains nearly full, but active Ray state uses `/dev/shm` and all persistent checkpoints use shared storage. This has not blocked A1.
- M5's next raw restore adds a large temporary shared write. The current 235.13-GiB headroom is sufficient, but the exact guard is remeasured before each restore and every long segment receives a two-hour snapshot heartbeat.

Decision:
- Do not interrupt A1 or A2.
- Keep one synchronous RL trainer per node. GPUs 4-7 being idle is deliberate host-memory protection.
- The retired v5 scheduler will not launch A2b ahead of M5. A dedicated queue waits for both A2 training completion and watcher completion, then serially executes M5 boundaries `200→250→300→350→400` with a fresh raw restore, Ray startup preflight, capacity check, and checkpoint/evaluation verification at every boundary.
- Any child failure, identity mismatch, contract-hash change, storage refusal, insufficient host memory, missing watcher, or incomplete registered evaluation stops the queue without signaling a trainer or launching another pilot arm.

Next actions:
- Commit the lifecycle queue and launch it in waiting state while A1/A2 continue.
- Observe its initial state and confirm it has launched no child job before A2 release.
- After A1 frees `an29`, schedule remaining seed-3 A2b/A3 without disturbing M5; keep values closed until all four arms complete and the unified readout opens them.
