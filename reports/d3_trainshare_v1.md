# D3 TrainShare with paired item-level CIs

Estimand from `docs/PAPER1_RESEARCH_DOC.md` §8:

    TrainShare = [Acc(train-blind, test-real) − Acc(base, test-real)]
                 / [Acc(A1, test-real) − Acc(base, test-real)]

Branches: ≥0.35 headline at full strength · 0.15–0.35 "a substantial minority of
the gain is image-free" · <0.15 training-time access dominates.

> **Ordering disclosure.** All 36 D3 cells were read under
> `docs/registered_d3_condition_matrix_v1.md`, whose branches are ratio-based,
> *before* this estimand was computed. TrainShare here is a **declared post-hoc
> recomputation of already-read data** — it does not satisfy I9 and must not be
> presented as a sealed pre-registered reading. It is reported because PAPER1 §8
> names this estimand and the paper will quote it.

| arm | seed 1 | seed 2 | seed 3 | pooled | 95% CI (paired item-level) | branch |
|---|---|---|---|---|---|---|
| A2 gray | 0.507 | 0.527 | 0.424 | **0.487** | [0.383, 0.588] | headline at full strength |
| A2b no-image | 0.572 | 0.493 | 0.518 | **0.528** | [0.424, 0.629] | headline at full strength |
| A3 caption | 0.743 | 0.716 | 0.691 | **0.718** | [0.617, 0.821] | headline at full strength |

**Branch: headline at full strength, and not marginally.** Every arm's pooled
TrainShare clears 0.35 with a paired item-level interval lying *entirely* above
the threshold — the nearest lower bound is A2 gray at 0.383 — and all nine
seed-arm values fall in the same branch. The bootstrap resamples the 601 items and
recomputes numerator and denominator together, so the ratio's correlation
structure is preserved rather than assumed away.

These reproduce the crossed recoveries already reported from D3 (A2 gray
0.507/0.527/0.424; A2b 0.572/0.493/0.518), so nothing new is being claimed — the
contribution is the interval and the branch evaluation.

## Read this together with G0.2

The pooled figure conceals real structure. `reports/gate0_stratification_v1.md`
shows A2b's share of A1's gain is **84%** on items with at least one observed
blind success and **42%** on items with none. TrainShare ≈ 0.53 is the average
over that gradient, not a constant. The honest formulation for the paper is that
roughly half of the gain is image-free *on average*, with the image-free share
falling as an item's dependence on the image rises — a headline at full strength
that carries its own scope qualifier rather than needing one bolted on.
