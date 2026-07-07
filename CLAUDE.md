# Blind Gains Agent Notes

Operational defaults:

- Use the current directory as the project root.
- Do not overwrite checkpoints, generated data, or evaluation outputs.
- Prefer ModelScope for Qwen-family and China-hosted model artifacts.
- Use Hugging Face and GitHub through explicit proxy wrappers only when needed.
- Long-running jobs must write logs under `logs/` or immutable run directories.
- Record node, command, git hash, config hash, seed, artifact path, and deviations.

Node split:

- `an12`: RL stack, local model serving, GRPO reproduction, pilot training.
- `an29`: FlipTrack generation, verifier stack, evaluation, batch scoring.

Pause only at the gates listed in the project prompt.

