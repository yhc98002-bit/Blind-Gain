# Registered: B1 premise-probe diagnostic (v1) — EXPLORATORY

Registered 2026-07-27, before any premise-probe inference is run.

## Why this exists

`reports/b1_trained_scoring_v1` landed on registered branch **(c)** of
`docs/registered_b1_trained_v1.md`: `chained_premise` sat at 0.000 pair-correct
for the base and every trained arm, so the construct was recorded as "not yet
discriminative at 3B scale" and labeled **a construct-development item rather
than a model finding**. This probe is that construct development. It asks the
one question that decides what to do with the construct:

> When a model fails a chained item, does it fail because it cannot extract the
> premise from the image, or because it extracts the premise and cannot chain
> from it?

The two answers imply opposite fixes: easier premise extraction versus a
retained construct that is correctly isolating a chaining gap.

## Instrument

The 20 `chained_premise` pairs in `data/b1_geometry_track_v1/manifest.jsonl`,
each carrying `premise_question` and `premise_answer`. The premise is invariant
across the counterfactual flip *by construction* (e.g. the nearest point stays
`B2`; the flip moves that point's x-coordinate from 3 to -1), so a single
`premise_answer` is gold for both members.

Derived manifest: identical images, `question := premise_question`,
`answer_a = answer_b := premise_answer`. Everything else — prompt contract
`answer-tags-v1`, parser `canonical-v2`, `max_new_tokens: 32`, decoding — is the
build used for `b1_trained_scoring_v1`, unchanged.

**Primary statistic is member-level accuracy, not pair accuracy.** Because both
golds are equal by design, `answers_equal` is true for every pair and the
harness's collapse/pair logic is degenerate here. Any pair-level figure from
this run is void and will not be reported.

Cells: base, A1 seed 1, A1 seed 2, A2b seed 1, A3 seed 1 — the same model set as
`b1_trained_scoring_v1`. 20 pairs x 2 members = 40 premise observations per cell.

## Pre-committed readings

Let `P` = premise member accuracy, and recall final member accuracy on these
same items is 0.150 (base) and 0.075–0.125 (arms).

- **(a) Extraction succeeds, chaining fails** — if base `P` >= 0.60 while final
  member accuracy stays at floor: the construct is isolating the chaining /
  realization step, not visual extraction. The items are sound; the construct is
  **retained** for the Track-B release with a "hard at 3B" difficulty note, and
  the floor result is reported as a realization-layer failure.
- **(b) Extraction itself fails** — if base `P` < 0.30: the items are visually
  too hard at 3B and cannot test chaining at all. The construct is **revised**
  before release (easier premise extraction, same chaining structure), and the
  0.000 chained result is reported as uninformative about chaining.
- **(c) Intermediate** — base `P` in [0.30, 0.60): reported descriptively; the
  construct is flagged for redesign and the specific premise-failure `pair_id`s
  are listed so the revision is targeted rather than global.

Secondary, and explicitly underpowered: the base-vs-arm contrast on `P`. With 40
observations per cell the 95% CI half-width is roughly +/-0.15, so only a very
large shift would be detectable. It is reported with that interval stated and
**no** directional claim is registered for it.

## Locks

- **EXPLORATORY.** This probe cannot change, strengthen, or weaken any canonical
  claim, any registered endpoint, or the R1–R6 ladder. Its only registered
  consequences are the construct decisions in (a)/(b)/(c).
- It bears on the §11 hypothesis (that RLVR improves evidence utilization and
  answer production rather than visual extraction) but **cannot license it**:
  n=20 items on one construct at one scale. Any write-up must say so.
- §7 language locks apply. "Extraction" and "chaining" name measurement layers
  here, not cognitive states.
- Power must be stated wherever `P` is reported.
