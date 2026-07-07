# Stage 1 FlipTrack V0

Status:
- Renderable FlipTrack families are implemented for charts, documents/OCR, and geometry.
- Smoke manifest has 30 pairs; expanded renderable manifest has 900 pairs, 300 per family.
- Every pair has image A/B, question, answer A/B, changed-region masks, category, template ID, provenance, verifier fields, and artifact-gate score.
- Qwen2.5-VL-3B baselines are complete for real, gray, and noise images on the 900-pair manifest.
- Base-model caption generation and caption-only QA are complete for the 900-pair manifest as an A3-style artifact.

Evidence:
- Generators: `src/fliptrack/render_chart.py`, `src/fliptrack/render_doc.py`, `src/fliptrack/render_geometry.py`
- Build script: `src/fliptrack/build_renderable_v0.py`
- Artifact gate scaffold: `src/fliptrack/artifact_gate.py`
- Metric code: `src/eval/fliptrack_metrics.py`
- Smoke manifest: `data/fliptrack_v0_manifest.jsonl`
- Expanded manifest: `data/fliptrack_renderable_900_manifest.jsonl`
- Real baseline: `experiments/runs/qwen25vl3b_fliptrack900_20260707T210537Z/metrics/aggregate.json`
- Gray baseline: `experiments/runs/qwen25vl3b_fliptrack900_gray_20260707T210856Z/metrics/aggregate.json`
- Noise baseline: `experiments/runs/qwen25vl3b_fliptrack900_noise_20260707T211055Z/metrics/aggregate.json`
- Captions: `experiments/runs/qwen25vl3b_fliptrack900_captions_20260707T211418Z/shards/`
- Caption-only QA: `experiments/runs/qwen25vl3b_fliptrack900_captionqa_20260707T211916Z/metrics/aggregate.json`
- 7B real baseline: `experiments/runs/qwen25vl7b_fliptrack900_real_20260707T212653Z/metrics/aggregate.json`
- 7B gray baseline: `experiments/runs/qwen25vl7b_fliptrack900_gray_20260707T212723Z/metrics/aggregate.json`
- 7B noise baseline: `experiments/runs/qwen25vl7b_fliptrack900_noise_20260707T213101Z/metrics/aggregate.json`
- 7B captions: `experiments/runs/qwen25vl7b_fliptrack900_captions_20260707T213451Z/shards/`
- 7B caption-only QA: `experiments/runs/qwen25vl7b_fliptrack900_captionqa_20260707T214548Z/metrics/aggregate.json`

Current Metrics:

| Mode | n | Pair accuracy | Member accuracy | Collapse rate | Null mean | p_ge |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 3B real images | 900 | 0.9989 | 0.9994 | 0.0000 | 0.4993 | 0.0010 |
| 3B gray images | 900 | 0.0000 | 0.1689 | 1.0000 | 0.0000 | 1.0000 |
| 3B noise images | 900 | 0.0800 | 0.1744 | 0.6400 | 0.0764 | 0.3357 |
| 3B base-model captions | 900 | 0.9967 | 0.9983 | 0.0000 | 0.4982 | 0.0010 |
| 7B real images | 900 | 1.0000 | 1.0000 | 0.0000 | 0.4999 | 0.0010 |
| 7B gray images | 900 | 0.0000 | 0.1667 | 1.0000 | 0.0000 | 1.0000 |
| 7B noise images | 900 | 0.0089 | 0.1700 | 0.6044 | 0.0056 | 0.0629 |
| 7B base-model captions | 900 | 1.0000 | 1.0000 | 0.0000 | 0.4999 | 0.0010 |

Problems:
- Renderable V0 is too easy for Qwen2.5-VL-3B under real images; it is a clean visual-dependence probe, not yet a difficult final benchmark.
- Artifact gate is still a simple metadata/statistical scaffold; DINOv2/frequency attacker ensemble is not implemented yet.
- Natural-scene pipeline remains a scaffold and needs detector/editor/verifier integration.

Decision:
- Use renderable V0 for early discrimination and pipeline validation.
- Add harder templates and natural-scene families before freezing the human-audit eval split.
- Treat gray/noise collapse as the first sanity check that FlipTrack is measuring visual dependence under controlled renderable conditions.

Next actions:
- Audit metric code against toy cases remains passed; next audit is artifact gate/verifier before mass production.
- Add DINOv2/frequency attacker probes and report filtering statistics before any frozen split.
- Add harder templates because caption-only QA saturates renderable V0 at both 3B and 7B.
