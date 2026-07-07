# Stage 0 Cluster Bring-Up

Status:
- SSH works for `an12` and `an29`.
- Both nodes expose 8x NVIDIA A800 80GB PCIe GPUs, driver `535.104.12`.
- GPU utilization logging is running on both nodes at 5 minute cadence.
- Topology and GPU inventory files are captured.
- Shared project storage `/XYFS02` has about 8.1P available.
- A 30-pair renderable FlipTrack smoke set was generated while GPU stack setup runs.

Evidence:
- `reports/gpu_inventory.json`
- `reports/nvidia_topo_an12.txt`
- `reports/nvidia_topo_an29.txt`
- `reports/env_an12.json`
- `reports/env_an29.json`
- `reports/env_login.json`
- `reports/disk_an12.txt`
- `reports/disk_an29.txt`
- `logs/gpu_util_an12.jsonl`
- `logs/gpu_util_an29.jsonl`
- `data/fliptrack_v0_manifest.jsonl`
- `data/fliptrack_v0_manifest_scored.jsonl`
- Reward/metric tests: `PYTHONPATH=. python3 -m pytest tests/test_reward_parser.py tests/test_fliptrack_metrics.py` passed 10 tests.

Problems:
- Compute-node system Python has no PyTorch, Transformers, ModelScope, vLLM, or verl.
- Compute nodes cannot resolve external hostnames directly; localhost proxy ports are not present on compute nodes.
- SSH reverse tunnels work in foreground but detached tunnels are unstable under the cluster SSH wrapper.
- `python3 -m venv` is missing `ensurepip`; bootstrap must use `virtualenv` fallback.
- GPUs are still idle because no CUDA Python stack is installed yet. Current safe work is environment/model acquisition on login/shared storage plus CPU data generation.

Decision:
- Build the shared `.venv` and download models on the login node, where direct domestic PyPI/ModelScope and `7890` proxy access work, then run GPU sanity checks from the shared environment on `an12`/`an29`.
- Keep ModelScope direct for large model downloads when possible; use Hugging Face/GitHub through explicit `7890` only as fallback.
- Treat Qwen2.5-VL-3B license as verification-needed before redistribution because public metadata is inconsistent.

Next actions:
- Finish shared `.venv` bootstrap from `logs/setup/bootstrap_env_login_fg.latest`.
- Run single-node PyTorch CUDA/DDP sanity on `an12` and `an29`.
- Install/verify vLLM and launch a 3B local serving smoke test.
- Start ModelScope downloads for Qwen2.5-VL-3B and Qwen2.5-VL-7B/Qwen3-VL-8B after ModelScope tooling is available.
- Expand FlipTrack renderable v0 and start verifier/artifact-gate audits.

