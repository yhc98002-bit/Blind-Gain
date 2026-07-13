# M2 Seed-1 Launch Status V5

Status:
- M2 remains `blocked` until all four registered runs and evaluations complete.
- A2b retry 2 is active on an29 GPUs 0-3. A1 real, A2 gray, and A3 caption
  remain active on their registered placements.
- This report contains process, authorization, and configuration evidence only.
  No reward, loss, accuracy, or validation metric was inspected.

Evidence:
- A2b run:
  `experiments/runs/mech_a2b_noimage_retry2_an29_20260713T111446Z`.
- Watcher:
  `experiments/runs/pilot_checkpoint_watch_mech_a2b_noimage_retry2_login_20260713T111524Z`.
- Start: `2026-07-13T11:15:01Z`; node: an29; GPUs: 0,1,2,3; TP: 1;
  replicas: 4; seed: 1.
- Git: `e940994953877f151494574de306c9e38fe7d6fd`.
- Effective-config SHA256:
  `98fca37b1afa068a2b783ea44d5c62106c280b934e2e3925902f4ad78713a58b`.
- Data-manifest SHA256:
  `f3d88dd1e52ccef833f266880e487eef252193f774c1076f7dfbccd180b450e6`.
- Filtered-ID SHA256:
  `8631d015ee8593669b46cc707b9fe1fb3690391520bccf416b64bbb2306ff7d1`.
- Authorization:
  `reports/pilot_launch_authorization_a2b_noimage_20260713T111446Z.json`;
  status `authorized`; SHA256
  `dee0bb8a2516f3624b87400378cda29de4febb9f2fb3896d9ed622072e66d71e`.
- Checkpoint namespace: `checkpoints/pilot/mech_a2b_noimage_retry2`.

Configuration audit:
- Parsed source-versus-effective YAML comparison found exactly two changes:
  `trainer.experiment_name` and `trainer.save_checkpoint_path`.
- Image condition, filtered data, reward, prompt, model, seed, rollout,
  optimizer, frozen-tower setting, validation cadence, checkpoint cadence, and
  100-step budget are unchanged.
- The process environment on an29 was read back as:
  `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`,
  `CUDA_VISIBLE_DEVICES=0,1,2,3`, and
  `EASYR1_ATTN_IMPLEMENTATION=sdpa`.
- The manifest records the allocator setting as an operational change with
  `scientific_config_change=false` and links retry 1 as its failed source.

Failure retention:
- Retry 1 remains immutable and documented in
  `reports/pilot_a2b_retry1_failure_v1.md`.
- Retry 1 has no `global_step_*` directory, so retry 2 starts from the registered
  base rather than resuming partial state.
- Its watcher was terminated after the training manifest failed; no raw or merged
  checkpoint was found or relocated.

Other arms:
- `mech_a1_real` is running on an12 GPUs 0-3.
- `mech_a2_gray` is running on an12 GPUs 4-7.
- `mech_a3_caption` is running on an29 GPUs 4-7.

Decision:
- Continue retry 2 and its checkpoint-retention watcher without changing the
  registered scientific configuration.
- Keep M11 dormant until both an29 blind-arm manifests complete successfully.

Next actions:
- Monitor only process health, storage guards, and checkpoint integrity before
  registered readout time.
- Do not inspect pilot performance until the preregistered evaluations.
