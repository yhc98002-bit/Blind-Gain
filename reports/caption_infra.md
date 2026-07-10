# Caption Infrastructure

Status:
- The reusable content-hash caption store is implemented and tested.
- Geometry3K train+test and the repacked R8 candidate images are complete at 384 tokens with both Qwen2.5-VL-3B and 7B.
- P1.8 remains blocked only because R8 failed scientific retention; a final V0.2 package will be re-encoded and therefore must be captioned again under its new hashes.

Evidence:
- Implementation: `src/captioning/store.py`, `scripts/caption_image_store.py`, and `scripts/launch_caption_store_shards.sh`.
- Schema: `blind-gains.caption-store.v1`; each row is keyed by SHA256 of image bytes and records duplicate paths, model path, prompt hash, token budget, and decoding settings.
- Decoding is fixed to greedy: temperature 0, top-p 1.0, one output, maximum 384 new tokens.
- Prompt SHA256: `9e8a66fb1fd5b8edc40647c670b0c8d75a99c1552a8edf307131d7648bd00ae0`.

Fixed question-blind prompt:
```text
Describe the image in one concise paragraph. Include visible text, labels, numbers, colors, shapes, counts, and spatial relations that could matter for answering questions.
```

Completed stores:
| Corpus | Model | Unique images | GPUs | Elapsed | Aggregate images/s | Shard bytes | Artifact SHA256 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Geometry3K train+test | Qwen2.5-VL-3B | 1,736 | 3 | 23m30s | 1.231 | 1,811,336 | `9c87a198b3398a37b0bfe0158f696fc0ec562494fc38ac3b3f30b8b8ea3c76e5` |
| Geometry3K train+test | Qwen2.5-VL-7B | 1,736 | 3 | 27m42s | 1.045 | 2,074,313 | `43316c1b688171ee3b39e16b1f8eed702d8373e7079da306eaf2581d644027fa` |
| FlipTrack R8 repacked candidate | Qwen2.5-VL-3B | 1,400 | 3 | 35m18s | 0.661 | 1,609,913 | `14769cf10b667c5c9df025dfc07a52c0097206811522c51821b48fa8daa2efde` |
| FlipTrack R8 repacked candidate | Qwen2.5-VL-7B | 1,400 | 2 | 52m50s | 0.442 | 1,835,903 | `d8004e642dafb5183c2353cc0e835d0f14dba843bea94a4cda74f7d97a332c52` |

Run directories:
- `experiments/runs/geometry3k_qwen25vl3b_captionstore384_20260710T005300Z`
- `experiments/runs/geometry3k_qwen25vl7b_captionstore384_20260710T011700Z`
- `experiments/runs/fliptrack_v02r8_qwen25vl3b_captionstore384_20260710T013000Z`
- `experiments/runs/fliptrack_v02r8_qwen25vl7b_captionstore384_20260710T013000Z`

Budget comparison:
| Template/model | 160-token caption pair accuracy | 384-token caption pair accuracy | Difference |
| --- | ---: | ---: | ---: |
| R7 eight-point geometry, Qwen2.5-VL-7B | 0.1633 | 0.1700 | +0.0067 at 384 |

- 160-token captions: `experiments/runs/fliptrack_v02r7_qwen25vl7b_captions160_20260710T011700Z`.
- 160-token QA: `experiments/runs/fliptrack_v02r7_qwen25vl7b_captionqa160_20260710T020500Z`.
- 384-token captions/QA: `experiments/runs/fliptrack_v02r7_qwen25vl7b_captions384_20260710T010800Z` and `experiments/runs/fliptrack_v02r7_qwen25vl7b_captionqa384_20260710T014100Z`.
- Both budgets violate the registered 0.15 ceiling. The shorter budget does not rescue R7.

Problems:
- R8 is a linter-valid but scientifically rejected candidate. Its stores are useful infrastructure evidence, not captions for a frozen evaluation release.
- Single-image eager generation leaves throughput below a batched vLLM implementation; correctness and resumable deterministic shards were prioritized for this gate.

Decision:
- Reuse the current schema and prompt for A3 and future caption-only evaluations.
- Never reuse an old caption after package re-encoding unless the new content hash matches exactly.
- Keep the token budget at 384 for certification; the 160-token result is a sensitivity diagnostic only.

Next actions:
- Caption the final packaged V0.2 images with both models after P1.6 retention and P1.4 re-encoding.
- Merge shards into a read-only hash index for A3 data loading without changing row content.
