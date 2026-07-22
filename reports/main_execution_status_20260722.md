# Main-Phase Execution Status, 2026-07-22

Status:
- Seed 2 is structurally complete. All eight registered checkpoint endpoints, four 601-row Geometry3K audits, and the unified four-arm readout completed. M3 remains open because seed 3 and the three-seed summary are pending.
- M5 is actively training on `an12` GPUs 0-3. At `2026-07-22T05:14Z`, the latest durable metric row was step 180 of 400. No CUDA, NCCL, Ray-worker, or reward failure is present in the active run.
- Seed-3 A1 is actively training on `an29` GPUs 0-3. It completed the step-0 validation and entered the first optimizer batch. The other seed-3 arms remain pending and no seed-3 performance result has been opened.
- M6 CP and matched member-level one-step smokes both completed. Their combined plumbing audit passes, while main M6 optimizer authorization remains zero.

Evidence:
- Seed-2 lifecycle: `experiments/runs/pilot_seed2_recovery_eval_lifecycle_login_20260722T034139Z`.
- Seed-2 readout queue: `experiments/runs/pilot_4arm_seed2_readout_queue_login_20260722T042415Z`.
- Seed-2 readout: `reports/pilot_4arm_seed2_results_v1.{md,json}`.
- M5 run: `experiments/runs/m5_anchor_longhorizon_400_resume150_an12_20260721T160431Z`.
- M5 metric source: `checkpoints/m5_anchor_longhorizon_400_resume150/experiment_log.jsonl`.
- M6 recovery controller: `experiments/runs/m6_member_smoke_recovery_login_20260722T045141Z`.
- M6 combined audit: `reports/mini_a5_plumbing_smoke_audit_v1.{md,json}`.
- Failed seed-3 outer queue, preserved: `experiments/runs/pilot_seed3_queue_v4_login_20260722T050221Z`.
- Active seed-3 A1: `experiments/runs/mech_a1_real_seed3_an29_20260722T050330Z`.
- Active A1 watcher: `experiments/runs/pilot_checkpoint_watch_mech_a1_real_seed3_login_20260722T050427Z`.
- Active recovery queue: `experiments/runs/pilot_seed3_queue_v5_login_20260722T051147Z`.
- Recovery fix commit: `7576d3d6a464d17feafdbf7c33dd0ec591b2ac12`; 18 focused tests pass.
- One-hour 16-GPU health run: `experiments/runs/gpu_health_16x60m_login_20260722T035242Z`; 121 samples, status complete.

Problems:
- The v4 seed-3 scheduler incorrectly tried to attach a second retention watcher after the arm launcher had already attached one. The duplicate guard stopped only the outer scheduler. A1 and its first watcher continued normally. V5 adopts their exact identities and never invokes a second watcher launcher.
- M5 host memory rises reproducibly after each restore. `perf.cpu_memory_used_gb` rose from 61.7 GiB at step 151 to 283.4 GiB at step 180, approximately 7.6 GiB per optimizer step. This is host-memory growth, not GPU OOM. The node still had about 412 GiB available at the latest inspection, so the current segment is safe through the registered step-200 checkpoint but is not safe to run uninterrupted to step 400.
- Lustre project quota currently reports about 288.4 GiB free; the 20-GiB shared guard leaves about 268.4 GiB operational headroom. Login `/tmp` has about 171 GiB free and its Blind Gains checkpoint archive occupies about 422 GiB. This is sufficient for the current A1 and M5 segment, but not for all remaining seed-3 archives without a verified sweep.
- `/HOME/paratera_xy/pxy1289` is full. `an29:/tmp` has about 1 GiB free, but active Ray state uses `/dev/shm`, which has about 279 GiB free. No checkpoint is routed to compute-node `/tmp`.

Decision:
- Do not interrupt A1. Keep one EasyR1 trainer per node; GPUs 4-7 being idle while a trainer is active is deliberate host-memory protection, not a scheduler failure.
- Keep M5 running to the fully saved and hash-verified step-200 boundary. Prepare a controlled checkpoint-boundary restart from step 200 so Ray and host memory reset before the next segment. Preserve any repeated post-200 work as explicit wall-clock overhead and do not change the terminal step or optimizer budget.
- Before seed-3 A1 produces enough scratch pressure to block the next arm, verify and retire only the two already documented, failed-and-superseded seed-1 shared archives, then relocate completed seed-2 scratch archives to shared storage under the Tier-S guard. No deletion occurs without a path/size/hash report first.
- Keep seed-3 values closed until its four arms and unified registered readout are complete.

Next actions:
- Observe A1 through its first completed optimizer step and then through step 20/checkpoint handling.
- Add a tested M5 step-200 boundary controller and resume-integrity audit before step 200 lands; do not change the currently loaded process.
- Publish the storage retirement inventory and verify every current archive hash before any exact-path deletion or relocation.
- Let v5 run A2-gray, A2b-no-image, and A3-caption sequentially as each preceding arm reaches step 100, merged-checkpoint verification, and raw-retention completion.
- After all four seed-3 arms finish, run the unified seed-3 evaluation and produce the registered three-seed summary.
