# Registered D3 — training-condition × test-condition matrix (v1)

Registered 2026-07-27 **before any D3 cell runs**. Inference-only; launches no
training; alters no frozen endpoint; uses only seed-1/2/3 lineages whose values
are already open. Terminology per `docs/RESEARCH_DOC.md` §7; the layer measured
is **open-form realization**.

## Question

Every published recovery figure compares each arm *in its own training
condition*: A1 evaluated with real images, A2 with gray, A2b with no image.
That design confounds **what an arm learned** with **what its evaluation
condition permits it to express**. The registered D2 secondary already shows the
confound is not hypothetical: A2b, trained with no images at all, scores
0.3195 / 0.2962 / 0.2945 when evaluated *with* images against a base of 0.1747 —
a gain of roughly half A1's, versus a published matched-condition recovery of
11.8 / 22.3 / 23.0%.

D3 crosses the two factors so the effects separate.

## Design

- **Rows (training condition), step-100 merged actors, seeds 1–3:**
  A1 real, A2 gray, A2b no-image, A3 caption.
- **Columns (test condition):** real, gray, none.
- **Base row** is not re-measured: the registered arm step-0 evaluations already
  measure the identical frozen base under all three conditions on this exact set
  and contract — real 0.1747, gray 0.0899, none 0.0682.
- **Frozen inputs:** `data/geometry3k_caption_images_manifest.jsonl` (601 rows),
  format prompt `r1v.jinja`, prompt contract `answer-tags-v1`
  (SHA256 `7ac39f53…`), greedy, `max_tokens` 2048, seed 20260710, canonical-v2
  parser — identical to the registered pilot Geometry3K evaluations and to D2.
- A3's matched condition is `caption`, which is **not** part of this matrix; A3's
  matched-condition recovery is taken from the published readouts and A3's row
  here is interpreted only across real/gray/none. This limitation is stated in
  the report.
- Cells already produced under D2 (A1 × three conditions × three seeds; A2b ×
  real × three seeds) are reused unchanged rather than re-run.

## Registered statistics

Per cell: `Acc_final`, `Acc_strict`, and contract-validity rate, each with a
2,000-resample item bootstrap 95% CI (seed 20260710).

For each blind arm b ∈ {A2 gray, A2b no-image} and each seed:

    matched_recovery(b)  = [Acc(b, matched(b)) − base(matched(b))] / [Acc(A1, real) − base(real)]
    crossed_recovery(b)  = [Acc(b, real)       − base(real)]       / [Acc(A1, real) − base(real)]
    ratio(b)             = crossed_recovery(b) / matched_recovery(b)

where matched(A2) = gray and matched(A2b) = none. Item-level paired bootstrap
CIs are computed for both recoveries and for the ratio.

**Format control (mandatory, applies in every branch):** the same three
quantities are recomputed on `Acc_strict`. A crossed-condition gain whose
`Acc_strict` component does not move is reported as improved answer emission or
format compliance — never as a capability or perception gain (§7 locks).

## Pre-committed readings (fixed before any cell runs)

- **(a) Evaluation-condition effect.** If, for both blind arms and in all three
  seeds, `ratio(b) > 2` with the crossed and matched recovery CIs
  non-overlapping, then the published low blind recovery substantially reflects
  the matched evaluation condition. Consequence, fixed here: the canonical claim
  in RESEARCH_DOC §1 carries the scope tag **"under matched evaluation"**, and
  the crossed-condition recovery is reported alongside it in the same table.
- **(b) Training-capability effect.** If `ratio(b)` lies within [0.8, 1.25] for
  both blind arms, the low recovery reflects what blind training learned, and
  the canonical claim stands unchanged.
- **(c) Intermediate or inconsistent.** Any other pattern — including seeds or
  arms disagreeing across bands — is reported descriptively, per arm and per
  seed, with no change to the canonical claim.
- In branches (a) and (c), if the `Acc_strict` recomputation does not reproduce
  the `Acc_final` pattern, the finding is reported as format/emission and the
  canonical claim is **not** rescoped.

No SESOI is registered for the ratio, so D3 assigns no B1/B2/B3 gate decision
and no equivalence verdict. D3 does not reopen any sealed value: all lineages
used here are already published.

## Deliverables

Immutable per-cell prediction files with run manifests, and
`reports/d3_condition_matrix_v1.{md,json}` plus an audit artifact containing the
registered tables and the branch obtained.
