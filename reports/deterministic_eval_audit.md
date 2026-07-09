# Deterministic Eval Audit

Status:
- FlipTrack evaluator uses greedy decoding (`do_sample=False`) and fixed max tokens.
- Gray/noise image materialization is deterministic by image path and seed.
- GRPO pre/post deterministic eval for Geometry3K is not implemented yet.

Evidence:
- Evaluator: `scripts/eval_qwen_vl_fliptrack.py`
- Aggregator: `scripts/aggregate_fliptrack_eval.py`
- Metrics: `src/eval/fliptrack_metrics.py`

Decision:
- Pass for FlipTrack baseline evaluation.
- Partial for GRPO recovery until base-vs-checkpoint eval is added.
