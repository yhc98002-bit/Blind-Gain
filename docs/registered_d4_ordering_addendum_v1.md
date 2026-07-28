# Registered: D4 addendum — the ordering reading

Addendum to `docs/registered_d3_caption_column_v1.md`. Registered 2026-07-28,
**before any caption-condition cell is run**.

## Why this addendum exists

The parent registration frames the caption column around A3's matched-versus-
crossed contrast. `docs/EXPERIMENT_TODO.md` 1C states the primary question
differently and better:

> **is the readout policy pixel-specific or evidence-general?** … If caption-at-test
> reproduces the real-image ordering, the policy reads evidence generally; if not,
> it is pixel-specific.

That is a different estimand — it concerns the **ordering of arms** under
caption-at-test, not one arm's recovery ratio. Selecting it after seeing cells
would be a post-hoc reading, so it is registered here first and becomes D4's
**primary**. The parent registration's A3 contrast is demoted to secondary and is
otherwise unchanged.

## Why the question is sharp

F1 establishes two regimes. Under blind evaluation (gray, none) the arms do not
order: every arm lands in +0.016 to +0.046 regardless of what it trained on.
Under real-image evaluation they order by training-time information
(gray +0.119 < no-image +0.129 < caption +0.175 < real +0.244).

Caption-at-test is neither: it carries genuine task information through a
non-pixel channel. So it separates two readings of the readout-policy thesis that
the existing matrix cannot distinguish — a policy that reads *evidence* wherever
it is, versus one that reads *pixels* specifically.

## Primary estimand

For each test condition c, let `Order(c)` be the four arms ranked by mean gain
over base across three seeds. Compare `Order(caption)` against `Order(real)` by
Spearman rank correlation, and compare the **spread** `max−min` of the caption
column against the spread of the two blind columns.

## Pre-committed branches

- **(a) Evidence-general.** Spearman ρ(caption, real) ≥ +0.70 **and** the caption
  column's spread exceeds the larger blind-column spread by at least 2×. Reading:
  the readout policy is not pixel-specific; it exploits task-relevant evidence
  through whatever channel supplies it, and the F1 two-regime split is about
  *information presence*, not *modality*.
- **(b) Pixel-specific.** The caption column's spread falls inside the range
  spanned by the two blind columns **and** ρ(caption, real) < +0.70. Reading: the
  ordering in F1's image-present regime depends on pixels specifically, and the
  readout policy is modality-bound. This would *narrow* the broader-claim
  paragraph (§3), which currently generalises the ceiling argument to any frozen
  non-text encoder.
- **(c) Intermediate.** Anything else is reported descriptively with the observed
  ordering stated, and no change to either claim.

Paired item-level bootstrap CIs are reported for every arm's caption-column gain.
Both `Acc_final` and `Acc_strict` are reported (I7); a caption-column gain whose
strict component does not move is reported as format/emission, never capability.

## Secondary (from the parent registration, unchanged)

A3 matched-versus-crossed: whether A3's crossed recovery exceeds its matched
recovery by more than 2× with non-overlapping paired item-level CIs, which would
let F1 state the protocol effect for three arms rather than two.

## Locks

- Additive only. No D3 cell is re-run, re-scored, or reinterpreted; registered
  branch (a) of the parent matrix stands.
- Base caption row is pinned from the registered arm step-0 evaluations, matching
  how the other three base cells were handled — not re-measured.
- Inference only, on free GPUs; trainer GPUs are never used.
- §9 language locks apply.
