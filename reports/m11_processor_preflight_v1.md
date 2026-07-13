# M11 Processor Preflight V1

Status:
- The CPU-only staged-asset preflight is complete for InternVL3-9B and
  Gemma-3-12B-IT.
- This is implementation readiness evidence, not a model-performance result.
  M11 remains `blocked` until the registered GPU inference matrix and final audit
  complete.

Evidence:
- Node: `an29`; `CUDA_VISIBLE_DEVICES` was empty for every command.
- Environment: Transformers `4.56.2`, local-files-only mode, no network access.
- InternVL stage: `/dev/shm/blind-gains/models/InternVL3-9B`.
  - Config type: `internvl_chat`.
  - Architecture: `InternVLChatModel`.
  - AutoModel mapping resolves to
    `modeling_internvl_chat.InternVLChatModel`.
  - Tokenizer: `InternLM3Tokenizer`; EOS token ID `128131`.
- Gemma stage: `/dev/shm/blind-gains/models/gemma-3-12b-it`.
  - Config type: `gemma3`.
  - Architecture: `Gemma3ForConditionalGeneration`.
  - Processor: `Gemma3Processor`.
  - `Gemma3ForConditionalGeneration` imports successfully from the installed
    Transformers environment.

Problem found and fixed:
- The first Gemma processor preflight warned that `use_fast` was implicit and
  could change behavior across Transformers defaults.
- `Gemma3Adapter.load()` now explicitly calls
  `AutoProcessor.from_pretrained(..., use_fast=False)`, preserving the processor
  implementation used by this environment.
- Adversarial fixture
  `test_gemma_adapter_explicitly_pins_slow_processor` uses synthetic framework
  modules and fails against the prior implementation because the argument is
  absent. It does not load Transformers, Torch, or model weights.
- Focused result: `tests/test_nonqwen_adapters.py`, 9/9 passed.
- Real staged-asset recheck with `use_fast=False`: `Gemma3Processor`, exit code 0,
  with no processor-default warning.

Decision:
- Pin the slow processor explicitly for M11 rather than accepting a version-
  dependent default.
- Keep all M11 child jobs TP1, greedy, and local-files-only as already registered.
- Do not inspect or report model performance before the queued smoke/full phases.

Next actions:
- The literal `python -m pytest tests/` suite passed 536/536 tests in 255.81
  seconds after the adapter and capacity-gate changes.
- Commit and push the changes before any queued M11 child starts, so every child
  run manifest records a revision containing the processor pin.
- Continue waiting for all four M2 prerequisite manifests; then execute the
  fail-closed smoke and full matrices.
