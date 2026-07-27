# Pooled item-level equivalence — FlipTrack geometry endpoint (v1)

Registered SESOI ±0.05 on Δ pair accuracy (step 100 − step 0), geometry
slice, 600 pairs × 3 seeds. Supersedes the seed-level normal-approximation
statistic in `three_seed_summary_v1` for the equivalence verdict; see
`reports/correction_three_seed_fliptrack_v1.md`.

**Method.** Per pair, the paired delta against the pinned base is averaged
over the three seeds; the CI is a cluster bootstrap over the 600 pair_ids
(20000 draws, seed 20260727). Clustering is required — the
same 600 pairs recur in every seed, so treating the 1,800 rows as
independent would understate the interval. Equivalence is declared by TOST:
the 90% CI must lie entirely inside ±0.05.

## Acc_final (lenient)

| arm | pooled Δ | 95% CI | 90% CI (TOST) | equivalent? | Δ≠0? |
|---|---|---|---|---|---|
| A1 real | +0.0056 | [-0.0189, +0.0294] | [-0.0150, +0.0256] | **yes** | no |
| A2 gray | -0.0422 | [-0.0689, -0.0161] | [-0.0644, -0.0206] | **NO** | yes |
| A2b no-image | -0.0272 | [-0.0528, -0.0017] | [-0.0483, -0.0061] | **yes** | yes |
| A3 caption | -0.0050 | [-0.0289, +0.0189] | [-0.0244, +0.0150] | **yes** | no |

## Acc_strict (contract-strict)

| arm | pooled Δ | 95% CI | 90% CI (TOST) | equivalent? |
|---|---|---|---|---|
| A1 real | -0.0400 | [-0.0667, -0.0139] | [-0.0622, -0.0178] | **NO** |
| A2 gray | -0.1933 | [-0.2272, -0.1600] | [-0.2217, -0.1656] | **NO** |
| A2b no-image | -0.1072 | [-0.1344, -0.0800] | [-0.1306, -0.0844] | **NO** |
| A3 caption | -0.1050 | [-0.1344, -0.0761] | [-0.1300, -0.0806] | **NO** |

## Findings

1. **A1's flat counterfactual endpoint survives its strongest test.** The
   pooled Δ is +0.0056 with a TOST interval of
   [-0.0150, +0.0256], entirely inside
   ±0.05, and the 95% CI covers zero. On the lenient endpoint the central
   dissociation holds under item-level inference, not merely at n=3 seeds.
2. **A2 gray is confirmed outside the band.** Pooled Δ -0.0422,
   TOST interval [-0.0644, -0.0206] — the
   lower limit exceeds the SESOI, so equivalence is **not** established. This
   reproduces, by a wholly independent route, the conclusion the t(2)
   correction reached at the seed level. The published "within band" verdict
   for A2 gray was an artefact of the normal approximation, and two methods
   now agree it is wrong.
3. **A2b is inside the band but marginal** (-0.0272, TOST
   lower limit -0.0483 against a −0.05 bound); it should be
   reported as equivalence-consistent rather than equivalence-established.
4. **The strict endpoint tells a different story than the lenient one** for
   A1, consistent with §2: the lenient flatness is partly held up by fallback
   extraction. Both are tabled above; neither is suppressed.

## Contract validity as a first-class result

Pair-level contract validity (both members emit a contract-valid answer),
geometry slice, mean over seeds:

| arm | contract validity | Δ vs base |
|---|---|---|
| base (step 0) | 0.9500 | — |
| A1 real | 0.8767 | -0.0733 |
| A2 gray | 0.6317 | -0.3183 |
| A2b no-image | 0.7728 | -0.1772 |
| A3 caption | 0.7578 | -0.1922 |

Every trained arm ends **below** the frozen base on contract validity, and
the ordering tracks how degraded the arm's endpoint is (A2 gray lowest at
0.6317). RL training on this task
erodes answer-contract compliance on the counterfactual probe even where it
raises task accuracy — an effect the lenient scorer's fallback extractor
hides. Reported here as a result in its own right, not as a caveat.

## Power

Bootstrap SE and the smallest true effect this design would detect at 80%
power (two-sided α=0.05), Acc_final:

| arm | bootstrap SE | min detectable effect |
|---|---|---|
| A1 real | 0.0124 | 0.0348 |
| A2 gray | 0.0134 | 0.0377 |
| A2b no-image | 0.0129 | 0.0360 |
| A3 caption | 0.0121 | 0.0338 |

For A1 the minimum detectable effect is ≈0.035, comfortably below the
±0.05 SESOI, so the null is informative rather than merely underpowered:
the design could have detected an effect half the size of the equivalence
bound. This is the power statement the audit asked for.
