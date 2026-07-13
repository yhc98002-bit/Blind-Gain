# M2 Seed-1 Launch Status V9

Status:
- M2 remains `blocked`; all four registered arm processes are active again.
- A2b retry 4 is resident on an29 GPUs 0-3 with the cumulative operational
  recovery fixes applied and no startup exception.
- No reward, loss, accuracy, or validation metric was inspected.

Evidence:
- Run: `experiments/runs/mech_a2b_noimage_retry4_an29_20260713T113556Z`.
- Watcher:
  `experiments/runs/pilot_checkpoint_watch_mech_a2b_noimage_retry4_login_20260713T113639Z`.
- Start: `2026-07-13T11:36:17Z`; node: an29; GPUs: 0,1,2,3; TP: 1;
  replicas: 4; seed: 1.
- Git: `46a350f047a6575c784d4321e027b6cf8aa0dc97`.
- Effective-config SHA256:
  `5d629d2f5bd8dd8b0af7b83e51213d57e21b93d4030eae82dc621c42c4026bfb`.
- Data-manifest SHA256:
  `f3d88dd1e52ccef833f266880e487eef252193f774c1076f7dfbccd180b450e6`.
- Authorization:
  `reports/pilot_launch_authorization_a2b_noimage_20260713T113556Z.json`;
  status `authorized`; SHA256
  `ff496617673053824859834d979ac71cb2a00afe8fba76af9ecd120b3cbd7b8a`.
- Parsed source-versus-effective YAML comparison again found exactly two
  changes: `trainer.experiment_name` and `trainer.save_checkpoint_path`.

Runtime audit:
- Remote child environment:
  `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`,
  `CUDA_VISIBLE_DEVICES=0,1,2,3`, and
  `EASYR1_ATTN_IMPLEMENTATION=sdpa`.
- `TMPDIR`, `TMP`, and `TEMP` all resolve to
  `/dev/shm/bg-ray-9c02dd294484/tmp`.
- Live `pymp-*` multiprocessing directories were observed under that exact
  runtime path, confirming the old `/tmp` failure mode is bypassed in practice.
- The held duplicate-launch lock is
  `/dev/shm/blind_gains_an29_mech_a2b_noimage_retry4.lock`.
- The run manifest records both paths, the failed retry-3 source, the recovery
  reason, and `scientific_config_change=false`.
- After model residency, GPUs 0-3 each held about 51 GiB at roughly 89-91%
  utilization, and the training log had no traceback, OOM, or no-space marker.

Failure lineage:
- Retry 1: allocator-fragmentation OOM, no checkpoint.
- Retry 2: compute-`/tmp` multiprocessing deadlock, no checkpoint.
- Retry 3: `/tmp` lock creation failed before process startup, no checkpoint.
- Each run and failure report is retained; retry 4 starts from the registered
  base and never consumes partial state.

Decision:
- Continue retry 4 and its checkpoint watcher without changing any registered
  scientific field.
- Keep M11 dormant until both an29 blind arms complete successfully.

Next actions:
- Monitor process health, `/dev/shm` headroom, storage guards, and immutable
  checkpoint creation only.
- Do not inspect pilot outcomes before the registered readout.
