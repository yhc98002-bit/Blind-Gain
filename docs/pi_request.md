# PI Request

Please provide when convenient; I am proceeding with local defaults meanwhile.

1. Qwen API key, preferably DashScope/Qwen-VL capable.
   - Use only for spot checks, judge calibration, and difficult VLM verification.
   - Bulk generation/evaluation will default to local deployment on the A800 nodes.
2. ModelScope account/token if Qwen or editor models are gated.
3. Canonical project storage path and quota confirmation.
   - Minimum target: several TB for models, datasets, checkpoints, generated images, logs, and evaluations.
4. Git remote for code, configs, manifests, and reports.
5. Experiment tracking preference.
   - Default if no answer: local TensorBoard plus structured JSONL logs.
6. Human audit commitment after Stage 1.
   - Small PI/team audit of the frozen FlipTrack eval split, examples, and failure report.
7. Paper constraints.
   - Venue preference, anonymity constraints, release restrictions, institutional licensing constraints.
8. Network clarification.
   - I see `7890` on login-node localhost only and no active `3138` listener. Please confirm the canonical domestic proxy endpoint if one exists.

Default Qwen recommendation:
- Use local deployment for bulk work because we have 16 A800s and ModelScope is preferred.
- Use API only for calibration/judge fallback or cases where local models are too weak.

