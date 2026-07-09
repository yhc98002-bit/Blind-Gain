# External Evaluation Harness Version

Status:
- VLMEvalKit source is pinned, installed in an isolated environment, and passes a full-package import smoke test.
- Base benchmark inference has not started, so P1.2 remains blocked.

Evidence:
- Repository: `https://github.com/open-compass/VLMEvalKit.git`
- Pinned commit: `6a02ab92471a8c544ff0769da5968a29fd75971f`
- Clone path: `artifacts/repos/VLMEvalKit`
- Environment recipe: `scripts/setup_vlmevalkit_env.sh`
- Environment config: `configs/env/vlmevalkit_p1_2.yaml`
- Isolated environment path: `artifacts/envs/vlmevalkit`
- Resolved package freeze: `artifacts/envs/vlmevalkit/requirements.freeze.txt`
- The environment reuses the validated `.venv` Torch/Transformers packages through a `.pth` file but installs benchmark-only dependencies into its own site-packages.
- The cluster Python lacks `ensurepip`; the recipe therefore falls back to the cluster-provided `virtualenv` executable when `python3 -m venv` cannot bootstrap pip.

Problems:
- The full upstream requirement set would install NumPy 2 and OpenCV 5 into the shared training environment. The isolated recipe pins NumPy 1.26.4 and OpenCV below 5 to preserve the working numerical ABI.
- Upstream imports `rouge_score` from its MMLongBench utility but omits `rouge-score` from `requirements.txt`; the local recipe pins `rouge-score==0.1.2` explicitly.
- `Qwen/Qwen2.5-7B-Instruct`, required as the local judge, is not yet available locally; its first background launcher exited before initialization and produced no log.

Decision:
- Do not modify the working training `.venv` for benchmark-harness setup.
- Use exact matching for applicable multiple-choice and yes/no datasets, and the pinned local OpenAI-compatible judge only where a judge is required.

Next actions:
- Finish the ModelScope-first local judge download and record its registry hash.
- Materialize benchmark inputs and run deterministic 3B/7B base inference.
