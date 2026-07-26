# Registered B1 trained-checkpoint scoring (v1)

Registered 2026-07-26 before any inference on trained checkpoints against the
B1 batch. Inference-only; opens no sealed value (seed-1 and seed-2 lineages
only); alters no frozen endpoint; adds no new batch (the declared 100-pair
calibration batch is reused unchanged, one shot, no acceptance iteration).

## Question

`reports/geometry_track_prototype_v1.md` calibrated the declared B1 batch on
the frozen base model only. It is therefore unknown whether RLVR moves any of
the six intervention types the Track-B construct is built from. This scoring
supplies that, and it is the evidence B2 (release framing) needs to say what
the six-layer profile measures on a trained model.

## Frozen inputs

- Batch: `data/b1_geometry_track_v1/manifest.jsonl`, SHA256 `b5f01945…`,
  unchanged from the declared build.
- Decoding contract identical to the base-model calibration: greedy,
  `max_new_tokens` 32, seed 0, canonical-v2 parser, real-image condition.
- Models (merged step-100 actors): `a1_seed1_step100`, `a1_seed2_step100`,
  `a2b_seed1_step100`, `a3_seed1_step100`.
- Base cells are pinned from `reports/geometry_track_prototype_v1.json`, not
  re-measured.
- Consistency pairs (`distractor_only`, `style_twin`) are scored single-gold
  exactly as in the base calibration, because the frozen two-gold ambiguity
  guard structurally fails equal-gold items.

## Registered statistics

Per model and intervention type: pair-correct and member-correct rates, and
the difference from the pinned base rate. No bootstrap is registered at this
batch size (100 pairs, 14–20 per type); differences are reported as point
estimates with the per-type item counts alongside.

## Registered readings (pre-committed)

- **(a)** If A1 improves `fact_read` while `distractor_only` and `style_twin`
  invariance do not decline, the batch behaves as a construct where RLVR
  improves fact extraction without costing invariance.
- **(b)** If A1 improves `fact_read` while invariance rates decline, the batch
  exposes a fact-extraction / invariance trade-off, which is reported as such
  and flagged for the Track-B release framing.
- **(c)** If `chained_premise` remains at floor for every trained model, the
  chained construct is reported as not yet discriminative at 3B scale and is
  labeled a construct-development item rather than a model finding.
- `prior_conflict` is descriptive in all branches: it is the smallest cell
  (14 pairs) and no directional prediction is registered for it.

No branch assigns a gate decision; this is construct calibration, not a
registered endpoint.
