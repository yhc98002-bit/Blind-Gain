> **RETRACTED — INVALID BUILD (2026-08-11 PI review; header added 2026-08-16
> per the 08-12 dispatch P0.2; the original readout below is retained
> unmodified, superseded not deleted).** All six rungs reference the
> byte-identical v07 image (pixel diff = 0;
> `replayed_from: starred_series_value_nine_v07`); the annotation layer never
> varied; golds were copied from the starred series while the
> named/none/decoy questions name other series (question–gold mismatch on 4
> of 6 rungs); the verifier's `gold_follows_question` checked gold against
> the *target*, not the question. The readout numbers below (+0.317 / −0.277)
> are wrong-gold artifacts; the "marker is cue and occluder" story and the
> text-priority micro-result are **retracted**. Arm cells were never scored.
> Superseded by the L1/L2/L3 hierarchy
> (`docs/registered_hier_benchmark_v1.md`); sibling artifacts
> `reports/cue_ladder_readout_v1.json` and
> `reports/cue_ladder_base_gates_v1.json` are covered by this same
> retraction. RESULTS §16 carries the matching header.

# Cue ladder (CL / F4b) — readout: both gates fail, branches void, instrument characterized

Registered: `docs/registered_cue_ladder_v1.md` + `docs/registered_cue_ladder_v2_amendment.md`.
Artifacts: `reports/cue_ladder_base_gates_v1.json`, `reports/cue_ladder_readout_v1.json`.
Base model only, 300 items per rung, item-paired with R19 by replaying each frozen
pair's `pair_seed` (300/300 integrity).

## Outcome

| gate | result |
|---|---|
| v1 gate 1 — `exact` reproduces R19 nine-series | **PASS** (paired delta +0.0167, CI [−0.0033, +0.0367]) |
| v1 gate 2 — base monotone across exact → region → none | **FAIL** (0.4533, 0.1367, 0.6167) |
| v2 gate — base monotone across named_exact → named_region → none | **FAIL** (0.3333, 0.6100, 0.6167) |

**Registered consequence: branches (a) and (b) are void.** No cue-ladder claim
about localization-specific corrosion is made. Per the v2 amendment there is **no
third attempt this round**, and **the twelve arm cells were not scored** — running
them would spend GPU on a decomposition whose readings are already void. F2d's
prediction therefore remains untested rather than confirmed or refuted.

## Why it failed — the annotation is a cue *and* an occluder

The full 2×2 (base pair accuracy, same 300 scene programs throughout):

| question form | on-point mark | legend star only | no marks |
|---|---|---|---|
| "the **starred** series" | 0.4533 | 0.1367 | — |
| "series **LABEL**" | 0.3333 | 0.6100 | 0.6167 |

Paired contrasts, 95% bootstrap CI (`*` excludes zero):

| contrast | delta |
|---|---|
| on-point mark vs legend-only, question names the series | **−0.2767** [−0.3433, −0.2067] `*` |
| on-point mark vs legend-only, question says "starred series" | **+0.3167** [+0.2533, +0.3800] `*` |
| legend star vs no marks, question names the series | −0.0067 [−0.0533, +0.0400] |
| decoy mark vs no marks, question names the series | −0.0100 [−0.0600, +0.0400] |
| question form, holding the on-point mark | +0.1200 [+0.0567, +0.1833] `*` |
| question form, holding legend-only | **−0.4733** [−0.5333, −0.4100] `*` |

The renderer draws the target annotation as a **white filled disc with a black
outline, centred on the target point, with a star on top** — it covers the data
marker whose value is being read. So the same annotation does two opposite jobs:

- when the question says "the *starred* series", the mark is the **only**
  identifier of which of nine series is queried, and it is worth **+0.317**;
- when the question already names the series, the mark identifies nothing and is
  pure occlusion, costing **−0.277**.

That interaction is why no ordering of these rungs is monotone, under either
question form. A ladder needs its rungs to differ in one direction; this
annotation moves two.

## What this says about the instrument

Three findings hold independently of the void branches:

1. **R19's nine-series annotation supplies localization by hiding the datum.**
   PAPER1 §5 certifies this task's construct as "oracle-localized visual readout:
   given a target already located, can the model read the local value". Measured
   here, the localization marker occludes the point whose value is the answer —
   with the series named in text and the scene otherwise identical, removing the
   disc raises base pair accuracy from 0.333 to 0.610. The construct is closer to
   *read a value from an occluded marker's position* than to *read an already-located
   value*. This does **not** disturb F2d: the occlusion is constant across base and
   all arms, so the deltas F2d reports are unaffected. It refines what the control
   certifies, not whether it moved.
2. **At 3B, a correct visual cue adds nothing once the series is named in text.**
   Legend star vs no marks is −0.0067 with a CI covering zero. The text channel
   saturates the identification problem.
3. **A misleading visual cue also costs almost nothing when text names the
   series**: decoy vs none is −0.0100, CI covering zero. On this task the base
   model already prefers the instruction over the annotation, so `CueFollowRate`
   has little room to move — reported with no directional claim, as registered.

## Consequences for Paper 2 Track 1

PAPER2 §4 calls the cue ladder "the cheapest new track and highest information
per unit cost." This build says it needs redesign before it earns that:

- the localization cue **must not occlude the queried datum** — mark it with an
  offset arrow, a ring drawn outside the marker radius, or an axis band;
- the question form must be **held constant** across rungs, and it must not name
  the series, or the text channel saturates identification and every visual rung
  collapses to the same score;
- with those two fixed, the intended rungs (exact → region → none → decoy) are
  worth building; the scene generator and the replay harness here are reusable.

The generator, manifests, and scoring path are committed and working, so a v3
build is cheap. It is **not** attempted this round, as registered.
