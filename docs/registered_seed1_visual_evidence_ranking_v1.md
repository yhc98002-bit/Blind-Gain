# Registered Seed-1 Visual-Evidence Ranking Diagnostic V1

## Status and scope

This is a post-seed-1, prospectively registered diagnostic. It is not part of the
original pilot preregistration, does not alter any M2 endpoint, and does not
retroactively promote a seed-1 result. Candidate construction was completed before
model inference. At registration, no model had been run under this scoring contract.

Human-facing text uses `visual-evidence ranking` or `candidate-answer ranking`. The
phrase `perception improved` is prohibited without additional direct evidence.

## Frozen inputs

- Instrument: all 1,200 FlipTrack R19 pairs from source-manifest SHA256
  `e1dde98451e1c7473906637c029713ab4f95ab4f7c915bd035f697953bf2ffb2`.
- Candidate registry: `data/fliptrack_r19_visual_evidence_candidates_v1.jsonl`,
  SHA256 `fa9456941a730e174b1ed4bb4caefc151778e3f1adc0ca77db941955a4215f81`.
- Candidate construction never reads model predictions or model scores.
- Models: the frozen 3B base model and A1 checkpoints at steps 60 and 100. Exact
  model-index hashes are pinned in
  `configs/eval/seed1_visual_evidence_ranking_v1.json`.
- Processor/tokenizer: always the frozen base-model processor, composite artifact
  SHA256 `bb6a1bfd88cb88a749ff1f86affa84907a70bfdf98c10e303368db5685c81544`.
- Prompt: the pilot answer-tag prompt contract, SHA256
  `7ac39f53a2a824490fc5ee22671a888d2d79d55e1d8351919006d7d71c7a8f3f`.

## Frozen candidate sets

The primary pairwise comparison uses exactly the two counterfactual gold answers for
that pair. Secondary top-1 and MRR use a frozen candidate set:

- mathematically equivalent answers are one canonical-v2 equivalence class;
- if a template has at most 16 classes, its complete R19 answer universe is used;
- otherwise, both pair golds plus 14 same-answer-signature distractors are selected
  by SHA256 of `(pair_id, answer)`; a broader same-template fallback is used only if
  needed to reach 16;
- candidate order is independently SHA256-derived and does not expose gold position;
- geometry has 14 candidates per pair, chart has all 9, and document has 16.

Each verbalization is exactly `<answer>{verbatim frozen answer}</answer>`, with no
leading text, trailing text, newline, reasoning, or EOS token. Unit-changing answers
remain distinct (`5 cm` is not equivalent to `5 m`). Numeric equivalence uses
canonical-v2 with tolerance `1e-4`.

## Frozen scoring

For every image side and candidate, teacher forcing scores every token in the exact
candidate verbalization conditional on the fixed multimodal prompt. The primary
candidate score is mean token log probability. The unnormalized sum is retained only
as a robustness field. The base tokenizer is right padded; the evaluator fails if the
prompt token sequence is not an exact prefix of the prompt-plus-candidate sequence.
Log-sum-exp is computed in float32 and totals are stored in float64.

For each pair:

- image A margin = `score(gold_A) - score(counterfactual_gold_B)`;
- image B margin = `score(gold_B) - score(counterfactual_gold_A)`;
- paired margin = the arithmetic mean of the two side margins;
- pair success requires both margins to be strictly greater than zero.

Ties do not count as top-1 and receive the conservative worst rank for MRR.

## Conditions and estimands

Every base/step-60/step-100 model is scored under identical `real`, `no_image`, and
`gray` conditions. `no_image` contains no image item or image token. `gray` preserves
the image-token path but replaces each source with a same-size constant RGB image.

The only primary category is R19 geometry. The primary checkpoint contrast is step
100 minus base, and the primary blind comparator is `no_image`:

`[(margin_100,real - margin_0,real) - (margin_100,no_image - margin_0,no_image)]`.

The effect is computed per pair and summarized by its mean and a 10,000-resample
pair-bootstrap 95% percentile interval with seed `20260717`. Gray is a pixel-free
image-token robustness comparator. Resampling uses NumPy Generator PCG64. Step 60 is descriptive. Pair success,
candidate-set top-1, and MRR are secondary.

The chart construct is always displayed as `cued chart point-value reading`; the old
identifier is retained only in machine fields. Document is calibration only.

## Interpretation branches

- B1: free generation improves while paired ranking and image-dependent margin remain
  flat, supporting an output/decision account.
- B2: chart image-dependent ranking improves while geometry remains flat, indicating
  better use of existing chart evidence; the geometry headline is retained.
- B3: A1 geometry image-dependent ranking improves, making the end-to-end
  dissociation partly compatible with measurement cancellation. The permitted claim
  is improved visual-evidence ranking, not proven internal perception gain.

No automatic branch verdict is registered because no log-probability-margin SESOI
was supplied. The report will publish estimates and confidence intervals; PIs may
interpret branch compatibility without an invented post-hoc equivalence threshold.

## Execution lock

The launcher requires this document, the exact config, and candidate registry to be
tracked and clean, records the commit introducing this document, and verifies that
commit is an ancestor of launch HEAD. Every run is immutable, TP1, single-node, and
records model/config/data hashes. No ranking inference may start before this lock is
satisfied.
