# Correction notice — three-seed FlipTrack equivalence claim (2026-07-27)

Raised by the adversarial statistical audit (workflow `wf_56123920-97d`, 8 agents,
independent re-derivation from raw shards) and **verified directly** before
acceptance. Applies to `reports/three_seed_summary_v1.{md,json}` and to
`reports/x_series_synthesis_v3.md` §1 (and the local copy of that file).

## What was claimed

> "A1 equivalence verdict: equivalence supported within the registered band" —
> geometry FlipTrack mean +0.0056, seed-level 95% CI [−0.0016, +0.0127],
> "within ±0.05: True" for all four arms.

## Three defects, all confirmed

**1. The null does not survive contract-strict scoring.** On the identical
registered slice (600 pairs, same images, same scorer), A1's geometry FlipTrack
delta is:

| seed | lenient (published) | contract-strict |
|---|---|---|
| 1 | −0.0017 | **−0.1267** |
| 2 | +0.0083 | +0.0333 |
| 3 | +0.0100 | **−0.0267** |
| mean | +0.0056 | −0.0400 |

Seed 1 breaches the ±0.05 band by 2.5×, and the sign is unstable across seeds.
The mechanism is measurable: A1 training drops FlipTrack answer-contract
compliance from 0.9500 at base to 0.7367 / 0.9917 / 0.9017, and the fallback
extractor absorbs exactly that instability. **The stability of the lenient
number is partly a property of the salvage parser, not of the model.**

**2. The wrong interval was used, and the SESOI test is item-level.**
`reports/preregistration_pilot_v1.md` line 114: "no material change is supported
only if the **paired CI** is entirely within [−0.05, +0.05]" — i.e. the
item-level paired bootstrap, not a seed-level interval over n = 3. The published
summary substituted a seed-level CI computed with z = 1.96 at df = 2; with the
correct t(0.975, 2) = 4.3027 the A2 gray row also leaves the band
([−0.0542, −0.0303]). On the properly paired item-level CIs the lenient A1 null
does hold per seed ([−0.0267, +0.0250], [−0.0167, +0.0334], [−0.0150, +0.0350]).

**3. "Registered band" overstates registration status for A1.** Line 104
registers the ±0.05 equivalence margin for `Δ_A2gray − Δ_A2b`, not for A1's
FlipTrack delta. Line 119–120 further record that the registered *confirmatory*
signature was a **material A1 geometry-FlipTrack gain**, and that A1's own branch
was declared non-confirmatory in advance because the engineering anchor had
already informed it. Presenting A1's null as a passed registered equivalence
test inverts that.

Additional context the audit surfaced: the step-0 minuend is a single pinned
legacy run shared by all three seeds (`fliptrack_v02r19_packaged_..._20260710T142716Z`,
0.4716667), so seed-level spread reflects step-100 variation only; the geometry
category is bit-identical to one 600-pair synthetic template; and on the
secondary overall-pair endpoint A1 *does* move (+0.0283 / +0.0208 / +0.0267,
CIs excluding zero in all three seeds).

## What survives unchanged

The Geometry3K task gain: **+0.2529 / +0.2463 / +0.2313, mean +0.2435** — and it
is not a formatting artifact. The strict-format gain is *larger* (+0.3583 mean),
so the conservative metric was the one reported. Recovery fractions, the
falsified 30–70% preregistration, and the caption inversion all reproduced
exactly under independent re-derivation.

## Corrected wording to use from here

> Across three seeds, A1 real-image RLVR raises Geometry3K Acc_final by +0.2435
> on average. On the preregistered geometry FlipTrack slice — a single 600-pair
> template — A1's lenient pair accuracy is statistically indistinguishable from
> base (mean +0.0056; per-seed paired item-level CIs all inside ±0.05). **This
> null is not robust and is not a passed registered control:** under
> contract-strict scoring the same checkpoints move −0.1267 / +0.0333 / −0.0267,
> outside the band in all three seeds, because A1 training degrades answer-contract
> compliance and the fallback extractor masks it.

## Required actions

1. Supersede `three_seed_summary_v1` with a v2 reporting lenient **and** strict
   endpoints, item-level paired CIs, and per-arm contract-validity at step 0/100.
2. Amend synthesis v3 §1 with the corrected wording; re-save locally.
3. Treat FlipTrack contract-validity as a first-class reported result.
4. Re-measure the base FlipTrack endpoint under the current harness before any
   claim rests on the step-0 minuend.
5. State a power analysis so the null is not read as evidence of absence.
