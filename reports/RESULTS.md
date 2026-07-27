# Blind Gains — Consolidated Results

**Single canonical results file.** Updated in place; supersedes
`x_series_synthesis_v1/v2/v3.md` (retained in git history on the cluster).
Last updated 2026-07-27. Facts and registered readings only; no interpretation
beyond the registered documents. Layer names: *candidate-evidence ranking* /
*open-form realization*. "Already perceived/understood" remains hypothesis
language only (X2 bottom branch).

---

## 0. Status at a glance

| chain | state |
|---|---|
| Pilot seeds 1–3 (C1) | **complete** — replication rung R2 |
| X1–X5 diagnostics | **complete** |
| B1 construct + trained scoring | **complete** |
| D2 test-time access (3 seeds) | **complete** |
| D3 train×test matrix | running, 19/36 cells |
| M5 long-horizon → step 400 (C3) | running, step 354 |
| Mini-A5 trainability (C2) | running, CP arm step 15/120 |
| M7 ViRL stratified (C4) | built, awaiting a free node |
| C5 7B, M9/M11, X6, human gates | not reached / owned elsewhere |

---

## 1. Headline: the task gain (three seeds, replicated)

Geometry3K `Acc_final`, step 100 − step 0, 601 held-out items per seed.

| arm | seed 1 | seed 2 | seed 3 | mean |
|---|---|---|---|---|
| A1 real | +0.2529 | +0.2463 | +0.2313 | **+0.2435** |
| A3 caption | +0.1098 | +0.0832 | +0.1215 | +0.1048 |
| A2b no-image | +0.0300 | +0.0549 | +0.0532 | +0.0460 |
| A2 gray | +0.0200 | +0.0100 | +0.0183 | +0.0161 |

**Recovery of the A1 gain (matched evaluation):** gray 7.9 / 4.1 / 7.9%
(mean 6.6%); no-image 11.8 / 22.3 / 23.0% (19.1%); caption 43.4 / 33.8 / 52.5%
(43.2%).

- The preregistered 30–70% blind-recovery interval is **falsified in every
  seed** for both zero-visual-bit arms.
- The **caption inversion** replicates 3/3: A3 starts above A1 at step 0 and
  ends below it at step 100.
- The gain is **not a formatting artifact** — the strict-format gain is *larger*
  (+0.3583 mean), so the conservative metric is the one reported. Independently
  re-derived from raw shards.

---

## 2. The counterfactual endpoint — corrected claim

Registered geometry FlipTrack slice (one 600-pair template).

| seed | lenient delta | contract-strict delta |
|---|---|---|
| 1 | −0.0017 | **−0.1267** |
| 2 | +0.0083 | +0.0333 |
| 3 | +0.0100 | **−0.0267** |
| mean | +0.0056 | −0.0400 |

**Defensible statement:** A1's *lenient* pair accuracy is statistically
indistinguishable from base (per-seed paired item-level CIs [−0.0267, +0.0250],
[−0.0167, +0.0334], [−0.0150, +0.0350], all inside ±0.05). **This null is not
robust and is not a passed registered control.** Under contract-strict scoring
the same checkpoints move outside the band in all three seeds, because A1
training degrades FlipTrack answer-contract compliance (base 0.9500 → 0.7367 /
0.9917 / 0.9017) and the fallback extractor masks it.

Three defects corrected here (see `reports/correction_three_seed_fliptrack_v1.md`):
the strict-scoring collapse; a seed-level CI used where the preregistration
requires the **paired item-level** CI (and z=1.96 at df=2 mis-sized it — under
t(2)=4.303 the A2 gray row also leaves the band); and the ±0.05 margin being
registered for the **Δ_A2gray − Δ_A2b** contrast, not for A1. On the secondary
overall-pair endpoint A1 *does* move (+0.0283 / +0.0208 / +0.0267, CIs excluding
zero in all three seeds).

Caveat carried: the step-0 minuend is a single pinned legacy run shared by all
three seeds, so seed spread reflects step-100 variation only.

---

## 3. Sharpening is content-bound (X1 seeds 1, X5 seed 2)

Margin inflation vs base, primary template:

| arm | seed 1 correct-image | seed 2 correct-image | mismatched-real (both) |
|---|---|---|---|
| A1 | +0.1501 | +0.1293 | ≈ 0, CI spans 0 |
| A3 caption | +0.0900 | +0.0760 | ≈ 0, CI spans 0 |
| A2b no-image | +0.0348 | +0.0577 | ≈ 0, CI spans 0 |
| A2 gray | +0.0356 | +0.0373 | ≈ 0, CI spans 0 |

A same-template image with the *wrong content* buys nothing. Under the twin
member's image, the twin's gold is preferred for **0.948–0.955 of members in
every model, including the frozen base**; open-form pair-correct is ≤ 0.006
under mismatched images and exactly 0 under twin/gray/no-image.

The registered ratio bands degenerate at a statistically-zero denominator; the
mechanical labels are recorded in the reports.

---

## 4. Test-time image access (D2, three seeds)

| seed | Acc(A1, real) | Acc(A1, none) | RetainedGainBlind | band |
|---|---|---|---|---|
| 1 | 0.4276 | 0.1082 | 0.158 | (a) image-mediated |
| 2 | 0.4210 | 0.0982 | 0.122 | (a) image-mediated |
| 3 | 0.4060 | 0.1065 | 0.166 | (a) image-mediated |

**Verdict `a_image_mediated_at_test_time` in all three seeds.** Reproduction
check reproduced each published step-100 value exactly.

**Registered secondary — the open question:** A2b, trained with *no images*,
scores **0.3195 / 0.2962 / 0.2945 when evaluated with images** (base 0.1747),
a benefit of **+0.221 / +0.173 / +0.173**. Measured on the same real-image test
condition, that is roughly half of A1's gain, versus the 11.8–23.0% published
under matched evaluation. D3 (below) tests whether the low blind recovery is
substantially an evaluation-condition effect.

---

## 5. The two-layer gap (X2, registered ladder)

The golds-only margin statistic is candidate-set-invariant by construction and
empirically: **exactly 0.9067** in v1 and v2 for base and both A1 checkpoints,
zero pair-level disagreements. Against the structured negative sets (five
registered types, 600 exactly-replayed scenes), base against-set pair-success is
**0.5167 [0.4750, 0.5567]**; A1 step-60 0.5267, step-100 0.5133.

**Registered branch (mechanical): bottom** — the 0.9067 is predominantly
candidate-set structure, and the realization gap is a measurement-methods
finding. Ships without renegotiation; the "already perceived" result-language
upgrade is off the table.

---

## 6. Blind-reward corrosion is item-identifiable (X3)

A2's exact −0.0450 geometry decline resolves at item level: base 0.4717 → A2
0.4267 in both seeds, via 51 and 49 correct→wrong pairs with **42 shared**
(Jaccard 0.7241 vs permutation null 0.0978, p = 1e-4, 10k draws). On shared
wrong slots the **same extracted wrong answer appears in 41/42 (97.6%)**.
Dominant taxon: nearest-gridline off-by-one (19/20). On those 42 items every arm
is disproportionately wrong (A1 26–28/42, A2b 34–38/42, A3 30–32/42).

---

## 7. Calibration (X4, EXPLORATORY)

Under real images all models are **underconfident** (top-candidate confidence
~0.18–0.20 vs accuracy ~0.75; ECE ~0.57). Under twin-counterfactual images
confidence is unchanged by construction while accuracy collapses to ~0.012 —
overconfidence gap **+0.17 to +0.19**. Blind/mismatched conditions sit near
chance with near-uniform confidence.

---

## 8. Track-B construct (B1 declared batch, one shot)

Base pair-correct by intervention type (real / blind / caption overall
0.33 / 0.03 / 0.04):

| type | base | A1 s1 | A1 s2 | A2b s1 | A3 s1 |
|---|---|---|---|---|---|
| fact_read | 0.600 | 0.550 | 0.500 | 0.500 | 0.500 |
| style_twin (invariance) | 0.643 | 0.643 | 0.714 | 0.571 | 0.643 |
| distractor_only (invariance) | 0.438 | 0.375 | 0.438 | 0.438 | 0.375 |
| binding_swap | 0.188 | 0.188 | 0.188 | 0.188 | 0.188 |
| prior_conflict | 0.143 | 0.357 | 0.286 | 0.429 | 0.429 |
| chained_premise | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

Registered branches (a) and (b) both required fact-read improvement, which did
not occur → **no_registered_branch**. `chained_premise` at floor for every model
→ **construct not discriminative at 3B**. Descriptive: `prior_conflict` rises in
every arm *including the blind-trained A2b*, so that movement is not
image-mediated. Cells are 14–20 pairs; point estimates only.

Instrument note: consistency pairs are scored single-gold, because the frozen
two-gold ambiguity guard structurally fails equal-gold items.

---

## 9. Corrections and integrity events

1. **FlipTrack equivalence overstated** (§2) — found by an 8-agent adversarial
   audit, verified directly, corrected in place.
2. **Seed-3 readout inherited seed-2 audits**, returning values byte-identical
   to seed 2; caught by the rule that seed 3 must not reproduce seed 2 exactly.
   Builder now resolves seed-3 audits and fails closed (`ac3f362`).
3. **M5 step-250 model state lost** when the node-local scratch archive was
   removed; step-300 merged weights regenerated from on-quota raw. No registered
   analysis consumes step-250. Policy adopted: durable artifacts never in `/tmp`.
4. **Orchestrator fragility** — transient `ssh` failures on the login node were
   raised as fatal; now retried with backoff, orphaned manifests reconciled, and
   the orchestrator relocated to the compute node.

---

## 10. Reserved slots (evidence not yet in hand)

D3 train×test matrix (running); M5 step-400 horizon rung R3; Mini-A5
trainability gate; M7 ViRL39K stratified dose-response rung R4 (data frozen,
image-disjoint split registered, eight matched configs and launcher committed);
C5 7B contrast; M11 non-Qwen; X6 related-work table (PI-owned); human gates —
chart-v08 no-zoom audit, 24-candidate support review, R19/R20 audit samples.
