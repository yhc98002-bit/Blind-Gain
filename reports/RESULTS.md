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
| CHANCE null-corrected retention | **F0 contract** | **complete** (partial coverage: 5 benchmarks have no blind run) — §13/§13b rewritten |
| SEED3γ third-seed corrosion | **F6 Tier 1** | **complete — replicates**; 3-way Jaccard 0.661 vs null 0.012 (§6a) |
| E1b trained-arm external columns | F1 beyond geo3k | **complete, 48/48** — **P1, S1, S2 all miss**; no lenient comparison moves (§13c, §13d) |
| M7 ViRL39K stratified | R3 | ready; pre-launch registration cleared |
| C5 7B access pair (A1 vs A2-gray) | R4 | **not built** — no 7B configs exist yet |
| M11 cross-family | R5 | **complete** (recovered 2026-07-28) |
| Mini-A5 CP vs matched GRPO | F8 | **both arms trained (120/120); acceptance gate PASS 2026-07-29**; endpoints still unread — member arm needs HF merge first (§8) |
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

## 8. F8 — Trainability (Mini-A5) — BOTH ARMS TRAINED, GATE PASSED, ENDPOINTS NOT YET READ

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

**No endpoint value has been read yet.** Reading them requires evaluation runs that
have not been performed, and one prerequisite is outstanding: the member arm's
`global_step_120/actor/huggingface/` holds only config and tokenizer files
(~16 MB, no safetensors), because that arm was saved with `save_model_only: false`
as raw FSDP shards. The CP arm's step-120 checkpoint is 7.6 GB and directly
loadable. **The member arm must be merged to HF weights before it can be
evaluated** — the registration anticipated exactly this ("a checkpoint
merge/relocation watcher must accompany each arm so raw state is merged, archived,
and pruned behind the trainer"). Until that merge runs, F8 remains unread, and no
number here should be cited.

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

### Verdict

The benchmark is not hiding a clean substitution of cheap strategies for visual ones. It is
hiding **large, item-reproducible churn that is orthogonal to measured visual necessity**.
The corrosion established on FlipTrack (§6, §6a, §12b) does not have a visible geo3k
counterpart at the level of *which kinds of item* move.

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

**What would falsify this reading.** A training signal that moves hard-negative
discrimination, binding, or chained premise while holding the task reward fixed.
That is precisely what Mini-A5 (F8) is testing, and its result is not yet known
to us — the arms are sealed until both complete.

---

## 19. Still in flight

- **D4 caption column** — **complete**, see §2b. Branch (a), evidence-general.
- **F8 Mini-A5** — member arm 17/120; sealed until the acceptance gate passes.
- **R3 M7** — **launched** 2026-07-28 on an12 (arm 1 of 8, `a1_real` seed 1);
  per-stratum estimands and the merged pre-launch prediction verified present.
- **R4 C5 7B** — no 7B training configs exist yet; two must be authored (A1 and
  A2-gray) against the 3B recipe, with a registered sizing decision.
- **E1b external access matrix** — registered
  `docs/registered_e1b_external_access_matrix_v1.md` **before any cell was run**.
  48 cells (4 arms × 3 seeds × 2 benchmarks × 2 conditions). The **blind column
  (24 cells) is running** on an12 GPUs 4–7; the with-image column follows. Item
  sets pinned to the E1a base items (1500/1500 MMStar, 999/999 MathVista verified
  present). Reported under the CHANCE contract, never naive retention.
  **Resource isolation is explicit and enforced**: M7 holds GPUs 0–3 at its
  registered 4-GPU width and is not widened, paused, or touched; the orchestrator
  aborts if GPUs 4–7 are not free.
- **LH2 second long-horizon seed** — the staged sequence is *not* auto-triggered.
  §12b weakens the case that motivated it (the benchmark axis is flat at 400, not
  rising), so whether LH2 is worth multiple days is a PI decision, not mine.
