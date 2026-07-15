# M11 Smoke Recovery V1

Status:
- Six one-pair smoke cells are mechanically complete: three retained Gemma-3
  cells and three fresh InternVL3 cells.
- M11 remains `blocked`; none of the 18 registered full-matrix cells has run.
- This report intentionally omits all smoke-item model-performance values.

Evidence:
| Backend | Condition | Run | Exit | Required artifacts |
| --- | --- | --- | ---: | --- |
| Gemma-3-12B-IT | real | `m11_smoke_gemma3_r19_real_gemma3_real_an29_20260714T165254Z` | 0 | prediction + metrics present |
| Gemma-3-12B-IT | no-image | `m11_smoke_gemma3_r19_none_gemma3_none_an29_20260714T165301Z` | 0 | prediction + metrics present |
| Gemma-3-12B-IT | caption | `m11_smoke_gemma3_r19_caption_gemma3_caption_an29_20260714T165307Z` | 0 | prediction + metrics present |
| InternVL3-9B | no-image | `m11_smoke_v3_cache_internvl3_r19_none_internvl3_none_an29_20260715T180223Z` | 0 | prediction + metrics present |
| InternVL3-9B | real | `m11_smoke_v3_cache_internvl3_r19_real_internvl3_real_an29_20260715T180309Z` | 0 | prediction + metrics present |
| InternVL3-9B | caption | `m11_smoke_v3_cache_internvl3_r19_caption_internvl3_caption_an29_20260715T180309Z` | 0 | prediction + metrics present |

Contract checks:
- Every cell has one output row, greedy decoding, temperature `0`, top-p `1`,
  `n=1`, and `max_new_tokens=384`.
- Every cell records parser `canonical-v2` and prompt-contract SHA256
  `7ac39f53a2a824490fc5ee22671a888d2d79d55e1d8351919006d7d71c7a8f3f`.
- Gemma runtime metadata records Torch `2.6.0+cu118`, callable generation,
  and the pinned slow processor.
- InternVL runtime metadata records callable generation, initialized generation
  config, `timm==0.9.12`, FlashAttention disabled, and legacy-cache-only mode.
- All jobs are single-node TP1 on `an29`; no cross-node serving occurred.

Retained failures:
- The three V2 InternVL smoke runs at `2026-07-15T17:55Z` passed dependency
  loading but failed because Transformers 4.56 initialized a dynamic cache while
  bundled InternLM2 expects legacy tuple caches.
- Those runs remain immutable with exit `1`; they were not overwritten or
  counted as successes.

Fix:
- Commit `8a5525b10e0d929e7b675feafb3160e2dc47f081` makes the existing
  generation shim declare legacy-cache-only support.
- The adversarial fixture supplies an empty dynamic-cache entry that triggers
  the old `NoneType.shape` failure, then verifies the shim disables that cache
  path.
- Focused cache/runtime-metadata tests: `3 passed`, `12 deselected`.

Decision:
- Treat smoke execution plumbing as mechanically covered, not as a model-quality
  result or scientific gate.
- Keep the full M11 matrix behind M2 step-100 checkpoint evaluations.

Next actions:
- Prepare a recovery queue that consumes these six immutable smoke manifests.
- Launch full cells only when M2 evaluation capacity is not at risk.
