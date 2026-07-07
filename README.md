# Blind Gains

Research code and operational logs for **Blind Gains: A Controlled Decomposition
of What RLVR Actually Improves in Vision-Language Models**.

Primary goals:

- Build FlipTrack, a paired counterfactual visual-dependence evaluation.
- Reproduce a small VLM GRPO/RLVR recipe as a training anchor.
- Compare matched-compute real-image, blind-image, caption-only, and CP-GRPO arms.
- Preserve reproducibility through immutable run directories, manifests, and logs.

Current default tracking is local-first:

- TensorBoard-compatible scalar logs when training is available.
- JSONL manifests for runs, downloads, GPU utilization, and evaluations.
- Reports under `reports/` using the operational format from the project prompt.

