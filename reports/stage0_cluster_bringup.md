# Stage 0 Cluster Bring-Up

Status:
- SSH works for `an12` and `an29`.
- Both nodes expose 8x NVIDIA A800 80GB PCIe GPUs, driver `535.104.12`.
- GPU utilization logging is running on both nodes at 5 minute cadence.
- Shared `.venv` is usable from both nodes with `torch 2.5.1+cu121`, `transformers 4.56.2`, `vllm 0.7.3`, and EasyR1/verl imports.
- Single-node CUDA, DDP/NCCL, cross-node DDP/NCCL, and FSDP toy sanity checks passed.
- A 900-pair renderable FlipTrack set was generated and scored.
- All 16 GPUs have been used for Qwen2.5-VL-3B and Qwen2.5-VL-7B FlipTrack real/gray/noise evaluation, caption generation, and caption-only QA.
- EasyR1 Qwen2.5-VL-3B GRPO smoke is running on `an12` GPUs 0-1 with SDPA attention after bypassing a FlashAttention2 dependency mismatch.
- Logged synthetic GPU profiles are occupying spare devices while long jobs run: `an12` GPUs 2-7 and `an29` GPUs 0-7.

Evidence:
- GPU inventory/topology: `reports/gpu_inventory.json`, `reports/nvidia_topo_an12.txt`, `reports/nvidia_topo_an29.txt`
- Environment checks: `reports/env_an12_after_vllm.json`, `reports/env_an29_after_vllm.json`
- CUDA/DDP/FSDP checks: `reports/torch_gpu_sanity_an12.json`, `reports/torch_gpu_sanity_an29.json`, `reports/ddp_sanity_an12.json`, `reports/ddp_sanity_an29.json`, `reports/ddp_sanity_crossnode_an12_rank0.json`, `reports/fsdp_toy_an12.json`, `reports/fsdp_toy_an29.json`
- Utilization logs: `logs/gpu_util_an12.jsonl`, `logs/gpu_util_an29.jsonl`
- FlipTrack manifests: `data/fliptrack_v0_manifest.jsonl`, `data/fliptrack_renderable_900_manifest.jsonl`
- GRPO smoke log: `experiments/runs/easyr1_geo3k_smoke_20260707T214035Z/logs/an12.log`
- Tests: `PYTHONPATH=. python3 -m pytest tests/test_reward_parser.py tests/test_fliptrack_metrics.py` passed 10 tests.

Problems:
- Compute nodes cannot resolve external hostnames directly; model/package downloads must run from the login node into shared storage.
- Detached SSH reverse tunnels to compute nodes were unstable, so direct compute-node downloads are avoided.
- `vllm 0.8.5` was rejected because it would force `torch 2.6.0`/CUDA 12.4 against driver `535.104.12`; pinned `vllm 0.7.3` is compatible with current `torch 2.5.1+cu121`.
- Qwen model license/redistribution status remains `VERIFY` before public release.
- EasyR1 assumes FlashAttention2 for Qwen2.5-VL by default; the local run uses an ignored workspace patch to allow `EASYR1_ATTN_IMPLEMENTATION=sdpa`.

Decision:
- Use login-node ModelScope downloads into `/XYFS02`, then serve/train from shared storage on `an12`/`an29`.
- Use EasyR1 as the first reproduction anchor because it has a Qwen2.5-VL-3B GRPO example; keep upstream verl as fallback/reference.
- Keep renderable FlipTrack generation as the primary Stage 1 path because labels are exact by construction.

Next actions:
- Let the EasyR1 smoke complete or fail, then record wall-clock, checkpoint/eval artifacts, and the next stability fix.
- Add harder FlipTrack renderable templates and artifact-gate attacker probes.
