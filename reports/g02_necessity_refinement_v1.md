# G0.2 necessity refinement — addendum to Gate 0

Artifact: `reports/g02_necessity_refinement_v1.json` · built by `scripts/build_g02_necessity_refinement.py` · git `80a2cb0625ca6b15e0dcfeb0d926d1d9861ac55f` · generated 2026-07-30T15:45:42Z · login node, CPU only, **no GPU job started**.

Addendum to `reports/gate0_stratification_v1.{json,md}`. The frozen Gate 0 artifact is **not modified**.

**Scope (I13).** This addendum operates only on Gate 0's **binary blind-answerable split**. It is never merged with the G0.1 / M5c **Δq tercile** analysis. The confound M5c found in the Δq terciles does not transfer literally to G0.2, because G0.2 is not built on Δq — it is built on `q_blind > ` the Jeffreys floor (`0.1386589899546222`), n=117 vs n=484.

**Reporting (I7).** Every estimand appears under both **lenient** (`acc_final`) and **strict** (`acc_strict`).

---

## 1. Reproduction of the published 84% / 42%

Pipeline validated against the frozen artifact before extension. Max absolute deviation across all 4 arms × 2 scopes × 2 strata: **2.776e-17** → **EXACT**.

| scope | stratum | n | A1 gain | A2b gain | recovery | published |
|---|---|---:|---:|---:|---:|---:|
| all_items | blind_answerable | 117 | +0.3276 | +0.2764 | 0.8435 | **84%** |
| all_items | not_blind_answerable | 484 | +0.2231 | +0.0930 | 0.4167 | **42%** |
| base_wrong_only | blind_answerable | 90 | +0.4667 | +0.4259 | 0.9127 | **91%** |
| base_wrong_only | not_blind_answerable | 406 | +0.3218 | +0.1970 | 0.6122 | **61%** |

The published **84%** and **42%** (and the base-wrong **91%** / **61%**) reproduce exactly from `reports/gate0_stratification_v1.json :: G0_2_headroom_control`, and independently from the per-item inputs.

## 2. Item-bootstrap intervals on the RATIOS

10,000 draws, seed 20260730, paired on items (A1 and A2b read from the same resampled item indices), within-stratum resampling with replacement, percentile 2.5 / 97.5. **No interval on these ratios existed anywhere in the repo before this addendum** — `gate0_stratification_v1.json` carried `ci95` on the component means only.

| mode | stratum | n | A1 gain [CI] | A2b gain [CI] | **recovery [CI]** | degenerate draws |
|---|---|---:|---|---|---|---:|
| lenient | blind-answerable | 117 | +0.3276 [0.25, 0.41] | +0.2764 [0.19, 0.36] | **0.8435** [0.68, 1.01] | 0 |
| lenient | no observed blind success | 484 | +0.2231 [0.18, 0.26] | +0.0930 [0.06, 0.13] | **0.4167** [0.28, 0.54] | 0 |
| strict | blind-answerable | 117 | +0.4986 [0.42, 0.58] | +0.4473 [0.37, 0.52] | **0.8971** [0.79, 1.01] | 0 |
| strict | no observed blind success | 484 | +0.3244 [0.29, 0.36] | +0.1942 [0.16, 0.23] | **0.5987** [0.52, 0.68] | 0 |

**Do the two intervals overlap?**

| mode | blind-answerable CI | no-blind-success CI | overlap | difference [CI] | bootstrap mass ≤ 0 |
|---|---|---|---|---|---:|
| lenient | [0.68, 1.01] | [0.28, 0.54] | **NO** | +0.4268 [0.22, 0.63] | <0.0001 |
| strict | [0.79, 1.01] | [0.52, 0.68] | **NO** | +0.2984 [0.17, 0.43] | <0.0001 |

**Answer: the intervals do NOT overlap, under either scoring.** The paired difference excludes zero in both. `difference` is the plug-in difference of the observed ratios; its interval is the 2.5/97.5 percentile of the bootstrap replicate differences.

Base-wrong headroom control, same bootstrap:

| mode | blind-answerable | no observed blind success | overlap | difference [CI] |
|---|---|---|---|---|
| lenient | 0.9127 [0.78, 1.06] (n=90) | 0.6122 [0.53, 0.70] (n=406) | **NO** | +0.3005 [0.14, 0.46] |
| strict | 0.9127 [0.78, 1.06] (n=90) | 0.6122 [0.53, 0.70] (n=406) | **NO** | +0.3005 [0.14, 0.46] |

*The lenient and strict base-wrong rows are identical, and that is expected, not a duplication error.* On base-wrong items lenient and strict gains are IDENTICAL by construction: base acc_final = 0 implies base acc_strict = 0 (verified for all 496 base-wrong items), and every trained arm satisfies acc_strict == acc_final on every item (G0.4 identity, re-verified here). The two rows are therefore expected to match exactly; this is not a duplication error.

## 3. B1 / B2 decomposition of the n=484 stratum

The stratum the published text labels *items requiring pixels* is defined **only** by absence of observed blind success. **252 of its 484 items have zero observed successes WITH the image too** (`c_real = 0` of 16) — the base solves them under no condition.

- **B1** — image demonstrably buys reward opportunity (`c_blind = 0`, `c_real > 0`): **n = 232**, base real greedy accuracy 0.2759
- **B2** — unsolved under every condition (`c_blind = 0`, `c_real = 0`): **n = 252**, base real greedy accuracy 0.0556

| mode | subgroup | n | A1 gain [CI] | A2b gain [CI] | **recovery [CI]** |
|---|---|---:|---|---|---|
| lenient | B1 image buys opportunity | 232 | +0.3420 [0.28, 0.41] | +0.1796 [0.11, 0.25] | **0.5252** [0.38, 0.66] |
| lenient | B2 never solved, any condition | 252 | +0.1138 [0.07, 0.16] | +0.0132 [-0.02, 0.05] | **0.1163** [-0.26, 0.36] |
| strict | B1 image buys opportunity | 232 | +0.5014 [0.44, 0.56] | +0.3391 [0.28, 0.39] | **0.6762** [0.59, 0.76] |
| strict | B2 never solved, any condition | 252 | +0.1614 [0.12, 0.20] | +0.0608 [0.04, 0.08] | **0.3770** [0.24, 0.54] |

| mode | B1 − B2 | CI | B2 interval includes 0 |
|---|---:|---|---|
| lenient | +0.4089 | [0.13, 0.79] | **YES** |
| strict | +0.2992 | [0.12, 0.47] | **no** |

Under lenient scoring A2b's gain on B2 is +0.0132 [-0.02, 0.05] and the recovery interval [-0.26, 0.36] includes zero and negative values.

## 4. Difficulty-standardised recovery

direct standardisation: both strata reweighted to the pooled 601-item q_real bin distribution; standardised gain_s = sum_k w_k * mean(gain | stratum s, bin k); recovery = std_A2b / std_A1. Binning variable: c_real = number correct among the 16 frozen base samples WITH the image (q_real is a strictly increasing function of c_real on this split).

Support per q_real bin (this is the honest limitation, stated before the result):

| q_real bin | target weight | n blind-answerable | n no-blind-success | pooled n |
|---|---:|---:|---:|---:|
| c_real=0 | 0.4626 | 26 | 252 | 278 |
| c_real=1 | 0.1880 | 18 | 95 | 113 |
| c_real=2 | 0.1231 | 19 | 55 | 74 |
| c_real=3-5 | 0.1514 | 35 | 56 | 91 |
| c_real>=6 | 0.0749 | 19 | 26 | 45 |

**Common-support limitation.** All five q_real bins have non-empty support in both strata, so no weight mass is discarded (retained 1.0000). Support is nevertheless badly unbalanced: the c_real=0 bin carries 0.463 of the target weight but is estimated from only 26 blind-answerable items against 252 not-blind-answerable items. Smallest cell overall is n=18. The standardised blind-answerable figure is therefore driven by small cells and its interval is correspondingly wide; it is reported as a sensitivity analysis, not as a replacement estimand.

| mode | stratum | std A1 gain | std A2b gain | **std recovery [CI]** |
|---|---|---:|---:|---|
| lenient | blind-answerable | +0.2822 | +0.2270 | **0.8045** [0.59, 1.03] |
| lenient | no observed blind success | +0.2386 | +0.1067 | **0.4472** [0.32, 0.56] |
| strict | blind-answerable | +0.3935 | +0.3383 | **0.8598** [0.71, 1.02] |
| strict | no observed blind success | +0.3530 | +0.2211 | **0.6263** [0.55, 0.70] |

| mode | standardised pair | overlap | difference [CI] |
|---|---|---|---|
| lenient | 0.8045 vs 0.4472 | **NO** | +0.3573 [0.11, 0.62] |
| strict | 0.8598 vs 0.6263 | **NO** | +0.2335 [0.07, 0.41] |

Per-bin recovery (lenient), showing where the standardised figures come from:

| q_real bin | weight | blind-answerable n / A1 / A2b / rec | no-blind-success n / A1 / A2b / rec |
|---|---:|---|---|
| c_real=0 | 0.463 | 26 / +0.179 / +0.154 / +0.857 | 252 / +0.114 / +0.013 / +0.116 |
| c_real=1 | 0.188 | 18 / +0.352 / +0.204 / +0.579 | 95 / +0.225 / +0.056 / +0.250 |
| c_real=2 | 0.123 | 19 / +0.439 / +0.333 / +0.760 | 55 / +0.545 / +0.345 / +0.633 |
| c_real=3-5 | 0.151 | 35 / +0.305 / +0.314 / +1.031 | 56 / +0.405 / +0.244 / +0.603 |
| c_real>=6 | 0.075 | 19 / +0.439 / +0.386 / +0.880 | 26 / +0.205 / +0.141 / +0.687 |

## 5. Proposed replacement wording (proposal only — the PI owns the prose)

**Why the label is wrong.** The published label 'items requiring pixels' is applied to the n=484 not-blind-answerable stratum. That stratum is defined only by the absence of observed BLIND success. It does not condition on the image buying anything: 252 of its 484 items (52.1%) also have zero observed successes WITH the image, i.e. the base model solves them under no condition. Those items cannot demonstrate that pixels are required; they only show the base fails.

**What is superseded.** The NUMBER 0.4167 (42%) is arithmetically correct and reproduces exactly; it is the label and its use as a single summary of 'image-requiring' items that are superseded.

### Target: `docs/EXPERIMENT_TODO.md line 52 (G0 ledger row)`

> **Current:** G0.2: image-free training recovers 84% of A1's gain on blind-answerable items and 42% on items requiring pixels

> **Proposed Minimal:** G0.2: image-free training recovers 84% [0.68, 1.01] of A1's gain on blind-answerable items (n=117) and 42% [0.28, 0.54] on items with no observed blind success (n=484); that second stratum splits into 53% [0.38, 0.66] where the image demonstrably buys reward opportunity (n=232) and 12% [-0.26, 0.36] on items the base solves under no condition (n=252)

> **Proposed Short:** G0.2: recovery 84% on blind-answerable items vs 42% on items with no observed blind success; intervals disjoint. The 42% is not a figure for image-requiring items — 252/484 of that stratum is never solved with the image either

### Target: `docs/PAPER1_RESEARCH_DOC.md line 70 (Gate 0 paragraph), clause on 42%`

> **Current:** recovering 84% of A1's gain where blind reward opportunity exists and 42% where none was observed (91% vs 61% under a base-wrong headroom control)

> **Proposed:** recovering 84% [0.68, 1.01] of A1's gain where blind reward opportunity exists (n=117) and 42% [0.28, 0.54] where none was observed (n=484); the two intervals are disjoint (difference +0.43 [0.22, 0.63]). The second stratum is not 'items requiring pixels': 252 of its 484 items have no observed success WITH the image either. Decomposed, recovery is 53% [0.38, 0.66] on the 232 items where the image demonstrably buys reward opportunity and 12% [-0.26, 0.36] on the 252 items the base solves under no condition (91% vs 61% under a base-wrong headroom control)

### Label substitutions

| do not use | use instead | why |
|---|---|---|
| items requiring pixels | items with no observed blind success | names exactly the measured condition (c_blind = 0 of 16), asserts nothing about image necessity |
| items requiring pixels | blind-unanswerable items | acceptable short form; still describes only the blind side of the measurement |
| — | items where the image demonstrably buys reward opportunity (c_blind = 0, c_real > 0, n=232) | this is the only subgroup in the analysis for which an image-necessity reading is licensed by data |
| — | items unsolved under every condition (c_blind = 0, c_real = 0, n=252) | measured description; these items carry no evidence about image necessity in either direction |

No edit was made to `docs/PAPER1_RESEARCH_DOC.md` or `docs/EXPERIMENT_TODO.md`.

## 6. Split-rule audit (found while verifying, reported not applied)

`q_i` is `q_i = mixed_group_probability(p_i, g) = 1 - p^g - (1-p)^g  (src/eval/blind_solvability.py:74-77, called at :235)`. q_i is symmetric under p -> 1-p, so c_i = 16/16 yields the SAME numeric q_i as c_i = 0/16.

- Registered rule: scripts/build_preregistration_pilot_draft.py:382 -- 'The floor is exactly c_i=0 (0/16 sampled successes, q_i=0.138659), not every item numerically sharing that symmetric q_i.'
- Rule as executed: scripts/build_g02_headroom_control.py:40-42 -- answerable = q_blind > min(q_blind) + 1e-9 (numeric)

Consequence: **1 item** is classified differently. Published rule gives 117 / 484; the registered rule gives 118 / 483.

| eval index | c_blind | q_blind | c_real | q_real | published rule | registered rule |
|---:|---:|---:|---:|---:|---|---|
| 567 | 16/16 | 0.1386589899546222 | 10/16 | 0.9019 | not_blind_answerable | blind_answerable |

Sensitivity — recovery ratios under the registered `c_blind = 0` rule:

| mode | stratum | n | recovery [CI] |
|---|---|---:|---|
| lenient | blind-answerable (c_blind > 0) | 118 | 0.8435 [0.68, 1.01] |
| lenient | no blind success (c_blind = 0) | 483 | 0.4167 [0.28, 0.54] |
| strict | blind-answerable (c_blind > 0) | 118 | 0.8989 [0.80, 1.01] |
| strict | no blind success (c_blind = 0) | 483 | 0.5962 [0.52, 0.67] |

*Why the lenient rows are unchanged:* Every discordant item has a LENIENT gain of exactly 0 for both A1 and A2b (base already correct with the image, arm still correct). Moving a zero-gain item between strata leaves both stratum sums unchanged and rescales numerator and denominator by the same n, so the lenient recovery ratios are numerically identical under both rules. The strict ratios do shift, because the item has a non-zero strict gain (base acc_strict = 0 while base acc_final = 1).

The published figures are left as-is in the frozen artifact; this addendum reports the discrepancy and its (negligible) numerical effect. Whether to re-run Gate 0 under the registered rule is a PI decision.

## 7. Superseded-figure ledger

| figure | status | still valid for | replaced by |
|---|---|---|---|
| 42% (0.4167) recovery on 'items requiring pixels' | **SUPERSEDED AS LABELLED — RETAINED AS A NUMBER** | recovery ratio on the not-blind-answerable stratum (n=484), reproduced exactly here | d3_b1_b2_decomposition + d2_ratio_intervals |
| 84% and 42% quoted without uncertainty | **SUPERSEDED — intervals now exist** | — | d2_ratio_intervals (10,000-draw paired item bootstrap, seed 20260730) |

The 42% figure is **retained, not deleted**: it is the correct recovery ratio for the n=484 not-blind-answerable stratum and reproduces exactly. What is superseded is its label and its use as a single summary of image-requiring items.
