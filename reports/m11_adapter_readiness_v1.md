# M11 Non-Qwen Adapter Readiness V1

Status:
- Deterministic InternVL3 and Gemma-3 adapters and an immutable TP1 launcher are
  implemented and CPU-tested.
- No non-Qwen performance result has been produced. GPU smoke and batch inference
  are queued until a pilot GPU is free; M11 remains `blocked`.

Implementation:
- `src/eval/nonqwen_adapters.py` owns backend-specific image preparation and
  generation while sharing one content contract.
- InternVL3 uses the model card's 448-pixel dynamic tiling, up to 12 patches,
  explicit multi-image numbering, `model.chat`, BF16, and `do_sample=false`.
- Gemma-3 uses `Gemma3ForConditionalGeneration`, `AutoProcessor` chat-template
  processing, BF16, and `do_sample=false`.
- `scripts/eval_nonqwen_fliptrack.py` applies the same answer-tag prompt contract,
  canonical-v2 pair scorer, and atomic non-overwrite output discipline to both
  backends.
- `scripts/launch_nonqwen_fliptrack_eval.sh` pins one node, one GPU, TP1, one
  replica, greedy decoding, temperature 0, top-p 1, n=1, and 384 output tokens in
  every run manifest.

Condition contract:

| Condition | Model payload | Fixed text source |
| --- | --- | --- |
| real | one image per pair member | registered question + answer-tag instruction |
| no-image | no image payload or image token | registered question + answer-tag instruction |
| caption | no image payload or image token | fixed 3B question-blind caption + registered question and instruction |

Caption pair identity and nonempty A/B captions are checked before model loading.
Missing/duplicate/mismatched caption IDs fail closed.

Frozen evaluation inputs:

| Split | Input | Rows | Use |
| --- | --- | ---: | --- |
| R19 | `experiments/runs/caption_qa_pair_build_fliptrack_v02r19_qwen25vl3b_384_20260710T140200Z/shards/captions_shard_0.jsonl` | 1,200 | real/no-image and fixed-3B-caption conditions |
| R20 | `experiments/runs/caption_qa_pair_build_fliptrack_r20_private_full_v1_20260711T124039Z/shards/captions_shard_0.jsonl` | 1,200 | real/no-image and fixed-3B-caption conditions |

Tests:
- `tests/test_nonqwen_adapters.py`: 8 tests pass.
- Covered failures include duplicate caption identity, missing/mismatched caption
  rows, empty captions, accidental image payload in blind conditions, unsupported
  content parts, and launcher overwrite/path/placement constraints.
- `tests/test_node_modelscope_download_launcher.py`: 2 staging/download tests pass.

Pending GPU smoke:
- Load each staged model on one free an29 GPU and run one real and one no-image
  pair before launching full cells.
- A smoke is accepted only if model load stays on the selected GPU, both outputs
  are nonempty, prompt-contract metadata is stamped, and no image tensor/token is
  present in no-image/caption conditions.
- Full R19/R20 cells launch only after the corresponding smoke; the registered
  blind-solvability sample adapter remains to be wired.
