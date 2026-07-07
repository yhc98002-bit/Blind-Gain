# Model Downloads

Status:
- No model weights have been downloaded yet.
- Preferred ModelScope targets are identified:
  - `Qwen/Qwen2.5-VL-3B-Instruct`
  - `Qwen/Qwen2.5-VL-7B-Instruct`
  - `Qwen/Qwen3-VL-8B-Instruct`
- Download tooling is pending shared `.venv` bootstrap.

Evidence:
- ModelScope pages were found for all three target model IDs.
- Local registry helper exists at `src/data/model_registry.py`.
- Artifact registry path: `experiments/manifests/model_registry.jsonl`.

Problems:
- Qwen2.5-VL-3B license needs verification before redistribution.
- Compute nodes cannot download directly; downloads should run from login node into `artifacts/models/`.

Decision:
- Start with Qwen2.5-VL-3B for pilot if license permits research use.
- Keep Qwen2.5-VL-7B as main default; Qwen3-VL-8B remains candidate after stack compatibility check.

Next actions:
- After `.venv` has ModelScope, run ModelScope snapshot downloads on login node.
- Record URL, source, revision, license, local path, and checksum/tree hash in `experiments/manifests/model_registry.jsonl`.

