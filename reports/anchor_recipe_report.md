# P1.1 Anchor Recipe Report

Status:
- P1.1 recipe-scale anchor is configured, but the first canonical attempt was stopped after a silent startup stall.
- A bounded foreground diagnostic subsequently reached dataset loading, four-rank NCCL, FSDP construction, and vLLM CUDA-graph capture. This establishes that the EasyR1 stack and recipe config can initialize.
- Completion remains pending; this report is not a pass report.

Evidence:
- Config: `configs/train/anchor_a0_recipe_3b_geo3k.yaml`
- Config diff: `reports/anchor_a0_recipe_config_diff.md`
- Machine diff: `reports/anchor_a0_recipe_config_diff.json`
- Canonical run directory: `experiments/runs/anchor_a0_recipe_3b_geo3k_20260709T213030Z`
- Canonical run manifest: `experiments/runs/anchor_a0_recipe_3b_geo3k_20260709T213030Z/run_manifest.json`
- Node/GPU allocation: `an12`, GPUs `0,1,2,3`
- PID at first post-launch inspection: `2686511`
- Config hash: `5bed99b9ec8204e05f77c237d217ef3b6c509c2263c9e225599bf217889fed39`
- Data hash: `f86c700640e1f72dea6ac8acb3004e74e38e1ffb262f36a994d54114d6d6cc56`
- Foreground diagnostic: exact EasyR1 entrypoint bounded by `timeout 180s` on `an12`, GPUs `0,1,2,3`, 2026-07-10 05:52-05:55 CST.
- First hardened relaunch: `experiments/runs/anchor_a0_recipe_3b_geo3k_20260709T215715Z`; failed before allocation with an explicit `AF_UNIX path length cannot exceed 107 bytes` error.
- Second hardened relaunch: `experiments/runs/anchor_a0_recipe_3b_geo3k_20260709T215854Z`; completed full step-0 validation and a 1,280-response rollout, then failed before optimizer step 1 with `NameError: unpad_input is not defined`.
- Immutable SDPA retry: `experiments/runs/anchor_a0_recipe_3b_geo3k_20260709T222659Z`; failed during step-0 validation when the 302-example multimodal batch stalled and aborted in `all_gather_data_proto`.

Config highlights:
- `rollout_batch_size: 512`
- `worker.actor.global_batch_size: 128`
- `worker.rollout.n: 5`
- `data.max_response_length: 2048`
- `worker.actor.model.freeze_vision_tower: false`
- `trainer.val_before_train: true`
- `trainer.val_freq: 10`
- `worker.rollout.val_override_config: {temperature: 0.0, top_p: 1.0, n: 1}`
- `trainer.save_freq: 20`
- `trainer.save_limit: -1`
- `trainer.max_steps: 100`

Known deviation:
- A duplicate debug launch was accidentally submitted at `experiments/runs/anchor_a0_recipe_3b_geo3k_20260709T213103Z` and then stopped intentionally. The canonical P1.1 attempt is the `20260709T213030Z` run.
- The first canonical attempt was stopped at 2026-07-09T21:36:27Z after more than five minutes with zero log bytes and no GPU allocation. Its manifest honestly records `status: fail`.
- The foreground diagnostic was intentionally terminated after 180 seconds during vLLM CUDA-graph capture; its SIGTERM/core-dump text reflects the external timeout, not an internal EasyR1 crash.
- The first hardened relaunch used a descriptive `RAY_TMPDIR` whose generated plasma-store socket path exceeded Linux's 107-byte limit. Its manifest records `status: fail`; the launcher now uses a deterministic 12-hex hash under `/tmp/bg-ray-*`, covered by `tests/test_run_paths.py`.
- The second relaunch exposed that EasyR1's `padding_free=true` path depends on `flash_attn.bert_padding`. The project environment intentionally uses SDPA and has no FlashAttention, so actor/reference padding-free execution is disabled and covered by `tests/test_easyr1_sdpa_patch.py`.
- A subsequent pre-training retry exposed that EasyR1's file logger truncates logs in a shared checkpoint directory. The launcher now overrides `save_checkpoint_path` and `experiment_name` with the immutable run id and uses `flock --no-fork` so the recorded PID owns the full process group.
- The first immutable retry showed that `val_batch_size=1024` creates one oversized multimodal object-gather for the full 302-example split. The full split remains unchanged, but validation now iterates in batches of 32.

Problems:
- The failed attempt and an accidental second launch overlapped in time, making Ray startup contention the leading explanation for the silent stall. The launcher previously had no duplicate-process guard or per-run Ray temporary directory.
- P1.1 still lacks the required step-0 validation point, training curves, and completed checkpoints.
- The raw log contains the step-0 validation generation and reward output, but the metric point still needs extraction into the report table.

Decision:
- Harden the launcher with duplicate-process detection, a node lock, a per-run `RAY_TMPDIR`, unbuffered output, and a five-second liveness check.
- Use padded actor/reference tensors under SDPA; retain `padding_free=true` only in a FlashAttention environment.
- Do not claim P1.1 completion until a canonical run completes with checkpoints/curves or produces a diagnosed failure log.

Next actions:
- Launch exactly one replacement canonical run with the hardened launcher.
- Allow the expected Ray/FSDP/vLLM initialization window and verify log growth plus GPU allocation before classifying startup.
- Extract step-0 and per-checkpoint curves after completion.
