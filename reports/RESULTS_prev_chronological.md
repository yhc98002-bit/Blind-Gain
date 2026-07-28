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
| D3 train×test matrix | **complete** - registered branch (a) |
| M5 long-horizon → step 400 (C3) | running, step 361 |
| Mini-A5 trainability (C2) | running, CP arm step 36/120 |
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

**Baseline verified (2026-07-27).** The audit flagged that the step-0 minuend
was a single pinned legacy run, shared across all three seeds and measured
under a possibly different harness build. It has now been re-measured from
scratch on the locked 1,200-pair R19 manifest with the current harness and
reproduces **exactly**: geometry lenient 0.4717 and strict 0.4433, matching
the pinned values to four decimals (run `fliptrack_base_remeasure_an12_20260727T124803Z`).
The minuend is therefore verified rather than inherited. The residual caveat
stands that it is still a single measurement, so seed-level spread reflects
step-100 variation only.

---

## 2b. Pooled item-level equivalence, contract validity, power (COMPLETE)

Artifacts: `reports/pooled_item_equivalence_v1.{md,json}`, built by
`scripts/build_pooled_item_equivalence.py`. This is the **primary** equivalence
statistic; the seed-level figure in `three_seed_summary_v1` is retained only as
a secondary. Method: per pair, the paired delta vs the pinned base is averaged
over three seeds, then a cluster bootstrap over the 600 pair_ids (20,000 draws).
Clustering is required — the same 600 pairs recur in every seed, so treating the
1,800 rows as independent understates the interval. TOST: the 90% CI must lie
inside +/-0.05. The pooled means reproduce the published per-seed values exactly;
only the aggregation changed.

| arm | pooled delta | 95% CI | 90% CI (TOST) | equivalent? |
|---|---|---|---|---|
| A1 real | +0.0056 | [-0.0189, +0.0294] | [-0.0150, +0.0256] | **yes** |
| A2 gray | -0.0422 | [-0.0689, -0.0161] | [-0.0644, -0.0206] | **NO** |
| A2b no-image | -0.0272 | [-0.0528, -0.0017] | [-0.0483, -0.0061] | marginal |
| A3 caption | -0.0050 | [-0.0289, +0.0189] | [-0.0244, +0.0150] | yes |

**A1's flat counterfactual endpoint survives its strongest test** — item-level
inference on the lenient endpoint, not merely n=3 seeds. **A2 gray is confirmed
outside the band** by a wholly independent route from the t(2) correction, so
two methods now agree the published "within band" verdict for A2 gray was an
artefact of the normal approximation (§9). A2b is inside but marginal (lower
limit -0.0483 against a -0.05 bound) and is reported as equivalence-*consistent*,
not equivalence-established.

**Contract validity, reported as a first-class result** (pair-level, geometry
slice, mean over seeds; base sourced from the 2026-07-27 re-measurement because
the pinned 2026-07-10 shards predate the field):

| base | A1 real | A2 gray | A2b no-image | A3 caption |
|---|---|---|---|---|
| 0.9500 | 0.8767 (-0.0733) | 0.6317 (-0.3183) | 0.7728 (-0.1772) | 0.7578 (-0.1922) |

Every trained arm ends **below** the frozen base, and the ordering tracks how
degraded the arm's endpoint is. RLVR on this task erodes answer-contract
compliance on the counterfactual probe even where it raises task accuracy — an
effect the lenient scorer's fallback extractor hides. This is a result in its
own right, not a caveat on another one.

**Power.** Minimum detectable effect at 80% power (two-sided alpha=0.05) is
0.0348 (A1), 0.0377 (A2 gray), 0.0360 (A2b), 0.0338 (A3) — all comfortably below
the +/-0.05 SESOI. The A1 null is therefore informative rather than underpowered:
the design could have detected an effect about 70% of the equivalence
bound (0.0348 / 0.05).

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

## 4b. D3 — training condition vs test condition (COMPLETE, 36 cells)

Registered: `docs/registered_d3_condition_matrix_v1.md`. Acc_final by arm x test
condition, mean over three seeds (base row pinned: real 0.1747, gray 0.0899,
none 0.0682):

| arm (trained) | tested real | tested gray | tested none |
|---|---|---|---|
| A1 real | 0.4182 | 0.1093 | 0.1043 |
| A3 caption | 0.3494 | 0.1143 | 0.1054 |
| A2b no-image | 0.3034 | 0.1065 | 0.1143 |
| A2 gray | 0.2934 | 0.1059 | 0.1015 |

Recovery of the A1 gain, matched vs crossed evaluation (per seed):

| arm | matched recovery (own condition) | crossed recovery (tested with images) | ratio |
|---|---|---|---|
| A2 gray | 0.079 / 0.040 / 0.079 | 0.507 / 0.527 / 0.425 | 6.43 / 13.07 / 5.38 |
| A2b no-image | 0.119 / 0.223 / 0.230 | 0.572 / 0.493 / 0.518 | 4.83 / 2.21 / 2.25 |

**Registered branch (a) obtains** on the primary Acc_final criterion (ratio > 2
for both blind arms in all three seeds): the published low blind recovery
substantially reflects the *matched evaluation condition*. Per the pre-committed
consequence, the canonical claim carries the scope tag **"under matched
evaluation"**, with the crossed-condition figure reported alongside it.

**Format control, reported honestly.** Recomputed on Acc_strict with the
registered strict step-0 bases (real 0.0599, gray 0.0050, none 0.0017), the
ratios are 2.32 / 2.58 / 2.06 (A2 gray) and 2.69 / 1.95 / 1.96 (A2b). The
direction and rough magnitude reproduce, so the effect is not merely improved
answer formatting - but two of six seed-arm cells fall marginally BELOW the 2x
threshold, so the strict control does not cleanly clear the same bar. The
registration's format-control clause did not define "reproduce the pattern"
numerically; that ambiguity is resolved here by reporting both and qualifying
the claim, not by choosing the favourable reading.

Interpretation limit: A3's matched condition is `caption`, which is not part of
this matrix, so A3 is reported across real/gray/none only.

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

---

## 11. Reflection — what the evidence adds up to

Written 2026-07-27, after C1, D2, D3 and the X-series. Registered language locks
apply: statements below are either registered results or explicitly marked as
hypothesis.

**1. The strongest single finding is that "blind training barely works" was
largely a measurement artifact.** Published recoveries (gray 6.6%, no-image
19.1% mean) compare each arm inside its own training condition. D3 crosses the
factors and the picture inverts: evaluated *with images*, the blind-trained arms
recover **42–57%** of A1's gain (registered branch (a), ratios 2.21–13.07, all
three seeds, both arms). Blind training learned considerably more than the
matched-condition figure implied — it simply had no channel to express it.

**2. Yet the image is required for expression, in every arm.** D2: only
12–17% of A1's gain survives removing the image at inference (three seeds,
registered band (a)). D3 shows the same for arms that never saw an image in
training — A2b scores 0.303 with images and 0.114 without. So the picture that
holds together is: RLVR improves something substantially condition-general,
**but realizing it requires visual input at test time**. That the training
signal could be image-free while the payoff cannot is the most surprising
structural result here.

**3. Whatever improves, it is content-bound, not presence-bound.** X1/X5: a
same-template image with the *wrong* content produces statistically zero margin
inflation in every arm and both seeds, while correct-image inflation is clearly
non-zero. Under the twin image, the twin's gold is preferred for ~95% of
members — including in the frozen base. The base model already tracks image
content closely; training sharpens margins on that existing signal.

**4. The headline dissociation survives, but weaker than first reported.** The
+0.2435 task gain is solid and is not a formatting artifact. The flat
counterfactual endpoint is *not* a passed control: it holds on lenient scoring
and collapses under contract-strict scoring, because A1 degrades answer-contract
compliance (0.9500 → 0.7367) and the fallback extractor masks it (§2). The
honest claim is a large task gain alongside a counterfactual endpoint that does
not move *when measured leniently*, with the measurement fragility disclosed.

**5. Costs are real and reproducible.** A2 gray's −0.045 geometry decline is
item-identifiable across seeds (Jaccard 0.724 vs null 0.098) and 97.6%
answer-deterministic, concentrated in nearest-gridline off-by-ones. Blind reward
does not merely fail to help; it corrodes specific, identifiable items.

**6. Two claims were downgraded by our own checks.** The 0.9067
latent-competence figure is predominantly candidate-set structure (X2 bottom
branch), and the three-seed equivalence verdict was overstated (§2, §9). Both
were found by adversarial re-derivation rather than by review.

**Hypothesis, not result (§7 locks):** these patterns are *consistent with*
RLVR improving evidence utilization and answer production on top of visual
representations the base model already has, rather than improving visual
extraction itself. The forced-choice and premise-probe evidence needed to
license that as a result has not been obtained.

---

## 12. Gate 0 and Phase 0 — results, implementation, and what they imply

Added 2026-07-27 under the three-document authority (`EXPERIMENT_TODO.md`,
`PAPER1_RESEARCH_DOC.md`, `PAPER2_RESEARCH_DOC.md`). All of this section is
cached-prediction or CPU work; no result here consumed a trainer GPU.

### 12.1 A scorer defect that was silently voiding invariance items (P0.2)

`src/eval/fliptrack_metrics.py` scored every member as

    acc_final = gold_tier > other_tier and gold_tier > 0

On a pair whose two members share a gold — every invariance item — `gold_tier`
and `other_tier` are computed from the *same string*, so the comparison is never
true. A member answering the gold exactly scored **wrong**, and every match was
flagged ambiguous. It surfaced when the premise probe returned member accuracy
**0.000 for all five models**, including a base that scores 0.150 on the strictly
harder final question.

Fixed with an equal-gold branch (`gold_tier > 0`, ambiguity disabled — there is no
competing answer to discriminate against). Ships a 7-case adversarial fixture the
pre-fix code fails, two cases of which lock causal-pair discrimination unchanged.

**Blast radius is nil for Paper 1.** R19 contains **zero** equal-gold pairs and
rescores to 0.4717 lenient / 0.4433 strict, matching pinned exactly. The frozen
R20 scorer is byte-identical (I11). What *was* affected: B1's `style_twin` (14/14)
and `distractor_only` (16/16), which had been resting on a single-gold workaround
— precisely the situation P0.2 was written to end. Those must be rescored before
reuse.

*Principle:* a discriminative criterion and an invariance construct are
incompatible by construction. Any scorer that credits "your gold beats the other
gold" silently reports 0 on every item where the two golds coincide. The
`collapsed` field already carried the guard, so this was an oversight rather than
a design choice — which is exactly why it survived: the code looked right.

### 12.2 Premise probe, five separate numbers (P0.1) — registered branch (b)

Twenty `chained_premise` pairs, 40 members per cell, rescored with the fixed
scorer.

| cell | premise member | premise pair | premise transition | final member | final pair | reasoning \| correct premise |
|---|---|---|---|---|---|---|
| base | 0.275 | 0.200 | 0.200 | 0.150 | 0.000 | 0.273 (n=11) |
| A1 real s1 | 0.225 | 0.200 | 0.200 | 0.100 | 0.000 | 0.222 (n=9) |
| A1 real s2 | 0.175 | 0.150 | 0.150 | 0.075 | 0.000 | 0.000 (n=7) |
| A2b no-image s1 | 0.300 | 0.200 | 0.200 | 0.125 | 0.000 | 0.250 (n=12) |
| A3 caption s1 | 0.250 | 0.200 | 0.200 | 0.075 | 0.000 | 0.200 (n=10) |

Base premise accuracy **0.275** (95% Wald [0.137, 0.413]) fires registered branch
**(b)**: the construct is revised before release, and its 0.000 pair accuracy is
*uninformative about chaining* rather than evidence against it. The interval
straddles the 0.30 (b)/(c) boundary; the consequence is identical either way.

Three consequences for Paper 2:

1. **Premise extraction is the first bottleneck but not the only one.** Even among
   members whose premise was extracted correctly, the base completes the chain
   only 0.273 of the time. An easier premise curriculum alone would raise the
   first factor and leave the second largely untouched.
2. **C3 has signal here, but thin.** Final pair accuracy is 0.000 for every model
   while premise-level correctness is non-zero for 17.5–30.0% of members, so the
   hierarchical reward does expose a non-empty gradient where the answer-level
   reward exposes none — which is C3's stated rationale, now measured. But the
   premise factor is itself sparse, which is the Phase-2 gate condition.
3. **Premise-transition accuracy is uninformative by construction.** It equals
   premise pair accuracy in all five cells because B1 holds the premise invariant
   across the flip (the nearest point stays the same; only its coordinate moves).
   **Track 4 needs items whose premise itself changes**, or the metric can never
   do independent work.

No arm beats base on premise extraction (base 0.275 is the highest of five
cells). Directionally consistent with RLVR not improving acquisition, but n=40
makes it far too underpowered to claim; recorded as consistent, not as evidence.

### 12.3 Gate 0 (G0.1–G0.4)

**Implementation note that changes the numbers.** Each arm's own geo audit is its
*matched* training condition — A2b's is `none`, A2's is `gray`. Every Gate-0
question is about the **image-present** gain, so all four analyses use the D3
crossed cells with the arm evaluated under `real`. Using the matched cells would
have reported A2b's gain as **−0.0605** instead of **+0.1287**. Base per-item comes
from the guarded-rescore `geo_baselines`, which reproduce registered step-0
exactly (0.1747 / 0.0599 / 0.4393), and A1 image-present reproduces the published
+0.2435 — an end-to-end consistency check on the join.

**G0.1 — do gains concentrate on high-Δq items? Yes, for both arms.**

| arm | low Δq | mid Δq | high Δq | Spearman ρ | perm p |
|---|---|---|---|---|---|
| A1 real | +0.149 | +0.278 | +0.422 | +0.198 | 0.0005 |
| A2b no-image | +0.061 | +0.121 | +0.283 | +0.192 | 0.0005 |

H1 is supported and **C1 necessity sampling earns its place in the method**:
selection on Δq targets exactly where RLVR already delivers most of its gain. The
effect is present in A2b too, so high-Δq items are not preferentially learned
*because* the image was shown in training.

**G0.2 — does A2b's image-present gain concentrate on low blind-solvability
items? No — the opposite, and it survives a headroom control.**

`q_blind` is Jeffreys-smoothed, so the split is "≥1 observed blind success"
(n=117) vs none (n=484). Those groups differ in base accuracy (0.2308 vs 0.1612),
so the contrast is also run restricted to base-wrong items, where every arm faces
identical 0→1 headroom.

| arm | all: blind-answerable | all: not | base-wrong: answerable | base-wrong: not |
|---|---|---|---|---|
| A1 real | +0.3276 | +0.2231 | +0.4667 | +0.3218 |
| A2b no-image | +0.2764 | +0.0930 | +0.4259 | +0.1970 |
| A2 gray | +0.2735 | +0.0813 | +0.4296 | +0.1839 |
| A3 caption | +0.2393 | +0.1591 | +0.3704 | +0.2635 |

As a share of A1's gain, A2b recovers **84%** where blind reward opportunity
exists and **42%** where it does not (91% vs 61% restricted to base-wrong). Both
blind-trained arms show the steep version; A1 and A3 do not.

*This is the sharpest result of the round.* The title claim survives with a scope
qualifier it can carry honestly: image-free RLVR produces a real image-dependent
gain on items that genuinely require the image (+0.197, far from zero), so it is
not merely generic text-side improvement — but it is **disproportionately** the
blind-attainable component. Image-free training harvests most of what was
reachable without pixels and about half of what was not. This is direct measured
support for Paper 2's **H1**.

**G0.3 — A1 and A2b newly-correct sets.** Jaccard 0.363–0.423 against a
permutation null of 0.157–0.177, p ≤ 0.004 in all three seeds. Substantially
overlapping policies — the two are moving much the same mechanism — but ~60% of
the union belongs to only one arm, so they are not interchangeable.

**G0.4 — answer vs format. The access matrix is format-free by identity.**

| arm | answer gain | strict gain | format gain | contract-validity gain |
|---|---|---|---|---|
| A1 real | +0.2435 | +0.3583 | +0.1148 | +0.543 |
| A2b no-image | +0.1287 | +0.2435 | +0.1148 | +0.538 |
| A2 gray | +0.1187 | +0.2335 | +0.1148 | +0.534 |
| A3 caption | +0.1747 | +0.2895 | +0.1148 | +0.528 |

Format gain is *exactly* +0.1148 for all four arms — not a coincidence but an
identity. Every trained arm satisfies `acc_strict == acc_final` on every item, so
FormatGain collapses to `base_final − base_strict` = 0.1747 − 0.0599 = 0.1148, a
constant depending only on the frozen base. **The formatting component therefore
cancels exactly in any arm-minus-arm comparison**, so the entire F1 access matrix
is format-free by construction. What differs between arms is answer content alone.

*Principle:* training saturates the answer-contract channel to ceiling in every
arm, including arms that never saw an image. Contract compliance is not a visual
capability and does not discriminate between training conditions — it is a
one-time fixed offset the base model pays and every trained model recovers.

### 12.4 F2d — where the R19 movement lands, and a correction to PAPER1

Base rates by task:

| task | role | n | pair | strict pair | member |
|---|---|---|---|---|---|
| coordinate survey register | primary visual anchor | 600 | 0.4717 | 0.4433 | 0.6450 |
| header-cued verification table | saturated control / retention canary | 300 | **0.8667** | 0.1800 | 0.9000 |
| nine-series calibration trace | oracle-localized readout control | 300 | 0.4367 | 0.4200 | 0.6617 |

**Correction.** PAPER1 §5 describes the header-cued table as "saturated at 1.000
for every model including base" and unable to show improvement, and §3 F2 builds
its mechanism on that table contributing "nothing to any delta." Measured on R19
the base is **0.8667**, not 1.000, and it moves in *every* arm (+0.019 to +0.023;
A2 gray's interval excludes zero), contributing **18.7%** of A1's overall
movement. The retention-canary function still holds — nothing drops — but the
premise that it is pinned at ceiling and arithmetically inert is false and needs
correcting in both sections. Note also its lenient/strict split (0.8667 vs
0.1800): it is the R19 task most dependent on fallback extraction.

**The F2 mechanism survives the correction.** For A1: the oracle-localized readout
control moves **+0.0711** (CI [+0.0256, +0.1167], excludes zero) supplying **70%**
of overall movement, while the primary visual anchor — the only R19 task requiring
search and binding — moves **+0.0056** with an interval spanning zero, supplying
11%. The gain lands where localization has already been supplied by the cue.

**New finding: the blind arms separate the layers more sharply than A1 does.**

| arm | primary visual anchor | oracle-localized readout control |
|---|---|---|
| A2 gray | **−0.0422** [−0.0683, −0.0161] | **+0.0556** [+0.0100, +0.1011] |
| A2b no-image | **−0.0272** [−0.0522, −0.0017] | +0.0233 [−0.0200, +0.0678] |

Both blind-trained arms **decline on the search-and-binding anchor** with
intervals excluding zero while **rising on the cued readout control**. Their flat
overall R19 numbers (−0.0014, −0.0019) are not inertness — they are two real
effects of opposite sign cancelling inside an aggregate that should never have
been read as one capability score.

*This localizes F5.* Blind-reward corrosion is not diffuse damage; it is specific
to the task requiring a model to locate a label and bind it to a point, and it
coexists with genuine improvement where the target is already marked. A cue that
supplies localization is enough to protect a blind-trained model from its own
corrosion. That is a sharper statement of the utilization thesis than any overall
number can express, and it yields a **falsifiable prediction for the cue ladder
(F4b): the damage should appear at the search rungs and vanish at the exact-cue
rung.**

### 12.5 D3 TrainShare (PAPER1 §8 estimand)

| arm | s1 | s2 | s3 | pooled | 95% CI (paired item-level) |
|---|---|---|---|---|---|
| A2 gray | 0.507 | 0.527 | 0.424 | **0.487** | [0.383, 0.588] |
| A2b no-image | 0.572 | 0.493 | 0.518 | **0.528** | [0.424, 0.629] |
| A3 caption | 0.743 | 0.716 | 0.691 | **0.718** | [0.617, 0.821] |

Branch: **headline at full strength**, and not marginally — every interval lies
entirely above 0.35 (nearest lower bound 0.383) and all nine seed-arm values fall
in the same branch.

> **Ordering disclosure.** All 36 D3 cells were read under the ratio-based
> `registered_d3_condition_matrix_v1.md` *before* TrainShare was computed. This is
> a **declared post-hoc recomputation of already-read data**; it does not satisfy
> I9 and is not a sealed pre-registered reading. Reported because PAPER1 §8 names
> the estimand.

Read with G0.2, the pooled 0.53 is an average over a gradient (84% blind-
answerable, 42% not), not a constant.

### 12.6 Instrument determinism (unplanned)

The premise probe was accidentally launched twice. All five cells came out
**byte-identical** across the two independent runs — an unplanned confirmation
that the locked greedy decoding contract is reproducible end to end (I7).
