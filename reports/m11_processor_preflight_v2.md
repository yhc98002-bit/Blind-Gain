# M11 Processor Preflight V2

Status:
- Both staged non-Qwen processor/config stacks and their model-class import paths
  now pass with CUDA hidden.
- M11 remains `blocked`: this preflight contains no generation or performance
  result, and the six registered GPU smoke cells have not run.

V1 residual found:
- V1 verified the InternVL config and tokenizer but did not import the remote
  `InternVLChatModel` class itself.
- The first class import failed before any model allocation:
  `ModuleNotFoundError: No module named 'timm'`, originating from
  `modeling_intern_vit.py` importing `timm.layers.DropPath`.
- This was a real runtime dependency gap; allowing the GPU smoke to discover it
  would have consumed a scarce slot without testing inference.

Repair:
- Added `configs/env/m11_inference_requirements.txt` with exact pin
  `timm==0.9.12`.
- Added the same M11 dependency contract to
  `configs/env/easyr1_or_verl_recovery.yaml`.
- The pin follows OpenGVLab InternVL's official chat requirements:
  `https://github.com/OpenGVLab/InternVL/blob/main/requirements/internvl_chat.txt`.
- The direct Tsinghua-mirror attempt failed after five retries with
  `Device or resource busy`; the logged fallback used the same mirror through the
  explicit `7890` proxy. No global proxy setting was changed.
- Installation added only `timm 0.9.12`; Torch, torchvision, PyYAML,
  huggingface-hub, and safetensors were already satisfied.

Post-repair evidence:
- Node: `an29`; `CUDA_VISIBLE_DEVICES` empty; Transformers offline mode enabled.
- `timm.__version__`: `0.9.12`.
- Resolved class:
  `transformers_modules.InternVL3-9B.modeling_internvl_chat.InternVLChatModel`.
- Exit code: 0.
- The informational `FlashAttention2 is not installed` message is expected;
  `InternVL3Adapter` explicitly passes `use_flash_attn=False` and uses BF16.
- Gemma remains pinned to `Gemma3Processor(use_fast=False)` from V1.

Adversarial fixture:
- `test_internvl_runtime_dependency_is_reproducibly_pinned` rejects an absent,
  floating, additional, or differently versioned M11 requirement. The prior tree
  fails because no M11 requirements file exists.
- The real class-import command independently proves the installed environment
  satisfies the source-level dependency rather than relying only on the fixture.

Decision:
- Keep `timm==0.9.12` isolated as an M11 inference requirement; do not alter the
  Qwen3-VL or EasyR1 dependency ranges.
- Keep the capacity-driven queue active. The shared `.venv` is visible on an29,
  so queued children inherit the repaired dependency.
- Do not mark M11 pass until the complete registered result artifacts pass their
  machine conjunction.

Next actions:
- Focused adapter tests passed 10/10; the literal `python -m pytest tests/`
  suite passed 537/537 in 93.73 seconds after the requirement pin.
- Monitor the capacity gate; execute six GPU smoke cells when stable capacity
  appears.
- Preserve any smoke failure as an immutable run and keep the full phase closed.
