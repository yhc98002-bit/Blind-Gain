# Local Serving Smoke

Status:
- Qwen2.5-VL-3B local inference works through Transformers on `an12`.
- vLLM `0.7.3` loads Qwen2.5-VL-3B on `an12` GPU0 and answers the same visual chart probe correctly.
- Batch evaluator works for renderable FlipTrack real, gray, and noise image modes.
- Qwen2.5-VL-7B local Transformers evaluation works for real, gray, noise, caption-generation, and caption-only QA modes.

Evidence:
- Transformers chart smoke: `reports/qwen25vl3b_smoke.jsonl`
- vLLM chart smoke log: `reports/vllm_qwen25vl3b_smoke.log`
- 20-pair smoke metrics after parser fix: `reports/qwen25vl3b_fliptrack20_metrics_recomputed.json`
- 900-pair real-image baseline: `experiments/runs/qwen25vl3b_fliptrack900_20260707T210537Z/metrics/aggregate.json`
- 900-pair gray baseline: `experiments/runs/qwen25vl3b_fliptrack900_gray_20260707T210856Z/metrics/aggregate.json`
- 900-pair noise baseline: `experiments/runs/qwen25vl3b_fliptrack900_noise_20260707T211055Z/metrics/aggregate.json`
- 900-pair caption-only QA baseline: `experiments/runs/qwen25vl3b_fliptrack900_captionqa_20260707T211916Z/metrics/aggregate.json`
- 7B real-image baseline: `experiments/runs/qwen25vl7b_fliptrack900_real_20260707T212653Z/metrics/aggregate.json`
- 7B gray-image baseline: `experiments/runs/qwen25vl7b_fliptrack900_gray_20260707T212723Z/metrics/aggregate.json`
- 7B noise-image baseline: `experiments/runs/qwen25vl7b_fliptrack900_noise_20260707T213101Z/metrics/aggregate.json`
- 7B caption-only QA baseline: `experiments/runs/qwen25vl7b_fliptrack900_captionqa_20260707T214548Z/metrics/aggregate.json`
- Real-image Qwen2.5-VL-3B: pair accuracy `0.9989`, member accuracy `0.9994`, collapse rate `0.0`.
- Gray-image Qwen2.5-VL-3B: pair accuracy `0.0`, member accuracy `0.1689`, collapse rate `1.0`.
- Noise-image Qwen2.5-VL-3B: pair accuracy `0.08`, member accuracy `0.1744`, collapse rate `0.64`.
- Caption-only Qwen2.5-VL-3B from base-model captions: pair accuracy `0.9967`, member accuracy `0.9983`, collapse rate `0.0`.
- Real-image Qwen2.5-VL-7B: pair accuracy `1.0`, member accuracy `1.0`, collapse rate `0.0`.
- Gray-image Qwen2.5-VL-7B: pair accuracy `0.0`, member accuracy `0.1667`, collapse rate `1.0`.
- Noise-image Qwen2.5-VL-7B: pair accuracy `0.0089`, member accuracy `0.1700`, collapse rate `0.6044`.
- Caption-only Qwen2.5-VL-7B from base-model captions: pair accuracy `1.0`, member accuracy `1.0`, collapse rate `0.0`.

Problems:
- vLLM exits with a PyTorch process-group teardown warning; smoke output is valid, but serving wrapper should explicitly clean up distributed state before long-lived service use.
- Renderable FlipTrack is currently easy for the base model with real images; it is still useful as a controlled visual-dependence probe but not as a hard benchmark.

Decision:
- Use Transformers scripts for deterministic evaluation until vLLM batch serving is wrapped cleanly.
- Keep gray/noise evaluation modes in the same evaluator to measure blind-eval deltas with identical prompts and decoding.

Next actions:
- Run a harder renderable template pass because both real images and captions saturate V0.
- Add vLLM batch server/client only after the teardown warning is handled.
