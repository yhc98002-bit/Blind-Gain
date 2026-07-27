# X-series synthesis — Paper-1 evidence map (v3)

Supersedes `reports/x_series_synthesis_v2.md`. v3 adds the completed
**three-seed replication (Track C1)**, the **D2 test-time image-access**
readout, and the **B1 trained-checkpoint** scoring. Facts and registered
readings only; no interpretation beyond the registered documents. Layer names:
candidate-evidence ranking / open-form realization. "Already perceived/
understood" remains hypothesis language (X2 bottom branch,
`docs/registered_x2_ladder_v1.md`). Ordering follows RESEARCH_DOC §11.

Status at 2026-07-27: seeds 1–3 complete; M5 long-horizon at step 345/400;
Mini-A5 and M7 built and queued behind hardware availability (an29 blocked by a
full node root filesystem, admin request outstanding).

## 1. The replication rung (Track C1, NEW in v3)

Three seeds, four matched arms, 601 held-out Geometry3K items per seed, all
step-100 endpoints registered before measurement.

**Task gain (Acc_final, step 100 − step 0):**

| arm | seed 1 | seed 2 | seed 3 | mean |
|---|---|---|---|---|
| A1 real | +0.2529 | +0.2463 | +0.2313 | **+0.2435** |
| A3 caption | +0.1098 | +0.0832 | +0.1215 | +0.1048 |
| A2b no-image | +0.0300 | +0.0549 | +0.0532 | +0.0460 |
| A2 gray | +0.0200 | +0.0100 | +0.0183 | +0.0161 |

**Recovery of the A1 gain:** gray 7.9 / 4.1 / 7.9% (mean 6.6%); no-image
11.8 / 22.3 / 23.0% (19.1%); caption 43.4 / 33.8 / 52.5% (43.2%). The
preregistered 30–70% blind-recovery interval is falsified in every seed for
both zero-visual-bit arms.

**Registered geometry FlipTrack endpoint (pair accuracy, step 100 − step 0):**

| arm | seed 1 | seed 2 | seed 3 | mean | seed-level 95% CI | within ±0.05 |
|---|---|---|---|---|---|---|
| A1 real | −0.0017 | +0.0083 | +0.0100 | **+0.0056** | [−0.0016, +0.0127] | yes |
| A3 caption | −0.0083 | −0.0117 | +0.0050 | −0.0050 | [−0.0150, +0.0050] | yes |
| A2b no-image | −0.0233 | −0.0250 | −0.0333 | −0.0272 | [−0.0333, −0.0212] | yes |
| A2 gray | −0.0450 | −0.0450 | −0.0367 | −0.0422 | [−0.0477, −0.0368] | yes |

**A1 equivalence verdict: supported within the registered band.** The caption
inversion (A3 starts above A1 at step 0 and ends below it at step 100)
replicates in all three seeds. Source: `reports/three_seed_summary_v1.{md,json}`,
built from the three registered four-arm readouts.

Defect caught and corrected before it propagated: the first seed-3 readout
inherited `geo_audits` from the seed-2 template and returned values
byte-identical to seed 2. The plan's verification rule (seed 3 must not
reproduce seed 2 exactly) surfaced it; the builder now resolves the seed-3
audits itself and fails closed. Recorded in commit `ac3f362`.

## 2. Test-time image access (D2, NEW in v3)

Registered before inference (`docs/registered_d2_testtime_ablation_v1.md`),
eight cells on the frozen 601-row set, decoding contract identical to the
registered pilot evaluations; base cells pinned from the registered arm step-0
evaluations rather than re-measured.

| seed | Acc(A1, real) | Acc(A1, none) | RetainedGainBlind | band |
|---|---|---|---|---|
| 1 | 0.4276 | 0.1082 | 0.158 | (a) image-mediated |
| 2 | 0.4210 | 0.0982 | 0.122 | (a) image-mediated |

**Registered verdict: `a_image_mediated_at_test_time`,** both seeds agreeing.
The reproduction check reproduced the published step-100 values exactly.

Registered secondary, and the result most likely to bear on the canonical
claim: **A2b — trained with no images at all — reaches 0.3195 / 0.2962 when
evaluated *with* images**, against its published blind 0.0982 / 0.1231, a
test-time image benefit of **+0.221 / +0.173**. Source:
`reports/d2_testtime_ablation_v1.{md,json}`.


## 3. B1 trained-checkpoint scoring (NEW in v3)

Registered pre-inference (`docs/registered_b1_trained_v1.md`); declared batch unchanged; base rates pinned. Registered branches (a) and (b) both required fact-read improvement, which did not occur (base 0.600 vs 0.500-0.550 in every trained arm), so the reading is **no_registered_branch**; `chained_premise` remains at floor for all four models, triggering the pre-committed reading that the chained construct is **not discriminative at 3B**. Descriptive: `prior_conflict` rises in every arm including the blind-trained A2b (0.143 -> 0.286-0.429), so that movement is not image-mediated. Cells are 14-20 pairs; point estimates only. Source: `reports/b1_trained_scoring_v1.{md,json}`.

"already perceived/understood" remains hypothesis language only (X2 bottom
branch; docs/registered_x2_ladder_v1.md). Ordering follows RESEARCH_DOC §11:
strengths first; every registered endpoint appears as pivot, finding, or
robustness evidence.

Sources: the M3 pilot endpoint readouts (seeds 1–2),
reports/seed1_visual_evidence_ranking_results_v1.*,
reports/x1_image_condition_matrix_v1.*, x5_seed2_*,
x2_hard_negative_ranking_v1.*, x3_a2_degradation_forensics_v1.*,
x4_visual_evidence_calibration_v1.* (EXPLORATORY),
blindarm_margin_calibration_results_v1.*, geometry_track_prototype_v1.*,
reports/blind_solvability_virl39k_sample_v1.json (frozen M7 basis).

## 4. The registered pilot endpoints (seeds 1–2, complete)

Geometry3K accuracy, step 0 → step 100, with recovery of the A1 gain:

| arm | seed 1 gain (recovery) | seed 2 gain (recovery) |
|---|---|---|
| A1 real | +0.2529 (100%) | +0.2463 (100%) |
| A3 caption | +0.1098 (43.4%) | +0.0832 (33.8%) |
| A2b no-image | +0.0300 (11.8%) | +0.0549 (22.3%) |
| A2 gray | +0.0200 (7.9%) | +0.0100 (4.1%) |

The preregistered expectation that zero-visual-bit training recovers 30–70%
of A1 is falsified in both seeds. The caption inversion replicates: A3 starts
above A1 (0.2097 vs 0.1747 at step 0) and ends below it in both seeds.

Registered Geometry FlipTrack endpoint (pair accuracy, real images): A1
−0.0017 (seed 1) and +0.0083 (seed 2) against base 0.4717 — within the
no-material-change region in both seeds, against a +25pp task gain. A2 gray
declines exactly −0.0450 in both seeds (item-level forensics in §C).

## 4b. Registered seed-1 visual-evidence ranking readout

The registered image-dependent paired-margin effect (A1 vs base, real minus
no-image, primary template): +0.0891 at step 60 and +0.1501 [0.1448, 0.1554]
at step 100, with discrete pair success, top-1, and MRR flat — the finding
the calibration (§B), X1/X5 (§A), and X2 (§D) subsequently decomposed.

## 5. Sharpening is content-bound, in both completed seeds (X1, X5)

Margin inflation under a same-template mismatched real image is statistically
zero for every trained arm in both seeds (all CIs span zero; |mean| ≤ 0.0006),
while correct-image inflation is far from zero for every arm:

| arm (step 100) | seed-1 correct-image inflation | seed-2 correct-image inflation | mismatched (both seeds) |
|---|---|---|---|
| A1 real | +0.1501 [+0.1448, +0.1554] | +0.1293 [+0.1241, +0.1345] | ≈ 0, CI spans 0 |
| A3 caption | +0.0900 [+0.0866, +0.0934] | +0.0760 [+0.0732, +0.0788] | ≈ 0, CI spans 0 |
| A2b no-image | +0.0348 [+0.0327, +0.0369] | +0.0577 [+0.0553, +0.0601] | ≈ 0, CI spans 0 |
| A2 gray | +0.0356 [+0.0337, +0.0375] | +0.0373 [+0.0352, +0.0394] | ≈ 0, CI spans 0 |

Registered-reading note: the ratio bands of docs/registered_x1_matrix_v1.md
degenerate at a statistically-zero denominator (arbitrary sign at |mean|~1e-4);
mechanical labels are recorded per arm in the reports.

Direct content sensitivity (reading c): under the twin member's image the
twin's gold is preferred over the own gold for 0.949–0.955 of members — for
every model including the frozen base — and open-form pair-correct is ≤ 0.006
under mismatched images and exactly 0 under twin/gray/no-image for all models
in both seeds.

## 6. The information-access gradient (registered calibration + X5)

Real-input margin effects order gray ≈ no-image < caption < real in seed 1
(+0.036 / +0.035 / +0.090 / +0.150) and reproduce in seed 2 with the known
seed-2 A2b>A2 ordering (+0.037 / +0.058 / +0.076 / +0.129). Blind-condition
margins are structurally zero in all 30 integrity cells (seed 1). The same
ordering appears in the Geometry3K task-gain recovery tables (seeds 1–2).

## 7. Blind-reward corrosion is item-identifiable and answer-deterministic (X3)

The exact −0.0450 A2 geometry decline (both seeds) resolves to correct→wrong
sets of 51 and 49 pairs with 42 shared: Jaccard 0.7241 against a permutation
null of 0.0978 (p = 1e-4, 10k draws). On shared wrong member slots the same
extracted wrong answer appears in 41/42 (0.9762). Transition taxa are
dominated by nearest-gridline off-by-ones (19/20 across seeds), then other
scene-point x values; the counterfactual twin's gold appears once per seed.
On the 42 shared items every arm is disproportionately wrong (A1 26–28/42,
A2b 34–38/42, A3 30–32/42 versus 28–43/283 on all base-correct items).

## 8. The two-layer gap, re-scoped by the registered ladder (X2)

The golds-only margin statistic is candidate-set-invariant by construction
and empirically: exactly 0.9067 in v1 and v2 for base and both A1 checkpoints,
zero pair-level disagreements. Against the structured negative sets
(five registered types, symmetric composition, 600 exactly-replayed scenes)
base against-set pair-success is 0.5167 [0.4750, 0.5567]; A1 step-60 0.5267,
step-100 0.5133. Registered ladder branch (mechanical, point estimate):
< 0.55 — the 0.9067 is predominantly candidate-set structure; the realization
gap is reported as a measurement-methods finding. The branch ships without
renegotiation; the CI spanning the boundary is recorded.

## 9. Confidence follows the image, not the truth (X4 — EXPLORATORY)

Member-level top-candidate confidence is identical under real and
twin-counterfactual images by construction (same image-question multiset)
while accuracy moves from ~0.75 to ~0.012: overconfidence gap +0.17–0.19
under twins for every model. Under real images all models are underconfident
(confidence ~0.18–0.20 vs accuracy ~0.75; ECE ~0.57); blind and mismatched
conditions sit near chance with near-uniform confidence.

## 10. Track-B construct calibration (B1, one declared batch)

Base-model pair-correct on the declared 100-pair batch (real / blind /
caption): fact-read 0.600 / 0 / 0; style-twin invariance 0.643; distractor
invariance 0.438; binding swap 0.188; prior-conflict 0.143 (versus 0.600
fact-read; member level 0.429 versus 0.700); chained two-hop 0.000 pair,
0.150 member. Overall real 0.33, blind 0.03, caption 0.04. Instrument note:
consistency pairs are single-gold scored because the frozen two-gold
ambiguity guard structurally fails equal-gold items.

## 11. ViRL39K basis for M7 (frozen)

The 3B blind-solvability audit of ViRL39K is the registered basis of the M7
within-corpus mechanism prediction: per-condition, per-answer-type
reward-opportunity estimates are frozen in
`reports/blind_solvability_virl39k_sample_v1.json` (for example, the
caption-condition multiple-choice stratum: q̄ 0.372 [0.358, 0.386],
n = 1,307); the audited 7B result is corroborating only. The 29,756-item
training subset is frozen and decontaminated
(`reports/decon_virl39k_vs_layer1_v1.*`), and the full question-blind 3B
caption store is audited at 28,768/28,768 coverage
(`reports/virl39k_caption_store_audit_v1.json`).

## Human-gated evidence (packets ready, not yet reviewable as findings)

- Chart-v08 no-zoom audit (`reports/human_audit_viewer_v3.md`).
- Qualitative review of the 24 support-expansion candidates
  (`reports/support_sharpening_seed1_v2.{md,json}`).
- R19 human audit (now) and R20 audit sample (this week) per RESEARCH_DOC.
- X6 related-work audit table (PI-owned; slot reserved for the novelty
  paragraph and its nine-column table).

## Registered evidence still to land (slots reserved)

- Seed-3 endpoints + three-seed pooled equivalence verdict (evaluation
  lifecycle armed; cohort release on A3 completion).
- Mini-A5 trainability contrast (PI-authorized; launches at the seed-3 queue
  drain) — decides whether pair consistency is optimizable at all.
- M5 step-400 long-horizon terminal readout (segments self-driving).
- M7 ViRL39K stratified decomposition (data frozen and audited; configs,
  parquets, launcher pending).
- Seed-3 instance of the X3 overlap (computable from the eval dumps at no
  extra GPU cost).

## PI decision hooks (owned by PIs, not the executor)

1. Paper-1 emphasis after the X2 bottom branch: candidates are A
   (content-bound sharpening), B (gradient), C (corrosion), D
   (measurement-methods realization gap), with Mini-A5 as the constructive
   arc if it prints.
2. Whether the ratio-band degeneracy in the X1/X5 registration warrants a
   registered amendment re-expressing reading (b) (e.g., correct-CI excludes
   zero AND mismatched-CI contains zero); the current mechanical labels are
   recorded as registered.
3. M7 two-seed budget versus an earlier single 7B contrast under wall-clock
   pressure.
