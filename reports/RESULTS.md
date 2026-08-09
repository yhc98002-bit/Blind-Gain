# Blind Gains — consolidated experimental results

*Learning Without Looking: Image-Dependent Gains from Image-Free RLVR*

Single results file for the programme. Organised by the paper's own argument
(F1–F8) and the claim ladder (R1–R5), not chronologically. Every registered
endpoint appears, including those that went against the hypothesis. Numbers are
copied from committed artifacts; each block names its artifact.

Updated 2026-07-28. Model: Qwen2.5-VL-3B-Instruct unless stated.

---

## 0. Status

| item | rung / figure | status |
|---|---|---|
| C1 three seeds × four arms, geo3k | R1, F1/F2 | **complete** |
| D2 test-time access, three seeds | F1 | **complete** |
| D3 train × test grid, 36 cells | **F1 central figure** | **complete**, registered branch (a) |
| D4 caption test column (4×3 → 4×4) | F1 | **complete** — branch (a), evidence-general |
| M5 long horizon → step 400 | **R2** | **complete — verdict FALLING** |
| M5b two-axis trajectory | R2 / title upgrade | **complete** — dissociation holds; **upgrade condition not met** (§12b) |
| CHANCE null-corrected retention | **F0 contract** | **complete** — §13/§13b rewritten |
| E1c blind columns, 5 remaining benchmarks | **F0 audit** | **complete** — audit now spans **7 benchmarks**; MMVP exactly 0.000, MMMU/MathVerse MC 0.53–0.64 (§13b-bis) |
| M5c item-level turnover + noise floor | R2 / mechanism | **complete** — 137/601 flips against a **measured zero** noise floor; churn structured but orthogonal to visual necessity (§12c) |
| SEED3γ third-seed corrosion | **F6 Tier 1** | **complete — replicates**; 3-way Jaccard 0.661 vs null 0.012 (§6a) |
| E1b trained-arm external columns | F1 beyond geo3k | **complete, 48/48** — **P1, S1, S2 all miss**; no lenient comparison moves (§13c, §13d) |
| M7 ViRL39K stratified | R3 | **complete (seed 1)** — matched recovery **0.72–0.88 vs 0.08–0.12 on geo3k** (registered secondary passes, +0.63–0.64, stable); ρ_gain direction **fails** all arms (gains track headroom); ρ_recovery point-positive for blind arms (§12d). Seed 2 relaunches after C5 |
| C5 7B access pair (A1 vs A2-gray) | R4 | **complete** — crossed TrainShare **0.78–0.84 vs 0.49 at 3B**, intervals disjoint; matched gain replicates (+0.2479 vs +0.2435). **Ladder R1–R5 closed** (§12e) |
| M11 cross-family | R5 | **complete** (recovered 2026-07-28) |
| Mini-A5 CP vs matched GRPO | F8 | **complete** — gate PASS, endpoints read under the pre-filed addendum. **Branch 2 fires**: primary anchor flat on content; the +0.07 strict gap is formatting (residual 1e−17). CP moves the oracle-localized readout on both R19 and R20 — the same layer ordinary RLVR moves (§8) |
| Gate 1 four-arm completion (std · member · necessity · cp) | Paper 2 | **complete 2026-08-09** — acceptance audit 9/9 PASS before unsealing. **No arm moves held-out content on the primary anchor** (lenient NOT MOVED, all contrasts, all roles); every registered difference is strict/format. **All four recipes move the oracle-localized readout +0.15–0.23** — F3's layer selectivity is recipe-independent. Data axis costs format (member −0.32 strict on the canary); necessity partially repairs it (+0.043 [0.018, 0.070]). See the 2026-08-09 Gate-1 section |
| X1–X5, B1, Gate 0, Phase 0 | F4–F7, Paper 2 | **complete** |
| Cue ladder | Paper 2 P1.1 | **closed — both validity gates failed** |

---

## 1. F1 — The access matrix: two regimes

Gain over base, mean of three seeds. Base: real 0.1747, gray 0.0899, none 0.0682.
Artifacts: `reports/d3_condition_matrix_v1.json`, `reports/gate0_stratification_v1.json`.

| trained ↓ / tested → | real | gray | none |
|---|---|---|---|
| A1 real | **+0.2435** | +0.019 | +0.036 |
| A3 caption | **+0.1747** | +0.024 | +0.037 |
| A2b no-image | **+0.1287** | +0.017 | +0.046 |
| A2 gray | **+0.1187** | +0.016 | +0.033 |

**Two regimes.** Tested blind, every arm lands between +0.016 and +0.046 with no
ordering: A1, trained on real images for 100 steps, gains +0.036; A2-gray, which
saw only uniform gray rectangles, gains +0.033. Tested with images, the arms
separate and order themselves by training-time information.

**The protocol effect.** The same gray checkpoint reports **6.6% recovery under
matched evaluation and ~48.6% under crossed evaluation** — a seven-fold
difference produced by the evaluation protocol. (6.6% and 48.6% are both
mean-of-ratios across seeds; the ratio-of-pooled-means is 48.7%. The two
estimators are mixed in some earlier text.) **Read this together with the failed
strict control above**: the magnitude of the gap is not in question, but the
registration's format/emission clause means it does not by itself license
rescoping the canonical claim.
**Registered branch (a): partially verified, and the format control did NOT
confirm.** Two things must be said plainly here.

*The strict control failed its own bar.* `d3_condition_matrix_v1.json` records
`"strict_control_confirms": false`. Recomputed on Acc_strict the ratios are
1.95–2.69, and **two of six seed-arm cells fall below the registered 2× bar**
(A2b seed 2 = 1.945, seed 3 = 1.958). The D3 registration pre-commits that "if
the Acc_strict recomputation does not reproduce the Acc_final pattern, the
finding is reported as format/emission and the canonical claim is not rescoped."
On a strict reading of that clause the protocol-effect framing below is **not**
licensed to rescope the canonical claim, and the crossed/matched gap should carry
a format/emission caveat. This disclosure was present in the predecessor results
file and was lost in consolidation; it is restored here.

*Only half of branch (a) is verifiable.* The branch requires ratio > 2 **and**
non-overlapping crossed-vs-matched recovery CIs. The ratio half holds in all
three seeds for both blind arms. The CI half cannot be checked: the artifact
contains point values only, and the registered audit artifact carrying the
per-cell bootstrap CIs does not exist in `reports/`.

**TrainShare** (PAPER1 §8 estimand, paired item-level bootstrap CIs) —
`reports/d3_trainshare_v1.json`:

| arm | s1 | s2 | s3 | pooled | 95% CI |
|---|---|---|---|---|---|
| A2 gray | 0.507 | 0.527 | 0.424 | **0.487** | [0.383, 0.588] |
| A2b no-image | 0.572 | 0.493 | 0.518 | **0.528** | [0.424, 0.629] |
| A3 caption | 0.743 | 0.716 | 0.691 | **0.718** | [0.617, 0.821] |

Branch: **headline at full strength on the pooled statistic** — every *pooled*
interval lies entirely above the 0.35 threshold, nearest lower bound 0.383, and
all nine seed-arm point values fall in the same branch. Per-seed intervals are
much wider and do **not** all clear it: A2 gray seed 3 is [0.272, 0.575]. *Ordering disclosure: the 36 cells were read under the
ratio-based D3 registration before TrainShare was computed, so TrainShare is a
declared post-hoc recomputation and does not satisfy I9.*

**Matched-condition gains, for contrast:** A1 +0.2435, A3 +0.1048, A2b +0.0460,
A2 gray +0.0161. *Convention warning:* these difference each arm against the base
**in its own condition**. §10 uses the other convention — everything against base
*real* — under which the same A2b figure is −0.0605. Both are correct; they
answer different questions and must never be mixed in one table.

---

## 2. F2 — The information ladder

Measured with images at test, over base: gray **+0.119 (49%)** → no-image
**+0.129 (53%)** → caption **+0.175 (72%)** → real **+0.2435 (100%)**.

So 49% of the gain requires no visual information during training at all; 28%
requires actual pixels during optimisation. The middle band is 23% measured from
the gray rung, or 19 points measured from the adjacent no-image rung (71.8 −
52.9) — the latter is the like-for-like comparison against the nearest image-free
condition.

**Each rung is an average over a gradient, not a constant.** G0.2 (§10) finds the
blind arms' image-present gain concentrates on blind-*answerable* items. For
**A2b** (the 53% rung): 84% of A1's gain where blind reward opportunity exists,
42% where none was observed — item-weighted average 52.9%, which is that rung.
For **A2 gray** (the 49% rung) the corresponding split is 83% and 36%, averaging
48.8%. The image-free share falls as an item's dependence on the image rises, in
both arms.

The caption inversion replicates 3/3: A3 starts above A1 at step 0 (0.2097 vs
0.1747) and ends below it at step 100.

---

## 2b. D4 — the caption test column (completes the matrix to 4×4)

`reports/d4_caption_column_v1.*`. Registered primary, filed before any cell ran:
is the readout policy pixel-specific or evidence-general? Base caption row pinned
at 0.2097; 12 cells, n=601.

| arm | caption accuracy | gain over base | 95% CI |
|---|---|---|---|
| A1 real | 0.3145 | **+0.1048** | [+0.0727, +0.1370] |
| A3 caption | 0.3145 | **+0.1048** | [+0.0732, +0.1375] |
| A2b no-image | 0.2751 | +0.0654 | [+0.0361, +0.0965] |
| A2 gray | 0.2629 | +0.0532 | [+0.0233, +0.0837] |

**Branch (a) fires — evidence-general.** Spearman ρ(caption, real) = **+0.800**
(threshold ≥ +0.70) and the caption column's spread is **4.0×** the larger blind
spread (0.0516 vs 0.0130; threshold ≥ 2×). Given frozen textual descriptions
instead of pixels the arms re-order as they do with images and spread apart four
times more than under a blind condition, so **the readout policy is not
pixel-specific**. F1's two-regime split is about information presence, not
modality — which is what licenses generalising the ceiling argument beyond pixels.

The A1/A3 tie at +0.1048 is a coincidence of the three-seed mean (distinct
checkpoints, per-seed accuracies differ, ~40% answer agreement); ρ = +0.800
rather than +1.000 is entirely that swap.

**Secondary — A3 does not clear the protocol-effect bar.** A3 matched (caption)
+0.1048 vs crossed (real) +0.1747 is a ratio of **1.67**, below the registered
2× threshold. So the matched-versus-crossed protocol effect is stated for **two
arms, not three**; A3 is an exception, reported as such under branch (c).

---

## 3. F3 — The exchange rate, and where it lands

+24.4 task points buy **+2.5 points** of overall certified counterfactual pair
accuracy (CIs excluding zero, 3/3 seeds); on the registered geometry primary,
**+0.006**. The instrument moves — it is not a dead ruler — which is what makes
the asymmetry a measurement rather than a failure to detect.

**Template decomposition** (F3d) — `reports/f2d_template_decomposition_v1.json`.
Base rates by task, and A1's movement:

| task | role | base pair | base strict | A1 Δ | share of overall |
|---|---|---|---|---|---|
| coordinate survey register (600) | primary visual anchor | 0.4717 | 0.4433 | +0.0056 [−0.0183, +0.0294] | 11% |
| header-cued verification table (300) | high-baseline control / retention canary | **0.8667** | 0.1800 | +0.0189 [−0.0022, +0.0422] | 18.7% |
| nine-series calibration trace (300) | oracle-localized readout control | 0.4367 | 0.4200 | **+0.0711 [+0.0256, +0.1167]** | **70.3%** |

**The gain lands exactly where the visual work has been done for the model** —
the oracle-localized control supplies 70% of the movement while the primary
anchor, the only R19 task requiring search and binding, stays flat with an
interval spanning zero.

> **Correction required in PAPER1 §3 and §5.** Both describe the header-cued
> table as "saturated at 1.000 for every model" and as contributing "nothing to
> any delta". Measured, its base is **0.8667** (strict 0.1800) and it moves in
> every arm (+0.019 to +0.023; A2 gray's CI excludes zero), contributing 18.7% of
> A1's overall movement. **The mechanism survives — only the premise is wrong.**
> It is also the R19 task most dependent on fallback extraction (0.8667 lenient
> vs 0.1800 strict).

**The blind arms separate the layers more sharply than A1 does:**

| arm | primary visual anchor | oracle-localized control |
|---|---|---|
| A2 gray | **−0.0422** [−0.0683, −0.0161] | **+0.0556** [+0.0100, +0.1011] |
| A2b no-image | **−0.0272** [−0.0522, −0.0017] | +0.0233 [−0.0200, +0.0678] |

Both blind arms *decline* on search-and-binding while *rising* on the cued
readout. Their flat overall R19 numbers (−0.0014, −0.0019) are two real effects
of opposite sign cancelling inside an aggregate that should never be read as one
capability score (I13).

---

## 4. F4 — Content-bound sharpening (mechanism)

`reports/x1_image_condition_matrix_v1.*`, `reports/x5_seed2_image_condition_matrix_v1.*`.

Margin inflation vs base under the **correct** image (seed 1, primary template):
A1 +0.150, caption +0.090, gray +0.036, no-image +0.035. The two blind arms are a
**tie, not an ordering** — their CIs overlap ([+0.0337, +0.0375] vs [+0.0327,
+0.0369]) and gray is nominally above no-image, the reverse of F2. The honest
statement is `gray ≈ no-image < caption < real`, which is F2's ordering only at
the coarse level. Seed 2 differs materially (A1 +0.129, caption +0.076, no-image
+0.058, gray +0.037), so these values are seed- and template-specific. Under a
same-template **mismatched** image: statistically zero for every arm, both seeds.
Under the **twin's** image every model including the frozen base prefers the
twin's gold — 0.948–0.955 on the primary template (0.920–0.938 on the nine-series
template, 1.000 on the header template; the direction holds in all 30 cells).
Blind-condition normalized entropy stays at 0.998
(`reports/blindarm_margin_calibration_results_v1.json`, not the X1/X5
artifacts), so this is not a global temperature change.

Presence-gating, global temperature change, and pure formatting are each excluded
by direct measurement.

---

## 5. F5 — What the residual does not buy

Structured hard-negative discrimination: base 0.517, A1 0.513–0.527. Binding
swap flat. Fact-read unimproved. Chained premise-to-reasoning sits at 0.000 pair
for every model — but per P0.1's registered branch (b) that floor is
**uninformative about chaining** rather than evidence against it (§11), so it
cannot be counted as a competence layer that failed to move.

**One intervention type does move, and it is reported here rather than omitted.**
`prior_conflict` rises in every trained cell: +0.214 and +0.143 (A1 seeds 1–2),
+0.286 (A2b), +0.286 (A3) on pair accuracy, with member-level gains of +0.107 to
+0.143. It is the only one of B1's six types to move in all cells, and it moves
*most* in the blind arms. n=14 pairs, so it is a small cell and no claim rests on
it — but a section arguing that competence layers stay flat must disclose the one
that did not.

With that qualification, the 28% requiring training-time pixels still looks like
readout policy tuned against real evidence rather than new visual distinctions.

**Candidate-set correction (X2, registered bottom branch fired).** The golds-only
figure of 0.9067 is predominantly *candidate-set structure*, not latent
competence; the realization gap ships as a measurement-methods finding, and
"already perceived" stays hypothesis language (§9).

---

## 6. F6 — Blind reward corrodes grounding, item-identifiably

`reports/x3_a2_degradation_forensics_v1.*`. A2 gray's exact −0.045, both seeds,
resolves to **42 shared pairs** (Jaccard 0.724 vs permutation null 0.098,
p = 1e-4), with the same extracted wrong answer in 41 of those 42. The
nearest-gridline transition accounts for **19 wrong member slots in seed 1 and 20
in seed 2** — i.e. roughly 37% of wrong slots in each seed (19/52 and 20/53), not
a 95% rate. An earlier phrasing of "19/20" invited exactly that misreading and is
corrected here.

### 6a. Seed 3 replicates it (SEED3γ) — Tier 1 now reads "across seeds"

`reports/x3_seed3_corrosion_replication_v1.*`. The seed-1/2 method was applied
**unchanged** (helpers imported, not transcribed) to the seed-3 A2-gray arm from
cached predictions; as a control the frozen v1 fields were recomputed and matched
**19/19**. Permutation nulls were redrawn for seed 3 (10,000 permutations, seed
20260728), not reused.

| | seed 1 | seed 2 | **seed 3** |
|---|---|---|---|
| A2-gray pair acc (base 0.4717) | 0.4267 | 0.4267 | **0.4350** |
| Δ vs base | −0.0450 [−0.0733, −0.0167] | −0.0450 [−0.0717, −0.0183] | **−0.0367 [−0.0633, −0.0100]** |
| correct→wrong | 51 | 49 | **45** |
| nearest-gridline wrong slots | 19 / 52 | 20 / 53 | **17 / 46** |

**It is the same items, and the same wrong answers.**

| overlap | Jaccard | null mean | p |
|---|---|---|---|
| seed3 vs seed1 | **0.811** | 0.093 | 1e−4 |
| seed3 vs seed2 | **0.741** | 0.091 | 1e−4 |
| seed1 vs seed2 | 0.724 | 0.097 | 1e−4 |
| **all three (3-way)** | **0.661** | **0.012** | **1e−4** |

Seed 3 recovers **39 of the 42** pairs that seeds 1 and 2 both degraded — 0.929
[0.810, 0.975]. On shared wrong member slots the *extracted answer is identical*
in 44/44 (vs seed 1), 40/41 (vs seed 2) and **39/40 three-way (0.975)**. A 3-way
Jaccard of 0.661 against a null of 0.012 is not a shared difficulty gradient; it
is the same failure reproduced.

**Tier 1 wording is therefore upgraded from "across two analyzed seeds" to
"across seeds" (three).** The Tier 2 attribution clause and the Tier 3 requirement
(a second long-horizon seed) are unchanged — SEED3γ speaks to the pilot A2-gray
arm, not to the long-horizon anchor.

### 6b. The same corrosion along the time axis (R2)

See §12. Extending training from 100 to 400 steps drives the same endpoint down
by −0.0667, in the arm trained on **real** images. Corrosion is not exclusive to
information-starved arms.

---

## 7. F7 — Confidence tracks image presence, not correctness

`reports/x4_visual_evidence_calibration_v1.*` (EXPLORATORY). Underconfident when
right (≈0.19 confidence vs 0.75 accuracy, ECE 0.57); identical confidence under
twin images where accuracy is 0.012 (+0.17–0.19 overconfidence gap).

---

## 8. F8 — Trainability (Mini-A5): the ceiling holds against a counterfactual-group objective

CP-GRPO vs matched same-data standard GRPO, 120 steps each, on held-out
FlipTrack templates. **Both arms are now complete**: CP arm `global_step_120`;
matched member arm reached `global_step_120` on an29 on 2026-07-29
(`checkpoint_tracker.json` → `last_global_step: 120`, trainer exited).

**The acceptance gate returned PASS on 2026-07-29** —
`scripts/audit_mini_a5_acceptance.py`, report
`reports/mini_a5_acceptance_audit_v1.json`:

| condition | verdict |
|---|---|
| 1. both manifests exit 0 with exactly 120 optimizer steps | ok |
| 2. config / data / model / registration / placement / EasyR1 hashes match | ok |
| 3. advantage grouping (CP logged joint-branch events, member never entered it) | ok |
| 4. no fatal log signatures (NaN, traceback, OOM, fatal NCCL) | ok |
| 5. checkpoint inventory | ok |
| 6. independent versioned report precedes any readout | ok |

**VERDICT: PASS.** The audit reads no endpoint metric and prints no accuracy by
construction; endpoint evaluation was gated on this verdict and is now authorized
for the first time.

### 8a. The endpoints, read under the merged addendum

`reports/f8_mini_a5_endpoint_readout_v1.{json,md}`, binding spec
`docs/registered_mini_a5_endpoint_readout_v1.md` (filed before any value was read).
Member arm merged from raw FSDP shards and verified (825 tensors, 8,131,575,808
bytes). Six cells on an29, ~14 min. Paired item bootstrap, 10,000 draws, seed
20260729, unit `pair_id`, both arms on identical replicate indices. Δ = CP − member.

**The pattern is the same on all three instruments, and it separates content from
format cleanly.**

| instrument / task | role | n | lenient Δ | 95% CI | strict Δ | 95% CI |
|---|---|---:|---:|:---:|---:|:---:|
| **R19 coordinate register** | **primary visual anchor** | 600 | **−0.0100** | [−0.030, +0.010] | **+0.0700** | [+0.042, +0.098] |
| R19 nine-series | oracle-localized readout | 300 | **+0.0767** | [+0.030, +0.127] | +0.0967 | [+0.047, +0.147] |
| R19 header table | saturated canary | 300 | +0.0000 | [−0.017, +0.017] | **−0.0400** | [−0.070, −0.013] |
| **R20 coordinate register** | primary anchor, private twin | 600 | +0.0067 | [−0.013, +0.027] | +0.0950 | [+0.067, +0.123] |
| R20 nine-series | oracle-localized readout | 300 | **+0.0600** | [+0.013, +0.103] | +0.1100 | [+0.063, +0.160] |
| R20 header table | saturated canary | 300 | −0.0067 | [−0.023, +0.010] | **−0.0733** | [−0.107, −0.040] |

**Registered branch: branch 2 fires.** On the primary anchor the lenient CI contains
zero (p = 0.405), so by the decision rule pinned before any value was read this is
**NOT MOVED**. Per `PAPER2 §6` the Paper-2 gate is reconsidered: premise-first
redesign (C3 before C2), C1 retained.

### 8b. The strict "win" is response formatting, decomposed to zero residual

The two registered contracts disagree, and the addendum pre-committed to treating the
disagreement as the result. It resolves exactly:

- `strict_delta = lenient_delta − (CP contract loss − member contract loss)`
  = −0.0100 − (0.0183 − 0.0983) = **+0.0700**, residual **1e−17**.
- `contract_valid_rate`: CP **0.9683** vs member **0.8133**. `acc_strict` is
  `contract_valid AND acc_final`, so strict is a subset of lenient by construction.
- Against the frozen base the strict gap is **(CP − base) − (member − base) =
  +0.0100 − (−0.0600)**, i.e. **85.7% of it is the member arm falling below base**,
  not CP rising.

**The entire +0.07 primary-endpoint "effect" is response-format contract validity.**
Reported as +0.0700 with p = 1.4e−06 it would read as a clean trainability win; it is
a formatting difference, and most of it is the comparison arm degrading.

### 8c. What did move: the same layer ordinary RLVR moves, replicated on the private twin

On answer content, CP moves the **oracle-localized readout control** — **+0.0767 on
R19 (p = 0.0027) and +0.0600 on R20 (p = 0.0133)** — and leaves the **search-and-binding
anchor flat** on both. R20 is the one-shot private twin from fresh generator seeds, so
this is a replicated content gain, not a single-set artifact.

**This is F3's mechanism reproduced by a method built to breach it.** F3 established
that RLVR's gain "lands exactly where the visual work has been done for the model" —
concentrated on the template where localization is supplied by the cue, flat on the
anchor requiring search, binding and read. CP-GRPO, whose reward is structurally
unsatisfiable by a text prior, **selects the same layer**: it improves readout given a
located target and does not install localization.

That makes F8 direct evidence for the representational-ceiling argument of §3 rather
than only a gate outcome: **the ceiling holds against a purpose-built counterfactual
intervention-group objective.**

*Retention canary.* The saturated control is flat on lenient and **drops on strict**
(−0.0400 R19, −0.0733 R20, both CIs excluding zero) — recorded as a damage signal per
its registered role. Absolute levels keep both arms above base on that contract (base
strict 0.1800, member 0.2600, CP 0.2200), so this is a formatting regression relative
to member, not absolute loss of the control.

### 8d. The ranking layer settles it: three of four measurements of the anchor are flat

`reports/f8_secondaries_v1.md`. The registered ranking instrument was run for both arms
at step 120 (1,200/1,200 rows each). Ranking removes the generation and formatting burden
entirely, so it is the clean test of whether the strict generation gain was competence.

**Primary anchor — coordinate survey register (n=600), CP − member:**

| layer / severity | Δ | 95% CI | p | excludes 0 |
|---|---:|:---:|---:|:---:|
| ranking, lenient | −0.0050 | [−0.015, +0.005] | 0.508 | no |
| ranking, strict | −0.0033 | [−0.023, +0.017] | 0.871 | no |
| generation, lenient | −0.0100 | [−0.030, +0.010] | 0.405 | no |
| generation, **strict** | **+0.0700** | [+0.043, +0.098] | 1.4e−06 | **yes** |

**Three independent measurements of the primary anchor are flat; only the one confounded
with response formatting moves.** On the ranking layer CP and member are
indistinguishable — 0.9450 vs 0.9500 lenient, both near ceiling. That layer shows a
**latent preference for the correct answer** which neither arm's free generation
realises, and CP does not close that gap on the anchor.

The oracle-localized readout control moves on **three of its four** measurements
(ranking strict +0.0467, p = 0.034; generation lenient +0.0767, p = 0.0027; generation
strict +0.0967, p = 3.4e−04), so §8c's layer-selectivity result is not a generation
artifact — it appears on the ranking layer too.

*Realization gap reproduced.* Ranking minus generation, within arm: **all twelve
contrasts exclude zero, positive** — X2's measurement-methods finding replicated inside F8.

### 8e. The invariance axis has no working instrument — a Paper-2 blocker

Catch-trial stability is reported **instrument-absent**, and the reason is sharper than
"no scorer exists". `scripts/audit_mini_a5_catch.py` loads no model (verified through all
four transitive imports: PIL diffing, hashing, set overlap only). More importantly, **no
existing metric field expresses the invariance criterion**: `pair_score`'s `collapsed`
flag is gated on `answer_a != answer_b`, so it is identically `False` on all 300
equal-gold catch pairs. Demonstrated by running the metric — a pair whose members
**agree but are both wrong** (invariance satisfied, answer wrong) scores
`pair_correct=False, collapsed=False`, **indistinguishable from a genuine invariance
failure**.

This matters beyond F8. `PAPER2` §2 C2 states invariance is "required, not optional" — it
is the control that forbids the change-detector heuristic (I5), and I13 requires it be
reported separately from causal sensitivity. **The P0.2 equal-gold fix repaired
`_score_member`, but `collapsed` remains uninformative on equal-gold pairs**, so the
specificity axis Paper 2 depends on cannot currently be measured. The scorer is fully
specified in the report and deliberately not built here.

"The registered task benchmark" is reported **unresolvable**: one binding occurrence, zero
referents, both training configs at `val_freq: 0` with `val_files` pointing at a 48-row
plumbing fixture never read. Geometry3K is named as the nearest convention referent and
explicitly not adopted — the convention arms train *on* Geometry3K while Mini-A5 trains on
`data/mini_a5_train_v1`, so adopting it would silently convert the endpoint into an
out-of-domain transfer measurement.

### 8f. The invariance instrument, built and read — and it completes the pattern

`reports/mini_a5_catch_stability_readout_v1.{json,md}`, instrument registered in
`docs/registered_mini_a5_catch_stability_v1.md` before its evaluation ran (27/27
adversarial fixtures, headed by the decisive agree-but-both-wrong case; per-template
output only — pooling structurally impossible in the schema). Both step-120 arms, 300
equal-gold catch pairs, same F8 shard path, ~3.5 min per arm.

**On answer content, invariance is at ceiling for both arms** (per template, n=100;
counts lenient / strict):

| template | CP stable | member stable | CP correct | member correct |
|---|---|---|---|---|
| matrix | 100 / 95 | 100 / 89 | 100 / 95 | 100 / 89 |
| scatter | 100 / 100 | 100 / 100 | 100 / 100 | 100 / 100 |
| trajectory | 98 / 64 | 96 / 28 | 96 / 64 | 95 / 28 |

All lenient CP−member contrasts are null (largest +0.02 [0.00, +0.05], p = 0.5), and
joint stable-and-correct equals correctness in every cell of both arms. **Neither arm
shows change-detector pathology**: under a non-queried visual change, both hold their
answer essentially always. The specificity axis Paper 2 requires (I5, I13) now has a
working instrument, and at Gate-1 scale it reads clean.

**The strict contrasts repeat the session's most replicated finding.** CP − member on
strict stability: trajectory **+0.36 [+0.27, +0.46], p = 2.9e−11** (discordant 0/36),
matrix +0.06 [+0.02, +0.11], p = 0.031, scatter at ceiling. With lenient at ceiling,
a strict-only gap is once again **answer-contract compliance, not content** — the same
formatting layer that produced F8's +0.07 strict "win" (§8b), E1b's only transfer
(§13c), and the F8 canary's strict drop. Four independent measurements now localise the
CP-vs-member difference to format compliance; none place it in visual competence.

*Recorded as the registration requires: this fills the instrument-absent F8 secondary
and cannot alter the published F8 primary or branch decision.*

*Scope.* Mini-A5 is Gate 1 — 120 steps, one run per arm; intervals are evaluation
uncertainty, not run-to-run RL variance. chart-v08 cells are n = 50 per template.
Attribution (VAG, `PAPER2` §3B) requires a matched blind control that is not among the
six F8 cells, so the lenient/strict contrast is **not** used as a proxy for it.

---

## 9. The claim ladder

| rung | content | status |
|---|---|---|
| **R1** | three seeds on geo3k | **in hand** |
| **R2** | long horizon to step 400 | **complete — FALLING**, see §12 |
| **R3** | second corpus, ViRL39K stratified | ready to launch |
| **R4** | scale, 7B access pair (A1 vs A2-gray) | not built |
| **R5** | cross-family | **complete**, see §13 |

---

## 10. Gate 0 — stratification (Paper 2 prerequisites, freezes the title claim)

`reports/gate0_stratification_v1.json`. Base per-item reproduces registered
step-0 exactly (acc_final 0.1747, strict 0.0599, contract 0.4393), and A1's
image-present gain reproduces the published +0.2435 — an end-to-end check on the
join. All four analyses use the D3 **crossed** cells; using each arm's matched
cell would have reported A2b's gain as −0.0605 instead of +0.1287.

**G0.1 — do gains concentrate on high-Δq items? Yes, for both arms.**

| arm | low Δq | mid Δq | high Δq | Spearman ρ | perm p |
|---|---|---|---|---|---|
| A1 real | +0.149 | +0.278 | +0.422 | +0.198 | 0.0005 |
| A2b no-image | +0.061 | +0.121 | +0.283 | +0.192 | 0.0005 |

H1 supported; C1 necessity sampling earns its place in Paper 2's method.

**G0.2 — the reversal.** A2b's image-present gain concentrates on
blind-**answerable** items, the opposite of the hypothesis, and it survives a
headroom control:

| arm | all: blind-answerable | all: not | base-wrong: answerable | base-wrong: not |
|---|---|---|---|---|
| A1 real | +0.3276 | +0.2231 | +0.4667 | +0.3218 |
| A2b no-image | +0.2764 | +0.0930 | +0.4259 | +0.1970 |
| A2 gray | +0.2735 | +0.0813 | +0.4296 | +0.1839 |
| A3 caption | +0.2393 | +0.1591 | +0.3704 | +0.2635 |

A2b recovers **84%** of A1's gain where blind reward opportunity exists and
**42%** where none was observed (91% vs 61% restricted to base-wrong items, where
headroom is identical). Both blind arms show the steep version; A1 and A3 do not.
The title claim survives with a scope qualifier: the image-free gain is real on
image-requiring items — **+0.197 restricted to base-wrong items** (n=406, where
headroom is identical), or **+0.093 across all** items in that stratum (n=484) —
but is disproportionately the blind-attainable component. Direct measured support for **H1**.

**G0.3 — policy overlap.** A1/A2b newly-correct sets: Jaccard 0.363–0.423 against
a permutation null of 0.157–0.177, p = 1e-4 in all three seeds (the weaker bound p ≤ 0.004 appears in some earlier text and understates it 40-fold). Substantially
overlapping policies, but ~60% of the union belongs to only one arm.

**G0.4 — the access matrix is format-free by identity.** Format gain is *exactly*
**+0.1148 for all four arms**: every trained arm satisfies
`acc_strict == acc_final`, so FormatGain collapses to
`base_final − base_strict` = 0.1747 − 0.0599. The formatting component cancels
exactly in any arm-minus-arm comparison.

### 10b. G0.2 refined — the title claim now carries intervals, and they separate

`reports/g02_necessity_refinement_v1.{json,md}`, addendum to the frozen Gate 0
artifact (not modified). Pipeline validated first: the published 84/42 (and
base-wrong 91/61) reproduce from the frozen artifact **exactly** (max deviation
2.8e−17). Binary blind-answerable split only, never merged with the Δq terciles
(I13) — so the difficulty confound M5c found in the terciles does not transfer to
G0.2, which is not built on Δq.

**The 84%/42% ratios had never carried intervals anywhere in the repo. Now they
do, and they don't overlap** (10,000 paired item-bootstrap draws, seed 20260730):

| scoring | blind-answerable (n=117) | no observed blind success (n=484) | difference |
|---|---|---|---|
| lenient | **0.844 [0.68, 1.01]** | **0.417 [0.28, 0.54]** | +0.427 [0.22, 0.63] |
| strict | **0.897 [0.79, 1.01]** | **0.599 [0.52, 0.68]** | +0.298 [0.17, 0.43] |

Bootstrap mass at or below zero difference: <0.0001 under both scorings. On
blind-answerable items, A2b's recovery of A1's gain is statistically
indistinguishable from 100% (upper bounds 1.01).

**The n=484 stratum decomposes, and the decomposition sharpens the claim.** The
published label "items requiring pixels" describes only part of it: **252 of the
484 have zero observed successes *with* the image too** (c_real = 0/16) — items the
base solves under no condition, where no arm's gain can be attributed to anything.

| subgroup | n | recovery, lenient | recovery, strict |
|---|---:|---|---|
| **B1 — image demonstrably buys opportunity** | 232 | **0.525 [0.38, 0.66]** | **0.676 [0.59, 0.76]** |
| B2 — never solved under any condition | 252 | 0.116 [−0.26, 0.36] | 0.377 [0.24, 0.54] |

So on the items where the image *demonstrably* buys reward opportunity, image-free
training recovers **half (lenient) to two-thirds (strict)** of A1's gain — a
better-founded figure than the published 42%, which averaged B1 with a subgroup
whose lenient recovery interval spans zero. (B2's strict recovery does exclude
zero; the "unmeasurable" reading is lenient-only and is stated as such.)

A difficulty-standardised sensitivity (both strata reweighted to the pooled q_real
bin distribution, full common support, retained weight 1.0000) preserves the
contrast; its blind-answerable figure rests on small cells (26 items carry 46% of
the weight) and is reported as sensitivity, not replacement.

**Proposed relabel** (PI-owned prose; proposal only): "items requiring pixels" →
**"items with no observed blind success"**, with the pixel-requiring claim carried
by B1. The refined headline: *image-free training captures most of the
blind-attainable component, and half to two-thirds of what genuinely needs
pixels.*

---

## 11. Phase 0 — Paper 2 blocking prerequisites (complete)

**P0.1 premise probe, five separate numbers** — `reports/p01_premise_probe_v1.*`:

| cell | premise member | final member | reasoning \| correct premise |
|---|---|---|---|
| base | 0.275 | 0.150 | 0.273 (n=11) |
| A1 s1 | 0.225 | 0.100 | 0.222 (n=9) |
| A1 s2 | 0.175 | 0.075 | 0.000 (n=7) |
| A2b s1 | **0.300** | 0.125 | 0.250 (n=12) |
| A3 s1 | 0.250 | 0.075 | 0.200 (n=10) |

*Pair-level and transition columns are omitted deliberately.* The probe's own
registration states that because both golds are equal by design, the harness's
pair logic is degenerate and **"any pair-level figure from this run is void and
will not be reported."* An earlier version of this file tabled them anyway.

Base premise accuracy **0.275** (95% Wald [0.137, 0.413]) fires registered branch
**(b)**: the chained construct is revised before release, and its 0.000 pair
accuracy is *uninformative about chaining* rather than evidence against it.
Reasoning given a correct premise is only 0.273 at base — premise extraction is
the first bottleneck but not the only one, so an easier premise curriculum alone
will not make these items trainable. Note the Wald interval straddles the
0.30 (b)/(c) boundary, so the evidence does not cleanly separate "too hard" from
"intermediate"; the consequence is identical under either branch. Note also that
A2b seed 1 reaches 0.300, *above* base — the claim "no arm beats base on premise
extraction" appears in the P0.1 markdown and is contradicted by its own table. Premise-transition accuracy equals premise
pair accuracy in every cell because B1 holds the premise invariant across the
flip; **Track 4 needs items whose premise itself changes** or the metric can
never do independent work.

**P0.2 equal-gold invariance scorer — a real defect, fixed.** `acc_final` was
`gold_tier > other_tier`, computed from the same string whenever a pair's two
members share a gold, so it was **never true** on invariance items: a member
answering the gold exactly scored wrong. Surfaced as premise member accuracy
0.000 for all five models. Fixed with an equal-gold branch and a 7-case
adversarial fixture the pre-fix code fails. **Blast radius nil for Paper 1**:
R19 has zero equal-gold pairs and rescores to 0.4717/0.4433 unchanged; the frozen
R20 scorer is byte-identical (I11). B1's 30 invariance items were rescored —
**nothing moves** across all 30 equal-gold items (10 model×type cells), so the
published B1 table stands.

Artifacts: `reports/b1_rescored_p02_v1.json` (rescore), `reports/p04_task_roles_v1.md` (roles).

**P0.3** intervention-group schema frozen and versioned with a 13-case loader
fixture (I15). **P0.4** task roles canonicalised in `src/eval/task_roles.py` with
an I13 guard that raises on any cross-role aggregate and fails closed on unknown
tasks.

---

## 12. R2 — M5 terminal readout: FALLING

`reports/m5_terminal_readout_v1.*`. Rule: `MAIN_PHASE_RULING_20260716` R1.
Endpoint is R19 **geometry** pair accuracy at step 400 minus step 100, n=600,
item-paired bootstrap.

| | step 100 | step 400 | Δ | 95% CI |
|---|---|---|---|---|
| lenient pair acc | 0.4800 | 0.4133 | **−0.0667** | [−0.0933, −0.0400] |
| contract-strict | 0.4800 | 0.4133 | −0.0667 | [−0.0933, −0.0400] |

**Verdict FALLING** — the rule requires Δ ≤ −0.05 *and* a CI upper bound below
zero; both hold, so no discretion was involved. **Step 400 is terminal: no
extension or rerun under any outcome.**

Step 400 (0.4133) is below its own step-100 value (0.4800) **and below the frozen
base (0.4717)**. Four times the training leaves the model worse on the primary
visual anchor than no RL training at all.

Strict and lenient move identically, so the decline is answer content, not
formatting.

**Registered secondaries** (the ruling designates overall R19 a secondary *under
the same rule*, not merely descriptive): overall R19 falls 0.5633 → 0.5167 from
step 100 to step 400, Δ = −0.0467. Blind-floor persistence at step 400 **passes**:
gray pair accuracy 0.0 with collapse 1.0, noise 0.0 with collapse 1.0 — the model
has not learned to answer these blind.

Steps 150/200/300 are descriptive only and cannot select the endpoint; their
overall values are 0.5600 / 0.5433 / 0.5383, so the trajectory from step 100
onward is monotone.

---

## 12b. M5b — the two-axis trajectory (the "scissors")

`reports/m5b_trajectory_v1.{json,md}`. Assembly and **recomputation** of existing
artifacts — no new inference. Both axes rescored from stored responses through the
canonical scorers, 2,000-draw paired item bootstrap, McNemar exact p on the same
paired indicators. Benchmark axis: Geometry3K test, greedy, n = 601. Grounding
axis: R19 `geometry_coordinate_indexing`, real images, n = 600 pairs.

> **Metric-identity correction.** The planning-level benchmark series I circulated
> (`0.4309 / 0.4692 / 0.4892 / 0.4742 / 0.4443`) **mixed two metrics**: the
> step-100 entry is `canonical_correct`, steps 150–400 are `acc_final`. Every
> step-vs-step-100 delta computed from it is **inflated by +0.0050**. The
> single-metric series below supersedes it. The grounding series reproduced
> exactly (all five residuals 0.0000).

| step | geo3k `acc_final` | Δ vs step 100 [95% CI] | p | R19 geometry pair acc | Δ vs step 100 [95% CI] | p |
|---|---|---|---|---|---|---|
| frozen base | 0.1498 | −0.2862 [−0.3261, −0.2463] | 2e−38 | 0.4717 | −0.0083 [−0.0367, +0.0217] | 0.64 |
| 100 | 0.4359 | — | — | 0.4800 | — | — |
| 150 | 0.4692 | +0.0333 [−0.0033, +0.0699] | 0.085 | 0.4733 | −0.0067 [−0.0300, +0.0167] | 0.67 |
| 200 | **0.4892** peak | +0.0532 [+0.0166, +0.0899] | **0.0086** | 0.4633 | −0.0167 [−0.0400, +0.0067] | 0.20 |
| 300 | 0.4742 | +0.0383 [+0.0000, +0.0749] | 0.065 | 0.4467 | −0.0333 [−0.0600, −0.0067] | **0.019** |
| 400 | 0.4443 | **+0.0083 [−0.0283, +0.0449]** | **0.73** | 0.4133 | **−0.0667 [−0.0933, −0.0400]** | **2.4e−06** |

**The two axes have different shapes, and the difference matters.**

- **Benchmark: rises, peaks at step 200, then reverses.** Monotone non-decreasing
  over 100→400 is **false**. The only step significantly above step 100 is 200
  (+0.0532). By step 400 the benchmark has returned to its step-100 level:
  **+0.0083, CI containing zero, p = 0.73.**
- **Grounding: monotone non-increasing throughout**, argmax at step 100, and the
  decline is unambiguous by 400 (−0.0667, p = 2.4e−06). It first falls below the
  frozen base at step 200; the benchmark never falls below the frozen base at all.

Relative to the **frozen base** at step 400: benchmark **+0.2945** [+0.2512,
+0.3378] while grounding is **−0.0583** [−0.0900, −0.0267], p = 4.25e−04.
*Strict qualifies this*: strict grounding vs frozen base is −0.0300 [−0.0633,
+0.0033], p = 0.11 — **not significant**. Lenient and strict are identical at
every trained step; they differ only at the frozen base (0.4717 vs 0.4433), so the
lenient-vs-base gap partly reflects the base's formatting failures, not content.

**Title-upgrade verdict — the condition as I stated it is NOT met.** I previously
reported that both conditions held. On the corrected single-metric series:

| condition | verdict |
|---|---|
| geo3k step 400 > step 100 | **not supported** — +0.0083, CI [−0.0283, +0.0449], p = 0.73 |
| grounding step 400 < frozen base | **supported lenient** (−0.0583, p = 4.25e−04); **not supported strict** (−0.0300, p = 0.11) |

The honest description is **not** "benchmark keeps rising while grounding falls."
It is that **benchmark accuracy rises, saturates, and returns to its early-training
level, while grounding decays monotonically and significantly throughout** — a
dissociation, but a weaker and differently-shaped one than the mixed-metric series
implied. The upgrade decision is the PI's; my role here is that the arithmetic no
longer supports the version I circulated.

**Attribution clause (mandatory in every mention).** This is the **long-horizon
anchor configuration** — unfrozen tower, native r1v reward, unfiltered corpus —
**not pilot A1**, and it is **one trajectory, one seed**. Tier-3 promotion needs a
second long-horizon seed (LH2).

**Blind floors at step 400 hold exactly**: gray and noise both 0.0000 pair accuracy
with collapse rate 1.0000, paired Δ vs real −0.4133, p = 4.4e−75. The model did not
learn to answer the anchor blind.

*Provenance/deviation.* Training lineage is continuous from step 100 across four
resumed segments. All contract hashes, the greedy sub-contract (`n=1`, `T=0.0`,
`top_p=1.0`, `max_tokens=2048`, `seed=20260710`), item-id sets and ground truths are
identical across runs; recomputed metrics equal stored fields 601/601 and 600/600.
One deviation: the raw `decoding` field is **not** byte-identical — base/step-100
guarded-rescore rows carry a combined `{greedy, sampled}` record where M5 rows carry
greedy only. The greedy sub-contract itself is identical.

---

## 12c. M5c — what the flat benchmark hides: turnover is huge, but it is not visual

`reports/m5c_item_substrate_v1.jsonl`, `reports/m5c_turnover_v1.json`,
`reports/m5c_necessity_stratification_v1.*`, `reports/m5c_lost_item_forensics_v1.*`.
Cached predictions only, no GPU. All five geo3k steps re-scored through
`score_greedy_item_pilot`; stored ≡ recomputed 601/601 at every step; item-id,
`ground_truth`, problem-sha256 and `image_sha256` sets identical across all five runs.
**`acc_final ≡ acc_strict` on all 601 items at every trained step**, so lenient and
strict tables are numerically identical (both computed and stored, not collapsed).

### The flat aggregate does hide large turnover

| | count | fraction |
|---|---:|---:|
| stable correct (1→1) | 196 | 0.326 |
| **gained (0→1)** | **71** | 0.118 |
| **lost (1→0)** | **66** | 0.110 |
| stable incorrect (0→0) | 268 | 0.446 |

Net is **+5 items (+0.0083)** while **137 items (22.8%) change state — turnover is 27.4×
the net**. Only 59.9% of items hold one state across all five steps. The peak-and-reverse
is real at item level and significant in both directions: 100→200 gains 86 / loses 54
(p=0.0086); 200→400 gains 44 / loses 71 (p=0.015).

### But the turnover is **not** organised by visual necessity — the hypothesis fails

Using Gate 0's own Δq terciles unchanged (bin sizes and edges reproduce
`gate0_stratification_v1.json` to full precision):

| stratum | n | acc@100 | acc@400 | Δ | 95% CI | McNemar p |
|---|---:|---:|---:|---:|:---:|---:|
| blind-solvable (low Δq) | 329 | 0.2523 | 0.2462 | **−0.0061** | [−0.055, +0.043] | 0.902 |
| intermediate | 121 | 0.5372 | 0.6198 | **+0.0826** | [−0.008, +0.174] | 0.121 |
| image-necessary (high Δq) | 151 | 0.7550 | 0.7351 | **−0.0199** | [−0.099, +0.060] | 0.743 |

**The bins move together, not against each other.** The predicted pattern —
blind-solvable improves while image-necessary declines — does not appear: blind-solvable
*also* declines, and the only bin that rises is the intermediate one, about which the
hypothesis says nothing. Direct contrast (image-necessary − blind-solvable) =
**−0.0138, CI [−0.104, +0.077], permutation p = 0.837**. Spearman(per-item change, Δq)
= **+0.021, p = 0.605**. Gained and lost items differ in mean Δq by +0.030 (p = 0.543).

**This is a non-rejection, not proof of no effect** — per-bin n runs as low as 121 and the
contrast CI still admits bin differences of ±0.10.

*The bins are not the problem.* At step 100 the real-minus-blind gap is strongly ordered
across them — **+0.137 / +0.413 / +0.669** — so Δq does capture image-dependence. The
change over training is simply unrelated to it. Two measured limits are recorded anyway:
**252 of the 329 low-Δq items have zero observed blind successes**, so that bin is
dominated by items the base solves under no condition rather than by blind-solvable ones;
and mean q_real rises 0.207 → 0.451 → 0.708 across bins, so Δq terciles confound necessity
with with-image difficulty. **That confound is a finding for Paper 2's C1**, which proposes
sampling on Δq.

### Which items are lost is reproducible; what they become is not

| probe | observed | null | p |
|---|---:|---:|---:|
| 3-way Jaccard of LOST(100→200, 100→300, 100→400) | **0.3118** | 0.0221 | **≤1e−4** |
| share of 100→400 lost already lost at both earlier hops | 0.4394 | — | — |
| step-400 wrong-answer entropy on lost items (norm.) | 0.9575 | 0.9578 | 0.449 |
| max multiplicity of any single wrong value | **2** | — | — |

**The same items keep being lost** — that is structured and highly significant. **But they
do not land on a shared wrong answer**: 55 distinct values over 63 contract-valid answers,
no value occurring more than twice, entropy indistinguishable from a matched permutation
null. Lost items repeat their step-400 value at step 300 only 22.9% of the time, versus
42.9% for stable-wrong items — they are *not* settling onto an attractor.

**This is the sharpest available contrast with F6 Tier 1.** On FlipTrack the gray arm
degrades to the *identical extracted wrong answer* in 39/40 three-way. On geo3k the
degradation is item-reproducible but answer-dispersed. The FlipTrack taxonomy
(`nearest_gridline` etc.) was **not** transplanted — it is defined over replayed coordinate
scene registers and is not computable on geo3k word problems.

One geo3k-native signal did clear the 15-test Holm family: lost items' step-400 answer is a
numeric near-miss (within 10% of gold) **20.4% of the time vs 8.7%** for stable-wrong
(p = 5.0e−4) — **not difficulty-controlled**, since lost items were correct at step 100 by
construction and the reference items were not.

### The turnover is policy, not measurement — the noise floor is exactly zero

`reports/m5c_noise_floor_replicate_v1.*`. The obvious rebuttal to a 22.8% turnover figure
is that evaluation noise produces it. Measured directly: the same checkpoint was
re-evaluated twice at step 400 and twice at step 100 under the identical decoding contract.

| comparison | discordant items | agreement |
|---|---:|---:|
| step 400, R1 vs R2 (both metrics) | **0 / 601** | 1.000000 |
| step 100, R1 vs R2 (both metrics) | **0 / 601** | 1.000000 |
| each replicate vs the cached substrate column | 0 / 601 | 1.000000 |

Stronger than the binary metric: **all 601 greedy response strings are byte-identical** in
all six compared pairs, and the whole `per_item.jsonl` files are **bit-identical** —
step-400 sha256 `60eac65a…`, exactly the provenance hash
`reports/m5c_turnover_v1.json` already recorded. Greedy decoding here is bitwise
reproducible across replicate, **node** (an12 vs an29), GPU index, date, and at step 100
across generation harness.

A determinism audit rules out a caching artifact: `resume_from` null, no `--resume-from`
flag, 0 resumed rows, 601/601 processed, two real vLLM safetensors shard loads per cell,
run-scoped node-local cache dirs, and the eval harness byte-identical between the cached
commit and the replicate commit.

**Measurement noise is 0 items, so all 137 flips are policy differences between
checkpoints.** The turnover/floor ratio is undefined rather than finite. The earlier
0.2133 "expected discordance" reference is **superseded, not confirmed** — it described
temperature-1.0 sampling dispersion, and the greedy harness has no dispersion at all.

### Evidence ledger: what survives multiplicity and what does not

`reports/m5c_evidence_ledger_v1.*`, 16 rows, Holm-corrected within a 10-test family.

| strand | statistic | verdict |
|---|---|---|
| noise floor | 0/601 discordant, bitwise identical | **SUPPORTS — decisive** |
| which items are lost, across checkpoints | 3-way Jaccard 0.3118 vs null 0.0221 | **SUPPORTS**, p ≤ 1e−4 |
| 5-step pattern structure | observed 429 flips **below the minimum of 10,000 nulls** holding each item's own correct-count fixed | **SUPPORTS** |
| what they degrade *to* | normalized entropy 0.9575 vs null 0.9578 | no attractor |
| problem-type concentration | LOST χ² 11.777, raw p 0.0461 → **Holm 0.1383** | **raw-p only, not corrected** |
| near-miss on lost items | best version **Holm 0.0592** | **raw-p only, not corrected** |
| margin / confidence collapse | no logprob field exists at any step | **not measurable** |

Three things stated plainly rather than smoothed:

1. **The bucket and near-miss strands do not survive correction.** Only the pattern-structure
   and Jaccard strands do. The lost/gained asymmetry in raw p is real but uncorrected.
2. **The near-miss p was partly a convention artifact.** The published 5.0e−4 reproduces
   exactly under its subset-draw null, but arm-label permutation on identical data gives
   0.0179. The requested stable-correct matching is **structurally degenerate** — those
   items are correct at step 400 by definition, so their near-miss rate is 1.0 by
   construction — and the substitute matched design rests on a single event in a 26-item
   reference arm.
3. **All five checkpoints are one trajectory sharing one step-100 anchor eval.** No
   permutation null here removes serial dependence between checkpoints, and there is no
   second training seed, so nothing separates *this run's* churn from *this recipe's* churn.

*A sampled expected-discordance null (Task B) did not complete and is recorded in the
ledger as an explicit gap. With the greedy floor measured at zero it is no longer
load-bearing: it was a proxy for the quantity now measured directly.*

### Verdict

The benchmark is not hiding a clean substitution of cheap strategies for visual ones. It is
hiding **large, item-reproducible, policy-driven churn — 137 flips against a measured zero
noise floor, with the movers sticky rather than random — that is orthogonal to measured
visual necessity.** The corrosion established on FlipTrack (§6, §6a, §12b) has no visible
geo3k counterpart at the level of *which kinds of item* move.

---

## 12d. R3 — the second corpus lands, and the access result generalises dramatically

`reports/m7_r3_readout_v1.{json,md}` (full registered readout, rc = 0, produced
autonomously by the waiter 2026-08-04T00:22Z). Four arms × 100 steps on the
decontaminated single-image ViRL39K corpus; every number carries the registered
**one-seed** tag; 4,239 paired held-out items; 5,000 within-stratum bootstrap
draws at seed 20260716; readout code fixture-validated before the data existed.

**Corpus aggregate — every arm gains, and the ladder orders as registered:**

| arm | q̄ (own condition) | step 0 | step 100 | gain [95% CI] |
|---|---:|---:|---:|---:|
| A1 real | 0.5122 | 0.2744 | 0.4805 | **+0.2062** [0.190, 0.222] |
| A3 caption | 0.4458 | 0.1849 | 0.3668 | **+0.1819** [0.167, 0.197] |
| A2b no-image | 0.4154 | 0.1538 | 0.3074 | **+0.1536** [0.140, 0.168] |
| A2 gray | 0.4235 | 0.1894 | 0.3373 | **+0.1479** [0.134, 0.162] |

**The headline: matched-evaluation recovery is corpus-dependent by a factor of
six to eight, exactly as the blind-opportunity audit predicted.** The registered
secondary — ViRL aggregate recovery greater than the fixed Geometry3K anchors —
passes with enormous margins, stable intervals, 0/5000 undefined draws:

| blind arm | geo3k anchor | ViRL recovery | difference [95% CI] |
|---|---:|---:|---:|
| A2 gray | 0.0789 | **0.7174** | **+0.6385** [0.563, 0.719] |
| A2b no-image | 0.1184 | **0.7449** | **+0.6265** [0.552, 0.706] |
| A3 caption | (no anchor) | 0.8822 | — |

On geo3k, blind arms recovered 8–12% of A1's gain under matched evaluation; on
ViRL39K they recover **72–88% under the same matched protocol**. This is the
corpus-level confirmation of §13's audit: ViRL39K's reward opportunity is largely
blind-attainable (free-form corrected retention 0.727 for Gemma-3), so a
blind-trained readout policy captures most of what image training captures. The
access matrix's "two regimes" are not a benchmark quirk — **which regime a corpus
sits in is measurable in advance from its blind-opportunity audit.**

**The registered stratum-rank prediction fails in direction, and the failure is
informative.** ρ_gain — gain vs stratum blind opportunity q̄ — is **negative for
all three blind arms** (A2 −0.259 [−0.446, −0.119]; A2b −0.265 [−0.437, −0.102];
A3 −0.734 [−0.809, −0.554]; all stable, direction > 0 **fails**). Gains
concentrate where the arm's own step-0 accuracy is *low* — headroom — not where
blind opportunity is high. ρ_recovery, which normalises by A1 within stratum, is
point-positive for both blind arms (A2 +0.210 [−0.139, +0.478]; A2b **+0.504**
[−0.036, +0.659]; 18/22 strata with stable denominators) and fails for A3
(−0.115). Reported exactly as registered: a failed direction on the primary rank
statistic, a passed direction on recovery for the blind arms with intervals
crossing zero. This is the third independent appearance of the same structure —
G0.2's headroom control and M5c's necessity-orthogonal churn found it on geo3k —
**raw gains track headroom; opportunity effects only emerge after normalising by
what the full-information arm achieves on the same items.**

*Scope, stated once: one seed; single-image restriction (93.2% / 94.2% retained);
per-stratum tables (22 eligible + 38 descriptive-small-n), source-only and
category-only views, and M10 candidates are in the report; the anchor comparison
is informed, not fully prospective (disclosure in the amendment); seed 2's first
attempt died in the 08-03 host-memory cascade and relaunches after the C5 pair.*

---

## 12e. R4 — the 7B access pair: the phenomenon grows with scale

`reports/c5_r4_readout_v1.{json,md}` (registered readout, produced autonomously by the
completion cascade 2026-08-07T00:25Z; all 18 registered checks true; 5,000 paired
bootstrap draws seed 20260730, 5000/5000 retained; both contracts computed and never
merged; every number one-seed-tagged). **This closes Paper 1's claim ladder: R1–R5 all
complete.**

**Cell accuracies, canonical contract** (n = 601 geo3k test items per cell):

| model | test real | test gray |
|---|---:|---:|
| 7B base | 0.2346 | 0.0799 |
| A1 real | **0.4825** | 0.1248 |
| A2 gray | **0.4276** | 0.1314 |

**Registered estimands:**

| estimand | canonical | strict |
|---|---:|---:|
| matched gain A1 | **+0.2479** [0.203, 0.291] | +0.3644 [0.325, 0.404] |
| matched gain A2-gray | +0.0516 [0.027, 0.078] | +0.1115 [0.083, 0.140] |
| crossed gain A2-gray | **+0.1930** [0.153, 0.235] | +0.3062 [0.265, 0.346] |
| **crossed TrainShare A2-gray** | **0.7785 [0.6418, 0.9214]** | **0.8402 [0.7457, 0.9456]** |

Denominator stable under the M7 rule on both contracts (paired SE 0.0218 / 0.0209).
Cross-scale descriptive anchor, labelled as such and not recomputed: the 3B pooled
crossed TrainShare was **0.487 [0.383, 0.588]**.

**The scale result, plainly.** A1's matched gain is nearly identical across scales
(+0.2435 at 3B, +0.2479 at 7B) — the recipe transfers. But the gray-trained arm now
recovers **78% (canonical) to 84% (strict)** of the full-image arm's gain under crossed
evaluation, versus 49% at 3B, and the two intervals do not overlap. Under matched
evaluation the 7B gray arm still shows only +0.05 — the two-regime structure of F1
reproduces exactly at scale, with the crossed/matched gap *wider*.

**Insight (hypothesis-level, per §9 locks).** The readout-policy account predicts this
direction: a larger pretrained encoder carries more latent visual competence, so a
readout policy learned *without images* has more to exploit at inference. Scale
amplifies rather than cures learning-without-looking — the blind-attainable share of
the gain is an increasing function of pretrained capability, which is exactly the wrong
direction for anyone hoping bigger models make outcome-reward RLVR more visual.
Consistent with, and sharpening, the representational-ceiling argument: the ceiling
rises with scale, and the policy's cheap path to it rises faster.

*Scope: one seed, single 7B pair; cross-scale comparison descriptive; A2b not run at
7B (registered choice, fired M8 fork rule).*

---

## 13. R5 — Cross-family generalization (complete)

`reports/generalization_audits_v2.json`, from
`m11_reconciled_backfill_v2_login_20260717T075457Z` (status complete, exit 0).
18 cells, status pass, zero errors, all six completeness checks true, values
opened only after the complete-queue gate.

| model | R19 real | R20 real | caption | no-image |
|---|---|---|---|---|
| Gemma-3 | 0.3333 | 0.3283 | 0.0058 / 0.0067 | **0.0000** (collapse 1.0) |
| InternVL3-9B | 0.6808 | 0.6783 | 0.0067 / 0.0133 | **0.0000** (collapse 1.0) |

R20 reproduces R19 almost exactly across both families — one-shot private
replication holding cross-family. But on the *ordinary* blind-sample benchmark
(the ViRL39K audit sample, n = 4,096 — the corpus family an RLVR run actually
trains on) the same models keep most of their accuracy with no image.

The naive ratios first, then the corrected ones. **The naive ratios are not the
result**; they are quoted only because earlier drafts used them.

| model | condition | real | blind | naive blind/real |
|---|---|---|---|---|
| Gemma-3 | none | 0.3418 | 0.2424 | 71% |
| Gemma-3 | caption | 0.3418 | 0.3091 | 90% |
| InternVL3-9B | none | 0.2805 | 0.1538 | 55% |
| InternVL3-9B | caption | 0.2805 | 0.1951 | 70% |

Chance-corrected, `(blind − null) / (with-image − null)`, split by answer format
because the sample is mixed (`reports/chance_corrected_retention_v1.json`,
10,000-draw paired item bootstrap):

| model | condition | subset | n | null | corrected retention [95% CI] |
|---|---|---|---|---|---|
| model | condition | subset | n | with image | blind | corrected retention [95% CI] |
|---|---|---|---|---|---|---|
| Gemma-3 | none | free-form pooled | 2,789 | 0.4295 | 0.3122 | **0.727 [0.690, 0.765]** |
| Gemma-3 | caption | free-form pooled | 2,789 | 0.4295 | 0.3965 | **0.923 [0.885, 0.964]** |
| InternVL3-9B | none | free-form pooled | 2,789 | 0.2685 | 0.1301 | **0.485 [0.439, 0.533]** |
| InternVL3-9B | caption | free-form pooled | 2,789 | 0.2685 | 0.2011 | **0.749 [0.693, 0.811]** |
| Gemma-3 | either | MC, k determinable | 1,215 | 0.1349 | — | **withheld — denominator negative** |
| InternVL3-9B | either | MC, k determinable | 1,215 | 0.2938 | — | **withheld — denominator degenerate** |

**Neither model's MC ratio is quoted, and the reason is not a technicality.** The
MC null on this sample is 0.2679, and **Gemma-3's with-image MC accuracy is
0.1349 — far *below* the chance floor**. The denominator `(with-image − null)` is
therefore negative, and `boot_denominator_nonpositive_frac = 1.0`: *every* one of
the 10,000 bootstrap replicates is degenerate. The arithmetic still emits 1.371
[1.218, 1.574], and that number means nothing at all. InternVL3-9B's MC
with-image accuracy (0.2938) sits just above the floor, giving −2.44
[−17.96, +6.51] with 2.7% of replicates degenerate — equally unusable.

> A model scoring **below chance with the image** on a multiple-choice slice is
> not evidence about blind solvability; it is evidence that the slice is broken
> for that model (options live in the image, extraction fails, or both). Reporting
> "retention > 1.0" from it would have inverted the finding.

The free-form rows carry the cross-family result on their own, and they are clean:
null = 0 there, so the denominator is just with-image accuracy and no correction
is needed or applied. **Gemma-3 retains 0.727 of its free-form accuracy with no
image; InternVL3-9B retains 0.485**, rising to 0.923 and 0.749 when a caption
replaces the image.

Two further subsets are excluded by rule and named rather than dropped silently:
92 MC rows whose options appear only inside the image (k indeterminable, so no
null can be assigned), and the whole-sample single-null figure, which the mixed
format forbids.

**This is the blind-reward-opportunity thesis measured on two foreign model
families**: on the corpus family that RLVR actually trains on, roughly half to
three-quarters of free-form accuracy is collectable without the image, while
FlipTrack collapses to exactly 0.0000 with collapse rate 1.0 for every model
tested. (Dossier note: §5's "caption ≤0.013" should read ≤0.0134 — the measured
maximum is 0.01333.)

---

## 13b. Blind solvability is benchmark-specific, not general — our own model family

> **Correction (2026-07-28).** Every earlier version of this section reported
> *naive* retention `blind / with-image` and concluded that "roughly half of
> standard-benchmark accuracy survives deleting the image entirely." **That
> conclusion was wrong for MMStar and it was my error.** MMStar is four-way
> multiple choice: a model that has deleted the image and guesses scores ~0.25 by
> construction, which is essentially all of the 0.2607 "retained" accuracy. The
> corrected figures below replace it. The measurement was right; the inference
> from it was not, and it sat in the paper's opening claim.

`reports/base_external_benchmarks.md`, recomputed in
`reports/chance_corrected_retention_v1.json`. The frozen base on public
benchmarks with and without the image, at two scales, same locked contract and
parser as everything else. Retention is
`(blind − null) / (with-image − null)`, with the null set by answer format —
MC → 1/k using **that item's own k**, free-form → 0 — and 95% CIs from a
10,000-draw paired item bootstrap that recomputes the ratio on every replicate
(a ratio of differences; naive intervals do not apply).

| benchmark / subset | model | n | null | with image | blind | naive | **corrected [95% CI]** |
|---|---|---|---|---|---|---|---|
| MMStar, all items (MC pooled) | 3B | 1,500 | 0.2688 | 0.5540 | 0.2607 | 47% | **−0.029 [−0.108, +0.049]** |
| MMStar, all items (MC pooled) | 7B | 1,500 | 0.2688 | 0.6320 | 0.2880 | 46% | **+0.053 [−0.010, +0.117]** |
| MathVista, MC pooled | 3B | 539 | 0.3316 | 0.7254 | 0.5120 | 71% | **+0.458 [+0.351, +0.564]** |
| MathVista, free-form | 3B | 460 | 0.0 | 0.5043 | 0.1152 | 23% | **+0.228 [+0.174, +0.287]** |
| MathVista, MC pooled | 7B | 539 | 0.3316 | 0.7606 | 0.5306 | 70% | **+0.464 [+0.368, +0.561]** |
| MathVista, free-form | 7B | 460 | 0.0 | 0.5478 | 0.1152 | 21% | **+0.210 [+0.160, +0.265]** |

**MathVista-testmini is deliberately not given a whole-benchmark number.** It is
mixed — 539 MC and 460 free-form items — and the null rule forbids one global
null across two formats. The old whole-benchmark "53% / 51%" figures were exactly
that forbidden average, and they are withdrawn.

The two benchmarks now say opposite things, and that is the finding:

- **MMStar is genuinely image-necessary.** Corrected retention is **−0.029 at 3B
  with the interval containing zero**, and **+0.053 at 7B**, also containing zero.
  Blind MMStar accuracy is statistically indistinguishable from guessing at both
  scales. (The one subset whose interval excludes zero is 7B on k = 4, +0.071
  [+0.004, +0.138] — 1,323 of the 1,500 items, and a hair off the floor.)
- **MathVista retains real blind-solvable structure.** Roughly **46% of the MC
  headroom above chance** survives image deletion at both scales, and free-form —
  where null = 0 and correction is a no-op, so the number was never inflated —
  retains 21–23%.

So the honest form of the claim is **not** "standard benchmarks are largely
answerable blind." It is that **visual necessity is a property that varies by
benchmark and by answer format, and it has to be measured rather than assumed** —
which is precisely why F0's reporting contract exists. Two benchmarks with
near-identical naive retention (47% and 53%) turn out to differ completely once
the guessing floor is removed.

Read together with §13, the surviving generalisation is about **the training
corpus, not public benchmarks**: on the ViRL39K audit sample, Gemma-3's corrected
MC retention exceeds 1.0 and its free-form retention is 0.727, while FlipTrack
collapses to exactly 0.0000 with collapse rate 1.0 for every model tested. **That
contrast is the case for the instrument** — not that FlipTrack is harder, but
that it is image-necessary by construction where the training corpus is not.

### 13b-bis. The audit completed: seven benchmarks, and visual necessity spans the full range

`reports/e1c_blind_columns_v1.{json,md}`. Five benchmarks had a with-image column but **no
image-removed run anywhere**, so no retention figure existed for them. All ten cells
(5 benchmarks × 2 scales) were run through `eval_layer1_blind.py`, which raises if a vision
token reaches the prompt; `image_removed=true` verified per cell. Same null rule, same
10,000-draw paired bootstrap (seed 20260729), mixed benchmarks split by format (I18).

**Corrected retention, lenient, pooled at the level each benchmark's format permits:**

| benchmark | n | null | with image | blind | **corrected** 3B | **corrected** 7B |
|---|---:|---:|---:|---:|---:|---:|
| **MMVP** (all k=2) | 300 | 0.500 | 0.660 / 0.743 | **0.5000** | **0.000** | **0.000** |
| MMStar (§13b) | 1,500 | 0.269 | 0.554 / 0.632 | 0.261 / 0.288 | −0.029 | +0.053 |
| BLINK | 1,901 | 0.377 | 0.493 / 0.557 | 0.409 / 0.387 | 0.271 | 0.055 |
| MathVerse, free-form | 1,760 | 0.0 | 0.055 / 0.087 | 0.019 / 0.031 | 0.340 | 0.359 |
| MathVista MC (§13b) | 539 | 0.332 | 0.725 / 0.761 | 0.512 / 0.531 | 0.458 | 0.464 |
| MathVerse, MC pooled | 2,180 | 0.260 | 0.465 / 0.545 | 0.394 / 0.412 | 0.655 | 0.534 |
| MMMU dev+val, MC pooled | 988 | 0.263 | 0.506 / 0.537 | 0.413 / 0.438 | 0.617 | 0.639 |

**MMVP is the cleanest demonstration in the set.** Every one of its 300 items is two-way,
and blind accuracy is **0.5000 to four decimals at both scales** — exactly the guessing
floor, corrected retention exactly zero. Deleting the image leaves the model with nothing
but a coin flip. MMStar behaves the same way within noise.

At the other end, **MMMU and MathVerse's MC slices retain 0.53–0.64 above chance**, and
MathVerse's free-form slice — where null = 0 and no correction is possible — retains
0.34–0.36. So across seven public benchmarks **visual necessity ranges from exactly zero
to roughly two-thirds, and the ordering is not recoverable from naive retention.** That is
F0's claim, measured rather than asserted.

*HallusionBench is reported with its null choice exposed, because the null decides the
answer.* It stores **no option labels on any of its 1,129 rows**, so the primary row applies
the existing rule literally — zero labels presented, therefore free-form, null = 0 — giving
**0.794 / 0.833**. But its gold vocabulary is in fact binary ({Yes: 484, No: 645}) while only
170 of 1,129 question texts say "yes or no". A null = 0.5 sensitivity row gives **−0.258 /
0.375**. Both are reported; the free-form row is primary as the conservative reading under
the registered rule, and **no options were synthesised**. This is the sharpest example in the
audit of why the null must be declared rather than assumed.

*Guards.* Where with-image accuracy equals the null the denominator is zero and retention is
reported as undefined rather than as a number (guarded at |d| ≤ 1e−12). Subsets with n < 30
carry `underpowered_subset=true` — MMMU k=6 (n=6), k=7 (n=2), k=9 (n=5). Blind prompts mirror
each benchmark's own builder, including MMMU's `<image N>` marker handling, which differs
from BLINK/MMVP/MMStar deliberately.

*Strict caveat (I7).* The same 1/k null is applied to `acc_strict`, which
additionally requires the `<answer>` wrapper. Where with-image `acc_strict` falls
below the null the denominator goes negative and the ratio is meaningless; those
rows carry `denominator_crosses_zero=true` and `boot_denominator_nonpositive_frac`
in the JSON and are not quoted here. MMStar strict with-image is 0.0013 (3B) —
far below the 0.2688 null — so **no strict corrected retention exists for MMStar**
and the naive strict ratio of 11.5 is an artifact of dividing by ~0.

Also complete for the base at both scales, without blind variants: BLINK
(0.4929 / 0.5565), HallusionBench (0.5979 / 0.6829), MMVP (0.6600 / 0.7433),
MathVerse (0.2817 / 0.3406), MMMU dev+validation (0.4819 / 0.5133).

---

## 13c. E1b — the blind gain does **not** transfer out of domain

`reports/e1b_blind_readout_v1.json`. Registered
`docs/registered_e1b_external_access_matrix_v1.md` **before any cell was run**.
24 blind cells (4 arms × 3 seeds × 2 benchmarks), all rc = 0, item sets pinned to
the E1a base items (1500/1500 MMStar, 999/999 MathVista). Same harness, decoding,
prompt contract and scorer as the base column — the E1b config differs from the
base config by exactly `_e1b` provenance and `model_path`. Deltas are paired
item-level, 10,000-draw bootstrap, arms averaged over their three seeds.

**Lenient (`acc_final`, answer content) — every arm is flat against base:**

| benchmark / subset | n | null | base | A1 real | A2 gray | A2b no-image | A3 caption |
|---|---|---|---|---|---|---|---|
| MMStar (MC pooled) | 1,500 | 0.2693 | 0.2607 | 0.2647 **+0.0040** | 0.2620 **+0.0013** | 0.2562 **−0.0044** | 0.2669 **+0.0062** |
| MathVista MC | 539 | 0.3316 | 0.5121 | 0.5121 **+0.0000** | 0.5182 **+0.0062** | 0.5182 **+0.0062** | 0.5114 **−0.0006** |
| MathVista free-form | 460 | 0.0 | 0.1152 | 0.1181 **+0.0029** | 0.1159 **+0.0007** | 0.1109 **−0.0043** | 0.1152 **+0.0000** |

**All twelve confidence intervals contain zero.** The widest deltas are ±0.006.
On MMStar every arm also sits *at or below the 0.2693 chance floor*, consistent
with §13b: there is nothing there to gain.

**P1 (primary) — branch (c), refuted on answer content.** The blind gain that RLVR
produces on geo3k and R19 **does not appear on either external benchmark**.

**P2 (primary) — not evaluable, and deliberately not forced.** P2 asks whether
A2b's blind gain matches A1's, scaled by A1's own gain over base. A1's lenient
gain is +0.0040 with an interval containing zero, so the scale is null and the
ratio is meaningless. Quoting one would repeat exactly the degenerate-denominator
error CHANCE was built to stop (cf. InternVL3-9B in §13). **Withheld**, because P1
failed and P2 was conditional on it.

**Strict (`acc_strict`) says something different, and it is about format:**

| benchmark / subset | base | A1 real | A2 gray | A2b no-image | A3 caption |
|---|---|---|---|---|---|
| MMStar | 0.0153 | 0.0564 **+0.0411** [+0.0329, +0.0500] | 0.0117 **−0.0036** [−0.0073, −0.0002] | 0.0117 −0.0036 [−0.0080, +0.0007] | 0.0275 **+0.0122** [+0.0062, +0.0184] |
| MathVista MC | 0.1706 | 0.2504 **+0.0798** [+0.0557, +0.1051] | 0.1533 **−0.0173** [−0.0322, −0.0025] | 0.1490 **−0.0216** [−0.0390, −0.0056] | 0.1799 +0.0093 [−0.0062, +0.0254] |
| MathVista free-form | 0.1021 | 0.1086 +0.0065 | 0.1014 −0.0007 | 0.0971 −0.0051 | 0.1000 −0.0022 |

Strict requires the `<answer>` wrapper **in addition to** a correct answer, so a
strict gain with a flat lenient gain can only come from formatting answers the
model already had. The contract-validity diagnostic confirms it directly
(seed 1): MMStar `Format_valid` base 0.0373 → A1 0.0653 → A3 0.1673, and
MathVista 0.6186 → A1 0.6687 → A3 0.6436, tracking `acc_strict` step for step.

So, reported under I7 with both metrics rather than the flattering one:

> **What transfers out of domain is output-format compliance, not blind answering
> ability.** And the format transfer *is* access-dependent — A1 (real images)
> carries it strongly (+0.041 / +0.080) while the blind-trained arms A2-gray and
> A2b carry it **negatively** — even though none of them transfers any answer
> content at all.

**Why this matters for the thesis.** §13 shows the *training corpus* is largely
blind-solvable, and F1 shows RLVR exploits that. E1b shows what the model takes
away is **specific to that distribution**: it is not a portable "answer without
looking" skill. The blind reward opportunity is a property of the corpus, and the
capability it installs does not generalise — which sharpens rather than weakens
the case for filtering the corpus.

### 13d. E1b with-image column — S1 and S2 both miss, the same way

`reports/e1b_image_readout_v1.json`. All 24 with-image cells inferred and scored;
inference fail rate 0/999 and 0/1500 in every cell. Scored through
`postprocess_vlmeval_predictions.py` (canonical-v2), the **same scorer and path
that produced the base with-image column** — it reads only the prediction and
answer columns and never a judge column, so base and E1b are comparable.

**Lenient (`acc_final`) — flat again, in all twelve cells:**

| benchmark / subset | base | A1 real | A2 gray | A2b no-image | A3 caption |
|---|---|---|---|---|---|
| MMStar (n=1,500) | 0.5540 | 0.5540 **+0.0000** | 0.5533 −0.0007 | 0.5489 −0.0051 | 0.5513 −0.0027 |
| MathVista MC (n=539) | 0.7254 | 0.7273 +0.0019 | 0.7229 −0.0025 | 0.7186 −0.0068 | 0.7186 −0.0068 |
| MathVista free-form (n=460) | 0.5043 | 0.5087 +0.0043 | 0.4993 −0.0051 | 0.5072 +0.0029 | 0.5051 +0.0007 |

**Every interval contains zero.**

- **S2 — not supported.** Trained arms do not beat base with images; they *match*
  it. Largest movement across all twelve cells is −0.0068.
- **S1 — not supported, and this bounds F6.** A2-gray minus A1-real on lenient is
  −0.0007 [−0.0067, +0.0053] (MMStar), −0.0043 [−0.0216, +0.0124] (MathVista MC),
  −0.0094 [−0.0225, +0.0029] (free-form). All contain zero. **The grounding
  corrosion that is item-identifiable on R19 (§6, §6a) does not show up as an
  accuracy loss on external benchmarks.** As the registration stated in advance,
  this does not overturn F6 — F6 is registered on R19 — it **bounds its external
  reach**, and is reported as the miss it is.

**Strict repeats the format story exactly.** A1 gains +0.0096 (MMStar), +0.1119
(MathVista MC) and +0.0399 (free-form), all intervals clear of zero, and S1 strict
is strongly negative — −0.0087, −0.1107, −0.0457, all significant. With lenient
flat, this is the `<answer>`-wrapper habit again, not answering ability.

### The whole E1b result in one line

**Across all 48 cells — blind and with-image, four arms, three seeds, two
benchmarks — not one lenient comparison moves.** Twenty-four intervals, every one
containing zero. The complete measurable out-of-domain effect of this RLVR recipe
is **output-format compliance**, which A1 acquires strongly and the blind-trained
arms do not.

That is a strong negative result and it is worth stating plainly: what the pilot
installs is **specific to the training distribution**. It transfers as formatting,
not as capability — in either direction, and whether or not the image is present.

---

## 14. The instrument (C4)

**R19, frozen, 1,200 pairs, three tasks with three distinct roles** — reported
separately, never aggregated across roles (I13): coordinate survey register
(600, primary visual anchor), header-cued verification table (300, high-baseline
control), nine-series calibration trace (300, oracle-localized readout control).
**R20**: one-shot private twin from fresh seeds, no iteration.

**Validity dossier.** 72B question-blind caption stress ≤0.062; artifact-attacker
gates with CIs; blind conditions at exactly 0.000 with answer collapse 1.0;
monotone degradation and scale controls; 60/60 human audit; cross-family
confirmation per §13.

**Base endpoint verified.** The step-0 FlipTrack minuend was re-measured from
scratch on the locked 1,200-pair manifest and reproduces **exactly** (geometry
lenient 0.4717, strict 0.4433) — verified rather than inherited.

**Instrument determinism.** The B1 premise probe was accidentally launched twice;
all five cells came out **byte-identical**, confirming the locked greedy decoding
contract is reproducible end to end (I7).

**B1 geometry track (prototype, 100 pairs, six intervention types):** fact-read
0.600, style-twin 0.643, distractor-only 0.438, binding swap 0.188, prior-conflict
0.143, chained premise 0.000 pair / 0.150 member.

---

## 15. Equivalence, contract validity, power

`reports/pooled_item_equivalence_v1.*`. Cluster bootstrap over the 600 pair_ids
(3 seeds); TOST against the registered ±0.05 SESOI. This is the **primary**
equivalence statistic; the seed-level figure is secondary.

| arm | pooled Δ | 90% CI (TOST) | equivalent? |
|---|---|---|---|
| A1 real | +0.0056 | [−0.0150, +0.0256] | **yes** |
| A2 gray | −0.0422 | [−0.0644, −0.0206] | **NO** |
| A2b no-image | −0.0272 | [−0.0483, −0.0061] | yes (marginal — lower bound −0.0483 against a −0.05 bound) |
| A3 caption | −0.0050 | [−0.0244, +0.0150] | yes |

**Contract validity as a first-class result** (pair-level, geometry slice): base
0.9500 → A1 0.8767, A2 gray 0.6317, A2b 0.7728, A3 0.7578. Every trained arm
falls **below** the frozen base. The ordering is *broadly* but not exactly aligned
with endpoint degradation: contract validity runs A1 > A2b > A3 > A2-gray while
the endpoint runs A1 > A3 > A2b > A2-gray, so A2b and A3 are inverted
(Spearman 0.8, not 1). RLVR erodes answer-contract compliance on the counterfactual probe
even where it raises task accuracy.

**Power.** Minimum detectable effect at 80% power is 0.0348 (A1), 0.0377
(A2 gray), 0.0360 (A2b), 0.0338 (A3) — about 70% of the ±0.05 SESOI, so the A1
null is informative rather than underpowered.

---

## 16. The cue ladder — a negative result about our own instrument

Registered `docs/registered_cue_ladder_v1.md` + v2 amendment. **Six** rung conditions were built and are reported — v1's exact / region / none
/ decoy plus v2's named_exact / named_region — all replayed from the frozen R19
nine-series `pair_seed`s (300/300 replay integrity), so the ladder is item-paired
with R19.

**Both monotonicity gates failed**, so branches (a)/(b) are void and the twelve
arm cells were deliberately **not scored** — F3d's prediction about
localization-specific corrosion is **untested, not refuted**.

Artifacts: `reports/cue_ladder_readout_v1.{json,md}`, `reports/cue_ladder_base_gates_v1.json`.

Base pair accuracy by rung: exact 0.4533, region 0.1367, none 0.6167, decoy
0.6067, named_exact 0.3333, named_region 0.6100.

**Cause: the annotation is a cue *and* an occluder.** R19's nine-series marker is
a white filled disc centred on the target point — it identifies the queried
series and simultaneously covers the datum whose value is the answer. Worth
**+0.317** [+0.253, +0.380] when it is the only identifier; costs **−0.277**
[−0.343, −0.207] when the question already names the series. Two directions at
once, so no rung ordering is monotone.

Consequences: R19's oracle-localized control supplies localization *by hiding the
datum* (removing the disc lifts base 0.333 → 0.610 with the series named) — which
refines what that control certifies without disturbing F3, since the occlusion is
constant across base and all arms. At 3B a correct visual cue adds nothing once
text names the series (−0.0067, CI covers zero), and a misleading one costs
nothing either (−0.0100, CI covers zero).

---

## 17. Corrections and integrity events

Recorded because the integrity anchor requires every registered endpoint to
appear, and because several of these were found by our own checks rather than by
review.

1. **A2 gray equivalence overstated.** The published "within band" verdict was an
   artefact of a normal approximation at n=3. Both the t(2) correction and the
   independent pooled item-level TOST agree it is **not** equivalent.
2. **The 0.9067 latent-competence figure** is predominantly candidate-set
   structure (X2 registered bottom branch).
3. **P0.2 scorer defect** — see §11. Found only because the premise probe
   returned an impossible 0.000.
4. **M11 wrongly recorded as never-run.** I checked the *failed* v1 queue's
   manifest and concluded the work never happened, without searching for a
   successor run; the reconciled backfill had completed it two days later. The
   lesson is that a failed run manifest does not mean the work never happened.
5. **Header table "saturated at 1.000"** — false; see §3.
6. **Power gloss** — an MDE of 0.0348 against a 0.05 SESOI is ~70% of the bound,
   not half.
7. **Seed-3 readout initially reproduced seed-2 byte-identically** (config
   builder inherited the wrong audits); caught by a plan verification rule and
   fixed to fail closed.
8. **Duplicate D3 cells** from restarts were deduplicated, keeping the earliest
   and marking later ones superseded.
9. **Naive retention reported as visual necessity — my error, and it sat in the
   paper's opening claim.** §13/§13b asserted "roughly half of standard-benchmark
   accuracy survives deleting the image." That divided blind by with-image without
   subtracting the guessing floor. On MMStar — four-way MC, chance 0.25 — the
   corrected retention is **−0.029 [−0.108, +0.049]**, i.e. indistinguishable from
   zero, against a naive 47%. MathVista's "53%" was worse than merely uncorrected:
   it averaged a single null across a **mixed** benchmark (539 MC + 460 free-form),
   which the null rule forbids; it is withdrawn and split. Corrected in §13/§13b
   from `reports/chance_corrected_retention_v1.json`. **The direction of the error
   was to overstate blind solvability on public benchmarks**; the thesis survives,
   but on the training corpus (§13), not on MMStar.
10. **M5b planning series mixed two metrics.** The benchmark trajectory I
   circulated took step 100 from `canonical_correct` and steps 150–400 from
   `acc_final`, inflating every step-vs-100 delta by +0.0050. Recomputed on one
   metric, the step-400-vs-100 gain is **+0.0083, p = 0.73** — not the increase I
   reported, and **the title-upgrade condition as I stated it is not met** (§12b).
   Caught by the readout's own recomputation rule, which forbids carrying
   planning-level greps into a reported number.
11. **E1b preflight raised a false comparability alarm.** It counted TSV *lines*
   where the pinned TSVs embed newlines in question text (2,106 lines / 1,500
   records), and a follow-up index check compared string ids to int ids and
   reported 0/1500 overlap. Both were defects in my checks, not the data: the base
   item sets are 1500/1500 and 999/999 intact. Fixed before any E1b cell ran.
   Logged because the failure mode — a check that manufactures a problem — is as
   costly as one that misses a real one.
12. **I published a degenerate ratio as a headline while writing the rule against
   it — same session, caught within the hour.** Rewriting §13 under the new CHANCE
   contract, I reported Gemma-3's cross-family MC retention as **1.371 [1.218,
   1.574]** and glossed it as "blind is at or above with-image." It is nothing of
   the kind: Gemma-3's *with-image* MC accuracy is 0.1349 against a 0.2679 null, so
   the denominator is negative and `boot_denominator_nonpositive_frac = 1.0` —
   every replicate degenerate. I had flagged exactly this failure for InternVL3-9B
   two paragraphs later and still quoted Gemma-3's. Both MC ratios are now
   withheld; the cross-family claim rests on the free-form rows, which are clean.
   **The lesson is that the guard has to run as a check, not as prose** — the
   `denominator_crosses_zero` flag was already in the JSON and I did not read it
   before writing.
13. **The on-quota step-300 M5 checkpoint is not the one that produced the reported
   step-300 numbers.** It was **re-merged on 2026-07-26**, and its
   `model.safetensors.index.json` sha256 (`0a640939…`) does **not** match the
   `checkpoint_index_sha256` recorded by the completed `m5_geo3k_step300` eval run
   (`236a9516…`). Total size (8,131,575,808) and all 825 tensor names are identical,
   but **419 of 825 tensors are assigned to a different shard file**, and byte
   identity was never established. The original is on **ln207 node-local scratch
   only**. Nothing reported so far is affected — the step-300 numbers came from the
   original — but **any re-evaluation at step 300 must restore the original**, or it
   will silently be a different checkpoint. Steps 150 and 400 match their eval runs;
   step 200 has no on-quota weights at all and survives only on ln207 scratch (index
   `d77c3fcb…`, which *does* match its eval run), with its raw shards deleted, so it
   can be **restored but never re-merged**.
14. **A run manifest saying `"running"` does not mean a run is live** — the mirror of
   entry 4. M7 arm 1 finished at step 100 with all five checkpoints written, and its
   manifest still read `"status": "running", "end_time_utc": null`; arm 4's OOM-killed
   first attempt read the same. Root cause: `launch_m7_virl_arm.sh` invoked
   `verl.trainer.main` directly instead of routing through `run_manifest_job.py` the
   way every other training launcher does, so M7 manifests never closed.
   **RESOLVED 2026-07-30**: arm 1's manifest closed via the standard
   `finalize_run_manifest.py` (not hand-edited), with the run-time-vs-true-completion
   timestamp discrepancy recorded; future launchers route through the wrapper. The
   principle stands: silently editing a run manifest is worse than a known-stale one.
15. **M7 arm 4's first attempt was killed by a race between two of our own
   workstreams.** The launcher checks GPU occupancy and then spends minutes in vLLM init
   holding no GPU memory; two `run_blind_solvability_v2.py` evaluation cells seized an29
   GPUs 4–5 inside that window (~62 GiB each, 7 minutes after launch) and the trainer
   OOM'd on KV-cache allocation. **The GPU-scope colocation guard was not at fault** — it
   correctly allowed GPUs that were genuinely free at check time. The defect is a
   time-of-check/time-of-use window plus the fact that only M7 launches consult the
   guard, so nothing protects an already-launched arm from a later non-M7 job. Arm 4 was
   relaunched on the quad arm 1 vacated; no scientific quantity is affected, and the
   guard's own log shows it consulting compute-app occupancy as well as trainer
   manifests. Recorded as an implementation defect, not a result.

---

## 18. Interpretation — what the results add up to

*Hypothesis-level reading, marked as such under §9 language locks.*

**RLVR here learns a readout policy over a frozen encoder, not new visual
distinctions.** Five independent measurements converge on it:

- **It is learnable without images.** Half the gain survives training with no
  visual information at all (F2), and under blind evaluation the training
  condition is irrelevant entirely (F1).
- **It is worthless without evidence at test.** Every arm's blind column is flat;
  the gain only appears when something readable is present (F1, D2).
- **It is content-bound, not presence-triggered.** Mismatched images buy exactly
  zero sharpening while correct images buy +0.15 (F4).
- **It lands where localization is already supplied.** 70% of the certified
  movement is on the oracle-localized control; the search-and-binding anchor is
  flat (F3).
- **The competence layers it should move do not move.** Hard negatives and
  binding are flat (F5). Chained premise is at floor but that floor is
  *uninformative* per P0.1 branch (b), so it is not counted as evidence here. The
  one exception is `prior_conflict`, which moves in every trained cell — a small
  cell (n=14) that the argument must acknowledge rather than omit.

**Two results sharpen this beyond the original claim.** First, G0.2: the
image-free gain is disproportionately the *blind-attainable* component — 84% of
A1's gain on items answerable without pixels, 42% on items that need them. What
image-free training harvests is largely reward opportunity that never required
the image. Second, R2: training four times as long makes the anchor *worse*, and
worse than the frozen base. A policy optimising a proxy it can satisfy without
looking will, given more steps, drift further from the thing the proxy was
supposed to stand for.

**The ceiling this implies.** If RL improves how the policy queries a frozen
representation rather than what that representation contains, the ceiling on
RL-driven multimodal improvement is representational. Raising it requires reward
variance resolvable *only* through distinctions the encoder can make but the
policy does not yet use — which is the argument Paper 2 is built on, and why
scalar answer rewards cannot supply it.

**Three further results sharpen it, all obtained after the account above was written.**

- **The gain is distribution-specific (E1b, 48 cells).** Across blind and
  with-image conditions, four arms, three seeds and two external benchmarks, **not
  one lenient comparison moves** — 24 intervals, all containing zero. What does
  transfer out of domain is output-format compliance, and it is access-dependent.
  So the readout policy is a policy over *this* task distribution's evidence, not a
  portable "answer better" capability. It also means **public benchmarks are
  insensitive instruments for both the gain and the damage**, which is the
  empirical case for the instrument (C4) rather than an aside about it.
- **The churn is real, structured, and invisible in the aggregate (M5c).** A flat
  geo3k score hides 137 of 601 items changing state against a **measured zero**
  noise floor — bitwise-identical replicates across node, GPU and date. Which items
  degrade reproduces across checkpoints (Jaccard 0.312 vs null 0.022); what they
  degrade *to* is dispersed, unlike the gray arm's identical-wrong-answer attractor.
  The churn is orthogonal to measured visual necessity.
- **Visual necessity is now measured across seven benchmarks (F0/E1c)** and spans
  the full range: exactly 0.000 on MMVP (blind = 0.5000 on a uniformly two-way set)
  through 0.53–0.64 on MMMU and MathVerse's MC slices. The ordering is not
  recoverable from naive retention.

**The falsification test ran, and the reading survived it.** The stated falsifier
was a training signal that moves hard-negative discrimination, binding or chained
premise while holding task reward fixed — which is what Mini-A5 was built to be.
Its endpoints are now read (§8): CP-GRPO's reward is structurally unsatisfiable by
a text prior, and **it did not move the primary visual anchor** on any of three
independent measurements (ranking lenient, ranking strict, generation lenient). The
one contract that moved decomposes to response formatting with a 1e−17 residual, and
85.7% of that comes from the comparison arm degrading. What CP *did* move is the
**oracle-localized readout control**, replicated on the one-shot private twin — the
same layer ordinary RLVR moves.

So the ceiling argument is no longer only implied by the pattern; it has withstood a
purpose-built attempt to breach it. That is a stronger claim than the one this
section originally made, and it is the claim Paper 2 inherits.

---

## 19. Still in flight

*Current as of 2026-07-30. D4, F8 and E1b have all landed and moved to their own
sections (§2b, §8, §13c–§13d); this list holds only what is genuinely open.*

**Running now** *(refreshed 2026-08-03T16:00Z; 14 of 16 GPUs working, the idle
pair on an12 held as the right-sized reserve for Gate 1's Δq pass pending PI
ratification)*

- **R3 endgame.** All four arms trained to step 100. The completion chain closed
  a1_real and a2b_noimage end-to-end autonomously; its loud give-up on the other
  two was orchestration, not science — a2_gray crossed step 100 **37 minutes
  after** the chain's 30-h limit expired, and a3_caption's eval launches died on
  the recurring jq PATH trap inside ssh-to-an12. Recovery 2026-08-03: a2_gray
  closed with full evidence and true completion time preserved
  (`observed_completion_utc: 2026-08-01T22:53:47Z`), merged and index-verified
  (825 / 8,131,575,808); both missing step-100 evals relaunched and generating;
  `r3_full_waiter.sh` armed to fire the **full R3 readout ~02:00Z 2026-08-04**.
  One orchestrator wobble recorded honestly in the gray eval's manifest: it was
  wrongly marked failed for ~20 min on a suspected merge race; log timestamps
  prove it loaded the merged weights cleanly after merge completion and was
  never interrupted.
- **C5 both 7B arms training.** A1-real at step ~80/100 (ahead of the 67–91
  min/step projection; ~08-04); A2-gray launched 2026-08-03 on an12 4–7
  (~08-06). Peak memory 73–78 GB of 79.33 at `gpu_memory_utilization 0.45` —
  inside the registered margin on both arms.
- **M7 seed 2 begun.** `a1_real` seed 2 launched on the freed an29 quad —
  registered work requiring no amendment (the seed-scope amendment deferred
  seed 2 explicitly as "not abandoned"), converting idle billed GPUs into the
  upgrade path from per-seed reporting back to the originally registered
  two-seed estimator. Full checkpoints (~205 GB) against 1,308 GiB free.

- **R3 M7 training** — **arm 1 complete at step 100/100**, all five checkpoints on
  disk; its step-100 checkpoint is **merged and verified** (825 weight entries,
  8,131,575,808 bytes — identical shape to every other 3B merge) and its manifest is
  **closed via the standard finalizer** (`status: complete`; `end_time_utc` stamped at
  finalizer run-time 15:45:49Z, true completion ~2026-07-30T20:57Z per checkpoint
  mtime — recorded, not hidden). Arms 2–4 (`a2_gray`, `a2b_noimage`, `a3_caption`,
  seed 1) training concurrently across an12 and an29 under
  `docs/registered_m7_seed_scope_v1.md`: seed 1 only, per-seed reporting, and
  `save_model_only: true` with `save_freq: 20` unchanged so the registered matched
  *cadence* holds. Four-arm access matrix on the second corpus expected **~2026-08-02**.
- **R3 step-0 held-out evaluations — COMPLETE** (all four manifests finalized
  2026-07-31 ~02:40Z), and the autonomous waiter ran the author-validated partial
  readout the moment they landed: `reports/m7_r3_readout_v1_partial.{json,md}`
  (rc = 0, `status: partial-step0-only`; every gain/recovery/ρ estimand refused by
  construction until step-100 exists). **R3's substrate is now real numbers:**

  | arm (own condition) | n | q̄ (blind opportunity) | Acc_final step 0 |
  |---|---:|---:|---:|
  | A1 real | 4,239 | 0.5122 | 0.2744 |
  | A2 gray | 4,239 | 0.4235 | 0.1894 |
  | A3 caption | 4,239 | 0.4458 | 0.1849 |
  | A2b no-image | 4,239 | 0.4154 | 0.1538 |

  Strata recount confirmed in production: 60 joint (source, category) strata =
  **22 eligible + 38 descriptive-small-n**, exactly as the fixture-validated
  assertion demands. The per-stratum q̄ spread is wide — `dvqa` charts are strongly
  image-dependent (q̄ A1 0.657 vs A2b 0.145) while `MMMath` non-geo is nearly fully
  blind-solvable (0.565 vs 0.547) — which is precisely the heterogeneity the
  registered prediction (stratum recovery tracks stratum blind-opportunity) needs to
  be a discriminating test rather than a formality.
- **C5 7B base cells — launched 2026-07-31T12:37Z** on an29 GPUs 4–5 through the
  project's own guarded launcher (`blind_solvability_v2_c5_7b_base_{real,gray}`),
  per the registration's explicit authorisation ("inference-only and may run before
  the training arms"). Same harness family as the 3B base rows, so the 7B access
  matrix will be methodologically parallel; 16-sample runs also bank per-item 7B
  `q_i` for future use.
- **R3 readout script — built and validated before its data exists** (`7b5176c`).
  `scripts/build_m7_r3_readout.py` implements the registered estimands exactly
  (q_bar / gain / recovery with the ≥2·paired_se stability rule, tie-corrected
  Spearman ρ_gain / ρ_recovery, 5,000 within-stratum bootstrap draws at seed 20260716
  with label-hashed streams, the >5% undefined-draw unstable rule, Geometry3K anchors
  0.0789/0.1184 labelled *informed*, M10 candidates, one-seed tag). **9/9 adversarial
  fixtures pass**, including planted rank correlations recovering their sign, unstable
  denominators excluded from ρ_recovery only, byte-identical reruns at the registered
  seed, and loud failure on missing items. The stratum recount asserts 22 eligible +
  38 descriptive-small-n from the jsonl (nearest boundary stratum has 34 items, so the
  count is not knife-edge). A real `--partial` invocation against the live step-0 runs
  passed the sha and recount assertions, then **refused at the readiness gate exactly
  as designed** (manifests still `running`, coverage ~20%) — fail-closed behaviour
  demonstrated on real data.

- **C5 7B (R4) — authored, registered, adversarially verified** (`50a16a9`; nothing
  launched). `docs/registered_c5_7b_access_pair_v1.md` amends Extension 4 to 2 arms ×
  1 seed on the geo3k pilot recipe (the ViRL flagship is *deferred with its pending
  fields intact, not discharged*), pins the 7B model by computed on-disk hashes (the
  dir carries no revision marker; equality with the M8 upstream revision is explicitly
  not asserted), quotes the fired M8 fork rule for A2-gray retention, and registers
  the 6-cell readout ({base, A1, A2-gray} × {real, gray}) with the M7
  stable-denominator rule at 5,000 draws seed 20260730. Configs verified byte-
  identical to the pilot templates except the five declared fields; both mechanics
  deviations (gpu_memory_utilization 0.45; save_model_only both arms) carried with
  their measured memory rationale. **The TOCTOU window that killed M7 arm 4 is closed
  and proven**: per-GPU claim files are now a third occupancy source in
  `m7_gpu_occupancy_guard.py`, and `tests/test_c5_gpu_claim_guard.py` (17/17)
  includes a test reproducing the exact arm-4 state, showing the old rule allows it
  and the new rule refuses; dry-probed on live hardware.
  **New launch precondition discovered and registered**: no geo3k evaluation of the
  7B base exists anywhere (1,619 runs scanned), so both base cells (test-real,
  test-gray) must be evaluated under the locked contract before any C5 estimand is
  read — schedulable on an29 GPUs 4–7 as soon as the step-0 evals finish.

**Open decisions (PI's, not mine)**

- **R4 C5 7B** — the only completely empty rung on the claim ladder. No 7B training
  configs exist; two must be authored (A1 and A2-gray) against the 3B recipe with a
  registered sizing decision. The 1 TiB quota top-up makes it affordable.
- **LH2 second long-horizon seed** — not auto-triggered. §12b weakened the case that
  motivated it (the benchmark axis is flat at step 400 vs 100, not rising), so whether
  a multi-day run is worth a Tier-3 upgrade is a judgement call.
- **Title upgrade** — resolved **negatively** by M5b against the registered condition;
  current title stands (§1 of PAPER1).

**Engineering debt that affects trust in artifacts**

- **M7 run manifests are not currently authoritative.** There is no M7 finalizer:
  arm 1's manifest still reads `"status": "running"` with `end_time_utc: null` despite
  finishing at step 100, and arm 4's first (OOM-killed) run reads `"running"` too.
  Both must be reconciled before the R3 readout treats manifests as ground truth —
  this is the mirror of the M11 lesson already in §17.
- **The launcher has a time-of-check/time-of-use window.** `launch_m7_virl_arm.sh`
  checks GPU occupancy, then the trainer spends minutes in vLLM init holding no GPU
  memory. A non-M7 job can seize the GPUs inside that window, which is exactly how M7
  arm 4's first attempt died. The GPU-scope guard is not at fault; the gap is that only
  M7 launches consult it, so nothing protects an already-launched arm.

**Blocked on an instrument that does not exist**

- **Paper 2's invariance/specificity axis.** Per §8e, no metric field expresses the
  invariance criterion — `collapsed` is gated on `answer_a != answer_b` and so is inert
  on equal-gold pairs. The scorer is specified but unbuilt, and `PAPER2` §2 C2 calls
  invariance "required, not optional". This blocks Phase-1 development groups that would
  be validated against it.

## 20. E2 — recipe variation: the dissociation is not the pilot recipe's artifact (2026-08-04, assembly only)

`reports/e2_recipe_variation_v1.{json,md}` + `scripts/build_e2_recipe_variation_v1.py`
(commit ab8530b, pushed to agent/gate2-recovery and master). No new runs, no GPU —
every number is read programmatically from the canonical artifacts (17 sources, sha256
recorded) and the build fails on any mismatch with RESULTS §§3, 6, 12, 12b.

Side-by-side, step 100 vs the same frozen base, same geo3k test split (n=601) and same
R19 geometry primary anchor (n=600 pairs):

| config | benchmark Δ (canonical / pilot-lenient) | primary grounding Δ (lenient) |
|---|---|---|
| pilot A1 — frozen tower, pilot reward, filtered 1,288-row corpus, 3 seeds | +0.2435 / +0.2684 (mean; every per-seed CI excludes zero) | +0.0056 [−0.0183, +0.0294] (all 3 seeds inside SESOI ±0.05, equivalence supported) |
| anchor — unfrozen tower, native r1v, unfiltered corpus, 1 seed | +0.2562 / +0.2862 (p ≤ 5.1e−31) | +0.0083 [−0.0217, +0.0367] (p = 0.6445) |

**Insight.** The benchmark-up / grounding-flat dissociation reproduces under a recipe
that differs in all three factors a reviewer would blame — tower freezing, reward
function, corpus filtering — so it is not an artifact of the pilot's frozen-tower /
canonical-reward configuration. The two configurations even land nearly identical
numbers on both axes, which was not guaranteed. Only the anchor was extended past 100:
benchmark peak-and-return (+0.0083 vs step 100, p = 0.73) against monotone grounding
decline (−0.0667, p = 2.4e−06) — reported with the I19 attribution clause verbatim.
Caveats stated plainly in the artifact: anchor is one seed; three coupled factors, so
no single-factor attribution — robustness evidence, not a factorial experiment; the
anchor's strict step-100 grounding delta is nominally +0.0367 (p = 0.026) purely
because strict scoring charges the frozen base's contract failures.

## Human-review packages round (2026-08-04): the two missing PI packages are built

Both outstanding human-review packages from the ledger's "Human items" table now exist
under `reports/human_packages/` (deterministic builds, no GPU touched, zips gitignored;
build scripts + manifests committed, `83d3b66`, pushed to `main` and `agent/gate2-recovery`):

| package | zip | size | contents |
|---|---|---|---|
| 24-candidate support-expansion review (~30 min) | `blind_gains_support_expansion_24_review_20260804_v1.zip` | 624,879 B, sha256 `c74ef0e4...4b6bed14` | all 24 high-confidence M10 seed-1 candidates (A1 16 / A2 1 / A2b 5 / A3 2), 22 images, static viewer, `response_sheet.csv` (2 decisions/item: trained_answer_verdict, item_legible), one-page guide |
| R20 human audit sample (~30 min) | `blind_gains_r20_human_audit_20260804_v1.zip` | 4,876,658 B, sha256 `662e8c39...55003497` | 60 pairs / 120 images, first-20-source-order per template (exact R19 audit design and builder), same viewer + six-check contract, R20-adapted guide carrying the R19 chart construct notes |

Selection is RNG-free in both packages (exhaustive over the 24 qualifying items;
first-N-per-template source order for R20 — the same deterministic rule the accepted R19
audit used), with every source manifest sha256-pinned in
`reports/support_expansion_review_bundle_v1.json` and `reports/r20_human_audit_bundle_v1.json`.

**Insight.** Assembling the 24-candidate set surfaced two things worth the reviewer's
attention before any interpretation: (1) two geo3k test items (rows 55 and 253) are
support-expansion candidates in *both* A1-real and A2b-no-image — the same question was
outside the base's sampled support under two different input conditions, so whatever the
trained arms installed there is not condition-specific; (2) several step-100 "correct"
answers match gold only through canonical normalization (`13` vs `13.0`, `45^\circ` vs
`45`, `\( 6\sqrt{3} \)` vs `6 \sqrt { 3 }`) — exactly the cases the `artifact` verdict in
the response sheet exists to separate from genuine solves. A2b's five items remain the
qualitative window: all five have plain integer golds and open with <think> reasoning
chains (673-2,434 chars), and one of them (`a2b_noimage_test_0055`) states "the problem
statement is not provided" mid-chain yet still lands the gold answer - the sharpest
guess-vs-solve call in the set.

## 2026-08-06 — C5/R4 registered readout script + adversarial fixtures (pre-data, plumbing only)

Built `scripts/build_c5_r4_readout.py` (the registered R4 readout for the 7B access
pair) BEFORE its arm data exists, bound to the "Registered Readout" section of
`docs/registered_c5_7b_access_pair_v1.md`: six cells {7B base, A1-real, A2-gray} x
test {real, gray}; matched gains, A2 crossed gain, crossed recovery TrainShare under
the M7 stability rule (denominator > 0 and >= 2*paired_se, else
undefined-unstable-denominator with the ratio not computed); A1-tested-gray
descriptive; 5,000 item-paired bootstrap draws, seed 20260730, percentile 95%; both
I7 scoring contracts (greedy_canonical_correct / greedy_acc_strict) computed
separately and never merged; every number carries the one-seed tag.

Adversarial fixtures (I10), all 8 passing on the remote
(`tests/test_c5_r4_readout_fixture.py`): planted matched/crossed gains and
TrainShare (0.5/0.5) recovered exactly under both contracts; poisoned train-split
rows with overlapping row_index never leak into estimands; unstable canonical A1
denominator (+1/40 vs 2SE~0.113) -> undefined-unstable-denominator with strict
still stable at 0.5 (contract independence); missing item -> loud item-identity
failure, no outputs; incomplete manifest refused; two runs at seed 20260730
byte-identical (JSON, markdown, joined artifact); partial mode verify-only.

Real-data proof: `--partial` run against the two existing 7B base cells (601 test
rows each) exits 0 with every check true (registered source-manifest / prompt /
format / filter hashes, decoding seed 20260710, item+content identity across
cells) and emits ZERO accuracy or performance values — the C5 inspection
discipline holds until both arms complete. Artifacts:
`reports/c5_r4_readout_v1_partial.{json,md}`. A recon disclosure (uniq -c over the
contract booleans during schema recon) was appended to the registration's
deviations log. Insight: the harness's train/test row_index ranges overlap
(train 0..2099, test 0..600), so pairing identity must be row_index WITHIN the
test split — a naive whole-file join would silently mispair; the readout gates on
exactly this.

## Round: LH2 stage-1 registration (2026-08-06, registration only — no training launched)

Filed `docs/registered_lh2_stage1_v1.md` + `configs/train/lh2_anchor_seed2_3b_geo3k.yaml`
(commit 7ab887e, pushed to agent/gate2-recovery + master + main). LH2 is the F6
Tier-3 second long-horizon seed of the anchor recipe. Design decision: a genuine
second seed CANNOT warm-start from the archived step-100 anchor — that checkpoint
IS seed 1's trajectory — so stage 1 is a fresh 0->200 run from the frozen base
with data.seed 2 (the only experiment-level stochasticity control the recipe
exposes; EasyR1 consumes it as the train-shuffle generator seed, verified in
verl/trainer/data_loader.py; the rollout seed stays at package default in both
seeds, matching every existing mech_*/m7_* seed-2 config). Cost from the measured
clean M5 segments (22.34 h + 21.73 h per 50 steps): 44.1 h/100 steps at 4 GPUs;
stage 1 ~88 h (~3.7 d), full 0->400 on GO ~176 h. Mandatory 50-step process
segmentation with hash-verified boundaries (the unsegmented M5 process died of
the Ray host-memory ramp, `reports/m5_host_memory_incident_v1.md`). Evals at
100/150/200 under the locked M5 contracts; registered go/no-go at 200: GO iff
g(200)-g(100) < 0 within seed 2 (directional only, no magnitude threshold, no
discretion); NO-GO -> stop, Tier 2 stands. Config diff machine-checked
(`scripts/check_lh2_config_diff.py`, exactly 5 leaves vs each reference config)
with an I10 adversarial fixture (clean passes, unregistered-leaf and
wrong-seed tampers both fail). Insight: the sharpest design fact is that
"second seed" is a property of the 0->100 history, not of the continuation —
any warm start from the existing anchor would have silently degraded Tier 3
into a second continuation of seed 1, and the registration now states that
disqualification explicitly so it cannot be relitigated at launch time.

## 2026-08-07 — Track-4 premise-construct v2: registration + schema v2 + generator + 160-group dev batch (CPU round, no GPU evals)

Design registered (docs/registered_track4_premise_v2_design_v1.md, commit
fb677d1) before any item existed; batch built one-shot after (commit 94fbd52).
The new premise_transition type inverts B1's frozen geometry instead of its
conditional: B1 constrains the moved nearest neighbour to STAY nearest
(dist(T,N') < d2-0.5), v2 pushes it beyond the runner-up with margin
(dist(T,N') >= d2+1.0) plus d3-d2 >= 1.0 so the B-side premise carries the
same >= 1.0 decidability margin as the A-side; the runner-up M never moves, so
the final-answer change is carried entirely by the premise change. premise_answer
becomes per-member (premise_answer_a/b); the old "premise_transition_accuracy"
(equal-gold rescore = invariance) is renamed premise_stability and the
redefined transition metric requires each member's premise to match its OWN
gold with golds differing by construction — a premise-frozen policy scores 0
(adversarial fixture proves the old metric rewarded exactly that policy).
Easier variant: n_points 20 -> 8, the only lever the frozen renderer already
parameterizes; registered band 0.40-0.60 base premise accuracy on
chained_premise_easy with pre-committed branches (n=12 if too easy, n=5 if too
hard, one re-measure, then declare the lever insufficient).

Numbers: schema v2 fixtures 27/27 (v1 loader refuses v2 and vice versa; frozen
v1 fixtures still 13/13; training path refuses measurement_state=pending);
generator fixtures 7/7. Batch: 160 groups (premise_transition 40 n20,
premise_transition_easy 40 n8, chained_premise_easy 40 n8, chained_premise 20
n20, fact_read 20 n20), 160 causal + 160 invariance pair rows (80 style twins /
80 answer-and-premise-preserving distractor moves), 140 premise-probe rows of
which 80 genuine transitions, all groups blind_solvability=pending, 0 frozen-B1
image-SHA collisions, attempts max 3304/120000 cap. Independent from-disk
verification recomputed every premise+final gold from serialized scene programs
on both physical sides, re-hashed all 640 images, confirmed all 80 transitions
violate B1's stay-nearest filter: 0 problems
(reports/track4_premise_v2_dev_build_v1_verification.json).

Insight: the rejection-sampling cost asymmetry is itself evidence the construct
is right — premise_transition burned 3304 attempts vs 363 for
chained_premise_easy because demanding BOTH sides of a transition be decidable
with margin >= 1.0 (plus the d3 gap) is genuinely harder geometry than letting
the premise stay put; invariance was cheap for B1 precisely because it never
had to pay for B-side decidability. GPU acceptance gates E1-E4 (difficulty
band, blind floor, caption stress, DINOv2/pixel attacker) are registered with
exact commands + pass criteria but NOT run; no training config exists or is
authorized until they pass.

## 2026-08-06 — LH2 stage 1: registration filed (no training launched)

Registration round, no new experimental numbers. docs/registered_lh2_stage1_v1.md
(commit 7ab887e) + configs/train/lh2_anchor_seed2_3b_geo3k.yaml register the F6
Tier-3 test: a SECOND SEED of the anchor recipe, defined as a fresh 0->200 run
from the frozen Qwen2.5-VL-3B base with data.seed 2 — NOT a warm start from the
step-100 anchor checkpoint, because that checkpoint IS seed 1 (its 0->100
history was optimized under data.seed 1; a continuation would only re-draw the
100->200 suffix and could not support the word "systematic"). data.seed is the
only experiment-level stochasticity control in the recipe (verified in EasyR1
data_loader.py: it seeds the train-dataloader shuffle generator), matching every
existing seed-2 config in the project. Machine-checked config diff: exactly 5
leaves vs the anchor template (seed, max_steps, save_freq, two renames), checker
+ adversarial fixture pass at HEAD (reports/lh2_config_diff_check_v1.json,
reports/lh2_adversarial_fixture_v1.json). Cost basis measured from the two
clean M5 segments (22.34 h + 21.73 h per 50 steps): 44.1 h/100 steps at 4 GPUs,
so stage 1 = ~88 h (~3.7 days); a full GO-through-400 LH2 = ~176 h. Go/no-go at
step 200 is directional only: GO iff lenient R19 geometry pair accuracy
g(200)-g(100) < 0 within seed 2; NO-GO -> stop, Tier 2 stands.

This round also replaced the launch chain (commit 1b6e01e,
scripts/lh2_segment_chain.sh): the prior draft died with its session and had
three registration violations (no hash-verified boundary audit, constant
experiment_name, checkpoint root missing the stage-run-id subdir) plus a
counting bug ("cmd || echo 0" double-prints 0, so its eval-proc and fatal-line
gates could never read clean). The rewrite audits every 50-step boundary with
audit_easyr1_resume_checkpoint.py under the exact M5 jq contract; I10 fixture
pass (reports/lh2_chain_boundary_fixture_v1.json: clean 0/contract 0, missing
optimizer shard 1, wrong expected step 1). Nothing launched: registration only;
gates verified read-only against an12 (GPU0 63.9 GB busy with live R4 evals —
chain correctly holds).

Insight: "second seed" is where long-horizon replications quietly go wrong —
the cheap version (warm-start the existing step-100 checkpoint, vary the
continuation) looks like a replication but shares 100% of the optimization
prefix that produced the Tier-2 observation, so it tests only suffix
sensitivity. Paying the full 0->100 cost again (~44 h) is exactly the price of
the word "systematic" in the Tier-3 sentence.

## 2026-08-09 — GATE 1 COMPLETE: the four-arm completion readout — no axis buys content; the readout layer moves under every recipe

Both new arms (arm 1 std = standard GRPO answer-only; arm 3 necessity = Δq-necessity-
sampled answer-only) trained 120 optimizer steps on an29 under
`docs/registered_mini_a5_gate1_completion_v1.md`; the section-9 acceptance audit
(`reports/mini_a5_gate1_acceptance_audit_v1.{json,md}`, new instrument
`scripts/audit_mini_a5_gate1_acceptance.py` with a 22-fixture adversarial suite incl. a
sealing guard) passed **9/9 conditions** before any endpoint value was read. Readout:
`reports/mini_a5_gate1_endpoint_readout_v1.json` (four arms on frozen R19 held-out, both
contracts, per-role, F8 cp/member cells carried not re-decided). One seed per arm.

**Primary visual anchor (600 pairs), lenient pair accuracy:** base 0.472, std 0.468,
member 0.482, necessity 0.493, cp 0.472 — **flat everywhere**. Registered contrasts:

| contrast (axis) | primary lenient | primary strict | canary strict | oracle strict |
|---|---|---|---|---|
| member − std (data/pairing) | NOT MOVED (+0.013) | **−0.080** (p=5.3e−7) | **−0.323** (p=4.1e−27) | −0.077 (p=2.2e−3) |
| necessity − member (selection) | NOT MOVED (+0.012) | **+0.043** [0.018, 0.070] | NOT MOVED (−0.023) | +0.057 |

**The one thing that moves is the oracle-localized readout, and it moves for every
recipe:** vs frozen base, lenient +0.18 (std), ≈+0.15 (member), ≈+0.18 (necessity),
+0.23 (cp). The primary anchor moves for none of them. F3/F8's layer selectivity —
readout trainable, search+binding not — is therefore **recipe-independent**: it survives
changes of data organization (pairing), sampling (necessity), and objective (relational
CP), not just the pilot recipe.

**Catch-trial stability (100 catch trials/arm):** lenient at ceiling for all four
(std 0.96, member 0.96, necessity 0.99, cp 0.98); strict separates: cp 0.64 ≈ std 0.62 >
necessity 0.49 > member 0.28 (`reports/mini_a5_catch_stability_{std,necessity}_v1.json`
via the new single-arm scorer; cp/member from the registered two-arm readout, pins
intact). Fifth independent localisation of arm differences to format.

**What Gate 1 answers for Paper 2 (data / selection / relational-reward in sequence):**
none of the three axes adds held-out content at 3B/step-120. The paired-data
organization alone (member) is strictly a format tax; necessity sampling refunds part of
that tax; the relational reward's remaining increment over plain GRPO is format-shaped
(F8's four-way localisation, now extended). The pre-committed branch structure and the
Paper-2 direction call on it are the PI's to read.

**Insight (hypothesis-level, per §9 locks).** The readout-policy account predicted the
oracle-readout movement would be objective-general: outcome reward at this scale can
strengthen how existing percepts are read out into answers, but supplies no gradient
through the search-and-binding stage that the primary anchor requires — under any of
the four reward/data configurations tried. If that is the right abstraction, the lever
that remains is not reward *shape* but reward *resolvability*: reward variance that only
encoder-level distinctions can resolve (the Track-4 premise-v2 construct is built to
test exactly this).

*Scope: one seed per arm; single scale (3B); R19 instrument; catch strict levels share
the format story. Operational deviations (first-attempt eval launches without merged
weights; two chain-script path bugs — fixed, committed, memory-noted) affected timing
only, never numbers; the acceptance audit binds the analysis cells regardless.*
