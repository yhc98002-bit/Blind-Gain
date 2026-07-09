# Training Stack Decision

Status:
- EasyR1 remains the primary recovery stack for Qwen2.5-VL-3B GRPO because it has a direct Geometry3K recipe and already completed a 2-step smoke.
- verl remains a viable fallback/reference because the cloned repo includes Qwen2.5-VL and Qwen3-VL GRPO examples, including `examples/grpo_trainer/run_qwen2_5_vl_7b_fsdp.sh`.
- The current environment is not a clean upstream EasyR1 environment: it uses `torch 2.5.1+cu121`, `transformers 4.56.2`, and `vllm 0.7.3`.

Evidence:
- EasyR1 requirements include `flash-attn>=2.4.3`, `vllm>=0.8.0`, and `transformers>=4.54.0,<5.0.0`.
- Current cluster driver is `535.104.12`; earlier `vllm>=0.8` install would force a newer Torch/CUDA stack, so it was not adopted in the shared Qwen2.5-VL environment.
- EasyR1 direct recipes:
  - `artifacts/repos/EasyR1/examples/qwen2_5_vl_3b_geo3k_grpo.sh`
  - `artifacts/repos/EasyR1/examples/qwen2_5_vl_7b_geo3k_grpo.sh`
- verl references:
  - `artifacts/repos/verl/examples/grpo_trainer/run_qwen2_5_vl_7b_fsdp.sh`
  - `artifacts/repos/verl/docs/ascend_tutorial/model_support/model_and_algorithm_support.md`

Problems:
- Upstream EasyR1 hardcodes FlashAttention2 for model loading. `flash_attn` is absent in the current env.
- The previous smoke used a manual local SDPA patch. That is now documented as `docs/easyr1_sdpa_patch.diff` and automated by `scripts/apply_easyr1_sdpa_patch.sh`.
- This is still not a containerized clean install. It is a reproducible recovery stack, not the final release environment.

Decision:
- Use EasyR1 with the explicit SDPA patch for the 30-step recovery anchor.
- Keep verl as the backup if EasyR1 shows persistent instability after the recovery run.
- Do not upgrade the shared Qwen2.5-VL environment for Qwen3-VL. Qwen3-VL requires a separate environment because newer Transformers/vLLM expectations can break current Qwen2.5-VL runs.

Next actions:
- If the 30-step EasyR1 recovery run passes, freeze this env as the engineering anchor and add a clean Apptainer/container recipe.
- If it fails before 30 steps, root-cause from the run log and decide whether to repair EasyR1 or switch to verl.
