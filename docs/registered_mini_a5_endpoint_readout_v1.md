# Registered: Mini-A5 endpoint readout specification (v1)

**Filed:** 2026-07-29, **before any Mini-A5 endpoint value has been read.**
**Status at filing:** both arms trained to `global_step_120` and exited 0; the
acceptance audit returned **PASS** on all six conditions
(`reports/mini_a5_acceptance_audit_v1.json`, which by construction reads no endpoint
metric); the member arm's raw FSDP state was merged to HF weights and verified (825
tensors, 8,131,575,808 bytes, index parses, `Qwen2_5_VLForConditionalGeneration`).
**Zero prediction, metric or accuracy file from either arm has been opened.**

## 1. Why this addendum exists

`docs/registered_mini_a5_main_v1.md` registers the endpoint as:

> "Primary: held-out FlipTrack counterfactual templates (never present in the
> training corpus, per the corpus audit) — CP-GRPO versus same-data standard GRPO at
> step 120, pair-level success with paired bootstrap."

That fixes the *contrast* but not the *procedure*. It names no dataset file, does not
define pair-level success operationally (lenient vs contract-strict), and pins no
bootstrap draws, seed or alpha. Its "Immutable inputs" table pins training-side
artifacts only — **no evaluation dataset is pinned anywhere.**

Choosing those now, after the gate has passed and before any value is read, is the
last moment at which they can be chosen without being a post-hoc analysis choice.
This addendum makes them explicit. It **adds no freedom** the main registration
withheld and **changes no registered quantity**; it removes latitude that the main
registration accidentally left open.

## 2. Evaluation item sets — pinned

The held-out sets are those the corpus audit itself certified, recorded in
`data/mini_a5_train_v1/decontamination.json` → `evaluation_manifests`, all three
sha256-verified present:

| manifest | rows | sha256 |
|---|---:|---|
| `data/fliptrack_v02r19_artifact_expanded_source_manifest.jsonl` (R19) | 1,200 | `23dd2445…` |
| `data/fliptrack_r20_source_manifest.jsonl` (R20, private twin) | 1,200 | `20222e60…` |
| `data/fliptrack_chart_v08_calibration_v1_manifest.jsonl` | 100 | `d90f3f13…` |

R19 and R20 share zero `pair_id`. Union = 2,500 rows over 5 template ids, matching
`evaluation_template_count: 5` in `reports/mini_a5_corpus_audit_v1.json`.

**Harness comparability.** R19 is evaluated through the **locked R19 manifest**
`experiments/runs/caption_qa_pair_build_fliptrack_v02r19_qwen25vl3b_384_20260710T140200Z/shards/captions_shard_0.jsonl`
(sha256 `e1dde984…`, the value hard-coded as `R19_MANIFEST_SHA256` in
`scripts/launch_fliptrack_eval_shards.sh`) — the same manifest every prior
trained-checkpoint FlipTrack evaluation used. This is deliberate: it makes the
Mini-A5 arms directly comparable to every Paper-1 FlipTrack number rather than to a
freshly-built variant.

## 3. Primary endpoint

**CP-GRPO minus same-data standard GRPO, at step 120, on R19 pair accuracy,
reported per task role and never aggregated across roles (I13).**

R19's three tasks hold three distinct scientific roles and the primary is one of
them, not their average:

| task | n pairs | role | status as endpoint |
|---|---:|---|---|
| coordinate survey register | 600 | **primary visual anchor** | **THE primary endpoint** |
| header-cued verification table | 300 | saturated positive control / retention canary | secondary; a drop signals damage |
| nine-series calibration trace | 300 | oracle-localized readout control | secondary |

Pair-level success is `src.eval.fliptrack_metrics.pair_score`: both members correct.

**Both scoring contracts are reported (I7):** lenient `pair_correct` and
contract-strict `strict_pair_correct`. Neither is privileged; if they disagree the
disagreement is the result.

## 4. Interval procedure — pinned

Paired item bootstrap, **10,000 draws, seed 20260729, percentile 2.5 / 97.5**, unit
= `pair_id`, both arms resampled on the **same** pair indices per replicate. Exact
McNemar two-sided p on the paired indicators alongside. Intervals quantify evaluation
uncertainty on a fixed pair set; **they do not estimate run-to-run RL variance**, and
each arm is one run.

## 5. Pre-committed branches — restated verbatim in force

From `PAPER1_RESEARCH_DOC.md` §8 and `PAPER2_RESEARCH_DOC.md` §6:

- **CP moves held-out FlipTrack while matched same-data GRPO does not** → trainability
  established, C2 validated, Paper 2 proceeds.
- **Both flat** → reported as-is and the Paper-2 gate is reconsidered; per PAPER2 §6
  this is the premise-first redesign branch (C3 before C2), with C1 retained.
- **Components move attribution but not competence** → engage C4.

**Decision rule.** "Moves" means the CP−member difference on the primary anchor has a
95% paired-bootstrap CI excluding zero in the positive direction. A positive point
estimate whose interval contains zero is reported as *not moved*, not as a trend.

## 6. Secondaries — stated honestly, including what cannot be run

The main registration lists three. Their instrument status was established before
this filing and is recorded here rather than discovered later:

1. **Free-generation vs candidate-ranking** — runnable
   (`scripts/eval_qwen_vl_visual_evidence_ranking.py`). Will be run.
2. **Catch-trial stability** — the 300-pair set exists
   (`data/mini_a5_catch_v1/`, decontamination `pass`) but **no scorer that loads a
   model exists**; `scripts/audit_mini_a5_catch.py` is a data-integrity audit that
   never instantiates a checkpoint. This endpoint is therefore **reported as
   instrument-absent** unless a scorer is built. It is not silently dropped.
3. **"The registered task benchmark"** — the phrase occurs exactly once in the repo
   and is bound to no dataset or config; the training configs evaluate no benchmark
   (`val_freq: 0`). It is **reported as unresolvable from the registration**. The
   nearest referent by project convention is Geometry3K; adopting it would be a
   choice this addendum declines to make silently.

## 7. Sealed

No endpoint value is read until this document is merged. R19 and R20 are never
modified, regenerated, or trained on (I11).
