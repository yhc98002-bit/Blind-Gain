# M11 Model Constructor Preflight V1

Status:
- Both staged architectures construct successfully under Accelerate empty weights
  with CUDA hidden, after applying one tracked InternVL compatibility repair.
- This is no-weight implementation evidence. It contains no generated answer or
  performance metric, and M11 remains `blocked` pending GPU smoke and full audit.

InternVL defect found:
- Transformers `4.56.2` no longer gives custom `PreTrainedModel` subclasses an
  inherited `GenerationMixin`.
- Staged InternVL3-9B constructs its nested language model as
  `InternLM2ForCausalLM`, whose observed MRO omitted `GenerationMixin` and whose
  `generate` attribute was absent.
- InternVL's tracked `chat()` path calls `self.language_model.generate(...)`.
  Without repair, the first real generation would fail after loading 9.14 billion
  parameters.

Tracked repair:
- `ensure_internvl_generation_compatibility()` leaves already-compatible models
  unchanged. Otherwise it creates a runtime subclass of the exact staged language
  model class plus Transformers' `GenerationMixin`, then switches only that
  language-model instance to the compatible class.
- The model checkout and its checksum manifest are not modified.
- The helper verifies `generate` is callable after repair and is idempotent.
- `InternVL3Adapter.load()` records whether the repair was applied before moving
  the model to its selected device.
- Every FlipTrack and ViRL row and aggregate now records backend-specific runtime
  metadata. Resume validation and the final M11 builder reject a missing/non-
  callable generation path, wrong timm version, unpinned Gemma processor, or
  inconsistent backend metadata.

Adversarial evidence:
- `test_internvl_generation_shim_repairs_transformers_456_break` models the exact
  missing-method failure, verifies original language-model behavior survives,
  verifies `generate` becomes callable, and verifies a second application is a
  no-op. The prior adapter fails because the helper does not exist.
- Focused adapter suite: 11/11 passed.
- Combined adapter, resume, aggregate, and final-builder checks: 22/22 passed.

Real staged empty-weight evidence:

| Backend | Resolved class | Parameters | Devices | Generation state | Result |
| --- | --- | ---: | --- | --- | --- |
| InternVL3-9B | `transformers_modules.InternVL3-9B.modeling_internvl_chat.InternVLChatModel` | 9,138,793,472 | `meta` only | shim applied=true; second application=false; nested `generate` callable | pass |
| Gemma-3-12B-IT | `transformers.models.gemma3.modeling_gemma3.Gemma3ForConditionalGeneration` | 13,194,203,760 | `meta` only | top-level `generate` callable without repair | pass |

Controls:
- Node: `an29`; `CUDA_VISIBLE_DEVICES` empty; local-files-only Transformers mode.
- No safetensor shard was loaded and no GPU memory was allocated.
- InternVL uses pinned `timm==0.9.12`; Gemma uses pinned slow processor mode.
- The informational FlashAttention warning is expected because the InternVL
  adapter explicitly requests `use_flash_attn=False`.

Decision:
- Use the tracked runtime shim rather than mutating checksum-pinned model source or
  downgrading the shared Qwen/EasyR1 Transformers environment.
- Keep the six-cell GPU smoke barrier. Empty-weight construction does not prove
  weight loading, image preprocessing, or token generation.
- Keep M11 blocked until all registered result cells and the final report builder
  pass.

Next actions:
- The literal `python -m pytest tests/` suite passed 539/539 in 301.73 seconds
  after the adapter repair and runtime-metadata audit wiring.
- Commit and push before any capacity-gated child starts so its run manifest pins
  the repaired adapter revision.
- Observe real smoke model load, selected-GPU placement, real/no-image/caption
  generation, and output contracts before the full phase opens.
