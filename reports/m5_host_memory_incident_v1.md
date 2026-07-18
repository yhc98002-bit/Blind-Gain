# M5 Host-Memory Incident V1

Status:
- M5 is recoverable but blocked pending a hash-verified step-150 raw-state restore and exclusive host-memory capacity.
- The original run failed at `2026-07-18T00:41:18Z`; this is not a scientific stopping decision, and M5's registered terminal step remains 400.

Evidence:
- Failed run: `experiments/runs/m5_anchor_longhorizon_400_an12_20260716T173030Z`; exit code 1.
- Ray exception: node memory was `957.22 / 1007.52 GB` (`0.950071`), above Ray's `0.95` kill threshold. Four M5 workers occupied `146.33`, `146.20`, `145.76`, and `145.37 GB` of host memory.
- Concurrent job: `experiments/runs/chart_v08_strong_caption_store_m12_v08_calibration_v1_an12_20260718T003420Z`, started seven minutes before the failure on disjoint GPUs 4–7. Its live captioning processes added about 43.7 GB in Ray's top-process report, while its 72B checkout occupied `146,833,337,667` bytes of `/dev/shm`.
- Last verified checkpoint: step 150. Merge run `experiments/runs/easyr1_checkpoint_merge_m5_anchor_longhorizon_400_step150_an12_20260717T224659Z` and raw relocation run `experiments/runs/easyr1_raw_relocation_m5_anchor_longhorizon_400_step150_login_20260717T225019Z` both completed with exit 0.
- Raw archive: `/tmp/blindgain_checkpoint_archive/m5_anchor_longhorizon_400_an12_20260716T173030Z/global_step_150/actor`, 44 GB, with all eight model/optimizer shards and checksum-manifest SHA256 `3805e66bd07a0e7cc144dda19bbcf02ee5839888e2279f74ef5076c5aab6bcbb`.
- Machine incident artifact: `reports/m5_host_memory_incident_v1.json`.
- Caption-store audit and cleanup: `reports/chart_v08_strong_caption_store_v1.json` and `reports/chart_v08_ephemeral_weights_deletion_v1.json`. Cleanup raised `/dev/shm` free space from `260,383,789,056` to `407,217,197,056` bytes.

Problems:
- GPU-only placement checks were insufficient. Disjoint GPU sets do not isolate host RAM or `/dev/shm`.
- The original M5 process completed optimizer work beyond step 150 before the OOM, but no later checkpoint exists. Recovery must resume from step 150; duplicated wall-clock/tokens are reported as operational overhead, not counted as additional optimizer budget.
- During root-cause triage, a partially redacted tail displayed non-endpoint training fields from steps 152–156. No value is used for stopping, scheduling, or interpretation; this is recorded in `reports/main_deviations.md`.

Decision:
- Do not lower or disable Ray's memory safety threshold.
- Do not colocate a 72B captioner with a Blind Gains RL trainer. The chart-v08 launcher now fails closed when any project RL trainer is active on the selected node.
- Leave the active A2-gray seed-2 run untouched. Hold only the CPU seed scheduler so an12 is reserved for M5 after A2 completes.
- Restore and verify the step-150 raw state, then resume to the fixed terminal step in a new immutable run/checkpoint root. Preserve the failed run and all logs.

Next actions:
- Complete the step-150 raw-state restore and exact shard audit.
- Launch the M5 recovery only when one whole node has at least 650 GiB host memory available and no other project trainer or 72B server.
- Relaunch checkpoint and relocation watchers against the recovery root; score registered steps without coupling evaluation to relocation.
