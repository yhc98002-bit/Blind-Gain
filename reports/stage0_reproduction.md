# Stage 0 Reproduction Anchor

Status:
- EasyR1 was selected as the first GRPO/VLM reproduction anchor because its public examples include Qwen2.5-VL-3B on Geometry3K.
- Geometry3K is cached locally from Hugging Face; train/test splits load offline from shared storage.
- A local smoke config is running for 2 max steps on `an12` GPUs 0-1 with Qwen2.5-VL-3B.
- The first attempt failed at model load because EasyR1 forced FlashAttention2 while `flash_attn` is not installed.
- The active retry uses a local EasyR1 patch that honors `EASYR1_ATTN_IMPLEMENTATION=sdpa`; it has passed dataset load, actor/ref load, vLLM rollout initialization, and is in the short GRPO training loop.
- The active retry also entered full Geometry3K validation (`76` batches), so it is slower than intended for a smoke run.

Evidence:
- Upstream EasyR1 repo: `artifacts/repos/EasyR1` at `dd71bbd252694f5f850213eec15795b6b88d9fea`
- Reference example: `artifacts/repos/EasyR1/examples/qwen2_5_vl_3b_geo3k_grpo.sh`
- Local config: `configs/train/easyr1_qwen25vl3b_geo3k_smoke.yaml`
- Launcher: `scripts/launch_easyr1_geo3k_smoke.sh`
- Tracked local patch note: `docs/easyr1_sdpa_patch.diff`
- Failed run log: `experiments/runs/easyr1_geo3k_smoke_20260707T212608Z/logs/an12.log`
- Active run log: `experiments/runs/easyr1_geo3k_smoke_20260707T214035Z/logs/an12.log`
- FlashAttention install logs: `experiments/logs/setup/install_flash_attn.log`, `experiments/logs/setup/install_flash_attn_retry.log`
- Geometry3K cache log: `experiments/logs/downloads/geometry3k_cache.log`

Problems:
- FlashAttention2 is not available in the current environment. Installing it against the current driver/Torch stack hit packaging/cache issues, so the smoke run uses SDPA instead.
- The SDPA compatibility patch is currently applied only inside ignored `artifacts/repos/EasyR1`; the exact diff is tracked for reapplication, but a longer run should vendor or automate it more cleanly.
- The smoke job is intentionally tiny and is not yet a scientific reproduction result.
- Validation volume is currently larger than intended; the next smoke config should use a tiny validation slice or disable validation more explicitly.

Decision:
- Continue with SDPA for the smoke because it tests the reward/data/Ray/vLLM/FSDP path without forcing a CUDA stack change.
- Keep 3B as the reproduction scale until the EasyR1 path completes a clean short run.

Next actions:
- On completion, record exit status, checkpoint path, generated validation outputs, and wall-clock.
- Audit reward parser, image preprocessing, chat template, and deterministic eval path before any longer GRPO run.
