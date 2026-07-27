# Registered: cue ladder v2 amendment — constant-question rungs

Amends `docs/registered_cue_ladder_v1.md`. Registered 2026-07-27, after the v1
base build-validity gates were read and **before any v2 rung is scored**.

## What the v1 gates returned

| gate | result |
|---|---|
| **1 — `exact` reproduces R19 nine-series** | **PASS.** Ladder 0.4533 vs R19 0.4367; paired item-level delta +0.0167, 95% CI [−0.0033, +0.0367] covers zero, 300/300 items joined. |
| **2 — base degrades across exact → region → none** | **FAIL.** exact 0.4533, region 0.1367, none 0.6167. Not monotone; `none` is the *easiest* rung. |

Per v1's own terms, **branches (a) and (b) are void** and no cue-ladder claim
about localization-specific corrosion may be read from the v1 build.

## Why it failed — a design fault, not a model finding

The v1 rungs varied **two** things at once. `exact` and `region` ask "What is the
value of *the starred series* at x = N?", so the star is load-bearing: it is the
only thing identifying which series is queried. `none` and `decoy` ask "What is
the value of *series LABEL* at x = N?", naming the series in text.

So `none` did not remove cue information — it **substituted a textual channel for
a visual one**, and the textual channel is stronger. That is why the nominally
cue-free rung scores highest, and why `region` (star reference retained, but only
a legend star to resolve it) collapses to 0.1367.

The v1 build therefore violates the spirit of I12: the annotation layer was not
the only thing changing between rungs. This amendment fixes that.

## v2 rungs — the question is held constant

All v2 rungs ask the **named-series** question, "What is the value of series
LABEL at x = N?", identical across rungs. Only the annotation layer varies:

| rung | on-point mark | legend star | status |
|---|---|---|---|
| `named_exact` | on the target point | on the target series | new |
| `named_region` | none | on the target series | new |
| `none` | none | none | reused from v1, unchanged |
| `decoy` | on a non-target point | on that non-target series | reused from v1, unchanged |

`none` and `decoy` are byte-identical to their v1 builds and are **not
regenerated**; only the two new rungs are rendered. Scene programs remain the
replayed frozen R19 `pair_seed`s, so the ladder stays item-paired with R19.

With the question naming the series, a correct visual mark is a redundant *aid*
rather than the sole identifier, so removing it should cost accuracy — which is
the manipulation the ladder was meant to make all along.

## v2 build-validity gate (checked before any arm is scored)

Base pair accuracy must satisfy `named_exact >= named_region >= none`. If it does
not, the ladder is again not measuring cue strength, and branches (a)/(b) stay
void — reported as such, with no third attempt in this round.

## Pre-committed readings for v2

Unchanged in substance from v1, restated over the v2 rungs. With
`Deficit(arm, rung) = Acc(A1, rung) − Acc(arm, rung)` for the blind arms:

- **(a)** If, for both blind arms, `Deficit(arm, none)` and
  `Deficit(arm, named_region)` each exceed `Deficit(arm, named_exact)` with
  non-overlapping paired item-level bootstrap CIs, the F2d reading is
  **confirmed**: blind-reward damage is specific to search and binding, and
  supplying localization removes it.
- **(b)** If the three deficits are mutually comparable, the F2d reading is
  **withdrawn**.
- **(c)** Any other pattern is descriptive, with the rung ordering stated.

`CueFollowRate` on `decoy` is reported per arm with no directional prediction, as
in v1.

## What v1 still supports

Two v1 contrasts held the question constant and remain valid, reported
descriptively under v1 branch (c):

- **`exact` vs `region`** (both "starred series"): base 0.4533 → 0.1367. When the
  star is the only identifier, moving it from the point to the legend alone costs
  0.317 of pair accuracy at base.
- **`none` vs `decoy`** (both named-series): base 0.6167 → 0.6067. When the series
  is named in text, a mark placed on the wrong series costs ≈0.01 at base.

Both are reported as descriptive base-model measurements, not as claims about
training effects.
