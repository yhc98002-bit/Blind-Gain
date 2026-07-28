# D4 — caption test column, completing the access matrix to 4×4

Registered before any cell ran: `docs/registered_d3_caption_column_v1.md` plus
`docs/registered_d4_ordering_addendum_v1.md`, which fixes the **primary**
estimand as the arm *ordering* under caption-at-test — is the readout policy
pixel-specific or evidence-general?

12 cells (4 arms × 3 seeds), n=601 items, base caption row pinned at
**0.2097** from the registered arm step-0 evaluations, not
re-measured. Artifact: `reports/d4_caption_column_v1.json`.

## The caption column

| arm | caption accuracy | gain over base | 95% CI |
|---|---|---|---|
| A1 real | 0.3145 | **+0.1048** | [+0.0727, +0.1370] |
| A3 caption | 0.3145 | **+0.1048** | [+0.0732, +0.1375] |
| A2b no-image | 0.2751 | **+0.0654** | [+0.0361, +0.0965] |
| A2 gray | 0.2629 | **+0.0532** | [+0.0233, +0.0837] |

*A1 and A3 tie at +0.1048.* This is a coincidence of the three-seed mean, not a
cell mix-up: the runs use distinct checkpoints, their per-seed accuracies differ
(A1 0.3161 / 0.2995 / 0.3278 vs A3 0.3195 / 0.2928 / 0.3311), and they agree on
only ~40% of extracted answers. Both means happen to land on 0.31447.

## Registered primary: branch (a) — evidence-general

- Ordering under caption: A3 caption > A1 real > A2b no-image > A2 gray
- Ordering under real: A1 real > A3 caption > A2b no-image > A2 gray
- Spearman ρ(caption, real) = **+0.800** (threshold ≥ +0.70)
- Spread: caption **0.0516** vs gray 0.0080 and
  none 0.0130 — **4.0×**
  the larger blind spread (threshold ≥ 2×)

Both conditions of branch (a) are met, so the registered reading is that **the
readout policy is not pixel-specific**. It exploits task-relevant evidence
through whatever channel supplies it: given frozen textual descriptions instead
of pixels, the arms re-order themselves the same way they do with images, and
they spread apart four times more than they do under a blind condition.

The one discrepancy in the ordering is A1 and A3 swapping at the top, which is
the tie above rather than a real inversion; ρ = +0.800 rather than +1.000 is
entirely that swap.

**What this licenses.** F1's two-regime split is about *information presence*,
not *modality*. That in turn supports the broader-claim paragraph: if the policy
reads evidence generally, the representational-ceiling argument is not specific
to pixels and should extend to any frozen non-text encoder.

## Secondary: A3 matched vs crossed — does NOT clear the bar

A3 matched (tested caption, its own training condition): **+0.1048**.
A3 crossed (tested real): **+0.1747**. Ratio **1.67**.

The registered bar for joining the protocol-effect finding was a ratio > 2 with
non-overlapping CIs. **1.67 does not clear it.** So F1 states the
matched-versus-crossed protocol effect for **two arms (A2 gray, A2b no-image),
not three** — A3 is an exception and is reported as one. This is the registered
branch (c) outcome for the secondary: descriptive, no claim change.

That A3 is the exception is unsurprising in hindsight — its training condition
already carried task information, so it has less to gain from being moved to a
richer test channel than an arm trained on gray rectangles does.
