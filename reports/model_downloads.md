# Model Downloads

Status:
- Qwen2.5-VL-3B-Instruct downloaded from ModelScope and registered.
- Qwen2.5-VL-7B-Instruct downloaded from ModelScope and registered.
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

Problems:
- License and redistribution are still recorded as `VERIFY`; do not redistribute model weights until the license text is reviewed.
- Compute nodes cannot download directly, so all large model acquisition runs on the login node.

Decision:
- Use Qwen2.5-VL-3B for Stage 0/Stage 1 smoke, baseline eval, caption generation, and GRPO reproduction setup.
- Use Qwen2.5-VL-7B as the main-scale candidate after the compatibility smoke pass.

Next actions:
- Inspect downloaded `LICENSE`/README files and update `reports/license_log.csv`.
- Use 7B as the main-scale candidate for the next reproduction/pilot run unless EasyR1 stability forces a 3B-only Stage 2 pilot.
