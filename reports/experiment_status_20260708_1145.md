# Blind Gains Experiment Status - 2026-07-08 11:45 CST

Status:
- Stage 0 cluster bring-up is functionally complete.
- Both compute nodes are reachable and currently active under logged GPU profile jobs.
- Qwen2.5-VL-3B and Qwen2.5-VL-7B are downloaded from ModelScope, registered, and evaluated on FlipTrack renderable V0.
- EasyR1 Qwen2.5-VL-3B GRPO smoke completed through `global_step_2` and wrote a checkpoint.
- FlipTrack renderable V0 exists with 900 generated paired examples across chart, document/OCR, and geometry families.
- A Stage 0 pass marker was created at `reports/stage0_done.json`.

## Current Node Utilization

Latest live poll:
- Timestamp: `Wed Jul 8 11:45:09 CST 2026`
- `an12`: 8x NVIDIA A800 80GB PCIe, all 8 GPUs at `100%`, each using about `727 MiB`.
- `an29`: 8x NVIDIA A800 80GB PCIe, all 8 GPUs at `100%`, each using about `727 MiB`.

Active logged background jobs:

| Node | GPUs | Purpose | Run directory |
| --- | ---: | --- | --- |
| `an12` | 0-7 | short throughput profile | `experiments/runs/an12_gpu0_7_profile_20260708T034331Z` |
| `an29` | 0-7 | short throughput profile | `experiments/runs/an29_gpu0_7_profile_20260708T034331Z` |

Interpretation:
- These are not scientific training jobs; they are safe profile jobs launched because both nodes had become idle after the completed smoke/profile runs.
- Previous experiment jobs completed cleanly; the current profiles keep the reserved GPUs active while the next research job is prepared.

## Repo State

Current committed baseline:
- `d07e8c3 Record EasyR1 smoke completion`
- Previous major checkpoint: `f917e62 Advance stage0 baselines and reproduction setup`

Working tree note:
- `prompt.md` remains untracked and is user-provided context.
- This status report and `reports/stage0_done.json` were created after the last commit.

Repository skeleton:
- Required directories are present: `configs/`, `scripts/`, `src/`, `experiments/`, `notebooks/`, `paper/`, `docs/`, and `reports/`.
- Subdirectories verified include `configs/env`, `configs/data`, `configs/train`, `configs/eval`, `src/data`, `src/fliptrack`, `src/verifiers`, `src/eval`, `src/train`, `src/rewards`, `src/analysis`, `experiments/manifests`, `experiments/logs`, and `experiments/reports`.

## Stage 0 Completion Marker

Created file:
- `reports/stage0_done.json`

Contents:

```json
{
  "status": "pass",
  "gpu_count_an12": 8,
  "gpu_count_an29": 8,
  "nccl_smoke_test": "pass",
  "modelscope_probe": "pass",
  "proxy_probe": "pass",
  "repo_skeleton": "pass"
}
```

Evidence:
- GPU counts come from `reports/gpu_inventory.json` and live `nvidia-smi` polling.
- NCCL/DDP smoke evidence is in `reports/ddp_sanity_an12.json`, `reports/ddp_sanity_an29.json`, and `reports/ddp_sanity_crossnode_an12_rank0.json`.
- Network probe evidence is in `reports/network_probe.md` and `reports/network_probe_login.md`.
- Repo skeleton was verified from the current filesystem.

## Environment And Cluster Bring-Up

Working environment:
- Shared `.venv` is usable from both nodes.
- Key stack in use: `torch 2.5.1+cu121`, `transformers 4.56.2`, `vllm 0.7.3`, EasyR1, and verl.

Passed checks:
- SSH to `an12` and `an29`.
- CUDA visibility on both nodes.
- `nvidia-smi topo -m` captured.
- Single-node DDP/NCCL checks.
- Cross-node DDP/NCCL check.
- FSDP toy training checks.
- vLLM Qwen2.5-VL-3B smoke test.

Evidence files:
- `reports/stage0_cluster_bringup.md`
- `reports/gpu_inventory.json`
- `reports/nvidia_topo_an12.txt`
- `reports/nvidia_topo_an29.txt`
- `reports/env_an12_after_vllm.json`
- `reports/env_an29_after_vllm.json`
- `reports/torch_gpu_sanity_an12.json`
- `reports/torch_gpu_sanity_an29.json`
- `reports/fsdp_toy_an12.json`
- `reports/fsdp_toy_an29.json`

Important constraint:
- Compute nodes cannot reliably resolve or download from external hosts directly.
- Downloads and package installs should run from the login node into shared storage.
- International proxy route on login works through `127.0.0.1:7890`.
- Domestic `3138` service was not discovered in this environment.

## Model Acquisition

Downloaded and registered:

| Model | Source | Local path | Tree SHA256 | License status |
| --- | --- | --- | --- | --- |
| Qwen2.5-VL-3B-Instruct | ModelScope | `artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct` | `84c656fb6d6a5f4ef3ccbf47c3880c3a3d22c63eb8736a88fa7a0ddb542e3568` | `VERIFY` |
| Qwen2.5-VL-7B-Instruct | ModelScope | `artifacts/models/Qwen/Qwen2.5-VL-7B-Instruct` | `82ef08f2f46f6d47aa2d3d2c2ae9b015f373be19c0a43efe81cd6f9c522d1369` | `VERIFY` |

Evidence:
- `experiments/manifests/model_registry.jsonl`
- `reports/model_downloads.md`
- `reports/license_log.csv`
- `reports/artifact_manifest.json`

Open issue:
- Model redistribution and release terms are still marked `VERIFY`. Do not publish weights or derived redistribution material until the model-card license review is finished.

## FlipTrack Renderable V0

Generated data:

| Manifest | Rows | Notes |
| --- | ---: | --- |
| `data/fliptrack_v0_manifest.jsonl` | 30 | smoke split |
| `data/fliptrack_v0_manifest_scored.jsonl` | 30 | scored smoke split |
| `data/fliptrack_renderable_900_manifest.jsonl` | 900 | 300 chart, 300 doc/OCR, 300 geometry |
| `data/fliptrack_renderable_900_scored.jsonl` | 900 | scored 900-pair split |

Implemented components:
- `src/fliptrack/render_chart.py`
- `src/fliptrack/render_doc.py`
- `src/fliptrack/render_geometry.py`
- `src/fliptrack/build_renderable_v0.py`
- `src/fliptrack/artifact_gate.py`
- `src/eval/fliptrack_metrics.py`

Interpretation:
- V0 is valid as a controlled visual-dependence sanity probe.
- V0 is too easy for Qwen2.5-VL with real images and for caption-only QA, so it should not be treated as the final hard benchmark.
- Harder renderable templates and natural-scene categories remain needed before freezing a human-audit eval split.

## FlipTrack Baseline Results

All rows below use the 900-pair renderable V0 manifest.

| Model / Mode | n pairs | Pair acc | Member acc | Collapse | Null mean | p_ge |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 3B real images | 900 | 0.9989 | 0.9994 | 0.0000 | 0.4993 | 0.0010 |
| 3B gray images | 900 | 0.0000 | 0.1689 | 1.0000 | 0.0000 | 1.0000 |
| 3B noise images | 900 | 0.0800 | 0.1744 | 0.6400 | 0.0764 | 0.3357 |
| 3B base-model captions | 900 | 0.9967 | 0.9983 | 0.0000 | 0.4982 | 0.0010 |
| 7B real images | 900 | 1.0000 | 1.0000 | 0.0000 | 0.4999 | 0.0010 |
| 7B gray images | 900 | 0.0000 | 0.1667 | 1.0000 | 0.0000 | 1.0000 |
| 7B noise images | 900 | 0.0089 | 0.1700 | 0.6044 | 0.0056 | 0.0629 |
| 7B base-model captions | 900 | 1.0000 | 1.0000 | 0.0000 | 0.4999 | 0.0010 |

Evidence:
- `experiments/runs/qwen25vl3b_fliptrack900_20260707T210537Z/metrics/aggregate.json`
- `experiments/runs/qwen25vl3b_fliptrack900_gray_20260707T210856Z/metrics/aggregate.json`
- `experiments/runs/qwen25vl3b_fliptrack900_noise_20260707T211055Z/metrics/aggregate.json`
- `experiments/runs/qwen25vl3b_fliptrack900_captionqa_20260707T211916Z/metrics/aggregate.json`
- `experiments/runs/qwen25vl7b_fliptrack900_real_20260707T212653Z/metrics/aggregate.json`
- `experiments/runs/qwen25vl7b_fliptrack900_gray_20260707T212723Z/metrics/aggregate.json`
- `experiments/runs/qwen25vl7b_fliptrack900_noise_20260707T213101Z/metrics/aggregate.json`
- `experiments/runs/qwen25vl7b_fliptrack900_captionqa_20260707T214548Z/metrics/aggregate.json`

Interpretation:
- Real-image performance saturates V0.
- Gray-image performance collapses completely for both 3B and 7B, which confirms the instrument requires visual evidence in this rendered setting.
- Caption-only QA also saturates V0, which means generated captions carry enough exact information for this version. This is expected for simple renderable charts/docs/geometry and reinforces the need for harder, less caption-compressible variants.

## EasyR1 GRPO Reproduction Anchor

Status:
- EasyR1 was chosen because it has a direct Qwen2.5-VL-3B Geometry3K GRPO example.
- First run failed because EasyR1 forced FlashAttention2 and `flash_attn` is not installed in the current environment.
- A local patch lets EasyR1 honor `EASYR1_ATTN_IMPLEMENTATION=sdpa`.
- Retry completed through `global_step_2`, validation, and checkpoint save.

Evidence:
- Config: `configs/train/easyr1_qwen25vl3b_geo3k_smoke.yaml`
- Launcher: `scripts/launch_easyr1_geo3k_smoke.sh`
- Patch note: `docs/easyr1_sdpa_patch.diff`
- Failed run log: `experiments/runs/easyr1_geo3k_smoke_20260707T212608Z/logs/an12.log`
- Successful run log: `experiments/runs/easyr1_geo3k_smoke_20260707T214035Z/logs/an12.log`
- Checkpoint tracker: `checkpoints/stage0_repro/easyr1_geo3k_smoke/checkpoint_tracker.json`
- Experiment metrics: `checkpoints/stage0_repro/easyr1_geo3k_smoke/experiment_log.jsonl`
- Final actor checkpoint: `checkpoints/stage0_repro/easyr1_geo3k_smoke/global_step_2/actor`

Final smoke metrics from tracker:
- `last_global_step`: `2`
- `best_global_step`: `2`
- `best_val_reward_score`: `0.0266`
- `last_actor_path`: `checkpoints/stage0_repro/easyr1_geo3k_smoke/global_step_2/actor`

Important caveat:
- The run entered full Geometry3K validation with `76` validation batches, so it was slower than a true tiny smoke. The next smoke should use a tiny validation slice or disable validation more explicitly.

## Tests And Validation

Passed:
- `PYTHONPATH=. python3 -m pytest tests/test_reward_parser.py tests/test_fliptrack_metrics.py`
- Result: `10 passed`
- Python compile checks passed for the touched evaluator, caption, profile, smoke, reward, and FlipTrack modules.
- Shell syntax checks passed for the launch scripts.

Relevant files:
- `tests/test_reward_parser.py`
- `tests/test_fliptrack_metrics.py`
- `src/rewards/answer_reward.py`
- `src/eval/fliptrack_metrics.py`

## Problems And Risks

Real blockers or near-blockers:
- Compute nodes cannot download from the internet directly. Continue using login-node downloads into shared storage.
- Qwen license/redistribution status is unresolved.
- The EasyR1 SDPA patch is currently a local patch against the ignored external clone. It is tracked as a diff, but should be applied by script or vendored cleanly before longer runs.
- FlipTrack V0 is too easy and too caption-compressible for final conclusions.
- Natural-scene FlipTrack pipeline is still a scaffold.
- DINOv2/frequency/statistical artifact attacker ensemble is not implemented yet.

Not currently blocked:
- SSH access works.
- GPU inventory and CUDA/NCCL basics are verified.
- Qwen2.5-VL-3B and 7B local inference/eval works.
- EasyR1 can run Qwen2.5-VL-3B GRPO under SDPA for a short smoke.

## Decision

- Treat Stage 0 bring-up as passed.
- Treat EasyR1 + Geometry3K as the current reproduction anchor, with ViRL39K still pending source/license verification.
- Treat FlipTrack renderable V0 as a sanity instrument, not the final benchmark.
- Keep using Transformers for deterministic local evaluation until vLLM batch serving is hardened.
- Use Qwen2.5-VL-7B as the likely main-scale candidate after the next EasyR1 stability pass.

## Next Actions

1. Build a tiny-validation EasyR1 config so smoke runs do not spend minutes on full Geometry3K validation.
2. Audit GRPO reward parser, image preprocessing, chat template, deterministic eval, and data leakage before any longer run.
3. Add harder FlipTrack renderable templates that are less caption-compressible.
4. Implement DINOv2/frequency/statistical artifact-gate attackers before mass-producing a frozen split.
5. Verify ViRL39K source/license; if blocked, continue with Geometry3K for Stage 0 reproduction and log the deviation.
6. Prepare A1/A2 3B pilot configs only after the GRPO audit passes.
