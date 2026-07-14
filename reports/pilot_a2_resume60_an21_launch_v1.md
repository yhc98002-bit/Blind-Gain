# A2-Gray Step-60 Recovery on an21

Status:
- A2-gray recovery is running on an21. Ray and all four workers initialized, and all step-60 model/optimizer/extra-state ranks were loaded; resumed validation/optimizer progress remains pending. This is an operational status, not a scientific gate decision.

Evidence:
- Training run: `experiments/runs/mech_a2_gray_resume60_an21_20260714T145532Z`.
- Launch commit: `6b67c2137e3c78b8a8c6b02855ce9a0755957664`, pushed to `origin/agent/gate2-recovery` before launch.
- Placement: an21 GPUs `0,1,2,3`, TP1, four replicas; no other trainer or GPU process was present on an21.
- Preflight inventory: eight A800-80GB GPUs at 2 MiB each; `1034780848` KiB `MemAvailable`; 504 GiB free under `/dev/shm`; shared repository and virtual environment visible.
- an21 `/tmp` had only about 24 GiB free, so `TMPDIR`, `TMP`, `TEMP`, and `RAY_TMPDIR` are routed to the job-specific `/dev/shm/bg-ray-1ddc210d815e` tree.
- Ray path probe passed for driver, worker, multiprocessing, tempfile, and Ray session paths under `/dev/shm`.
- Source checkpoint: `checkpoints/pilot/mech_a2_gray/global_step_60`.
- Checkpoint audit: `experiments/runs/mech_a2_gray_resume60_an21_20260714T145532Z/resume_checkpoint_audit.json`.
- The audit verified four model ranks, four optimizer ranks, four extra-state ranks, and dataloader state: 13 stable files totaling `40954358136` bytes. Checksum-manifest SHA256: `81d2fd7641099bf674f6c3deef641e0d99a87ae87c4c9893a9ed0acf44771105`.
- Resume config SHA256: `f2b4d380384723d98b493105ea7c3408578c549a80aaafea18f0f2070bbcaffe`; audit records `scientific_config_changed=false`.
- Checkpoint watcher: `experiments/runs/pilot_resume60_checkpoint_watch_mech_a2_gray_resume60_login_20260714T145952Z`, handling only steps 80 and 100.
- Four-arm completion watchdog: `experiments/runs/m2_pilot_completion_watchdog_login_20260714T150106Z`, with A2 pinned to an21.
- Three-node health monitor: `experiments/runs/gpu_health_24x60m_login_20260714T150057Z`, observing 24 GPUs, host memory, process state, and operational progress.
- Interim monitor evidence through `2026-07-14T15:13:30Z`: 22 samples over about 12 minutes, nine healthy A2 intervals, no fatal signature, an21 minimum `MemAvailable` about 845 GiB, and sampled A2 GPU memory up to 50,986 MiB.
- The training log explicitly records model, optimizer, and extra-state loading for ranks 0-3 from `checkpoints/pilot/mech_a2_gray/global_step_60`.

Problems:
- an21 had a cold shared-filesystem cache: initial import/Ray startup spent several minutes in advancing `cl_sync_io_wait`. This cleared without intervention. Some monitor intervals remain warnings during long initialization phases without operational-step advancement.
- The retired release queue `experiments/runs/a2_resume60_release_queue_login_20260714T081148Z` was intentionally terminated with exit `-15` before direct launch, preventing a later duplicate A2 start on an12/an29.

Decision:
- Continue the run: log output, checkpoint-rank loading, GPU allocation, and host-memory headroom are now observed without a fatal signature.
- Do not classify resume completion until post-load validation and optimizer-step progress are observed.
- Keep A2 isolated on an21; do not place another pilot trainer on that node.

Next actions:
- Continue the one-hour three-node health observation.
- If shared-I/O counters stop advancing or initialization fails, preserve the immutable run and use a separately logged node-local runtime staging recovery.
- After device loading, verify resumed step-60 validation and subsequent optimizer progress without inspecting scientific metric values.
