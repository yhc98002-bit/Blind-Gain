# Blind Gains — consolidated experimental results

*Learning Without Looking: Image-Dependent Gains from Image-Free RLVR*

Single results file for the programme. Organised by the paper's own argument
(F1–F8) and the claim ladder (R1–R5), not chronologically. Every registered
endpoint appears, including those that went against the hypothesis. Numbers are
copied from committed artifacts; each block names its artifact.

Updated 2026-08-16. Model: Qwen2.5-VL-3B-Instruct unless stated.

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
| M7 ViRL39K stratified | R3 | **complete — two seeds, registered estimator (2026-08-16)**: matched recovery **0.71–0.88 vs 0.08–0.12 on geo3k** (A2 gray 0.7265 [0.6592, 0.7961], A2b 0.7132 [0.6483, 0.7844], A3 0.8840 [0.8091, 0.9632]); geo3k-anchor differences +0.6476/+0.5948, both registered directions hold; ρ_gain direction **fails** all blind arms (gains track headroom — the seed-1 pattern reproduces); ρ_recovery point-positive for gray/no-image, direction holds (§ "2026-08-16 — Consolidation round"; seed-1 readout §12d) |
| C5 7B access pair (A1 vs A2-gray) | R4 | **complete** — crossed TrainShare **0.78–0.84 vs 0.49 at 3B**, intervals disjoint; matched gain replicates (+0.2479 vs +0.2435). **Ladder R1–R5 closed** (§12e) |
| M11 cross-family | R5 | **complete** (recovered 2026-07-28) |
| Mini-A5 CP vs matched GRPO | F8 | **complete** — gate PASS, endpoints read under the pre-filed addendum. **Branch 2 fires**: primary anchor flat on content; the +0.07 strict gap is formatting (residual 1e−17). CP moves the oracle-localized readout on both R19 and R20 — the same layer ordinary RLVR moves (§8) |
| Gate 1 four-arm completion (std · member · necessity · cp) | Paper 2 | **complete 2026-08-09** — acceptance audit 9/9 PASS before unsealing. **No arm moves held-out content on the primary anchor** (lenient NOT MOVED, all contrasts, all roles); every registered difference is strict/format. **All four recipes move the oracle-localized readout +0.15–0.23** — F3's layer selectivity is recipe-independent. Data axis costs format (member −0.32 strict on the canary); necessity partially repairs it (+0.043 [0.018, 0.070]). See the 2026-08-09 Gate-1 section |
| X1–X5, B1, Gate 0, Phase 0 | F4–F7, Paper 2 | **complete** |
| Cue ladder | Paper 2 P1.1 | **closed — both validity gates failed** |
| C6 mechanism at 7B (A1/A2-gray on R19+R20) | F4 at scale / Paper 2 §5 | **complete 2026-08-11** — the 3B dissociation **inverts at 7B, and only for the real-image arm**: A1-real moves the primary anchor (+0.0250/+0.0233, CIs exclude 0, both contracts, both instruments — branch (d)); readout flat; A2-gray moves neither (branch (c)). One seed, descriptive; re-decides neither Gate 1 nor R4 (§ "2026-08-11 — C6") |
| Track-4 premise-v2 acceptance gates E1–E4 | Paper 2 P1.5 / I14 | **all four run 2026-08-11; E1/E2/E3 re-run on the regenerated dev_v2 batch 2026-08-16** — E1 **PASS** both contracts (0.5125 in [0.40, 0.60]; branch (a) band hit at the branch-(c) n=5 re-measure — n=5 frozen, no further lever moves); E2 **FAIL persists** all five types (0.15–0.20 vs 0.133) with the mechanism now fully diagnosed: blind constant `-1` + tier-1 lenient containment scores gold `1` correct against `-1`, so the effective constant-attacker share is two value-classes (0.20) while the registered per-value balance cap held at 0.10; blind pair accuracy 0.000; exclusions from training stand; E3 **PASS all five types under BOTH readings** on dev_v2 — `chained_premise_easy` 0.2000 ≤ 0.233 resolves under unmodified reading (a); E4 PASS unchanged, wording resolved via unfolded per-attacker CIs (§ "2026-08-16 — Consolidation round") |
| LH2 stage 1 (anchor seed 2) | Paper 1 §7 | **training since 2026-08-16T17:22Z** — seg-1 (`lh2_seed2_seg1_an12_20260816T172233Z`, an12 0–3, steps 0 → 50 of the segmented 0 → 200 stage, hash-audited boundaries between segments) after the 08-15 logger livelock was cleared (§ "2026-08-16 — Consolidation round") |

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

> **RETRACTED — INVALID BUILD (2026-08-11 PI review; header added 2026-08-16
> per the 08-12 dispatch P0.2; body below retained unmodified, superseded not
> deleted).** All six rungs reference the byte-identical v07 image (pixel
> diff = 0; `replayed_from: starred_series_value_nine_v07`); the annotation
> layer never varied; golds were copied from the starred series while the
> named/none/decoy questions name other series (question–gold mismatch on 4
> of 6 rungs); the verifier's `gold_follows_question` checked gold against
> the *target*, not the question. The July readout numbers (+0.317 / −0.277)
> are wrong-gold artifacts; the "marker is cue and occluder" story and the
> text-priority micro-result are **retracted**. Arm cells were never scored —
> nothing propagated to results. Superseded by the L1/L2/L3 hierarchy
> (`docs/registered_hier_benchmark_v1.md`).

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

*Current as of 2026-08-17T09:40Z. The 08-12→08-14 storage deadlock and its
recovery are recorded in `reports/storage_cleanup_20260814.md` and the
2026-08-14 commit history; the 08-15 chain outcomes and their diagnosis are in
the "2026-08-16 — Consolidation round" section.*

**Running now**

- **LH2 stage 1, seg-1 training** since 2026-08-16T17:22:36Z
  (`lh2_seed2_seg1_an12_20260816T172233Z`, an12 0–3; the chain runs from the
  immutable copy `tmp/immutable_lh2_segment_chain_20260816.sh`, banks and
  hash-audits each 50-step boundary, and stops at the registered step-200
  go/no-go).
- Nothing else: HB P2 is fully complete (caption-stress chain landed
  2026-08-17T03:11Z) and the pre-freeze cleanup round is closed — the r2
  re-measure battery, census v4, and the PI report
  (`reports/hier_v1_prefreeze_cleanup_v1.md`) are all banked; next GPU
  campaign is the ratified chart-v2 cycle.

**Open, not running**

- **E2 lenient-class fork — PI call.** The registered balance cap (max
  per-value gold share ≤ 0.10, `docs/registered_hier_benchmark_v1.md` §8) held
  on dev_v2, but the tier-1 lenient matcher scores gold `1` correct against
  the blind constant `-1` (30/30 + 30/30 golds in the gray final cell, all
  other golds 0), so the effective constant-attacker share is
  share(`1`) + share(`-1`) = 0.20 (0.15 for `premise_transition`) and E2 fails
  all five regenerated types; blind pair accuracy 0.000 everywhere; exclusions
  from training stand. Candidate revisions — cap lenient-equivalence-class
  shares, make the answer support sign-unambiguous, or revise the matcher
  tier — are the PI's to pick before any further regeneration (one-shot
  discipline, no silent iteration).
- **ST3-7B ratification**: `docs/registered_stage3_7b_v1.md` is an unsigned
  DRAFT; launch gates = two-seed R3 landed + HB P2 informativeness gates + PI
  merge with the launch-time amendment (training-batch pin, configs,
  blind-control decision).
- **Coordinate freeze — three PI items**: human audit of the r2 render;
  disposition of the template-unstable dinov2 marginal (n12 0.5569 on r2 vs
  n20 0.5577 on v1); a registered caption ceiling for HB.
- **HB chart revision (ratified, next up).** `hier_chart_v1` fails the P2.3
  artifact-attacker gate decisively (numbers in the 2026-08-17 section); the
  leak is numerically pinned to the unidirectional switch edit + the
  filter-induced direction bias of low-crossing stable edits. Any fix is a
  registered revision cycle (one-shot discipline), not silent regeneration.
  Coord's single marginal template (dinov2 n20 folded 0.5577) is part of the
  same disposition. The chart-v08 no-zoom audit (Richard) additionally still
  blocks chart-side P2 freeze.
- **§21 ledger gaps** surfaced by the M13 table
  (`reports/paper1_numbers_table_v1.md`): F1b, F2, F4, F5, F6 Tier 1, F7 have
  no §21 row; F0/F1/F10 rows carry artifacts but no numbers.
- **PI-owned prose**: X6 related-work table; PAPER1 §3/§5 header-table wording.
- **Richard's review** of the delivered human packages (+ chart-v08 no-zoom,
  R20 sample).

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

## 2026-08-11 — C6: the mechanism at 7B. The dissociation does not survive scale — it **inverts**, and only for the real-image arm

**What C6 asked.** Two of the program's strongest results ran along different
axes. Gate 1 fixed scale (3B) and varied recipe: across four recipes, no axis
bought held-out content on the primary visual anchor, while the oracle-localized
readout moved under every recipe. R4 fixed recipe and varied scale: the
blind-attainable share of the training gain *grows* at 7B. C6 joins them —
does the readout/anchor dissociation still hold when the trained model is 7B?

Six cells, three models × two instruments, on banked C5 checkpoints:
frozen 7B base, `c5_a1_real_seed1_7b/global_step_100`,
`c5_a2_gray_seed1_7b/global_step_100`, each on R19 (1,200 pairs, pinned
`e1dde984…2ffb2`) and the R20 private twin (`20222e60…2ef3`, zero shared
`pair_id`). Registered **before** any value was read
(`docs/registered_c6_mechanism_at_scale_v1.md`, filed while the cells were still
generating); instrument fixtures (61 adversarial cases) green before the
instrument touched a real cell; all 16 registered acceptance checks pass.

**Result — A1-real (trained on real images), per task role, arm minus base:**

| role | R19 lenient | R19 strict | R20 lenient | R20 strict |
|---|---|---|---|---|
| **primary visual anchor** `coordinate_register_twenty_point_x_v02` (n=600) | **+0.0250 [0.0033, 0.0467] MOVED** | **+0.0250 [0.0050, 0.0467] MOVED** | **+0.0233 [0.0017, 0.0433] MOVED** | **+0.0233 [0.0033, 0.0450] MOVED** |
| oracle-localized readout `starred_series_value_nine_v07` (n=300) | +0.0300 [−0.0067, 0.0667] NOT MOVED | +0.0300 [−0.0067, 0.0667] NOT MOVED | +0.0133 [−0.0300, 0.0600] NOT MOVED | +0.0133 [−0.0300, 0.0600] NOT MOVED |
| saturated canary `header_cued_table_code_v02` (n=300) | 0.0000 NOT MOVED | 0.0000 NOT MOVED | 0.0000 NOT MOVED | +0.0067 NOT MOVED |

**Result — A2-gray (blind-trained), same six numbers:** every role NOT MOVED on
both instruments under both contracts (anchor +0.0067 / 0.0000, readout +0.0167 /
+0.0133, canary −0.0033 / −0.0067 with CIs touching zero).

**Branches.** A1-real fires registered branch **(d) anchor MOVED, readout NOT
MOVED** on R19 *and* on R20, under lenient *and* strict — a clean 4-way
replication. A2-gray fires **(c) neither MOVED**, likewise 4-way. The two
contracts agree everywhere; the canary holds everywhere (no damage flag).

**Insight (H-C6, mechanism × scale).** *At 3B the movable layer was the
oracle-localized readout and the primary visual anchor was immovable by every
recipe we tried. At 7B that ordering reverses: the anchor moves and the readout
does not.* This is the first result in the program where an RLVR arm moves the
**primary visual anchor** on a held-out counterfactual instrument at all. The
A2-gray control is what makes it a content statement rather than a
format-or-competence statement: the blind-trained arm, same recipe, same steps,
same everything but real pixels, moves **neither** role. So the anchor movement
at 7B is *image-dependent* — it required real visual input to acquire.

Read together with R4 this sharpens rather than softens the program's thesis.
R4 says that on the *training* distribution the blind-attainable share grows with
scale (TrainShare 0.78–0.84 at 7B vs 0.487 at 3B). C6 says that on a *held-out*
counterfactual instrument the same 7B pair separates the arms in the opposite
direction: only the sighted arm moves the visual anchor. Different estimands,
different corpora, and no cross-scale or cross-corpus statistic is computed here
— but jointly they locate exactly where visual content does and does not get
bought, and they say the answer depends on scale.

**Scope, stated plainly.** One seed, one 7B training pair; every number carries
the one-seed tag. The anchor effect is small in absolute terms (+2.3 to +2.5
points) against a strong base (0.757–0.785), and its interval clears zero without
a wide margin — what carries it is that the *same* branch replicates on an
instrument sharing no items, under both contracts, while the blind arm's does
not. Branch (d) was named in the registration precisely so it could not be
folded into (a) or (b), and it carries **no pre-committed interpretation**: the
reading above is descriptive, and C6 re-decides neither Gate 1 nor R4.

Artifacts: `reports/c6_mechanism_at_scale_v1.{json,md}`;
instrument `scripts/build_c6_mechanism_at_scale_readout.py`;
fixtures `tests/test_build_c6_mechanism_at_scale_readout_fixture.py` (61 passed).
Cell pointers `logs/c6_cells/`, generation log `logs/c6_cells_chain.log`.

*Fixture note (an instrument bug caught before any real cell was read):* the
adversarial suite refused the instrument's own payload — its acceptance-check key
`check_13_i13_labelling_and_no_shard_quantities` contained the substring "shard",
which the I13 guard forbids in any emitted key. Renamed to
`check_13_i13_labelling` with the full statement moved into the value (values are
not scanned), so the guard stays universal rather than being exempted. This is
what "fixtures before data" is for.

**Independent reproduction — all 24 registered numbers agree exactly
(2026-08-11T15:41Z).** The C6 report was re-derived by a second instrument
authored independently against the same registration, with no sight of the first
instrument's source: different internal layout and different key names, but the
same registered engine (`compare_rows`, seed 20260712, 2,000 draws), the same
16 acceptance checks, and its own 24-case adversarial fixture suite (green before
it touched a real cell). Every one of the four contrasts × three roles × two
contracts matches to floating-point equality on all six reported quantities —
base level, arm level, arm−base, both CI bounds, and the MOVED / NOT MOVED
decision — and every branch reading and twin-replication verdict is identical.
Branch (d) for A1-real on both instruments under both contracts, branch (c) for
A2-gray, canary clean: reproduced independently.

Two details make that reproduction worth more than a rerun. The two instruments
were written from the registration alone, so the agreement tests the
*registration's* determinacy, not just the code's. And they converged on the same
latent trap without communicating: the second instrument's I13 guard also
initially refused its own acceptance-check key for containing the substring
"shard", and was fixed the same way — the guard stays universal, the prose moves
into the value. A registration that induces the same bug and the same fix in two
independent implementations is specified tightly enough to be reproducible.

Reproduction artifacts:
`reports/c6_mechanism_at_scale_v1_independent_replicate.{json,md}`;
instrument `scripts/build_c6_mechanism_at_scale_readout.py` (the second author's,
now the file at that path);
fixtures `tests/test_build_c6_mechanism_at_scale_readout_fixture.py` (24 passed).

*Why it was run, recorded (no estimand affected).* Two drivers advanced C6
concurrently on shared storage. A file copy at 15:39:57Z replaced
`scripts/build_c6_mechanism_at_scale_readout.py` with the second author's version
about ninety seconds after the first had written
`reports/c6_mechanism_at_scale_v1.json` at 15:38:00Z. The banked report and all
six cells were untouched, but the instrument that produced the report no longer
existed to re-run, so reproducibility could not be shown by byte-identity and was
established by independent result agreement instead — which is the stronger of
the two demonstrations, though it was not the one that was planned. Cost, stated:
the first instrument's source is not recoverable, so the ledger's reproduction
command names the second. The values in this section are the banked report's and
are unchanged by any of it.

**Third check, orthogonal to both instruments — and it closes off the format
explanation.** Both readouts compute pair success by calling
`fliptrack_metrics.pair_score`, which *re-derives* correctness from
`prediction_a`/`prediction_b` at readout time. That shared code path is a common
mode: if it were wrong, two independent instruments would agree and both be
wrong. So the levels were recomputed a third way, from the `pair_correct` /
`strict_pair_correct` fields written into each row at **generation** time, as
plain arithmetic with no re-scoring
(`scripts/verify_c6_stored_fields.py`). All eighteen per-role levels and all
twelve role × contract arm-minus-base deltas reproduce exactly; 7,200 rows
checked with **zero** internal field disagreements; R19 ∩ R20 = 0 pair_ids
confirmed independently.

That check surfaced something the branch reading did not need but strongly
benefits from: **strict and lenient are identical on the anchor and the readout
roles in all six cells** (0.7850/0.7850, 0.8100/0.8100, 0.6733/0.6733, …), while
the canary separates (0.9933 lenient vs 0.9800 strict). Registration §6 excluded
the 2026-07-10 base cells partly *because* their strict channel was degenerate,
so this pattern had to be distinguished from that failure rather than assumed
benign. Reading contract validity directly settles it
(`scripts/verify_c6_contract_validity.py`):

| role | contract validity, all six cells | strict−lenient gap |
|---|---|---|
| primary visual anchor (600) | **1.0000** (every cell, every model) | 0.0000 |
| oracle-localized readout (300) | **1.0000** (every cell, every model) | 0.0000 |
| saturated canary (300) | 0.9867 – 0.9967 | 0.0033 – 0.0133 |

The strict channel is **live and discriminating** — it separates on the canary in
five of six cells — and format compliance is simply *saturated* at 7B on the two
roles that carry the branch decision.

**Insight (H-C6b, the format explanation is arithmetically excluded here).**
The single most persistent alternative explanation in this program has been that
apparent gains are output-format compliance rather than visual content: F8's
+0.07 generation-strict gap decomposed exactly to contract validity (residual
1e−17); E1b's strict external gains tracked `Format_valid` step for step; Gate 1
found a fifth independent format localisation. On the C6 anchor there is
**nothing left for format to contribute** — validity is pinned at 1.000 for base
and both arms, so the strict and lenient channels are the same measurement — and
the anchor still moves +0.0250 for the sighted arm and +0.0067 (NOT MOVED) for
the blind one. Whatever A1-real acquired at 7B, it is not compliance. This does
not upgrade branch (d) into a registered claim — it remains the unregistered cell
of the 2×2, one seed, one training pair — but it removes the explanation that
would otherwise have to be excluded before anyone could take it seriously.

---

## 2026-08-11 — Track-4 premise-v2 acceptance gates: E4 PASS, E1 FAIL (branch c), E2 FAIL on the final clause, E3 not caption-leaky — all four gates run

**E4 — attacker check: PASS.** DINOv2, pixel-frequency and metadata attackers
over the packaged 160-pair / 320-member release, 5-fold grouped CV by pair.
The instrument's registered gate is `status: true` on all three checks —
`all_attackers_available`, `all_point_estimates_at_most_0_55`,
`no_ci_upper_above_0_62`. Largest folded statistic 0.5460 (frequency_stat
pooled), largest CI upper 0.5755. DINOv2 reaches train AUC 1.0 on every fold and
still lands at OOF 0.529 — it memorises the training folds and transfers nothing
across pairs, which is exactly what an artifact-free release looks like.

*Criterion note (worth carrying).* The registration's prose criterion reads
"every attacker's side-prediction accuracy 95% bootstrap CI includes 0.5", but
`src/fliptrack/artifact_attackers.py` folds the statistic to `max(AUC, 1−AUC)`
(line 228) before taking percentiles, so the interval lives on [0.5, 1] **by
construction** and cannot include 0.5 for any attacker, signal or noise —
`metadata`'s point estimate 0.4994 sits below its own CI lower bound 0.5002,
which is the tell. The operative criterion is therefore the folded one the
instrument implements and records (≤0.55 point, ≤0.62 CI upper), and E4 passes
it comfortably. The prose should be reconciled to the folded statistic in the
next registration revision; no number changes.
Artifact: `reports/track4_premise_v2_attacker_gate_v1.json`,
log `logs/track4_gates/e4_attacker_gate.log`.

**E1 — difficulty band: FAIL, branch (c) "still too hard".** Carrier
`chained_premise_easy`, premise member accuracy on real images = **0.2875**
(23/80), target band [0.40, 0.60]. Both contracts agree. The registered branch
(c) fires: one pre-committed step to `n=5`.

**Insight (H-T4a, the lever did not lever).** The easier variant dropped the
coordinate register from n=20 to n=8 — a 2.5× smaller search — and premise
solvability moved from the P0.1 anchor 0.275 to 0.2875. Essentially nothing.
Whatever makes this premise hard is **not** the size of the candidate set, so
shrinking it further to n=5 is a weak lever; the registered step should be taken,
but the diagnosis it will produce matters more than the number.

**E2 — blind floor: premise clause PASSES everywhere, final clause FAILS
everywhere.** Blind (gray and no_image) **premise** member accuracy is exactly
**0.000** for all four premise-bearing types, against ceilings 0.105 (n=20) and
0.286 (n=8) — the strongest possible pass. Blind **final** member accuracy
exceeds the registered 0.133 ceiling for all five types:

| type | blind final member acc (gray = no_image) | ceiling | verdict |
|---|---|---|---|
| `chained_premise` | 0.250 | 0.133 | FAIL |
| `chained_premise_easy` | 0.225 | 0.133 | FAIL |
| `premise_transition_easy` | 0.225 | 0.133 | FAIL |
| `fact_read` | 0.200 | 0.133 | FAIL |
| `premise_transition` | 0.1375 | 0.133 | FAIL |

**Insight (H-T4b, the leak is degenerate, not visual).** Blind *pair* accuracy is
0.000 and blind collapse rate is 1.000 across every failing cell: the blind model
emits one constant answer for both members and is never right about a pair. What
clears the 0.133 member ceiling is that constant colliding with a non-uniform
gold distribution over the 15 offsets — a **generator** property (answer
balance), not a visual leak, and the premise clause's exact 0.000 confirms the
new construct itself is blind-unsolvable as designed. The registered consequence
still binds — the failing types are excluded from training use until revised —
but the fix is to balance the final-answer distribution, and the construct that
Track 4 was built to test is the part that already works.

Artifacts: `reports/track4_premise_v2_gate_readout_v1.{json,md}`;
instrument `scripts/build_track4_premise_v2_gate_readout.py`;
fixtures `tests/test_build_track4_premise_v2_gate_readout.py` (26 passed).

**E3 — caption stress: COMPLETE. The batch is not caption-leaky — and for four
of five types a caption is *worse* than no image at all.** The registered
captioner command ran verbatim over all of `$DATA/images` (640 files / 480
distinct sha256) on an29 GPU 3, 1,680 s, status complete. The merge received a
coverage manifest whose hash set is exactly those 480, so
`merge_caption_rows`' exact-coverage assertion still ran and reported
`coverage_complete=true` — no override, no registered code touched. Restriction
to the 320-member causal release happened one step later at
`build_caption_qa_pairs.py --allow-extra-captions` (160 pairs / 320 members
built; the 160 non-causal captions carried and unused), then the 3B caption-QA
FlipTrack eval.

Per-type, both contracts, never merged (I7); nothing pooled across types (I13):

| type | n | caption member acc (lenient = strict) | blind floor (E2) | **caption − blind** | ceiling (a) 0.233 | ceiling (b) floor+0.10 |
|---|---:|---:|---:|---:|---|---|
| `fact_read` | 20 | 0.0750 | 0.200 | **−0.1250** | PASS | PASS |
| `premise_transition` | 40 | 0.1125 | 0.1375 | **−0.0250** | PASS | PASS |
| `premise_transition_easy` | 40 | 0.2125 | 0.225 | **−0.0125** | PASS | PASS |
| `chained_premise` | 20 | 0.2250 | 0.250 | **−0.0250** | PASS | PASS |
| `chained_premise_easy` | 40 | 0.2625 | 0.225 | **+0.0375** | **FAIL** | PASS |

*The one thing the registration leaves open, reported rather than decided.*
Section 7's "caption member accuracy ≤ blind-floor threshold + 0.10" does not say
which blind-floor threshold. Reading **(a)** takes E2's registered literal 0.133,
giving a 0.233 ceiling; reading **(b)** takes each type's own *measured* blind
final member accuracy. Under (a) one type fails; under (b) all five pass. Both
are reported and the choice is the PI's — the instrument does not pick.

**Insight (H-T4c, the caption tells the model nothing, and often misleads).**
The registered quantity E3 exists to bound is what a caption *buys* over
blindness, and that increment is at or below zero for **four of the five types**
(−0.125 to −0.0125) and +0.0375 for the fifth — every one of them far inside the
registered 0.10 margin. These renders are coordinate registers; a 7B captioner
cannot serialize twenty labelled point positions accurately, and a confidently
wrong caption is worse than the prior-driven constant a blind model falls back
on — which is exactly the shape of a −0.125 on `fact_read`, the pure reading
control. So the single FAIL under reading (a) is **not** caption leakage: at
+0.0375 over blind, `chained_premise_easy` clears the 0.233 line only because its
blind floor was already 0.225, i.e. the same degenerate final-answer imbalance
E2 diagnosed. Reading (a) partly re-measures E2's generator defect; reading (b)
isolates what E3 is actually about. **Balancing the final-answer distribution
should clear E2 and E3 together**, and no caption-side revision is indicated.

Taken with E2, the construct now has two independent clean bills: the premise
clause is blind-unsolvable at exactly 0.000, and the items are not caption-
solvable either. The one defect is a fixable property of the answer sampler.

Artifacts: `reports/track4_premise_v2_e3_readout_v1.{json,md}`; instrument
`scripts/build_track4_premise_v2_e3_readout.py`; fixtures
`tests/test_build_track4_premise_v2_e3_readout.py` (14 passed, green before the
instrument read a real cell). Predictions
`experiments/runs/track4_premise_v2_e3_an29_20260811T155104Z/finish_20260811T162332Z/`;
caption store `…_caption_store_an29_20260811T155104Z` (480 rows); merge
`experiments/runs/caption_store_merge_track4_premise_v2_dev_v1_20260811T162332Z`.
Logs `logs/track4_gates/e3_caption_stress.log` (stage A) and
`logs/track4_gates/e3_finish_from_banked_captions.log` (stages B–D).

*One-line bug fixed to unblock the gate:*
`scripts/launch_caption_store_merge.sh` guarded arity with `$# -lt 4`, i.e.
RUN_TAG + RELEASE_MANIFEST + **two or more** shards, so it rejected the
single-shard merge the registered E3 command produces and exited 2 with a usage
message. Corrected to `-lt 3`. The captioner pass was **not** re-run: stages B–D
were completed from the banked shard by
`scripts/e3_finish_from_banked_captions.sh`, using the same underlying commands
the aborted runner had already logged verbatim.

*Concurrency incident, recorded (no E3 verdict affected — none had been
produced).* A second E3 driver captioned the same 480 images on an29 GPUs 0–3 in
4 shards, completing at 15:47:59Z
(`experiments/runs/t4v2_e3_caption_store_an29_20260811T152952Z`), while holding
GPU claims on those four devices. The registered runner's guard did exactly its
job: it refused to launch against the held GPUs twice (15:46:38Z, 15:47:51Z) and
wrote a `…failed_*.json` provenance stub each time rather than colliding. The
second driver's own chain then died between stages when its script file was
overwritten at the same path — bash re-reads a running script at its saved byte
offset, so the next boundary landed mid-sentence in the replacement file's
prose and aborted at "line 79: syntax error" — leaving its captions banked and
its merge / QA-build / eval stages unrun. Its claims were released and the
registered runner relaunched from a snapshot outside the repo so the same
overwrite cannot recur. The duplicate caption store is redundant rather than
contradictory (same registered command, same image set, same captioner) and
enters no gate. Two operational lessons, both already program invariants
elsewhere: run long shell chains from an immutable copy, and give concurrent
drivers distinct script paths.

---

## 2026-08-16 — Consolidation round: E1 PASSES at n=5, E3 clean under both readings, E2's blind leak re-diagnosed as a lenient-class collision; E4 wording resolved; storage rule applied; Stage-2 cancelled

*Per the PI dispatch of 2026-08-16 and EXPERIMENT_TODO PART 5. Ledger rows in
`reports/main_progress.md` §"Consolidation round"; task-level provenance in the
artifacts below.*

**Two-seed R3 readout — the R3 rung upgrades to the registered two-seed
estimator.** All four M7 seed-2 arms complete with held-out evals banked
(4,239 paired items each; a2_gray and a3_caption landed 2026-08-16 after the
08-15 operational failures were fixed). Registered estimator
(`docs/registered_m7_amendment_v1.md:52`: seed mean taken per item before any
stratum mean, ratio, rank statistic, or bootstrap; schema
`blind-gains.m7-r3-readout.v2`, status complete; A1 denominator stable;
0/5,000 undefined draws in all nine bootstrap intervals that can carry them —
the recovery and rank statistics; the gain and anchor-difference intervals are
means and cannot be undefined):

- **Corpus-aggregate gains** (two-seed mean, 95% CI): A1 real **+0.2044**
  [0.1898, 0.2189] · A2 gray **+0.1485** [0.1359, 0.1615] · A2b no-image
  **+0.1458** [0.1332, 0.1583] · A3 caption **+0.1807** [0.1673, 0.1939].
- **Aggregate recovery vs A1**: A2 gray **0.7265** [0.6592, 0.7961] · A2b
  **0.7132** [0.6483, 0.7844] · A3 caption **0.8840** [0.8091, 0.9632].
- **Registered secondary** (informed comparison, disclosed in the
  registration): ViRL recovery above the geo3k seed-1 anchors — A2 gray
  0.7265 vs 0.0789, difference **+0.6476** [0.5803, 0.7172]; A2b 0.7132 vs
  0.1184, **+0.5948** [0.5299, 0.6660]; both registered directions hold.
- **Rank statistics** (22 eligible strata): ρ_gain fails its registered
  direction (> 0) for all three blind arms — a2_gray −0.2253 [−0.3924,
  −0.1078], a2b −0.3077 [−0.4579, −0.1666], a3 −0.7403 [−0.8125, −0.5709] —
  the seed-1 pattern (gains track headroom) reproduces under the two-seed
  estimator; ρ_recovery point-positive with direction holding for a2_gray
  +0.4226 [−0.0030, 0.6079] and a2b +0.2917 [−0.0497, 0.6051]; a3 −0.0346
  [−0.4361, 0.3086], direction fails.
- **Seed dispersion** (descriptive; n_seeds = 2, no seed-level claim
  registered or made): per-arm corpus-gain differences (seed1 − seed2)
  ≤ 0.0156 in magnitude; aggregate-recovery differences ≤ 0.0639.

Artifacts: `reports/m7_r3_readout_v2.{json,md}`,
`reports/m7_r3_readout_v2_artifacts/`; command in §21 block M. The JSON is the
artifact of record for the recovery CIs — the `.md` renderer prints them as
`[NA]` (renderer defect in `scripts/build_m7_r3_readout.py`, queued, numbers
unaffected). **LH2 stage-1 seg-1**: gates passed 2026-08-16T17:22:33Z, seg-1
launched 17:22:36Z (`lh2_seed2_seg1_an12_20260816T172233Z`, an12 0–3, steps
0 → 50 of the segmented 0 → 200 stage) once the gpu-7 eval cleared the
chain's gate.

**dev_v2 regeneration (one-shot) — the approved branch-(c) n=5 step and the
registered answer-balance constraint, executed together.** Registration first:
`docs/registered_hier_benchmark_v1.md` (full HB.0 content + §8 balance
constraint, max per-value gold share ≤ 0.10) merged at `2248c7f` before any
item existed. Builder `scripts/build_track4_premise_v2_dev_batch_v2.py`
(reuses the frozen v1 geometry/renderer paths; overrides recorded): 160
groups, counts unchanged (40/40/40/20/20), easy types at n_points 5
(`t4v2_coordinate_register_n5_v1`), n=20 types unchanged, batch seed 20260816,
zero scene-program collisions with v1, zero image collisions with frozen B1,
from-disk verification 0 problems over 640 rehashed images
(`reports/track4_premise_v2_dev_v2_verification.json`; the verifier was
parameterized first — its pre-fix form had no argparse and silently ignored
arguments, so it would have re-verified v1; caught by this round's adversarial
verification pass). Balance held exactly: max
per-value share ≤ 0.1000 every type (support k = 13–14); balance rejections
4–25 per type inside the deterministic attempt stream. Batch:
`data/track4_premise_v2_dev_v2`; build report
`reports/track4_premise_v2_dev_v2_build_v1.json`. The v1 batch is untouched.

**E1 — difficulty band: PASS, both contracts.** `chained_premise_easy` premise
member accuracy **0.5125** (lenient = strict), inside the registered
[0.40, 0.60] band → branch **(a) band hit** fires at the branch-(c)
re-measure: **n=5 is frozen** as the curriculum entry difficulty, no further
lever moves. Secondary `premise_transition_easy` 0.4750, also in band.
`reports/track4_premise_v2_gate_readout_v2.{json,md}`, composition enforced as
`registered-v2-branch-c`.

**E2 — blind floor: FAIL persists on all five types, and the mechanism is now
fully pinned.** Blind final member accuracy 0.150–0.200 vs the registered
0.133 ceiling (gray = no_image, lenient = strict); blind **pair** accuracy
0.000 and blind **premise** accuracy 0.000 everywhere. The blind model still
collapses to the constant `-1` (every gray-cell prediction for four of five
types — 80/80 or 40/40 per type; `fact_read` 32/40 in gray and fully constant
under no_image); the
registered per-value balance cap did its registered job — a constant can
harvest at most 0.10 per gold value — but the **tier-1 lenient matcher scores
gold `1` correct against extracted `-1`** (verified: 30/30 golds `1` and 30/30
golds `-1` marked correct in the gray final cell, every other gold 0), so one
constant harvests two value-classes: 0.10 + 0.10 = 0.20 (0.15 for
`premise_transition`, whose class shares are 0.075 + 0.075). Registered
consequence binds: the five types remain **excluded from training use**; the
revision fork (lenient-class-aware cap / sign-unambiguous answer support /
matcher-tier change) is the PI's (§19). One-shot discipline: no further
regeneration this round.

**E3 — caption stress on dev_v2: PASS, all five types, BOTH readings — the
`chained_premise_easy` indeterminacy resolves.** Caption member accuracy vs
ceilings: `chained_premise` 0.1750, `chained_premise_easy` **0.2000**,
`fact_read` 0.1000, `premise_transition` 0.1375, `premise_transition_easy`
0.1625 — every type under the registered-literal ceiling 0.233 (reading (a),
unmodified) and under its measured floor + 0.10 (reading (b); floors from the
v2 E2 cells: 0.20/0.20/0.20/0.15/0.20). Full pipeline re-run:
`reports/track4_premise_v2_e3_caption_stress_run_provenance_v2.json`, readout
`reports/track4_premise_v2_e3_readout_v2.{json,md}`.

**E4 — wording resolved; criterion untouched, verdict unchanged.** The
attacker instrument was extended to compute UNfolded directed-AUC CIs from the
same bootstrap draws as the folded ones and to persist per-member OOF scores
(previously discarded in memory). Deterministic re-run (seed 20260710)
reproduced **every v1 folded number exactly, dinov2 included**. Literal
"CI includes 0.5", per attacker: all six per-template scopes include 0.5
(dinov2 n20 [0.4756, 0.5366], n8 [0.4706, 0.5433]; frequency_stat n20
[0.4966, 0.5780], n8 [0.4828, 0.5467]; metadata n20 [0.4922, 0.5064], n8
[0.4881, 0.5072]); the two pooled scopes that exclude it are dinov2
[0.5080, 0.5527] and frequency_stat [0.5164, 0.5755]; metadata pooled includes
it [0.4967, 0.5074]. The operative folded gate (≤ 0.55 point, ≤ 0.62 CI
upper) is unmodified and still PASS.
`reports/track4_premise_v2_e4_wording_resolution_v1.{json,md}`,
`reports/track4_premise_v2_attacker_gate_v2_unfolded.json`, per-item scores
`reports/track4_premise_v2_attacker_oof_scores_v1.jsonl` (1,920 rows).

**Storage rule applied (PI decision; replaces the 08-14 menu).**
**854,949,371,942 bytes** deleted across 65 `global_step` dirs in 20 runs
under the mechanical rule (delete non-terminal steps not §21-referenced; keep
terminal + best + every §21-referenced step; three-tier §21 resolution
committed in `scripts/apply_storage_retention_rule_20260816.py`); 39 step dirs
kept; one tracker-less pilot run skipped fail-closed; `m7/` and `lh2/`
untouched. Byte-exact record appended to `reports/storage_cleanup_20260814.md`.
After: used 1.217 TB / free 1.531 TB under the 2.5 TiB soft quota;
`checkpoints/` 1,003 G.

**Infra fixes (dispatch item 1; each ships an I10 fixture the pre-fix code
fails).** (1a) `scripts/measure_storage_usage.py` now writes `status:"fail"`
when used > quota — the live snapshot had carried `free_bytes:
-461,684,596,736` with `status:"pass"` because the Jul-19 refresh-loop process
predated the 2.5 TiB constant; loop restarted (new run
`storage_snapshot_refresh_loop_login_20260816T084012Z`), snapshot now truthful
(quota 2,748,779,069,440). The checkpoint guard raises
`StorageQuotaExhaustedError` immediately on used ≥ capacity instead of
retrying forever; transient headroom refusals keep the 300-s retry. (1b)
`scripts/chain_wait_helper.py`: waiters now score an ACTIVE deadline —
alive-but-storage-stalled reads WEDGED (visible, clock paused), dead chains
stop loudly; both canonical waiters retrofitted. (1c) the E3 STAGE-B defect
was the merge-launcher arity check, fixed at `da0751d` without its fixture;
the fixture now exists (`tests/test_launch_caption_store_merge_arity.py`).
Test files: `tests/test_measure_storage_usage.py`,
`tests/test_easyr1_checkpoint_guard.py`, `tests/test_storage_guard.py`,
`tests/test_chain_wait_helper.py` — storage suites 33 passed (those three
plus the conservative-snapshot and refresh-loop suites), waiter + arity
fixtures 9 passed (6 + 3).

**Operational recovery of the 08-15 chain outcomes** *(operational finding,
not a result)*. Both re-armed chains fired on time on 08-15 and both evals
failed: a3_caption exited 127 because
`${caption_env:+VIRL_CAPTION_SHARDS=...}` expands into a command name (bash
fixes the assignment/command split at parse time — the caption arm had never
launched through this script); a2_gray was refused because the guard
fail-closed on a malformed claim file — the LH2 chain writes **plain-text**
claims while the m7 guard requires JSON (cross-format incompatibility,
flagged, unfixed this round). The LH2 seg-1 relaunch died at ~20 min in a
deterministic livelock: the resume-safe logger guard refused three stale
08-06 logger artifacts in a stage dir with zero banked boundaries. Fixes:
launcher env-array form (+5-test fixture,
`tests/test_launch_m7_seed2_eval_env.py`); both evals relaunched 08:25/08:26Z;
LH2 artifacts archived aside, orphan manifest closed, chain re-armed. Both
merged step-100 HF checkpoints verified (8131575808 bytes / 825 weights).

**Stage-2 3B ablation matrix — CANCELLED** (PI decision, rationale PAPER2 §5).
Repo sweep: no Stage-2 configs, launchers, or waiters exist (`configs/`,
`scripts/`, no registration) — nothing to remove; record only. The "stage 2"
inside `docs/registered_lh2_stage1_v1.md` is LH2's steps 200→400, untouched.

**New registrations and drafting support.** `docs/registered_stage3_7b_v1.md`
— ST3-7B two-arm decisive pilot, PAPER2 §5 quoted verbatim, **DRAFT,
unsigned**, no launcher. `docs/registered_hier_benchmark_v1.md` — HB.0
registration (above). `reports/paper1_numbers_table_v1.md` — M13 paper-facing
numbers table, one row per PAPER1 §3 claim, frozen slots marked (two-seed R3,
LH2 direction, C6 tier), §21 gaps listed.

## 2026-08-17 — HB P0–P2 development validation: the hierarchy is informative (family L3 floors pass; 3/7 cells clean on every gate), blind floors are hard zeros/near-chance, and the attacker gate catches a real construction artifact in the chart family before any training

*Per the 08-12 HB dispatch (P0–P2, STOP after P2). Ledger:
`reports/hier_benchmark_progress.md`; registration
`docs/registered_hier_benchmark_v1.md` + Amendments A1/A2. Instruments: the
registered FlipTrack open-form eval (I7 locked decoding) and the sha-pinned
candidate-ranking eval; 7 knob cells × 4 layers × 4 models; 150 mother-items
per family per cell, one shot, from-disk re-verification 0 problems.*

**P2.2 informativeness gates (base 3B, registered HB.7 criteria).** Family L3
floor (≥ 0.05 in ≥ 1 cell) **passes both families**. Monotone L1>L2>L3 in 6/7
cells. Cells passing every per-cell gate: coord n8 (L1/L2/L3
0.725/0.640/0.425), coord n12 (0.675/0.595/0.325), chart s9_low
(0.795/0.745/0.200). Band failures are calibration signal, not noise: s5_high
fails monotone+L1 (0.495/0.535 — the L1 cue does not rescue dense 5-series
crossings), s9_high L1 0.450, s5_low L2 0.880 (too easy), n20 L1 0.575.
Target-switch L3 (reported separately per A2): 0.040–0.370.
`reports/hier_p2_gate_readout_v1.{json,md}`.

**P2.3 blind floors are clean.** Chart L3 blind member accuracy is exactly
**0.0000 in all four cells** (gray AND no_image); every discovery probe is
0.0000; coord L3 sits at 0.1200/0.1133/0.1367 (n8/n12/n20) with gray =
no_image to four decimals — i.e., the image channel carries everything the
gates measure. `reports/hier_p23_readout_v1.{json,md}`.

**P2.3 attacker gates: coord near-clean, chart fails decisively — and the
failure is diagnosable to the constructor.** Registered criterion: folded
AUC ≤ 0.55 point and CI-upper ≤ 0.62, per attacker, pooled + per template.

- `hier_coord_v1`: pooled clean (dinov2 0.5096, frequency_stat 0.5096,
  metadata 0.5137); gate **false** by exactly one per-template point —
  dinov2 n20 folded **0.5577** (CI up 0.5897, under the CI criterion).
- `hier_chart_v1`: pooled dinov2 **0.6711** [0.6472, 0.6969], frequency_stat
  **0.6957** [0.6661, 0.7241], metadata 0.5910 — and per-template the
  low-crossing cells are near-perfectly separable: s5_low frequency **0.9819**
  (CI up 0.9962), metadata 0.9315, dinov2 0.9190; s9_low 0.7831/0.8637/0.8103;
  the high-crossing cells only graze the line (dinov2 s5_high 0.5629, s9_high
  0.5609).

**The leak is numerically pinned** (`scripts/verify_hier_leak_direction.py` →
`reports/hier_p2_leak_verification_v1.json`, causal pairs, swap-honoring):

- The chart **target_switch edit lowers the target's value at the asked x in
  200/200 pairs** — the constructor's switch edit is unidirectional by
  construction (all four cells 50/50).
- The chart **target_stable edit is direction-biased only where the attacker
  fires**: 99/100 downward in the low-crossing cells (the registered
  low-crossing FILTER kills upward proposals) vs balanced 25/25 and 20/30 in
  the high cells.
- The pixel side-channel follows: in low cells the edited side's PNG is larger
  in **198/200** pairs (cell means +1,053 to +1,521 B — banded base compresses
  well, the band-breaking edit doesn't); that is the metadata/frequency
  signal. Coord's
  stable edits are balanced and its switch is a 2-D move; its one marginal
  template (n20) shows the same size skew in miniature (38/50 smaller, mean
  −148 B).

Insight: the acceptance machinery worked exactly as designed — a brand-new
track shipped with a systematic side signature and the gate caught it at
development time, before any training or freeze. The fix (symmetrized switch
edit; band-preserving low-cell stable edits, or band-breaking jitter on both
sides) changes the registered construction, so it is a **PI-visible
registered revision cycle**, not a silent regeneration. Chart P3 is blocked
at this gate; coord's disposition (one template at 0.5577) rides the same
decision.

**P2.1 candidate-ranking readout**
(`reports/hier_p2_ranking_readout_v1.{json,md}`; mean pair MRR (top-1 rate),
14 registered sha-pinned configs × 4 models). The layer split reproduces in
ranking form: **L2 is largely solvable** — chart L2 0.8332–1.0000 MRR (base
7B a perfect 1.0000 on s5_low), coord L2 0.6363–0.8857 — while **L3 drops
sharply in every cell** (coord n8 base 3B 0.4851 vs 0.7209 at L2; base 7B
0.7760 vs 0.8777). Base 7B leads base 3B on all seven L3 cells
(0.5306–0.7965 vs 0.4033–0.6395). The Gate-1 step-120 checkpoints
(`mini_a5_std`/`cp`) sit within ±0.08 MRR of base 3B in every cell at both
layers — RL training moved no hierarchy-discovery capability, matching the
open-form picture. Caution (numbers only): the two low-crossing chart cells
the attacker flags are also the L3 cells with the highest 3B MRR (s5_low
0.6395, s9_low 0.5936, vs 0.4428/0.4033 in the high cells) — consistent with
the band-breaking edit being visually salient; the registered revision will
resolve how much low-cell L3 "discovery" rides that artifact.

**P2.4 census review package v3 → human gates queue.** Census v3
(`reports/generator_census_v3.{json,md}`): 138 manifests, 51 families, 217
variants, 84 loudly stage-unmapped; the hier cells appear as 100-pair
variants across their L1/L2/L3 stages. Package
`reports/review_packages/hier_v1_census_v3{,.zip}` (zip sha256
`4b55781197ea399300653efe6a53d157a43870035106db2161d2fa753acb1530`):
deterministic no-RNG sample per the R19/R20 discipline (first 2 mother-pairs
per cell × role — 42 pairs, 280 images, all existing layers joined by
`mother_item_id`), README + `queue.md` with four human gates (chart-v08
no-zoom [Richard, blocks chart-side P2 freeze], hier_coord legibility + cue
visibility, hier_chart review marked diagnostic-only pending the revision,
census v3 sign-off). Nothing self-certified.

**In flight at collection time**: the 72B caption-stress chain (P2.3's last
cell; §19) — its readout (`reports/hier_caption_stress_readout_v1.*`) will be
appended to this section when it lands. Post-P2 branch selection (band
recalibration, chart symmetrization, coord n20 disposition) is PI work; per
the dispatch this round reports gate outcomes as numbers only.

## 2026-08-17 — Pre-freeze cleanup: the coordinate footer was the L2 procedure printed inside every layer's image; fixed, re-rendered, re-measured — n8/n12 gates land within 0.02 of v1 (n20 shifts −0.035/−0.045) and coord n8/n12 are freeze-ready on the corrected render

*PI review directive (supersedes the immediate execution of dispatch
2026-08-16b, which stays ratified and queued). Ledger: hier ledger
"Pre-freeze cleanup" section; full report
`reports/hier_v1_prefreeze_cleanup_v1.md`.*

**What was wrong (three defects, all now guard-covered).** (1) Every
`hier_coord_v1` image carried the frozen-renderer footer *"Locate the
requested label, then read its coordinate from the numbered axes."* — the
L3→L2 decomposition handed over in-image, contradicting the L3/probe
capability contract ("the requested label" presupposes an identity-given
question). (2) The census staged variants by template-id substring and the
generic `"chart"` needle shadowed `"hier_chart"` (dead map entry): every
hier chart variant was labeled L1 with a chart-v08 doc attribution. (3) No
check anywhere inspected in-image text, and the operand audit's gates keyed
on field names hier rows don't carry — the audit silently asserted nothing
for the hier families.

**What was NOT wrong.** The layer questions themselves classify correctly
against the intended hierarchy (L1 readout / L2 grounding / L3 discovery;
probe = the selection step isolated), the switch-role L3-only design stands
(A2), and the coord mother-item construction + non-occluding cue are
untouched.

**The fix and its null result.** Hier-owned renderer with the layer-neutral
footer "Each point is identified by its printed label." (frozen module
untouched; renders pinned by fixture to differ only in the footer strip);
all 450 coord mothers re-rendered from RECORDED scenes (no RNG, cue pixel
counts reproduced exactly) into `data/hier_v1_dev_r2/`; from-disk verify
**0 problems**; 1,500/1,500 manifest rows byte-identical outside
image/provenance fields; registries rebuilt semantically identical. The full
acceptance battery re-ran on r2: **n8/n12 gates land within 0.02 of v1**
(n8 0.7050/0.6300/0.4250, n12 0.6550/0.6150/0.3300, all cell gates pass) —
for the freeze-candidate cells the instruction footer was doing no
measurable work. **n20 is footer-sensitive**: L1 −0.0450 (0.5300 vs 0.5750)
and L3 −0.0350 (0.2800 vs 0.3150); greedy decoding makes these real
image-sensitivity of the crowded 20-point scenes, not noise — additional
empirical support for its exploratory hard tier (its L1 band fails under
both renders).

**Attacker profile on r2 — the marginal moved.** Pooled clean for all four
attackers (dinov2 0.5159, frequency 0.5103, metadata 0.5136, and the new
permanent **file_size** attacker 0.5092; CI-uppers ≤ 0.5954). The gate's
sole point violation is dinov2 n12 0.5569 — on v1 it was dinov2 **n20**
0.5577. A threshold-grazing violation that jumps templates under a pure
footer re-render is fold-noise around the 0.55 line, not a stable
construction signature; disposition is the PI's.

**Caption stress re-run on r2** (72B question-blind → base-3B QA): family
member accuracy 0.2200 (v1 0.2367) — n8 0.30–0.39, n12 0.18–0.22, n20
0.08–0.15 vs blind floors 0.11–0.14. The footer removal did not collapse the
caption channel: coord caption leakage rides label/position transcription,
strongest in sparse n8 scenes. Chart (v1 batch) remains caption-resistant at
0.0413 ≈ its 0.0000 floor. Ranking on r2 reproduces the v1 structure (L3
base3b 0.4363–0.5009; base7b leads all cells 0.5686–0.7975; Gate-1
checkpoints within +0.08 — still no trained discovery).

**Census v4** (162 manifests / 52 families / 249 variants): stages now
derive from the manifest `layer` field — hier variants read L1/L2/L3/
L3-probe per manifest; attacker keys and registries are `derived-artifact`;
the shadowing bug is dead and test-pinned. v3's hier rows are superseded.

**Freeze verdict (coordinate):** ready on the r2 render for **n8 and n12**,
pending three PI-side items — the human audit (never self-certified), the
dinov2-marginal disposition, and a registered caption ceiling. n20 enters
only as the exploratory hard tier (PART 6). Chart-side: unchanged —
the ratified chart-v2 revision executes next under the corrected
conventions; direction symmetrization alone will not fix the low-cell size
leak (any band-breaking edit adds ink), so the revision pairs small-magnitude
switch edits (top-2 adjacency at the anchor x) with in-band stable edits.

## 2026-08-17b — The scorer fix, the coordinate freeze, chart-v2 by construction, and the instrument's first verdict: blind RLVR moves hierarchy discovery exactly as much as sighted RLVR

*PI dispatch 2026-08-17 (human review passed; move aggressively, fill the
GPUs). Registrations: HB Amendments A4/A5, `registered_hier_instrument_sweep_v1.md`.
Ledger rows in `reports/hier_benchmark_progress.md`; freeze record
`reports/hier_freeze_v1.md`.*

**The scorer fix changed what we were about to freeze on.** Applying the
ratified sign-aware matcher (dispatch 16b ruling 2) exposed that **721 of 785
lenient credits in the hierarchy runs were sign collisions** — gold `1` scored
correct against `-1`, because the old word-boundary guard treats `-` as a
non-word character. Re-scoring isolates the matcher properly (every row scored
twice with today's code, since banked booleans predate the earlier P0.2
equal-gold fix; `reports/matcher_v3_rescore_v1.*`):

- HB gate **outcomes hold** — coord n8 **0.685/0.605/0.330** and n12
  **0.655/0.605/0.260** still pass every HB.7 gate; n20 **0.520/0.480/0.245**
  still fails only its L1 band.
- **Blind floors halve**: 0.120/0.113/0.137 → **0.067/0.040/0.067**. The
  benchmark is stronger than it was reported to be.
- **E2 flips to PASS**: premise-v2 blind finals 0.1875 → **0.0938** against
  the registered 0.133 ceiling. The "blind leak" that has sat open since
  2026-08-11 was a scorer artifact, not a generator defect.
- Paper-1 exposure is bounded: across every FlipTrack coordinate-register cell
  the isolated matcher effect is **max |Δ| = 0.031** (b1 base −0.030, m11 real
  −0.008 to −0.015, m11 blind "none" +0.007 to +0.031); arm *differences* move
  less. M7/R3 uses the geo3k answer-reward path and is untouched.

**Coordinate family FROZEN** (`reports/hier_freeze_v1.md`) as the
**training/development instrument**: n8/n12 pass every gate, n20 is the
exploratory hard tier, the human audit is recorded as passed by the PI, and
the one attacker marginal was resolved by seed replication — the flagged
template **moves** (dinov2 n12 0.5569 → none → n20 0.5646) while pooled stays
at 0.514–0.516, so it is CV-fold noise and the family is attacker-clean.
**chart-v08 calibration is frozen** on the passed no-zoom audit.

Coord is deliberately *not* the confirmatory instrument. Caption leakage falls
monotonically with density — **0.265 / 0.150 / 0.075** for n8/n12/n20 against
A5 ceilings 0.167/0.140/0.167, i.e. caption recovery fractions **0.75 / 0.50 /
0.05** — while the L1 band fails in exactly the densest cell. No coord cell is
both informative and caption-resistant; the 9-series chart cells (caption
0.0413 vs a 0.0000 floor) carry that role, as §6 of the registration
anticipated.

**chart-v2 fixes the attacker leak by construction, not by tuning.** v1 failed
structurally: every causal edit added ink to one side (switch unidirectional
200/200; low-cell PNG larger 198/200), so symmetrising direction could not
help. In v2 (Amendment A4) **every causal edit is a transposition within a
column** — switch swaps the top-2 values at the anchor x, stable swaps the
target's value at the read x with a non-target's, invariance swaps two
non-targets — so both sides carry the **identical per-column value multiset**
and neither side is structurally "the edited one". The crossing band is now
checked on both sides (v1 checked side A only). Generated one-shot, 4 cells;
**from-disk verification 0 problems**; acceptance battery running.

**The instrument's first verdict (HB diagnostic D1,
`reports/hier_instrument_sweep_v1.*`)** — 10 already-trained checkpoints
against the frozen coordinate instrument, two-seed arms summarised by the
registered per-item seed mean:

- At 3B, **every** M7 ViRL arm lifts L3 above the frozen base by a similar
  margin — n8 base **0.3300** → real 0.3825 / gray 0.3725 / no-image 0.3675 /
  caption 0.3700; n12 0.2600 → 0.2975–0.3375; n20 0.2450 → 0.3150–0.3400.
  **Blind-trained arms move discovery as much as the sighted arm.** The
  discovery probe behaves the same way (0.705 → 0.71–0.73).
- At 7B the movement is confined to the easiest cell: n8 L3 base **0.6600** →
  real **0.7650**, gray **0.7200**; at n12 and n20 neither 7B arm moves at all
  (0.575/0.470 base vs 0.570–0.575 / 0.460).
- Scale, not recipe, is what buys discovery: base 7B doubles base 3B at L3
  (0.660 vs 0.330 at n8).

This is Paper 1's thesis reproduced on an instrument built after the claim:
RLVR's L3 gain is real but **not visual** — it survives removing the image
during training. It also sets ST3's bar: an IGPO advantage must beat the
~+0.04–0.05 generic-RLVR L3 bump that blind training already produces.


**chart-v2 acceptance: FAILED, and the failure is informative**
(`reports/hier_chart_v2_acceptance_v1.md`). The transposition construction did
what A4 claimed — every column's value multiset is identical across sides,
verifier-enforced — but the inference from that was wrong: **pixels follow line
paths, not column multisets.** In a banded low-crossing scene each series holds
its own lane ~19–24 units wide, so any level-changing edit forces two large
excursions out of the lanes: +1.9–2.2 KB on the edited side, edited-larger
**50/50 · 50/50**, and the attackers read it perfectly (s5_low frequency
**1.0000**, dinov2 0.9999). v2 is *worse* than v1 here because it moves two
values ~19–24 units where v1 moved one 5–15.

But the failures are confined to the low-crossing cells, and **`s5_high` and
`s9_high` pass every attacker per template** — the first chart cells ever to,
with the size channel a coin flip (25–28/50, ±80 B). The informativeness gates
then invert exactly: s9_low passes every gate, s5_low fails L2 (0.910, too
easy), and both high cells fail monotone and the L1 band (0.4300 / 0.2850 —
the readout layer itself). **Informativeness and attacker-resistance are
anti-correlated along the crossing-density knob**, and for a single mechanism:
visual crowding hides the edit from the attacker and the data from the model in
equal measure.

Across the whole benchmark no cell yet passes all three criteria — coord
n8/n12 are informative and attacker-clean but caption-leaky; chart-v2 s9_low is
informative and caption-resistant but attacker-leaky; the chart high cells are
clean on both adversarial axes and unreadable. `s9_low` is one criterion short,
and the only edit channel left that does not move ink is permuting series
*identity* (legend colour/style/label) rather than values — a v3 proposal, and
the PI's call, since this is the first of the two pre-committed chart failures.

## 21. Evidence & reproduction ledger (maintained)

*Convention: every collection round appends or updates its row here. Each row:
what the claim shows, where the registered definition lives, which artifacts
carry the evidence, and how to reproduce. For rows without an inline command,
the authoritative reproduction source is the report's own provenance block
(`inputs_sha256` / run-dir lists) plus its registration doc — never a
reconstructed command. All artifact paths are repo-relative on the cluster
(`/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain`); the repo
mirrors to GitHub refs `agent/gate2-recovery` = `master` = `main`.*

| claim (one line) | registration | evidence artifacts | reproduce via |
|---|---|---|---|
| F1 two-regime access matrix: blind arms flat tested-blind, ordered tested-sighted | D3 estimand registration | `reports/d3_condition_matrix_v1.json`, `gate0_stratification_v1.json` | report provenance |
| R2: anchor-recipe gains FALL by step 400 | M5 registration | `reports/m5_terminal_readout_v1.*` | report provenance |
| M5c: benchmark-flat hides huge non-visual turnover (noise floor exactly zero) | M5c task docs | `reports/m5c_*` incl. evidence ledger + noise-floor replicates | report provenance |
| R3 (two-seed, registered estimator): ViRL blind arms recover 0.71–0.88 of A1 matched (vs 0.08–0.12 geo3k); geo3k-anchor differences +0.6476 [0.5803, 0.7172] / +0.5948 [0.5299, 0.6660]; ρ_gain < 0 all blind arms, ρ_recovery point-positive gray/no-image | `docs/registered_m7_amendment_v1.md` (two-seed estimator, :52) + `docs/registered_m7_seed_scope_v1.md` | `reports/m7_r3_readout_v2.{json,md}` + `_artifacts/`; seed-1 readout retained: `reports/m7_r3_readout_v1.{json,md}` | inline cmd blocks A (seed 1) + M (two-seed) |
| R4: 7B crossed TrainShare 0.7785/0.8402 vs 0.487 at 3B — grows with scale | `docs/registered_c5_7b_access_pair_v1.md` | `reports/c5_r4_readout_v1.{json,md}` + `_artifacts/` (6 cell run dirs + per-item sha256s) | inline cmd block B |
| R5: cross-family generalization | M11 registration | `reports/m11_*` | report provenance |
| F8: CP vs matched GRPO — content ceiling holds; strict gap = format (residual 1e−17) | Mini-A5 registrations + pre-filed addendum | `reports/f8_mini_a5_endpoint_readout_v1.*`, `f8_secondaries_v1.md` | report provenance |
| Catch-stability (cp/member): invariance at ceiling; strict gap = format | `docs/registered_mini_a5_catch_stability_v1.md` (scorer + test sha256-pinned) | `reports/mini_a5_catch_stability_readout_v1.*`, `mini_a5_catch_run_provenance_v1.json` | report provenance |
| Gate 1: no axis (data/selection/relational reward) buys held-out content; oracle readout moves under every recipe | `docs/registered_mini_a5_gate1_completion_v1.md` (§8 sealing, §9 acceptance) | `reports/mini_a5_gate1_acceptance_audit_v1.{json,md}`, `mini_a5_gate1_endpoint_readout_v1.json`, `mini_a5_catch_stability_{std,necessity}_v1.json` | inline cmd blocks C–E |
| E1b/E1c: blind gain does not transfer out of domain; blind columns across 7 benchmarks | E1b access-matrix registration | `reports/e1b_*`, `e1c_blind_columns_v1.*`, `chance_corrected_retention_v1.*` | report provenance |
| C6: at 7B the real-image arm moves the primary visual anchor (+0.025/+0.023, CIs exclude 0, both contracts, both instruments) and the readout does not; the blind arm moves neither | `docs/registered_c6_mechanism_at_scale_v1.md` (filed pre-read; §7 estimands, §8 branches, §9 checks) | `reports/c6_mechanism_at_scale_v1.{json,md}` (report of record); independently reproduced, all 24 registered numbers exact, by `reports/c6_mechanism_at_scale_v1_independent_replicate.{json,md}`; cell pointers `logs/c6_cells/`, gen log `logs/c6_cells_chain.log` | inline cmd block F |
| E4: premise-v2 release carries no transferable artifact signal (folded gate 0.546 max, CI upper 0.576 max) | `docs/registered_track4_premise_v2_design_v1.md` §7-E4 | `reports/track4_premise_v2_attacker_gate_v1.json`, `logs/track4_gates/e4_attacker_gate.log` | inline cmd block G |
| E1/E2: premise clause blind-unsolvable (0.000); final clause leaks a degenerate constant above the 0.133 ceiling; difficulty branch (c) fires at 0.2875 | `docs/registered_track4_premise_v2_design_v1.md` §7-E1/E2, §5 branches | `reports/track4_premise_v2_gate_readout_v1.{json,md}`, cells under `experiments/runs/track4_premise_v2_gates_an29_20260811T095522Z` | inline cmd block H |
| E3: the batch is not caption-leaky — caption minus blind ≤ 0 for four of five types, +0.0375 for the fifth; all five pass against their own measured floor + 0.10, one fails the registered literal ceiling for an E2-inherited reason | `docs/registered_track4_premise_v2_design_v1.md` §7-E3 | `reports/track4_premise_v2_e3_readout_v1.{json,md}`, caption store `experiments/runs/track4_premise_v2_caption_store_an29_20260811T155104Z`, merge `…caption_store_merge_track4_premise_v2_dev_v1_20260811T162332Z`, predictions under `…track4_premise_v2_e3_an29_20260811T155104Z/finish_20260811T162332Z/` | inline cmd block I |
| E4 wording resolution: literal "CI includes 0.5" holds in every per-template scope for all three attackers; excluded only by pooled dinov2 [0.508, 0.553] and pooled frequency_stat [0.516, 0.576]; v1 folded numbers reproduced exactly; folded criterion and verdict untouched | `docs/registered_track4_premise_v2_design_v1.md` §7-E4 + PI decision 2026-08-16 (EXPERIMENT_TODO PART 5) | `reports/track4_premise_v2_e4_wording_resolution_v1.{json,md}`, `track4_premise_v2_attacker_gate_v2_unfolded.json`, `track4_premise_v2_attacker_oof_scores_v1.jsonl` | inline cmd block J |
| E1/E2 on dev_v2 (branch-(c) n=5 + registered balance cap, one-shot): E1 PASS both contracts (0.5125 in [0.40, 0.60], branch (a) — n=5 frozen); E2 FAIL all five (0.15–0.20 vs 0.133) via the tier-1 lenient class collision (constant `-1` harvests golds `1` and `-1`; per-value cap held at 0.10; blind pair acc 0.000) — exclusions stand | `docs/registered_track4_premise_v2_design_v1.md` §5/§7 + `docs/registered_hier_benchmark_v1.md` §8 | `reports/track4_premise_v2_gate_readout_v2.{json,md}`, `track4_premise_v2_dev_v2_build_v1.json`, cells under `experiments/runs/track4_premise_v2_gates_an29_20260816T090907Z` | inline cmd block K |
| E3 on dev_v2: PASS all five types under BOTH readings — `chained_premise_easy` 0.2000 ≤ 0.233 (reading (a), unmodified) and ≤ 0.300 (measured floor + 0.10); the v1 indeterminacy resolves | `docs/registered_track4_premise_v2_design_v1.md` §7-E3 + `docs/registered_hier_benchmark_v1.md` §8 | `reports/track4_premise_v2_e3_readout_v2.{json,md}`, provenance `track4_premise_v2_e3_caption_stress_run_provenance_v2.json`, run dirs `experiments/runs/track4_premise_v2_e3_an29_20260816T091115Z` + caption store/merge siblings | inline cmd block L |
| HB P2.2 informativeness (base 3B): family L3 floor PASS both families; monotone 6/7 cells; all-gates cells coord n8/n12 + chart s9_low; band failures s5_high/s9_high/s5_low/n20 as listed | `docs/registered_hier_benchmark_v1.md` §7 + Amendments A1/A2 | `reports/hier_p2_gate_readout_v1.{json,md}`; open-form run dirs `experiments/runs/hier_p2_openform_*_20260816T2109*` | report provenance |
| HB P2.3 blind floors: chart L3 0.0000 all cells, probes 0.0000, coord L3 0.1133–0.1367 with gray = no_image | `docs/registered_hier_benchmark_v1.md` §7 (P3-freeze prerequisite) | `reports/hier_p23_readout_v1.{json,md}`; run dirs `hier_p2_openform_base3b_{gray,no_image}_*_20260816T2244*` | report provenance |
| HB P2.3 attacker gates: coord pooled clean (≤ 0.5137), gate false only via dinov2 n20 0.5577; chart fails decisively (pooled freq 0.6957; s5_low freq 0.9819) — leak pinned: switch edit unidirectional 200/200, low-cell stable 99/100, PNG size 198/200 | premise-v2 attacker criterion (folded ≤ 0.55 / CI-up ≤ 0.62) carried by `docs/registered_hier_benchmark_v1.md` §7 | `reports/hier_p2_attacker_gate_hier_{coord,chart}_v1.json`, `reports/hier_p2_leak_verification_v1.json`, `reports/hier_p23_readout_v1.{json,md}`; releases `data/hier_v1_dev/attacker_release_*` | `scripts/verify_hier_leak_direction.py` + report provenance |
| HB P2.4 census review package v3: census 138 manifests / 51 families / 217 variants / 84 stage-unmapped; deterministic 42-pair sample; 4-gate human queue | R19/R20 audit-package discipline; `docs/registered_hier_benchmark_v1.md` §7 (HB.8) | `reports/generator_census_v3.{json,md}`, `reports/review_packages/hier_v1_census_v3{,.zip}` (zip sha `4b55781197ea…1530`), `reports/hier_census_review_package_v3.json` | `scripts/build_hier_census_review_package.py` |
| HB P2.1 candidate-ranking: L2 largely solvable (chart 0.8332–1.0000 MRR), L3 drops sharply every cell (base 3B 0.4033–0.6395); base 7B leads all L3 cells; Gate-1 step-120 checkpoints within ±0.08 of base 3B everywhere; low-crossing L3 elevation coincides with attacker-flagged cells | `docs/registered_hier_benchmark_v1.md` §7 | `reports/hier_p2_ranking_readout_v1.{json,md}`; run dirs `hier_p2_ranking_*_20260816T212*` | report provenance |
| HB caption stress (v1 batch): coord 0.2367 vs floors 0.11–0.14 (modest label/position leakage, strongest n8); chart 0.0413 ≈ 0.0000 floor — caption-resistant | `docs/registered_hier_benchmark_v1.md` §7 (HB.8 prerequisite; ceiling unregistered) | `reports/hier_caption_stress_readout_v1.{json,md}`; store `strong_caption_store_hier_v1_l3_an29_20260817T021703Z` | report provenance |
| Pre-freeze cleanup: coord footer (in-image L2 procedure) neutralized + r2 re-render (scenes untouched, verify 0 problems, 1500/1500 rows identical outside image fields); every gate within 0.02 of v1; attacker marginal moved templates (dinov2 n12 0.5569 vs v1 n20 0.5577 — fold noise); file_size attacker permanent (coord pooled 0.5092); census v4 stages by layer field; coord n8/n12 freeze-ready on r2 pending human audit + marginal disposition + caption ceiling | Amendment A3 in `docs/registered_hier_benchmark_v1.md` + PI review directive 2026-08-17 | `reports/hier_v1_prefreeze_cleanup_v1.md`, `hier_coord_r2_rerender_v1.json`, `hier_r2_{gate,p23,ranking,caption_stress}_readout_v1.*`, `hier_r2_attacker_gate_hier_coord_v1.json`, `generator_census_v4.{json,md}`, `data/hier_v1_dev_r2/` | `scripts/rerender_hier_coord_r2.py` + report provenance |
| Blind diagnostics (descriptive): chart blind 0.0000 for all 4 models × gray/no_image; coord floors ≤ 0.09 (base-7B lowest); ranking no_image floors quantify the image-free candidate prior | PI utilization directive 2026-08-17 | `reports/hier_blind_diagnostics_v1.{json,md}`; run dirs `hier_p2_*_20260817T014*` | `scripts/build_hier_blind_diagnostics_v1.py` |

**Inline command blocks** *(verbatim as run; working dir = repo root; PATH must
include `~/.local/bin` (jq); Python = `.venv/bin/python`; scripts importing
`scripts.*`/`src.*` need `-m` module form or `PYTHONPATH=.`).*

**A — R3 readout** (fired by `scripts/r4_readout_runner.sh`'s sibling flow; run
dirs listed in the report's `runs` block):
see `reports/m7_r3_readout_v1.json` `.runs` for the eight cell run dirs; the
readout script is `scripts/build_m7_r3_readout.py` (fixture-validated).

**B — R4 readout** (from `scripts/r4_readout_runner.sh`):

    .venv/bin/python scripts/build_c5_r4_readout.py \
      --cell base:real=experiments/runs/blind_solvability_v2_c5_7b_base_real_an29_20260731T123739Z \
      --cell base:gray=experiments/runs/blind_solvability_v2_c5_7b_base_gray_an29_20260731T123835Z \
      --cell a1_real:real=<logs/c5_endgame_state/cell_a1_real_real> \
      --cell a1_real:gray=<logs/c5_endgame_state/cell_a1_real_gray> \
      --cell a2_gray:real=<logs/c5_endgame_state/cell_a2_gray_real> \
      --cell a2_gray:gray=<logs/c5_endgame_state/cell_a2_gray_gray> \
      --json-output reports/c5_r4_readout_v1.json \
      --markdown-output reports/c5_r4_readout_v1.md \
      --artifact-dir reports/c5_r4_readout_v1_artifacts

(the four `<...>` run dirs are recorded verbatim in the report's provenance table)

**C — Gate-1 acceptance audit** (9/9 PASS, 2026-08-09; sealed-file guard active):

    .venv/bin/python -m scripts.audit_mini_a5_gate1_acceptance \
      --std-run experiments/runs/mini_a5_std_main_an29_20260807T013033Z \
      --necessity-run experiments/runs/mini_a5_necessity_main_an29_20260807T222122Z \
      --out-json reports/mini_a5_gate1_acceptance_audit_v1.json \
      --out-md reports/mini_a5_gate1_acceptance_audit_v1.md

**D — Gate-1 four-arm endpoint readout** (only after C passes; F8 cells carried,
never re-run):

    PYTHONPATH=. .venv/bin/python -m scripts.build_mini_a5_gate1_endpoint_readout \
      --arm-std experiments/runs/mini_a5_gate1_r19_std_step120_real_an12_20260807T235840Z \
      --arm-member experiments/runs/mini_a5_f8_r19_member_step120_real_an29_20260730T004031Z \
      --arm-necessity experiments/runs/mini_a5_gate1_r19_necessity_step120_real_an29_20260809T143630Z \
      --arm-cp experiments/runs/mini_a5_f8_r19_cp_step120_real_an29_20260730T004031Z \
      --base-report reports/f2d_template_decomposition_v1.json \
      --f8-report reports/f8_mini_a5_endpoint_readout_v1.json \
      --output reports/mini_a5_gate1_endpoint_readout_v1.json

**E — Gate-1 catch-stability, new arms** (single-arm scorer; the registered
two-arm scorer stays sha256-pinned and untouched):

    .venv/bin/python -m src.eval.catch_stability_single_arm --arm-label std \
      --run-dir experiments/runs/mini_a5_catch_std_step120_real_an12_20260807T235840Z \
      --output reports/mini_a5_catch_stability_std_v1.json --expect registered
    .venv/bin/python -m src.eval.catch_stability_single_arm --arm-label necessity \
      --run-dir experiments/runs/mini_a5_catch_necessity_step120_real_an29_20260809T143630Z \
      --output reports/mini_a5_catch_stability_necessity_v1.json --expect registered

**F — C6 mechanism-at-scale readout.** Two instruments have produced this
readout; the command below is the one that reproduces it **today**, because the
file at `scripts/build_c6_mechanism_at_scale_readout.py` is now the second,
independently-authored instrument (see the reproduction note in the C6 section).
It resolves all six cells through the pointer files `logs/c6_cells/<label>` —
`r19_base7b`, `r19_a1real`, `r19_a2gray`, `r20_base7b`, `r20_a1real`,
`r20_a2gray` — and re-verifies every binding field from each cell's own
`run_manifest.json`, so cells are bound by manifest content and not by directory
name (registration §5). Fixtures green first:
`.venv/bin/python -m pytest tests/test_build_c6_mechanism_at_scale_readout_fixture.py`
→ 24 passed. Cells generated by `scripts/c6_cells_chain.sh`.

    .venv/bin/python scripts/build_c6_mechanism_at_scale_readout.py \
      --output reports/c6_mechanism_at_scale_v1_independent_replicate.json \
      --markdown-output reports/c6_mechanism_at_scale_v1_independent_replicate.md

(defaults are the registered values: `--seed 20260712`, `--bootstrap-draws 2000`,
pointer dir `logs/c6_cells`; non-registered values are refused by check 11 unless
`--fixture-registry` is given, which is fixtures-only and stamps
`fixture_mode: true` on the output. The script refuses to overwrite an existing
report, which is why the reproduction writes to the `_independent_replicate`
path rather than over the banked `reports/c6_mechanism_at_scale_v1.json`.)

The first instrument produced `reports/c6_mechanism_at_scale_v1.json` — the
banked report of record, cited by the C6 section — under the CLI
`--cell <label>=<run_dir> … --require-cell-pointers --json-output …`, with a
61-case fixture suite. Its source was overwritten before it could be re-run, so
that command is recorded here for provenance but **will not execute**; the two
reports agree on all 24 registered numbers, which is what licenses reproduction
by the command above.

**G — E4 attacker gate** (run by `scripts/run_e4_gate.sh` on an29 GPU 2, guard →
claim → release; the verdict is read separately against the registered
criterion — see the criterion note above):

    bash scripts/launch_artifact_gate_v02.sh an29 2 \
      data/track4_premise_v2_dev_v1/attacker_release \
      data/track4_premise_v2_dev_v1/attacker_key.jsonl \
      reports/track4_premise_v2_attacker_gate_v1.json

**H — E1/E2 per-type gate readout** (fixtures green first:
`tests/test_build_track4_premise_v2_gate_readout.py` → 26 passed; the six cells
were produced by `scripts/track4_premise_v2_gates.sh`, raw, no rescore):

    R=experiments/runs/track4_premise_v2_gates_an29_20260811T095522Z
    D=data/track4_premise_v2_dev_v1
    .venv/bin/python -m scripts.build_track4_premise_v2_gate_readout \
      --probe-real $R/premise_probe --probe-gray $R/premise_probe_gray \
      --probe-no-image $R/premise_probe_no_image \
      --final-real $R/final --final-gray $R/final_gray \
      --final-no-image $R/final_no_image \
      --probe-manifest $D/manifest_premise_probe.jsonl \
      --causal-manifest $D/manifest_causal_pairs.jsonl \
      --json-output reports/track4_premise_v2_gate_readout_v1.json \
      --markdown-output reports/track4_premise_v2_gate_readout_v1.md

**I — E3 caption stress** (fixtures green first:
`tests/test_build_track4_premise_v2_e3_readout.py` → 14 passed). Generation:
stage A is the registered captioner command, run by
`scripts/run_e3_caption_stress.sh` on an29 GPU 3; stages B–D were completed from
the banked shard by `scripts/e3_finish_from_banked_captions.sh` after the
single-shard arity fix to `scripts/launch_caption_store_merge.sh`. The readout:

    E=experiments/runs/track4_premise_v2_e3_an29_20260811T155104Z/finish_20260811T162332Z
    .venv/bin/python scripts/build_track4_premise_v2_e3_readout.py \
      --predictions $E/caption_qa_predictions.jsonl \
      --causal-manifest data/track4_premise_v2_dev_v1/manifest_causal_pairs.jsonl \
      --measured-blind-floors tmp/e3_measured_blind_floors.json \
      --json-output reports/track4_premise_v2_e3_readout_v1.json \
      --markdown-output reports/track4_premise_v2_e3_readout_v1.md

(the measured floors are each type's blind final member accuracy read out of
`reports/track4_premise_v2_gate_readout_v1.json`; omitting the flag reports
reading (a) alone. Intervention type is taken from the causal manifest's own
`intervention_type` field, never parsed from `pair_id` — the type names are
prefixes of one another.)

**J — E4 wording resolution** (fixtures green first:
`tests/test_artifact_attackers_v02.py` → 10 passed; folded and unfolded CIs
are quantiles of the same bootstrap draws, so v1 reproduction is structural):

    bash scripts/launch_artifact_gate_v02.sh an29 2 \
      data/track4_premise_v2_dev_v1/attacker_release \
      data/track4_premise_v2_dev_v1/attacker_key.jsonl \
      reports/track4_premise_v2_attacker_gate_v2_unfolded.json \
      "--per-item-scores reports/track4_premise_v2_attacker_oof_scores_v1.jsonl"
    .venv/bin/python scripts/build_e4_wording_resolution.py \
      --v1 reports/track4_premise_v2_attacker_gate_v1.json \
      --v2 reports/track4_premise_v2_attacker_gate_v2_unfolded.json \
      --output-json reports/track4_premise_v2_e4_wording_resolution_v1.json \
      --output-md reports/track4_premise_v2_e4_wording_resolution_v1.md

(guard → claim → release around the launcher as in block G; reproduction check
inside the builder: exact for the CPU attackers, 1e-9 for dinov2 — measured
exact for all three.)

**K — E1/E2 on dev_v2** (fixtures green first:
`tests/test_track4_premise_v2_dev_v2.py` → 6 passed, including the fixture
that the v1 batch FAILS the balance cap; batch verifier 0 problems):

    .venv/bin/python scripts/build_track4_premise_v2_dev_batch_v2.py   # one-shot
    GATES_DATA_DIR=data/track4_premise_v2_dev_v2 GATES_ONLY="E1 E2" \
      bash scripts/track4_premise_v2_gates.sh
    R=experiments/runs/track4_premise_v2_gates_an29_20260816T090907Z
    D=data/track4_premise_v2_dev_v2
    .venv/bin/python -m scripts.build_track4_premise_v2_gate_readout \
      --probe-real $R/premise_probe --probe-gray $R/premise_probe_gray \
      --probe-no-image $R/premise_probe_no_image \
      --final-real $R/final --final-gray $R/final_gray \
      --final-no-image $R/final_no_image \
      --probe-manifest $D/manifest_premise_probe.jsonl \
      --causal-manifest $D/manifest_causal_pairs.jsonl \
      --expect registered-v2-branch-c \
      --json-output reports/track4_premise_v2_gate_readout_v2.json \
      --markdown-output reports/track4_premise_v2_gate_readout_v2.md

**L — E3 on dev_v2** (same instrument as block I; measured floors from the v2
E2 cells):

    E3_DATA_DIR=data/track4_premise_v2_dev_v2 E3_PROV_TAG=v2 \
    E3_RELEASE_MANIFEST_SHA256=77021b66e37afae23e0320ce6915ddb74af96963a0745d7cc150f24d3abc656f \
    E3_RELEASE_KEY_SHA256=9e8fba20f226d8adf030ca72a3a06b5e6ab40cd4d110496684a3dbdfc588fbe4 \
      bash scripts/run_e3_caption_stress.sh
    E=experiments/runs/track4_premise_v2_e3_an29_20260816T091115Z
    .venv/bin/python scripts/build_track4_premise_v2_e3_readout.py \
      --predictions $E/caption_qa/predictions.jsonl \
      --causal-manifest data/track4_premise_v2_dev_v2/manifest_causal_pairs.jsonl \
      --measured-blind-floors tmp/e3_v2_measured_blind_floors.json \
      --json-output reports/track4_premise_v2_e3_readout_v2.json \
      --markdown-output reports/track4_premise_v2_e3_readout_v2.md

**M — two-seed R3 readout** (instrument + fixtures from the 08-12 extension
round, `scripts/build_m7_r3_readout.py`; seed-1 run dirs verbatim from
`reports/m7_r3_readout_v1.json` `provenance.runs`; the invocation is preserved
verbatim as `tmp/run_m7_r3_readout_v2_20260816.sh`):

    bash tmp/run_m7_r3_readout_v2_20260816.sh
    # = build_m7_r3_readout.py with --step0/--step100 (seed-1 cells, 4 arms each)
    #   + --step100-seed2 a1_real=…20260809T144439Z a2b_noimage=…20260811T041120Z
    #     a2_gray=…20260816T082503Z a3_caption=…20260816T082631Z
    #   --artifact-dir reports/m7_r3_readout_v2_artifacts
    #   --json-output reports/m7_r3_readout_v2.json
    #   --markdown-output reports/m7_r3_readout_v2.md
    # registered defaults carried: 5000 draws, bootstrap seed 20260716,
    # held-out sha/rows/strata pins

*Eval-cell generation for the Gate-1 arms (merge → R19/R20/chartv08/catch) is
scripted end-to-end in `scripts/gate1_std_evals_chain.sh` and
`scripts/gate1_necessity_evals_chain.sh`; M7 seed-2 held-out evals in
`scripts/launch_m7_seed2_eval.sh`. All committed at `4ac5c57` or earlier.*
