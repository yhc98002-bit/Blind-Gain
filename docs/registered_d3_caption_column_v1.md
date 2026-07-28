# Registered: D3 caption-column amendment (v1)

Amends `docs/registered_d3_condition_matrix_v1.md`. Registered 2026-07-27,
**before any caption-condition cell is run**.

## Why

The merged D3 registration fixed the test-condition columns at `real`, `gray`,
`none` and recorded the resulting gap explicitly: "A3's matched condition is
`caption`, which is **not** part of this matrix". `docs/EXPERIMENT_TODO.md` §1B
specifies the fuller grid — all four training arms × {real, gray, no-image,
caption} × 3 seeds. The registration governs, so D3 as read out is complete and
correct; this amendment adds the missing column rather than reinterpreting
anything already read.

The scientific reason to add it is specific. F1's central argument is that the
same checkpoint reports a very different recovery depending only on the
evaluation condition — 6.6% matched versus 48.6% crossed for A2 gray. That
matched-versus-crossed contrast can currently be drawn **inside the matrix** for
A2 gray and A2b no-image but **not for A3 caption**, whose matched condition is
absent. A3 now carries real weight in the information ladder (+0.175, 72% of
A1's gain), so its matched cell should come from the same harness and the same
frozen 601-row set as every other cell, not from a separately published readout.

## Cells

12 new cells: A1 real, A2 gray, A2b no-image, A3 caption × seeds 1–3, each
evaluated under test condition `caption`. Plus the base row under `caption`,
pinned from the registered arm step-0 evaluations exactly as the base row for
the other three columns was pinned.

Frozen inputs, decoding contract, parser, and the 601-row manifest are unchanged
from D3 v1. `caption` is an already-supported condition in
`src/eval/conditioned_inputs.py` (`CONDITIONS = ("real","gray","noise","none","caption")`)
and is the same condition A3 was trained under, so no new rendering path is
introduced.

## Pre-committed readings

- **Primary (descriptive).** Report `Acc_final` and `Acc_strict` for all 13
  caption cells, and add the caption column to the published matrix. No claim in
  Paper 1 changes on the basis of this column alone.
- **(a) A3 matched-vs-crossed.** If A3's crossed recovery (trained caption,
  tested real) exceeds its matched recovery (trained caption, tested caption) by
  more than 2× with non-overlapping paired item-level CIs, A3 joins A2 gray and
  A2b in the protocol-effect finding, and F1 may state the effect for **three**
  arms rather than two.
- **(b)** If the two are comparable (ratio in [0.8, 1.25]), A3 is reported as an
  exception to the protocol effect and that exception is stated explicitly in F1.
- **(c)** Intermediate ratios are reported descriptively.

In every branch, a caption-column gain whose `Acc_strict` component does not move
is reported as format/emission, never as capability (§9 language locks).

## Locks

- This column is **additive**. No cell already read under D3 v1 is re-run,
  re-scored, or reinterpreted, and the registered branch (a) that already fired
  stands unchanged.
- Base caption row is pinned, not re-measured, matching how the other three base
  cells were handled.
- Trainer GPUs are never used; this is inference-only on free GPUs.
