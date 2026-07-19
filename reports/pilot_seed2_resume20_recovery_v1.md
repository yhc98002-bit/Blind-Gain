# Pilot Seed-2 Step-20 Recovery

Status:
- Operational recovery is active; this is not an M3 scientific pass.
- A2-gray resumed on `an12` GPUs `0,1,2,3` from the hash-verified step-20 state.
- A2b-no-image resumed on `an29` GPUs `0,1,2,3` from the hash-verified step-20 state.
- Both replacement runs use new immutable checkpoint namespaces and leave the failed source runs unchanged.

Evidence:
- Recovery code commits: `cff2167` and `08adf1d`.
- Focused regression suite: 42 tests passed; the storage/parser subset passed 28 tests before launch.
- Storage measurement: `reports/storage_usage_snapshot_lustre_project_20260719T130240Z.json`.
  - Lustre project ID: `2228473301`.
  - Used: `1,295,714,107,392` bytes.
  - Headroom under the conservative 1,500-GiB allocation: `314,898,628,608` bytes.
- A2 restore run: `experiments/runs/mech_a2_gray_seed2_step20_raw_restore_login_20260719T125036Z`.
  - Restore guard allowed exactly `40,954,297,772` bytes.
  - Independent audit covered 13 files totaling `40,954,358,136` bytes.
  - Stable checksum-manifest digest: `9c5c1c004069c6ca1beeb801d03e47c849a6323531c9f84303bfe83f8983011e`.
- A2 replacement: `experiments/runs/mech_a2_gray_seed2_resume20_an12_20260719T125918Z`.
  - Checkpoints: `checkpoints/pilot/mech_a2_gray_seed2_resume20`.
  - Repeats uncheckpointed source steps 21-39; these rows are excluded from the retained source trajectory.
- A2b replacement: `experiments/runs/mech_a2b_noimage_seed2_resume20_an29_20260719T125447Z`.
  - Checkpoints: `checkpoints/pilot/mech_a2b_noimage_seed2_resume20`.
  - No post-step-20 source metric rows existed to exclude.
  - Independent source digest: `7e568129d11e131a44d97f5fa448120889a3d2cf46c497c44c6a514eba7307a2`.
- Retention watchers:
  - `experiments/runs/pilot_resume_checkpoint_watch_mech_a2_gray_seed2_resume20_login_20260719T130104Z`.
  - `experiments/runs/pilot_resume_checkpoint_watch_mech_a2b_noimage_seed2_resume20_login_20260719T125711Z`.
- One-hour all-process monitor: `experiments/runs/gpu_health_16x60m_login_20260719T130134Z`.
- Quota refresh loop: `experiments/runs/storage_snapshot_refresh_loop_login_20260719T125232Z`.

Problems:
- The original A2 run failed while writing step 40 after producing uncheckpointed rows through step 39. Its partial step-40 directory was audited as invalid and removed under the 2026-07-19 storage-cleanup record.
- The original A2b process completed a valid step-20 save but then made no log or GPU progress for more than 20 hours. The project-owned child accepted `SIGTERM`; its wrapper finalized the source manifest as failed at `2026-07-19T12:43:44Z`.
- Compute-node `/tmp` is only about 32 GiB and is full on an29 from content not attributable to this recovery. No foreign process or directory was modified. All Ray and runtime temporary paths are pinned to `/dev/shm`; a real Ray driver/worker probe passed on each node before launch.
- M5 remains queued. Running a second synchronous EasyR1 trainer on either node would violate the one-project-trainer-per-node host-memory policy while A2/A2b are active.

Decision:
- Resume from step 20 rather than reconstruct or overwrite either failed run.
- Reserve `110,000,000,000` bytes at each checkpoint guard call while the two arms may save concurrently.
- Use Lustre project-quota accounting instead of recursive `du`, which included files charged to other project IDs and falsely refused writes.
- Keep GPUs 4-7 free for now because synchronous GRPO already uses the node-level Ray object store and host-memory budget; idle GPU percentage is not a gate.

Next actions:
- Observe startup, GPU memory, fatal log patterns, and the first recovered optimizer step.
- Let the retention watchers merge and archive steps 40/60/80 while preserving step 100 on shared storage.
- Start M5 on the first fully released node, then continue the registered seed-2 queue.
