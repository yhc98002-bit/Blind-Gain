# Caption Infrastructure

Status:
- The reusable content-hash caption store is implemented and tested.
- Geometry3K train+test and the repacked R8 candidate images are complete at 384 tokens with both Qwen2.5-VL-3B and 7B.
- The final R19 candidate has exact-coverage 3B and 7B stores for all 2,400 release images; P1.8 passes.
- The 4,096-item ViRL39K audit manifest has exact 3B caption coverage over all 4,297 unique image hashes; a supplemental 7B store is active.

Evidence:
- Implementation: `src/captioning/store.py`, `scripts/caption_image_store.py`, `scripts/audit_caption_store.py`, and `scripts/launch_caption_store_shards.sh`.
- Schema: `blind-gains.caption-store.v1`; each row is keyed by SHA256 of image bytes and records duplicate paths, model path, prompt hash, token budget, and decoding settings.
- Decoding is fixed to greedy: temperature 0, top-p 1.0, one output, maximum 384 new tokens.
- Prompt SHA256: `9e8a66fb1fd5b8edc40647c670b0c8d75a99c1552a8edf307131d7648bd00ae0`.
- Contract enforcement: `merge_caption_rows` and the blind-evaluation loader reject the wrong schema, any prompt other than the registered literal prompt, prompt-hash drift, non-greedy decoding, token budgets below 384, mixed model/prompt/budget stores, and question/answer fields.
- Resume enforcement: a retry accepts only a canonical content-hash shard prefix with matching image path/duplicate metadata, caption model, prompt, decoding, and token budget; the new run records and hashes the failed source run.
- Machine audits: `reports/caption_store_contract_geo3k_3b.json`, `reports/caption_store_contract_geo3k_7b.json`, `reports/caption_store_contract_fliptrack_v02r19_3b.json`, `reports/caption_store_contract_fliptrack_v02r19_7b.json`, and `reports/caption_store_contract_virl39k4096_3b.json`; all checks pass with exact manifest-image coverage.

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
| FlipTrack R19 final candidate | Qwen2.5-VL-3B | 2,400 | 3 | 1h19m17s wall window | 0.505 | 2,840,433 | `85e657b2b06f3bec4fdbe49cb1e537e4ba995701042873b9f4105b33328c89fa` |
| FlipTrack R19 final candidate | Qwen2.5-VL-7B | 2,400 | 3 | 1h01m07s wall window | 0.654 | 3,158,540 | `e9f19128bd5fea96464b34fa7dbb2a4ac579b9477e57373f299bc0e22713ac4d` |
| ViRL39K 4,096-item audit | Qwen2.5-VL-3B | 4,297 | 3 | 2h10m11s | 0.550 | 5,177,446 | `b0253ce2df994638caea8fd04c65d092e025562594d4f5c446e9a1c1f3972ebb` |

Run directories:
- `experiments/runs/geometry3k_qwen25vl3b_captionstore384_20260710T005300Z`
- `experiments/runs/geometry3k_qwen25vl7b_captionstore384_20260710T011700Z`
- `experiments/runs/fliptrack_v02r8_qwen25vl3b_captionstore384_20260710T013000Z`
- `experiments/runs/fliptrack_v02r8_qwen25vl7b_captionstore384_20260710T013000Z`
- `experiments/runs/fliptrack_v02r17_qwen25vl3b_captionstore384_an12_20260710T122730Z`
- `experiments/runs/fliptrack_v02r18_qwen25vl3b_captionstore384_an12_20260710T131300Z`
- `experiments/runs/caption_store_merge_fliptrack_v02r19_qwen25vl3b_384_20260710T134825Z`
- `experiments/runs/fliptrack_v02r17_qwen25vl7b_captionstore384_an12_20260710T132519Z`
- `experiments/runs/fliptrack_v02r18_qwen25vl7b_captionstore384_an12_20260710T134741Z`
- `experiments/runs/caption_store_merge_fliptrack_v02r19_qwen25vl7b_384_20260710T142844Z`
- `experiments/runs/virl39k_sample4096_qwen25vl3b_captionstore384_20260710T094300Z`

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
- The stores establish exact question-blind caption inputs; they do not by themselves establish caption-only task accuracy, which requires the separately logged QA runs.
- One supplemental ViRL 7B launch was invalidated when two launcher invocations reached the same run directory during the expensive input hash. It is marked `fail`, its partial shard is quarantined, and an atomic pre-hash run lock now prevents recurrence.

Decision:
- Reuse the current schema and prompt for A3 and future caption-only evaluations.
- Never reuse an old caption after package re-encoding unless the new content hash matches exactly.
- Keep the token budget at 384 for certification; the 160-token result is a sensitivity diagnostic only.

Next actions:
- Treat both exact-coverage merged files as read-only hash indexes for A3 data loading without changing row content.
- Finish and contract-audit the active ViRL 7B store at `experiments/runs/virl39k_sample4096_qwen25vl7b_captionstore384_retry_20260710T163500Z`.
- Use that store only for a labeled caption-generator sensitivity evaluation; keep the registered fixed-3B-caption 7B cell unchanged.
