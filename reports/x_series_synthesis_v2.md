# X-series synthesis — Paper-1 evidence map (v2)

Supersedes reports/x_series_synthesis_v1.md (X-dispatch-only scope). v2 adds
the registered pilot endpoints (seeds 1-2), the seed-1 ranking readout, the
frozen ViRL39K/M7 basis, and the human-gated appendix — the complete map of
evidence in hand at 2026-07-25.

Facts and registered readings only; no interpretation beyond the registered
documents. Layer names: candidate-evidence ranking / open-form realization.
"Latent preference for the correct answer" is the licensed construct term;
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

## 0. The registered pilot endpoints (seeds 1–2, complete)

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

## 0b. Registered seed-1 visual-evidence ranking readout

The registered image-dependent paired-margin effect (A1 vs base, real minus
no-image, primary template): +0.0891 at step 60 and +0.1501 [0.1448, 0.1554]
at step 100, with discrete pair success, top-1, and MRR flat — the finding
the calibration (§B), X1/X5 (§A), and X2 (§D) subsequently decomposed.

## A. Sharpening is content-bound, in both completed seeds (X1, X5)

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

## B. The information-access gradient (registered calibration + X5)

Real-input margin effects order gray ≈ no-image < caption < real in seed 1
(+0.036 / +0.035 / +0.090 / +0.150) and reproduce in seed 2 with the known
seed-2 A2b>A2 ordering (+0.037 / +0.058 / +0.076 / +0.129). Blind-condition
margins are structurally zero in all 30 integrity cells (seed 1). The same
ordering appears in the Geometry3K task-gain recovery tables (seeds 1–2).

## C. Blind-reward corrosion is item-identifiable and answer-deterministic (X3)

The exact −0.0450 A2 geometry decline (both seeds) resolves to correct→wrong
sets of 51 and 49 pairs with 42 shared: Jaccard 0.7241 against a permutation
null of 0.0978 (p = 1e-4, 10k draws). On shared wrong member slots the same
extracted wrong answer appears in 41/42 (0.9762). Transition taxa are
dominated by nearest-gridline off-by-ones (19/20 across seeds), then other
scene-point x values; the counterfactual twin's gold appears once per seed.
On the 42 shared items every arm is disproportionately wrong (A1 26–28/42,
A2b 34–38/42, A3 30–32/42 versus 28–43/283 on all base-correct items).

## D. The two-layer gap, re-scoped by the registered ladder (X2)

The golds-only margin statistic is candidate-set-invariant by construction
and empirically: exactly 0.9067 in v1 and v2 for base and both A1 checkpoints,
zero pair-level disagreements. Against the structured negative sets
(five registered types, symmetric composition, 600 exactly-replayed scenes)
base against-set pair-success is 0.5167 [0.4750, 0.5567]; A1 step-60 0.5267,
step-100 0.5133. Registered ladder branch (mechanical, point estimate):
< 0.55 — the 0.9067 is predominantly candidate-set structure; the realization
gap is reported as a measurement-methods finding. The branch ships without
renegotiation; the CI spanning the boundary is recorded.

## E. Confidence follows the image, not the truth (X4 — EXPLORATORY)

Member-level top-candidate confidence is identical under real and
twin-counterfactual images by construction (same image-question multiset)
while accuracy moves from ~0.75 to ~0.012: overconfidence gap +0.17–0.19
under twins for every model. Under real images all models are underconfident
(confidence ~0.18–0.20 vs accuracy ~0.75; ECE ~0.57); blind and mismatched
conditions sit near chance with near-uniform confidence.

## F. Track-B construct calibration (B1, one declared batch)

Base-model pair-correct on the declared 100-pair batch (real / blind /
caption): fact-read 0.600 / 0 / 0; style-twin invariance 0.643; distractor
invariance 0.438; binding swap 0.188; prior-conflict 0.143 (versus 0.600
fact-read; member level 0.429 versus 0.700); chained two-hop 0.000 pair,
0.150 member. Overall real 0.33, blind 0.03, caption 0.04. Instrument note:
consistency pairs are single-gold scored because the frozen two-gold
ambiguity guard structurally fails equal-gold items.

## G. ViRL39K basis for M7 (frozen)

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
