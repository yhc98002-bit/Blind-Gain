# M5c — evidence ledger for the geo3k step-100 → step-400 turnover finding (v1)

Generated 2026-07-30T13:22:05Z. git `8aeb7203061194f884144138ea3330fb8400a807`. CPU only on the login node; cached predictions and the existing substrate only; no GPU job started.
Facts, checks and provenance only.

## THE LEDGER

One row per piece of evidence. `p` is raw; `p (adj)` is Holm-adjusted where a correction applies.

| # | claim it supports | statistic | null | p | p (adj) | verdict |
|---|---|---|---|---|---|---|
| L01 | The step-100 -> step-400 NET accuracy change is not distinguishable from zero. | McNemar exact two-sided on 71 gained / 66 lost; net +5 items, +0.008319 | no net asymmetry between gained and lost (binomial 137 discordant pairs, p=0.5) | 0.7327 | — | **SUPPORTS** |
| L02 | 137 of 601 items (22.80%) change state between step 100 and step 400 -- turnover 27.4x the net. | discordant pairs 137/601 = 0.227953; turnover/\|net\| = 27.4 | descriptive count -- no null; the noise question is answered by L03 | — | — | **SUPPORTS** |
| L03 | The 137-item turnover is NOT evaluation or decoding noise. | replicate discordance 0/601 on acc_final AND 0/601 on acc_strict at BOTH step 400 and step 100; all 601 greedy response strings byte-identical; per_item.jsonl bit-identical (step-400 sha256 60eac65a8b5bb9b3..., step-100 4a4a840f9a3edb1b...) | directly measured replicate floor -- no model needed | — | — | **SUPPORTS** |
| L04 | (prior weakest link) 16-sample dispersion implies expected discordance 0.2133 vs 0.2280 observed. | expected discordance fraction 0.21327735 between two independent Bernoulli(p_i) draws at step 100 | temperature-1.0 sampling dispersion -- NOT the greedy harness | — | — | **DOES NOT SUPPORT (and was never a test)** |
| L05 | Intermediate hops move accuracy significantly in BOTH directions, so the flat endpoint is a cancellation. | 100->200: +86/-54, net +32; 200->400: +44/-71, net -27 (McNemar exact two-sided) | no net asymmetry at each hop | 0.008557 (100->200); 0.014965 (200->400) | — | **SUPPORTS (100->200); QUALIFIES (200->400 does not survive a 7-hop Bonferroni)** |
| L06 | WHICH items are lost is reproducible across checkpoints. | 3-way Jaccard of LOST(100->200), LOST(100->300), LOST(100->400) = 0.3118 vs permutation null mean 0.0221 | 10,000 equal-size random subsets of the step-100-correct pool (n=262), seed 20260729 | <= 1e-04 | 0.0015 | **SUPPORTS** |
| L07 | LOST items concentrate by problem type (derived stem bucket). | chi-square 11.7769 on 9 buckets (null mean 6.0463, 95th pct 11.5905); angle_measure lost rate 0.4500 | 10,000 random equal-size (66) subsets of the step-100-correct pool (n=262), seed 20260729 | 0.0461 | 0.1383 | **QUALIFIES -- raw p significant at 0.05 but does NOT survive Holm over this report's 10-test family** |
| L08 | GAINED items concentrate by problem type. | chi-square 8.8062 (null mean 5.5763, 95th pct 11.2271) | 10,000 random equal-size (71) subsets of the step-100-WRONG pool (n=339), seed 20260729 | 0.1334 | 0.1383 | **DOES NOT SUPPORT** |
| L09 | (uncontrolled) LOST items land on a numeric near-miss more often than stable-wrong items. | 11/54 = 0.2037 vs 20/230 = 0.0870 | equal-size random subsets of the stable-wrong set (published) / arm-label permutation (here) | 0.0005 | 0.0055 | **QUALIFIES** |
| L10 | The near-miss effect survives matching on step-100 correctness using STABLE_CORRECT as reference. | LOST 11/54 = 0.2037 vs STABLE_CORRECT 176/176 = 1.0000 | none run -- the comparison is degenerate | — | — | **DOES NOT SUPPORT -- the requested matched comparison is DEGENERATE** |
| L11 | The near-miss effect survives a non-degenerate match on step-100 correctness. | LOST(100->400) at step 400 11/54 = 0.2037 vs DIP-AND-RECOVER at first dip step 1/26 = 0.0385; difference +0.1652 | 10,000 arm-label permutations, seed 20260729 | 0.0482 | 0.1383 | **QUALIFIES -- raw p significant at 0.05 but does NOT survive Holm over this report's 10-test family** |
| L12 | The near-miss effect is not an artefact of LOST items having larger gold answers (the +/-10% window widens with \|gold\|). | \|gold\|-quartile-stratified rate difference +0.1201 (median \|gold\| LOST 25.50 vs stable-wrong 33.00) | 10,000 within-stratum arm-label permutations, seed 20260729 | 0.0148 | 0.0592 | **QUALIFIES -- raw p significant at 0.05 but does NOT survive Holm over this report's 10-test family** |
| L13 | LOST items were already marginal at step 100 in the decoder's own margin / logprob. | not computable | n/a | — | — | **NOT MEASURABLE** |
| L14 | (separate quantity, NOT the L13 margin test) LOST items had a lower step-100 16-sample pass rate than STABLE_CORRECT items. | mean canonical_p_sample 0.4233 (n=66) vs 0.7886 (n=196); difference -0.3653 | 10,000 arm-label permutations, seed 20260729 | <= 1e-04 | 0.0010 | **SUPPORTS** |
| L15 | The five-step correctness patterns are not what independent per-step flipping produces. | G2 = 1289.82 and Pearson X2 = 3070.95 over 32 patterns (null max G2 across 10,000 replicates = 70.91, null mean 26.44) | 10,000 parametric-bootstrap datasets in which each item flips independently between steps at the observed per-step marginal accuracies, seed 20260729 | <= 1e-04 | 0.0010 | **SUPPORTS** |
| L16 | Correctness is stickier in TIME than chance, holding each item's own number of correct steps fixed. | total adjacent flips 429 vs within-item order-permutation null mean 480.62 (sd 11.41) and row+column-margin-preserving null mean 480.99 (sd 11.16) | N2: 10,000 within-item permutations of the five step labels. N3: 10,000 curveball samples preserving every item's correct-step count AND every step's accuracy count. seed 20260729 | N2 <= 1e-04; N3 <= 1e-04 | N2 0.0010; N3 0.0010 | **SUPPORTS** |

Row notes:

- **L01** — This is the only thing McNemar tests. It does NOT bound total turnover. _(source: reports/m5c_turnover_v1.json; adjustment: none (single pre-registered primary endpoint of the turnover report))_
- **L02** — Count, not a test. Its interpretation depends entirely on the noise floor (L03). _(source: reports/m5c_turnover_v1.json; adjustment: n/a)_
- **L03** — Floor = 0 items, so turnover/floor is undefined (zero denominator) and floor-subtracted turnover = 137 - 0 = 137. TASK A. _(source: reports/m5c_noise_floor_replicate_v1.json; adjustment: n/a (a measured floor, not a test))_
- **L04** — Explicitly labelled not-a-test when recorded; superseded by the measured zero floor in L03. It describes temperature-1.0 sampling, not replicate noise of the greedy eval that produced the 137. _(source: reports/m5c_turnover_v1.json :: noise_reference_not_a_test; superseded per reports/m5c_noise_floor_replicate_v1.json :: superseded_reference; adjustment: n/a)_
- **L05** — Correction arithmetic stated here explicitly; the source report reports the raw p only. _(source: reports/m5c_turnover_v1.json; adjustment: not corrected in the source report; 7 hop tests exist, Bonferroni 0.05/7 = 0.00714 -> 100->200 survives, 200->400 does not)_
- **L06** — Robust to per-item noise in either direction: noise would REDUCE cross-checkpoint agreement, not manufacture it. Limitation: the three lost sets share one step-100 anchor eval and come from one training trajectory, so serial dependence is not removed. _(source: reports/m5c_lost_item_forensics_v1.json; adjustment: Holm-Bonferroni, 15-test family in the forensics artifact (reject: True))_
- **L07** — Buckets are DEFINED BY THE ANALYSIS from the problem string (regex, fixed order, reused verbatim); geo3k carries no template/category/source field and qid and source_metadata are null on all 601 rows at all five steps. _(source: this report, task 1; adjustment: Holm-Bonferroni over the 10 tests computed in this report)_
- **L08** — Asymmetry with L07 is the substantive point: losses look type-structured, gains less so. _(source: this report, task 1; adjustment: Holm-Bonferroni over the 10 tests computed in this report)_
- **L09** — NOT difficulty-controlled: LOST items were correct at step 100 by construction, stable-wrong items were not. See L10-L12. The raw p is also convention-dependent: the published subset-draw convention reproduces here at 0.0005, but arm-label permutation on the same data gives 0.0179. The subset-draw null puts sampling variance on one arm only. _(source: reports/m5c_lost_item_forensics_v1.json; recomputed here; adjustment: Holm-Bonferroni, 15-test forensics family (reject: True))_
- **L10** — STABLE_CORRECT items are correct at step 400 by definition, so their step-400 answer IS gold and their near-miss rate is 1.0 by construction. The matched pool as literally specified cannot test the hypothesis. _(source: this report, task 2; adjustment: excluded from the Holm family (not a test))_
- **L11** — Both arms are correct at step 100 and both are scored on a WRONG answer. Like-for-like (arm-label permutation on both sides): arm-label p 0.0179 (unmatched, effect +0.1167) -> 0.0482 (matched, effect +0.1652); the effect SIZE is preserved or larger under matching, the p rises because the matched reference arm has only 26 numeric-comparable items. Residual limitation: the reference arm's wrong answer is read at step 150/200/300, not 400, because among step-100-correct items 'wrong at step S' IS lost-at-S. _(source: this report, task 2; adjustment: Holm-Bonferroni over the 10 tests computed in this report)_
- **L12** — Controls answer SCALE, not step-100 correctness. Complementary to L11, not a substitute. _(source: this report, task 2; adjustment: Holm-Bonferroni over the 10 tests computed in this report)_
- **L13** — No logprob, token-probability, logit, decoding-score or margin field exists in any of the five cached geo3k per-item files (full field census in the JSON). Steps 150/200/300/400 additionally have no sampled decode of any kind. No proxy is substituted. _(source: this report, task 3; adjustment: n/a)_
- **L14** — This is a temperature-1.0 n=16 empirical PASS RATE, not a decoding margin, and it exists only at step 100. It is reported as its own line so that L13 stays honestly NOT MEASURABLE. A reader wanting only the requested margin test should read L13. _(source: this report, task 3 (side measurement); adjustment: Holm-Bonferroni over the 10 tests computed in this report)_
- **L15** — Direction: MORE PERSISTENCE. never-correct 198 vs null mean 26.8; always-correct 162 vs 12.7; total adjacent flips 429 vs 1197.0. _(source: this report, task 4; adjustment: Holm-Bonferroni over the 10 tests computed in this report)_
- **L16** — This is the test that separates 'items differ in difficulty' (already implied by L15) from 'movement is temporally ordered'. N3 is the strict version: it fixes both margins. _(source: this report, task 4; adjustment: Holm-Bonferroni over the 10 tests computed in this report)_

## Verification

| check | result |
|---|---|
| bucket rules imported from | `scripts/m5c_lost_item_forensics.py::STEM_RULES` |
| imported bucket rules identical to the published artifact's recorded rules | True |
| test items per step (100/150/200/300/400) | 601/601/601/601/601 |
| item-key sets identical across all five steps | True |
| ground_truth identical across all five steps | True |
| problem sha256 identical across all five steps | True |
| substrate rows / value mismatches vs the cached runs | 601 / 0 |
| acc_final == acc_strict on every item at every step | True |
| set sizes reproduce the forensics artifact (lost/gained/stable_correct/stable_wrong) | {'lost': True, 'gained': True, 'stable_correct': True, 'stable_wrong': True} |
| LOST bucket chi-square reproduces published statistic to 1e-9 | True (11.776933 vs 11.776933) |
| GAINED bucket chi-square reproduces published statistic to 1e-9 | True (8.806222 vs 8.806222) |

The chi-square STATISTIC is deterministic and must match to machine precision. The permutation p may differ in the 3rd decimal from the published value because the published run drew its permutations from an RNG stream shared with the Jaccard and gold-entropy statistics, whereas this run uses a dedicated stream at the same seed. Both are valid Monte-Carlo estimates of the same p.

Everything below is reported under acc_final. acc_strict is stored separately in the JSON and is numerically identical, because acc_final == acc_strict on all 601 items at all five steps.

## 1. Problem-type concentration, corrected

Full derived-bucket × transition table. `stable` = stable_correct + stable_wrong; the four transition columns partition all 601 items.

| derived bucket | total | lost | gained | stable | stable_correct | stable_wrong | correct@100 | wrong@100 | lost rate within correct@100 | gained rate within wrong@100 |
|---|---|---|---|---|---|---|---|---|---|---|
| angle_measure | 143 | 18 | 19 | 106 | 22 | 84 | 40 | 103 | 0.4500 | 0.1845 |
| arc_measure | 38 | 3 | 5 | 30 | 7 | 23 | 10 | 28 | 0.3000 | 0.1786 |
| area | 60 | 9 | 4 | 47 | 20 | 27 | 29 | 31 | 0.3103 | 0.1290 |
| circumference | 4 | 1 | 0 | 3 | 3 | 0 | 4 | 0 | 0.2500 | — |
| length_measure | 14 | 0 | 1 | 13 | 8 | 5 | 8 | 6 | 0.0000 | 0.1667 |
| other | 124 | 10 | 14 | 100 | 51 | 49 | 61 | 63 | 0.1639 | 0.2222 |
| perimeter | 19 | 3 | 3 | 13 | 8 | 5 | 11 | 8 | 0.2727 | 0.3750 |
| ratio | 10 | 3 | 2 | 5 | 5 | 0 | 8 | 2 | 0.3750 | 1.0000 |
| solve_for_variable | 189 | 19 | 23 | 147 | 72 | 75 | 91 | 98 | 0.2088 | 0.2347 |
| **TOTAL** | **601** | **66** | **71** | **464** | **196** | **268** | **262** | **339** | | |

Table consistency checks (all run in code): {'row_sums_equal_total': True, 'col_lost_sums': True, 'col_gained_sums': True, 'col_stable_sums': True, 'grand_total': True}

- **LOST** bucket concentration vs items correct at step 100 (pool n = 262, draw 66): chi-square **11.7769**, null mean 6.0463 (sd 2.9362, 95th pct 11.5905), 10000 permutations at seed 20260729, raw p **0.0461**.
- **GAINED** bucket concentration vs items wrong at step 100 (pool n = 339, draw 71): chi-square **8.8062**, null mean 5.5763 (sd 2.9243, 95th pct 11.2271), 10000 permutations at seed 20260729, raw p **0.1334**.

**Does LOST concentration survive correction?** Raw p 0.0461; Holm-adjusted p **0.1383** over the 10-test family computed in this report; Holm reject at family alpha 0.05: **False**. It also failed Holm inside the earlier 15-test forensics family (reject: False).
GAINED: raw p 0.1334, Holm-adjusted 0.1383, reject: False.

## 2. Difficulty control for the near-miss result

Near-miss rule (identical to the forensics artifact): step-S extracted answer must be contract-valid; pred and gold must both parse numerically and gold != 0; near miss iff |pred-gold|/|gold| <= 0.10. Identical rule to reports/m5c_lost_item_forensics_v1.json.

| design | arm A | rate A | arm B | rate B | difference | raw p | Holm p | controlled for |
|---|---|---|---|---|---|---|---|---|
| uncontrolled (published) | LOST @400 | 11/54 = 0.2037 | stable-wrong @400 | 20/230 = 0.0870 | +0.1167 | 0.0179 | — | nothing |
| literal matched pool | LOST @400 | 11/54 = 0.2037 | stable_correct @400 | 176/176 = 1.0000 | — | DEGENERATE | — | step-100 correctness |
| matched, non-degenerate | LOST @400 | 11/54 = 0.2037 | dip-and-recover @first dip | 1/26 = 0.0385 | +0.1652 | 0.0482 | 0.1383 | step-100 correctness |
| \|gold\|-stratified | LOST @400 | — | stable-wrong @400 | — | +0.1201 | 0.0148 | 0.0592 | answer scale |

**The permutation convention matters.** The published p for the uncontrolled near-miss contrast (5.0e-4) uses the subset-draw convention, in which only the small arm carries sampling variance. The same data under arm-label permutation, which treats both arms as exchangeable, gives a much larger p. The matched design CANNOT be run under the subset-draw convention because its reference arm has fewer numeric-comparable items than the LOST arm, so a same-size subset cannot be drawn. The like-for-like comparison of unmatched vs matched is therefore arm-label vs arm-label.

Published subset-draw convention reproduced here: p 0.0005 (published value 0.0005). Same data, arm-label permutation: p 0.0179. Matched design, arm-label permutation: p 0.0482.

Like-for-like: arm-label p 0.0179 (unmatched, effect +0.1167) -> 0.0482 (matched, effect +0.1652); the effect SIZE is preserved or larger under matching, the p rises because the matched reference arm has only 26 numeric-comparable items.

**Why the literal matched pool is degenerate.** STABLE_CORRECT items are CORRECT at step 400 by definition, so their step-400 extracted answer equals gold and |pred-gold|/|gold| = 0 <= 0.10 for every numeric-comparable item. The reference near-miss rate is therefore 1.0 by construction and the contrast cannot test the hypothesis in this direction.

**The non-degenerate matched design.** Both arms restricted to items CORRECT at step 100, and both arms measured on a WRONG answer. Arm A = LOST(100->400), wrong answer taken at step 400. Arm B = DIP-AND-RECOVER: correct at 100, correct at 400, wrong at at least one of steps 150/200/300; wrong answer taken at the FIRST such step.

Among items correct at step 100, 'wrong at step S' IS the definition of LOST(100->S). There is therefore no set that is simultaneously matched on step-100 correctness, measured on a wrong answer, and not lost at the same step. The only free axis is the step at which the wrong answer is read, so the matched reference must be read at an earlier checkpoint. That checkpoint difference is a genuine limitation of this design and is not removed.

Reference arm size 34; first-dip step histogram {150: 17, 200: 9, 300: 8}.

**Scale control.** the answer-scale confound: the near-miss window is +/-10% of gold, so its width scales with |gold|. It does NOT control step-100 correctness. |gold| quartile cuts [10.375, 34.8, 76.0]; median |gold| LOST 25.50 vs stable-wrong 33.00.

| \|gold\| stratum | range | n LOST | n stable-wrong | near-miss rate LOST | near-miss rate stable-wrong |
|---|---|---|---|---|---|
| 0 | [0.333, 10] | 18 | 53 | 0.2222 | 0.0943 |
| 1 | [10.5, 34.6] | 9 | 62 | 0.4444 | 0.0806 |
| 2 | [35, 74] | 15 | 55 | 0.0000 | 0.0909 |
| 3 | [76, 1.21e+03] | 12 | 60 | 0.2500 | 0.0833 |

**Does the effect survive matching?** QUALIFIES -- raw p significant at 0.05 but does NOT survive Holm over this report's 10-test family (row L11); scale-stratified: QUALIFIES -- raw p significant at 0.05 but does NOT survive Holm over this report's 10-test family (row L12).

## 3. Margin / confidence collapse — field census

**NO. No logprob, token-probability, logit, decoding-score or margin field exists in any of the five cached geo3k per-item files.**

| step | per_item.jsonl | fields | fields matching logprob/score/margin candidates |
|---|---|---|---|
| 100 | `experiments/runs/blind_solvability_v2_guarded_rescore_anchor_step100_geo3k_real_login_20260712T082107Z/per_item.jsonl` | 61 | `guarded_rescore_source_row_sha256`, `guarded_rescore_source_run`, `guarded_rescore_version` |
| 150 | `experiments/runs/m5_geo3k_step150_an12_gpu4_20260718T051839Z/per_item.jsonl` | 39 | **none** |
| 200 | `experiments/runs/m5_geo3k_step200_an29_gpu4_20260722T141052Z/per_item.jsonl` | 39 | **none** |
| 300 | `experiments/runs/m5_geo3k_step300_an12_gpu0_20260726T083303Z/per_item.jsonl` | 39 | **none** |
| 400 | `experiments/runs/m5_geo3k_step400_an12_gpu0_20260728T053115Z/per_item.jsonl` | 39 | **none** |

The only substring hits anywhere are at step 100: guarded_rescore_source_row_sha256, guarded_rescore_source_run and guarded_rescore_version. They match because 'rescore' contains 'score'. They are a provenance sha256, a run id and a version string. Steps 150/200/300/400 have zero substring hits. There is no true logprob/score/margin field at any step.

The step-100 guarded-rescore file carries p_greedy, p_sample, canonical_p_sample, p_i_jeffreys, variance_proxy, q_i and pass_at_k16. These are summaries of a 16-sample temperature-1.0 decode (sample_count = 16) plus the binary greedy outcome. They are empirical correctness FREQUENCIES, not token logprobs and not a decoding margin. Steps 150/200/300/400 have no sampled decode at all: the only numeric non-binary fields there are format_reward / training_reward / canonical_eval_reward / pilot_accuracy_reward, which are deterministic functions of the binary correctness and format flags (verified: those four fields take exactly 4 distinct joint values across 601 items at step 400).

**Verdict: NOT MEASURABLE. The requested comparisons -- step-100 margin of LOST vs STABLE_CORRECT, and step-400 margin of LOST vs STABLE_WRONG -- cannot be run on cached data. No proxy is substituted for the margin.**

There is no sampled decode at step 400 in the cached set, so not even a sampled pass-rate analogue exists at the second endpoint. A step-400 16-sample run (experiments/runs/m5c_sampled_m5c-taskb-step400_an29_gpu4_20260730T122620Z) was in flight for M5C Task B while this report was being written and was incomplete; it is not used here.

### Separate measurement that is NOT the margin test

What it is: step-100 16-sample temperature-1.0 empirical pass rate (canonical_p_sample) of LOST(100->400) items vs STABLE_CORRECT items, both correct at greedy step 100.

What it is not: It is NOT the logprob/margin comparison requested, and it is NOT offered as a proxy for one. The margin comparison stays NOT MEASURABLE. This is a separate, directly measured quantity from a different decode (temperature 1.0, n=16) that exists only at step 100. It is reported as its own line in the ledger and is included in the Holm family. A reader who wants only the requested test should read the verdict above.

LOST mean canonical_p_sample 0.4233 (median 0.4375, n=66) vs STABLE_CORRECT 0.7886 (median 0.8750, n=196); difference -0.3653; two-sided permutation p <= 1e-04, Holm-adjusted 0.0010.

## 4. Five-step pattern structure vs independence

Per-step marginal accuracy: step 100 = 0.435940, step 150 = 0.469218, step 200 = 0.489185, step 300 = 0.474210, step 400 = 0.444260.
32 of 32 possible 5-bit patterns occur. never correct 198, always correct 162, moved at least once 241. Total adjacent flips 429; items with zero flips 360.

### Null N1 — each item flips independently between steps at the observed per-step rates

Each item's state at each step is an independent Bernoulli draw at that step's OBSERVED marginal accuracy; items are exchangeable. Per replicate the expected pattern counts are refit from the replicate's own marginals (parametric bootstrap), so the statistic is calibrated the same way as the observed one.

| statistic | observed | null mean | null sd | null extreme | raw p | Holm p |
|---|---|---|---|---|---|---|
| G² likelihood ratio (32 patterns) | 1289.8185 | 26.4386 | 7.2666 | max 70.9135 | <= 1e-04 | 0.0010 |
| Pearson X² (32 patterns) | 3070.9523 | 26.1476 | — | max 73.8267 | <= 1e-04 | 0.0010 |
| total adjacent flips | 429 | 1197.04 | 24.55 | min 1091 | <= 1e-04 | 0.0010 |
| never correct | 198 | 26.82 | — | — | <= 1e-04 | not in family |
| always correct | 162 | 12.66 | — | — | <= 1e-04 | not in family |
| items with zero flips | 360 | 39.48 | — | — | <= 1e-04 | not in family |

Analytic expected total flips under N1: 1197.17. Asymptotic df, reference only: {'32_cells_minus_1': 31, 'minus_5_fitted_marginals': 26}.

**Direction vs N1:** MORE PERSISTENCE than independence: observed total adjacent flips 429 vs null mean 1197.0; observed items with zero flips 360 vs null mean 39.5; observed never-correct 198 vs null mean 26.8; observed always-correct 162 vs null mean 12.7.

### Nulls N2 and N3 — hold each item's own difficulty fixed, randomise only the temporal order

- **N2.** Each item keeps its own number of correct steps; the five step labels are permuted uniformly within the item. Item difficulty is held fixed and only the temporal ORDER is randomised. Does not preserve per-step column margins. Observed flips 429 vs null mean 480.62 (sd 11.41, min 438), raw p(flips ≤ observed) <= 1e-04, Holm 0.0010.
- **N3.** Curveball trades on the 601x5 binary matrix, preserving every item's number of correct steps AND every step's accuracy count exactly. 20000 burn-in trades, 200 trades between successive samples. Margins preserved at every sample: True. Observed flips 429 vs null mean 480.99 (sd 11.16, min 439), raw p(flips ≤ observed) <= 1e-04, Holm 0.0010.

**Direction vs N2/N3:** observed flips 429 vs N2 null mean 480.6 and N3 null mean 481.0. Sign of (observed - null mean) determines whether states are sticky (negative) or alternating (positive) once each item's own number of correct steps is held fixed.

Observed − null-mean flips: N1 -768.04, N2 -51.62, N3 -51.99.

Pattern-by-pattern observed vs independence expectation (steps 100/150/200/300/400):

| pattern | steps correct | flips | observed | expected under N1 | obs − exp |
|---|---|---|---|---|---|
| `00000` | 0 | 0 | 198 | 26.86 | +171.14 |
| `11111` | 5 | 0 | 162 | 12.67 | +149.33 |
| `01111` | 4 | 1 | 22 | 16.39 | +5.61 |
| `10000` | 1 | 1 | 19 | 20.76 | -1.76 |
| `00111` | 3 | 1 | 16 | 18.54 | -2.54 |
| `00010` | 1 | 2 | 13 | 24.22 | -11.22 |
| `00100` | 1 | 2 | 13 | 25.72 | -12.72 |
| `00001` | 1 | 1 | 12 | 21.47 | -9.47 |
| `01000` | 1 | 2 | 11 | 23.74 | -12.74 |
| `00110` | 2 | 2 | 10 | 23.20 | -13.20 |
| `01100` | 2 | 2 | 10 | 22.74 | -12.74 |
| `11000` | 2 | 1 | 10 | 18.35 | -8.35 |
| `01110` | 3 | 2 | 9 | 20.51 | -11.51 |
| `11100` | 3 | 1 | 9 | 17.57 | -8.57 |
| `11110` | 4 | 1 | 9 | 15.85 | -6.85 |
| `10100` | 2 | 3 | 8 | 19.88 | -11.88 |
| `11011` | 4 | 2 | 8 | 13.23 | -5.23 |
| `11101` | 4 | 2 | 8 | 14.05 | -6.05 |
| `10111` | 4 | 2 | 7 | 14.33 | -7.33 |
| `01001` | 2 | 3 | 6 | 18.98 | -12.98 |
| `01011` | 3 | 3 | 5 | 17.12 | -12.12 |
| `10011` | 3 | 2 | 5 | 14.97 | -9.97 |
| `00011` | 2 | 1 | 4 | 19.36 | -15.36 |
| `01010` | 2 | 4 | 4 | 21.41 | -17.41 |
| `01101` | 3 | 3 | 4 | 18.18 | -14.18 |
| `10010` | 2 | 3 | 4 | 18.72 | -14.72 |
| `11010` | 3 | 3 | 4 | 16.55 | -12.55 |
| `10001` | 2 | 2 | 3 | 16.59 | -13.59 |
| `10110` | 3 | 3 | 3 | 17.93 | -14.93 |
| `00101` | 2 | 3 | 2 | 20.56 | -18.56 |
| `10101` | 3 | 4 | 2 | 15.89 | -13.89 |
| `11001` | 3 | 2 | 1 | 14.67 | -13.67 |

## 5. Multiplicity

The ten permutation tests COMPUTED IN THIS REPORT under acc_final. The acc_strict family is numerically identical because acc_final == acc_strict on all 601 items at all five steps (verified here).
Family alpha 0.05, 10 tests, plain Bonferroni threshold 0.005000.

| test | raw p | Holm rank | Holm threshold | Holm-adjusted p | reject at 0.05 |
|---|---|---|---|---|---|
| `T5_step100_sampled_pass_rate_lost_vs_stable_correct_two_sided` | <= 1e-04 | 1 | 0.005000 | 0.0010 | True |
| `T6_pattern_G2_vs_independence` | <= 1e-04 | 2 | 0.005556 | 0.0010 | True |
| `T7_pattern_X2_vs_independence` | <= 1e-04 | 3 | 0.006250 | 0.0010 | True |
| `T8_total_flips_vs_independence` | <= 1e-04 | 4 | 0.007143 | 0.0010 | True |
| `T9_total_flips_vs_within_item_order_permutation` | <= 1e-04 | 5 | 0.008333 | 0.0010 | True |
| `T10_total_flips_vs_row_col_margin_preserving` | <= 1e-04 | 6 | 0.010000 | 0.0010 | True |
| `T4_near_miss_gold_magnitude_stratified_one_sided` | 0.0148 | 7 | 0.012500 | 0.0592 | False |
| `T1_lost_bucket_chi2` | 0.0461 | 8 | 0.016667 | 0.1383 | False |
| `T3_near_miss_matched_dip_and_recover_one_sided` | 0.0482 | 9 | 0.025000 | 0.1383 | False |
| `T2_gained_bucket_chi2` | 0.1334 | 10 | 0.050000 | 0.1383 | False |

Excluded from this family, and why:
- `literal_matched_pool_lost_vs_stable_correct` — DEGENERATE by construction (reference rate = 1.0 because STABLE_CORRECT items are correct at step 400), so it is not a test of the hypothesis and no p is entered into the family.
- `uncontrolled_near_miss_contrast` — Already published and Holm-corrected inside the 15-test family of reports/m5c_lost_item_forensics_v1.json; recomputed here for continuity, not re-entered into this family.
- `prior_published_tests` — McNemar exact p values, the 3-way/pairwise Jaccard tests and the wrong-answer concentration tests belong to the earlier families in reports/m5c_turnover_v1.json and reports/m5c_lost_item_forensics_v1.json; their own corrections are carried through into the ledger and are not recomputed.

## Task B status

M5C Task B (expected-discordance null from sampled p_i at both endpoints) had NOT emitted a report at the time this ledger was written; its two sampled evals were still writing rows. The ledger therefore carries Task A's measured floor (L03) and the superseded prior reference (L04) but no Task B result. This is a gap in the ledger, not a null result.

- `step400_sampled`: `experiments/runs/m5c_sampled_m5c-taskb-step400_an29_gpu4_20260730T122620Z` — 572/601 rows written when this report read it.
- `step100_sampled_repro`: `experiments/runs/m5c_sampled_m5c-taskb-step100-repro_an29_gpu5_20260730T122701Z` — 601/601 rows written when this report read it.

## Scope limits

- **derived_buckets_are_analysis_defined** — The problem-type buckets are regex rules defined by the earlier forensics analysis and reused verbatim here. They are NOT dataset metadata: qid and source_metadata are null on all 601 test rows at all five steps and the manifest carries only answer/images/problem/row_index/split. Any bucket-level result is a result about these rules, not about a curated taxonomy.
- **serial_dependence** — All five checkpoints come from ONE training trajectory. Permutation nulls here randomise item membership or within-item temporal order; none of them removes dependence between checkpoints of the same run.
- **no_second_trajectory** — There is no second training seed for this trajectory in this analysis, so nothing here separates 'this run's churn' from 'churn of this recipe'.
- **matched_near_miss_caveat** — The only non-degenerate step-100-matched reference for the near-miss contrast reads its wrong answer at an EARLIER checkpoint than the LOST arm. That asymmetry is inherent to the design space, not a choice that could have been avoided.

## Provenance

- substrate: `reports/m5c_item_substrate_v1.jsonl` sha256 `1fc5310785680afbf5420166c97d776ea77ab0b4081533097fd225648882a864`
- turnover: `reports/m5c_turnover_v1.json` sha256 `7584ee6b070dfe4f73a7b017913f40206fffb99973ea8809bc9024f7c9752a73`
- forensics: `reports/m5c_lost_item_forensics_v1.json` sha256 `4feba1f2a09b65750d2969919235ceba8cec6521d6a7ad4d7f7a61352b50e532`
- noise_floor_task_a: `reports/m5c_noise_floor_replicate_v1.json` sha256 `54e5e8c3f5d07deb8f2ed093ba9c1cb6fb73fd37753c0da7fac5bf29a408c7e5`
- step 100: `experiments/runs/blind_solvability_v2_guarded_rescore_anchor_step100_geo3k_real_login_20260712T082107Z/per_item.jsonl`
- step 150: `experiments/runs/m5_geo3k_step150_an12_gpu4_20260718T051839Z/per_item.jsonl`
- step 200: `experiments/runs/m5_geo3k_step200_an29_gpu4_20260722T141052Z/per_item.jsonl`
- step 300: `experiments/runs/m5_geo3k_step300_an12_gpu0_20260726T083303Z/per_item.jsonl`
- step 400: `experiments/runs/m5_geo3k_step400_an12_gpu0_20260728T053115Z/per_item.jsonl`
- scorer: `src.eval.blind_solvability.score_greedy_item_pilot under DEFAULT_PROMPT_CONTRACT (uniform re-score of cached predictions)`
- permutation convention: p = (hits+1)/(n_perm+1), n_perm = 10000, seed = 20260729, reported as max(p, 1e-04); reported as max((hits+1)/(n_perm+1), 1e-4); the floor binds only at zero hits

