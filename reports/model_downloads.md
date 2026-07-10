# Model Downloads

Status:
- Qwen2.5-VL-3B-Instruct downloaded from ModelScope and registered.
- Qwen2.5-VL-7B-Instruct downloaded from ModelScope and registered.
- Qwen2.5-7B-Instruct downloaded from ModelScope for the local evaluation judge and registered.
- Qwen3-VL-8B-Instruct remains a candidate but is not downloaded yet.

Evidence:
- 3B local path: `artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct`
- 3B source: `https://modelscope.cn/models/Qwen/Qwen2.5-VL-3B-Instruct`
- 3B revision: `master`
- 3B tree SHA256: `84c656fb6d6a5f4ef3ccbf47c3880c3a3d22c63eb8736a88fa7a0ddb542e3568`
- Registry: `experiments/manifests/model_registry.jsonl`
- 7B local path: `artifacts/models/Qwen/Qwen2.5-VL-7B-Instruct`
- 7B download log: `experiments/logs/downloads/qwen25vl7b_modelscope.log`
- 7B source: `https://modelscope.cn/models/Qwen/Qwen2.5-VL-7B-Instruct`
- 7B revision: `master`
- 7B tree SHA256: `82ef08f2f46f6d47aa2d3d2c2ae9b015f373be19c0a43efe81cd6f9c522d1369`
- Local judge path: `artifacts/models/Qwen/Qwen2.5-7B-Instruct`
- Local judge source: `https://modelscope.cn/models/Qwen/Qwen2.5-7B-Instruct`
- Local judge tree SHA256: `1e8d53b21b997eb18436573d3f5cc961fbaf00cd583131f6a89a05617e24c72c`
- Local judge license: Apache-2.0; bundled `LICENSE` SHA256 `832dd9e00a68dd83b3c3fb9f5588dad7dcf337a0db50f7d9483f310cd292e92e`.
- Route: ModelScope through `7890` after direct DNS failed and the documented `3138` domestic endpoint refused connections.

Problems:
- License and redistribution are still recorded as `VERIFY`; do not redistribute model weights until the license text is reviewed.
- Compute nodes cannot download directly, so all large model acquisition runs on the login node.

Decision:
- Use Qwen2.5-VL-3B for Stage 0/Stage 1 smoke, baseline eval, caption generation, and GRPO reproduction setup.
- Use Qwen2.5-VL-7B as the main-scale candidate after the compatibility smoke pass.

Next actions:
- Inspect downloaded `LICENSE`/README files and update `reports/license_log.csv`.
- Use 7B as the main-scale candidate for the next reproduction/pilot run unless EasyR1 stability forces a 3B-only Stage 2 pilot.
