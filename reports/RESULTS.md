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
| D4 caption test column (4×3 → 4×4) | F1 | **running** — 4/12 cells done |
| M5 long horizon → step 400 | **R2** | **complete — verdict FALLING** |
| M7 ViRL39K stratified | R3 | ready; pre-launch registration cleared |
| C5 7B access pair (A1 vs A2-gray) | R4 | **not built** — no 7B configs exist yet |
| M11 cross-family | R5 | **complete** (recovered 2026-07-28) |
| Mini-A5 CP vs matched GRPO | F8 | CP arm complete; member arm 17/120 |
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
matched evaluation and 48.7% under crossed evaluation** — a seven-fold difference
in the scientific conclusion, produced by the evaluation protocol alone.
Registered branch (a) obtains: ratio > 2 for both blind arms in all three seeds.
Strict-scoring control reproduces direction and rough magnitude (ratios
1.95–2.69), qualifying rather than overturning the claim.

**TrainShare** (PAPER1 §8 estimand, paired item-level bootstrap CIs) —
`reports/d3_trainshare_v1.json`:

| arm | s1 | s2 | s3 | pooled | 95% CI |
|---|---|---|---|---|---|
| A2 gray | 0.507 | 0.527 | 0.424 | **0.487** | [0.383, 0.588] |
| A2b no-image | 0.572 | 0.493 | 0.518 | **0.528** | [0.424, 0.629] |
| A3 caption | 0.743 | 0.716 | 0.691 | **0.718** | [0.617, 0.821] |

Branch: **headline at full strength** — every interval lies entirely above the
0.35 threshold, nearest lower bound 0.383, and all nine seed-arm values fall in
the same branch. *Ordering disclosure: the 36 cells were read under the
ratio-based D3 registration before TrainShare was computed, so TrainShare is a
declared post-hoc recomputation and does not satisfy I9.*

**Matched-condition gains, for contrast:** A1 +0.2435, A3 +0.1048, A2b +0.0460,
A2 gray +0.0161.

---

## 2. F2 — The information ladder

Measured with images at test, over base: gray **+0.119 (49%)** → no-image
**+0.129 (53%)** → caption **+0.175 (72%)** → real **+0.244 (100%)**.

So 49% of the gain requires no visual information during training at all; a
further 23% is transmissible through frozen textual descriptions; 28% requires
actual pixels during optimisation.

**The 49% is an average over a gradient, not a constant.** G0.2 (§10) finds A2b's
image-present gain concentrates on blind-*answerable* items: 84% of A1's gain
where blind reward opportunity exists, 42% where none was observed. The
image-free share falls as an item's dependence on the image rises.

The caption inversion replicates 3/3: A3 starts above A1 at step 0 (0.2097 vs
0.1747) and ends below it at step 100.

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

Margin inflation vs base under the **correct** image: A1 +0.150, caption +0.090,
no-image +0.035, gray +0.036 — the same information ordering as F2. Under a
same-template **mismatched** image: statistically zero for every arm, both seeds.
Under the **twin's** image every model including the frozen base prefers the
twin's gold (0.948–0.955). Blind-condition entropy stays at 0.998, so this is not
a global temperature change.

Presence-gating, global temperature change, and pure formatting are each excluded
by direct measurement.

---

## 5. F5 — What the residual does not buy

Structured hard-negative discrimination: base 0.517, A1 0.513–0.527. Chained
premise-to-reasoning at floor for every model (0.000 pair). Binding swap flat.
Fact-read unimproved. The 28% that requires training-time pixels is more readout
policy tuned against real evidence — not new visual distinctions.

**Candidate-set correction (X2, registered bottom branch fired).** The golds-only
figure of 0.9067 is predominantly *candidate-set structure*, not latent
competence; the realization gap ships as a measurement-methods finding, and
"already perceived" stays hypothesis language (§9).

---

## 6. F6 — Blind reward corrodes grounding, item-identifiably

`reports/x3_a2_degradation_forensics_v1.*`. A2 gray's exact −0.045, both seeds,
resolves to **42 shared pairs** (Jaccard 0.724 vs permutation null 0.098,
p = 1e-4), the same extracted wrong answer in 41/42, nearest-gridline off-by-one
in 19/20.

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

## 8. F8 — Trainability (Mini-A5) — IN FLIGHT

CP-GRPO vs matched same-data standard GRPO, 120 steps each, on held-out
FlipTrack templates. CP arm **complete** (status complete, `global_step_120`);
matched member arm at 17/120 on an29.

**No value from either arm has been opened.** The registration prohibits partial
readouts until both arms and their endpoint evaluations complete. An acceptance
audit of all six conditions (`scripts/audit_mini_a5_acceptance.py`) must return
PASS before any endpoint is read; it currently fails on condition 1 alone
(member arm still running), with the other five passing — including the
structural check that the CP arm logged its advantage-audit events and the member
arm never entered the joint branch.

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
image-requiring items (+0.197) but is disproportionately the blind-attainable
component. Direct measured support for **H1**.

**G0.3 — policy overlap.** A1/A2b newly-correct sets: Jaccard 0.363–0.423 against
a permutation null of 0.157–0.177, p ≤ 0.004 in all three seeds. Substantially
overlapping policies, but ~60% of the union belongs to only one arm.

**G0.4 — the access matrix is format-free by identity.** Format gain is *exactly*
**+0.1148 for all four arms**: every trained arm satisfies
`acc_strict == acc_final`, so FormatGain collapses to
`base_final − base_strict` = 0.1747 − 0.0599. The formatting component cancels
exactly in any arm-minus-arm comparison.

---

## 11. Phase 0 — Paper 2 blocking prerequisites (complete)

**P0.1 premise probe, five separate numbers** — `reports/p01_premise_probe_v1.*`:

| cell | premise member | premise pair | transition | final member | final pair | reasoning \| premise |
|---|---|---|---|---|---|---|
| base | 0.275 | 0.200 | 0.200 | 0.150 | 0.000 | 0.273 (n=11) |
| A1 s1 | 0.225 | 0.200 | 0.200 | 0.100 | 0.000 | 0.222 (n=9) |
| A1 s2 | 0.175 | 0.150 | 0.150 | 0.075 | 0.000 | 0.000 (n=7) |
| A2b s1 | 0.300 | 0.200 | 0.200 | 0.125 | 0.000 | 0.250 (n=12) |
| A3 s1 | 0.250 | 0.200 | 0.200 | 0.075 | 0.000 | 0.200 (n=10) |

Base premise accuracy **0.275** (95% Wald [0.137, 0.413]) fires registered branch
**(b)**: the chained construct is revised before release, and its 0.000 pair
accuracy is *uninformative about chaining* rather than evidence against it.
Reasoning given a correct premise is only 0.273 at base — premise extraction is
the first bottleneck but not the only one, so an easier premise curriculum alone
will not make these items trainable. Premise-transition accuracy equals premise
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
**0 of 30 cells move**, so the published B1 table stands.

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
formatting. Descriptive trajectory (overall R19, cannot select the endpoint per
the ruling): 0.5600 → 0.5433 → 0.5383 → 0.5167 at steps 150/200/300/400 —
monotone.

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
the same models keep most of their accuracy with no image:

| model | real | caption | none | none/real |
|---|---|---|---|---|
| Gemma-3 | 0.3418 | 0.3091 | 0.2424 | **71%** |
| InternVL3-9B | 0.2805 | 0.1951 | 0.1538 | **55%** |

**This is the blind-reward-opportunity thesis measured on two foreign model
families:** standard benchmarks are largely answerable blind, while FlipTrack is
image-necessary by construction. (Dossier note: §5's "caption ≤0.013" should read
≤0.0134 — the measured maximum is 0.01333.)

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
| A2b no-image | −0.0272 | [−0.0483, −0.0061] | marginal |
| A3 caption | −0.0050 | [−0.0244, +0.0150] | yes |

**Contract validity as a first-class result** (pair-level, geometry slice): base
0.9500 → A1 0.8767, A2 gray 0.6317, A2b 0.7728, A3 0.7578. Every trained arm
falls **below** the frozen base, and the ordering tracks how degraded the arm's
endpoint is. RLVR erodes answer-contract compliance on the counterfactual probe
even where it raises task accuracy.

**Power.** Minimum detectable effect at 80% power is 0.0348 (A1), 0.0377
(A2 gray), 0.0360 (A2b), 0.0338 (A3) — about 70% of the ±0.05 SESOI, so the A1
null is informative rather than underpowered.

---

## 16. The cue ladder — a negative result about our own instrument

Registered `docs/registered_cue_ladder_v1.md` + v2 amendment. Four rungs replayed
from the frozen R19 nine-series `pair_seed`s (300/300 replay integrity), so the
ladder is item-paired with R19.

**Both monotonicity gates failed**, so branches (a)/(b) are void and the twelve
arm cells were deliberately **not scored** — F3d's prediction about
localization-specific corrosion is **untested, not refuted**.

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
- **The competence layers it should move do not move.** Hard negatives, binding,
  chained premise all flat or at floor (F5).

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

**What would falsify this reading.** A training signal that moves hard-negative
discrimination, binding, or chained premise while holding the task reward fixed.
That is precisely what Mini-A5 (F8) is testing, and its result is not yet known
to us — the arms are sealed until both complete.

---

## 19. Still in flight

- **D4 caption column** — 4/12 cells complete; 2 failed on CUDA OOM from a
  scheduler double-booking and are queued for retry. Registered reading (ordering
  under caption-at-test: pixel-specific vs evidence-general) filed before any
  cell ran.
- **F8 Mini-A5** — member arm 17/120; sealed until the acceptance gate passes.
- **R3 M7** — ready; per-stratum estimands and the merged pre-launch prediction
  verified present.
- **R4 C5 7B** — no 7B training configs exist yet; two must be authored (A1 and
  A2-gray) against the 3B recipe, with a registered sizing decision.
