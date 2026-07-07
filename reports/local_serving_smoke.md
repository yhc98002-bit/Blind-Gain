# Local Serving Smoke

Status:
- Local VLM client scaffold exists at `src/eval/local_vlm_client.py`.
- Serving smoke is not yet run because model weights and GPU Python stack are pending.

Evidence:
- Environment checks: `reports/env_an12.json`, `reports/env_an29.json`.
- Shared environment bootstrap log pointer: `logs/setup/bootstrap_env_login_fg.latest`.

Problems:
- vLLM/Transformers not yet installed in a usable compute-node environment.
- No Qwen-VL weights downloaded yet.

Decision:
- Use Transformers client first for deterministic 20-example smoke.
- Add vLLM serving after model weights load successfully.

Next actions:
- Run a 20-example renderable FlipTrack prompt smoke after Qwen2.5-VL-3B is downloaded.

