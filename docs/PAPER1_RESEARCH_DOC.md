# Paper 1 — Research Document
*Learning Without Looking: Image-Dependent Gains from Image-Free RLVR*

Living document. PIs own all sections except §6–§7 evidence tables, which the executor updates with each ledger pass. Operational detail lives in `EXPERIMENT_TODO.md`; the method sequel lives in `PAPER2_RESEARCH_DOC.md`. Updated 2026-07-27.

## 1. Title and framing guard

**Title (frozen 2026-07-27):** *Learning Without Looking: Image-Dependent Gains from Image-Free RLVR.*

**Guard:** the title omits the model class, so the abstract's first sentence and the introduction's first paragraph must establish that this is an RLVR stage applied to a *pretrained vision-language model*. "Image-free" refers to the RL stage only, never to pretraining. Same guard applies to talk titles and slides.

## 2. Canonical claim and the ladder

**Claim.** Multimodal RLVR needs images at inference, not at training. Most of what standard RLVR teaches on Geometry3K is learnable with no visual input at all — training entirely without images captures roughly half the image-present improvement — while every layer of visual competence we can certify stays where it started. What training reliably changes is the confidence placed on answers the model already prefers, and only when the correct image is present.

**Ladder** (scope tags drop when a rung lands, never rhetorically): R1 three seeds on geo3k (in hand) → R2 long-horizon to step 400 (running) → R3 second corpus, ViRL39K stratified (built) → R4 scale, 7B access pair → R5 cross-family audits.

## 3. Narrative arc (section = claim = figure)

1. **F1 — The access matrix.** Train {real, none} × test {real, none}: +0.243 / ~+0.040 / +0.145 / +0.046. Inference-time access is necessary for the gain; training-time access is worth about half of it. The same checkpoint reports 12–23% or ~50% recovery depending only on the evaluation condition — an ablation-practice result for the field.
2. **F2 — The exchange rate, and where it lands.** +24.4 benchmark points buy +2.5 points of overall certified counterfactual pair accuracy (CIs excluding zero, 3/3 seeds); on the registered geometry primary, +0.006. The instrument moves — it is not a dead ruler — which is what makes the asymmetry a measurement rather than a failure to detect. **Decompose the numerator by template and the result sharpens into a mechanism:** the saturated header table sits at 1.000 for every model and contributes nothing to any delta, so the movement concentrates on the oracle-localized readout control — the template where localization is supplied by the cue — while the primary anchor, which requires search, binding, and read, stays flat. The gain lands exactly where the visual work has been done for the model.
3. **F3 — Content-bound sharpening (mechanism).** Margin inflation vs base under the correct image: A1 +0.150, caption +0.090, no-image +0.035, gray +0.036 — an information-ordered gradient. Under a same-template mismatched image: statistically zero for every arm, both seeds. Under the twin's image every model including the frozen base prefers the twin's gold (0.948–0.955).
4. **F4 — What does not move.** Structured hard-negative discrimination: base 0.517, A1 0.513–0.527. Chained premise-to-reasoning at floor for every model. Binding swap flat. Fact-read unimproved.
4b. **F4b — The cue ladder (registered post-hoc decomposition).** One scene family rendered at four cue strengths — exact cue (the current circle), region cue (target series or region only), no cue (question specifies series and abscissa), decoy cue (the circle marks a neighbouring or wrong-series point; gold follows the question). Scored on base and all four arms across three seeds, inference only. Differences between rungs localize the bottleneck to local readout, search, binding, or distractor suppression, and test directly whether RLVR improves readout while leaving search and binding untouched. Registered before scoring; labeled a post-hoc decomposition.
5. **F5 — Blind reward corrodes grounding, item-identifiably.** Gray's exact −0.045, both seeds, resolves to 42 shared pairs (Jaccard 0.724 vs permutation null 0.098, p=1e-4), same extracted wrong answer 41/42, nearest-gridline off-by-one 19/20.
6. **F6 — Confidence tracks image presence, not correctness.** Underconfident when right (≈0.19 vs 0.75 accuracy, ECE 0.57); identical confidence under twin images where accuracy is 0.012 (+0.17–0.19 overconfidence gap).
7. **F7 — Trainability (Mini-A5).** CP-GRPO vs matched same-data standard GRPO on held-out templates.
8. **Prescription.** Ablate at inference, not only at training; report the exchange rate; audit the corpus before spending compute.

**Sub-findings with their own paragraphs:** the caption inversion (3/3 seeds — A3 starts above A1 and ends below); out-of-domain format-transfer cost (FlipTrack contract compliance 0.95 → 0.74/0.99/0.90 under A1); the candidate-set correction (golds-only 0.9067 is candidate-set structure — a methods lesson for every ranking-based evaluation).

## 4. Contributions

- **C1** the access decomposition and the ablation-practice result.
- **C2** the mechanism: content-bound, information-ordered confidence sharpening with flat competence layers.
- **C3** FlipTrack — instrument, generator, validity dossier, multi-layer readout — released as protocol (§5).
- **C4** the blind reward-opportunity audit and corpus shortcut map.
- **C5** blind-reward corrosion as a measured, item-identifiable harm.
- **C6** Mini-A5 as published trainability validation.

## 5. The benchmark (C3)

**Construction.** Render-twice counterfactual minimal pairs: both members generated from one scene program, differing in exactly one answer-changing fact, with identical question text. Success requires both members correct. Blind answering is capped by construction, and there is no original-versus-edited artifact channel because neither member is an edit of the other.

**R19 (frozen, 1,200 pairs) — three tasks, three scientific roles.** Each is reported separately; no unified average is computed across roles.
- *Coordinate survey register* (600 pairs) — locate the label, bind it to the point, read the coordinate. The **primary visual anchor**; base pair accuracy 0.4717. The only R19 task requiring search and binding.
- *Header-cued verification table* (300 pairs) — saturated at 1.000 for every model including base. A **saturated positive control and retention canary**: it cannot show improvement, but any drop is signal that training damaged simple visual readout or the scoring pipeline. Excluded from every capability aggregate.
- *Nine-series calibration trace* (300 pairs) — the circle marks the queried point, supplying localization. The certified construct is **oracle-localized visual readout**: given a target already located, can the model read the local value and does that reading track image content? Reported as a control condition, never as chart reasoning; the legend-to-series localization hop is not certified here.

**R20.** One-shot private twin generated from fresh seeds under the frozen generator, no iteration, no regeneration; failures downgrade certification rather than triggering a retry.

**Validity dossier.** 72B question-blind caption stress ≤0.062; artifact-attacker gates with CIs; blind conditions at exactly 0.000 with answer collapse 1.0; monotone degradation and scale controls; 60/60 human audit with construct notes; cross-family confirmation (InternVL3-9B, Gemma-3) showing no-image collapse and caption ≤0.013.

**Multi-layer readout on identical pairs.** Open-form realization · candidate-evidence ranking · structured hard negatives (same-point other-axis, nearest-neighbour, look-alike label, nearest gridline, twin's gold) · calibration. This decomposition is what separated the utilization result from an apparent competence result.

**Release form.** Instrument + generator + dossier as a protocol rather than a static leaderboard — regeneration from fresh seeds makes it contamination-resistant — plus the blind reward-opportunity audit as a corpus-side tool.

**B1 geometry track (prototype).** Six intervention types with premise probes: fact-read 0.600, style-twin invariance 0.643, distractor-only invariance 0.438, binding swap 0.188, prior-conflict 0.143, chained premise 0.000 pair / 0.150 member. Development continues under Paper 2's build phase, where the track becomes training data as well as evaluation.

## 6. Evidence in hand

Three-seed task gains: A1 +0.2435, A3 +0.1048 (43.2%), A2b +0.0460 (19.1%), A2 +0.0161 (6.6%); strict-format gain larger (+0.3583), so the reported lenient figure is the conservative one. D2 access matrix, 3/3 seeds, verdict image-mediated-at-inference. X1/X5 sharpening table. X2 hard negatives. X3 corrosion forensics. X4 calibration (exploratory). B1 declared batch. Instrument dossier as §5.

**D3 complete (36/36 cells) — F1 closed.** Registered branch (a). TrainShare pooled 0.487 (A2 gray), 0.528 (A2b), 0.718 (A3), every paired item-level CI lying entirely above the 0.35 threshold and all nine seed-arm values in the same branch: **headline at full strength**. Ordering disclosure: the cells were read under the ratio-based D3 registration before TrainShare was computed, so TrainShare is a declared post-hoc recomputation and does not satisfy I9.

**Base endpoint verified.** The step-0 FlipTrack minuend was re-measured from scratch on the locked 1,200-pair R19 manifest and reproduces exactly (geometry lenient 0.4717, strict 0.4433) — verified rather than inherited.

**Equivalence, item-level.** Cluster bootstrap over the 600 pair_ids (3 seeds): A1 equivalent, TOST [−0.0150, +0.0256]; A2 gray **not** equivalent, TOST [−0.0644, −0.0206]; A2b marginal. The published seed-level "within band" verdict for A2 gray was a normal-approximation artefact at n=3. Minimum detectable effect ≈0.034–0.038, below the ±0.05 SESOI, so the A1 null is informative rather than underpowered. Contract validity is a first-class result: every trained arm falls below the frozen base (0.9500), A2 gray lowest at 0.6317.

**Gate 0 (freezes the title claim).** G0.1: gains rise monotonically across Δq terciles for both A1 and A2b (ρ +0.198 / +0.192, perm p ≤ 0.0005) — H1 supported, C1 necessity sampling earns its place. **G0.2 came out opposite to the hypothesis:** A2b's image-present gain concentrates on blind-*answerable* items, recovering 84% of A1's gain where blind reward opportunity exists and 42% where none was observed (91% vs 61% under a base-wrong headroom control). The title claim survives with a scope qualifier — the image-free gain is real on image-requiring items (+0.197) but is disproportionately the blind-attainable component. G0.3: A1/A2b newly-correct sets overlap far above chance (Jaccard 0.363–0.423 vs null 0.157–0.177, p ≤ 0.004) yet share only ~40% of their union. G0.4: format gain is **exactly +0.1148 for all four arms** by identity (every trained arm has `acc_strict == acc_final`, so it collapses to `base_final − base_strict`), hence the access matrix is format-free by construction.

**F2d.** For A1 the movement concentrates on the oracle-localized readout control (+0.0711, CI excludes zero; 70% of the overall figure) while the primary visual anchor is flat (+0.0056, CI spans zero; 11%). Both blind arms **decline on the anchor** (A2 gray −0.0422, A2b −0.0272, CIs excluding zero) while **rising on the cued control** — their flat overall numbers are two opposite-sign effects cancelling. This localizes F5 to the search-and-binding layer.

**Phase 0 (Paper 2 prerequisites) complete.** P0.1 premise probe fired branch (b): base premise accuracy 0.275, and reasoning given a correct premise only 0.273, so premise extraction is the first bottleneck but not the only one. P0.2 fixed a scorer defect that scored every equal-gold invariance item wrong regardless of content (R19 unaffected — zero equal-gold pairs, rescores identical). P0.3 froze the intervention-group schema; P0.4 canonicalised task roles with an I13 guard.

## 7. Pending

Cue ladder (F4b): four rungs built, item-paired with R19 by replaying each frozen pair's `pair_seed` (300/300 replay integrity); base is scoring the two registered build-validity gates, then the remaining 12 model cells. M5 step-400 (R2, at ~372). Mini-A5 both arms (F7, CP arm at ~65/120; matched same-data GRPO arm queued, 4-arm Gate-1 registration to be prepared in parallel). M7 ViRL stratified (R3, built, awaiting a node). 7B access pair (R4) — re-scoped to A1 and A2b only, one seed. Cross-family completion (R5, inference only; prior ledger state is ambiguous and must be resolved before any claim). Human gates. X6 related-work table (PI-owned).

**Needs PI action — two prose corrections this evidence forces:**
1. §5 describes the header-cued verification table as "saturated at 1.000 for every model including base" and unable to show improvement. Measured on R19 it is **0.8667** (strict 0.1800) and moves in every arm (+0.019 to +0.023; A2 gray's CI excludes zero), contributing 18.7% of A1's overall movement. The retention-canary function is intact; the saturation claim is not. §3 F2 builds its mechanism on that table "contributing nothing to any delta" and needs the same fix — the mechanism itself survives, only its premise changes.
2. §2's canonical claim and the title guard should carry G0.2's scope qualifier: roughly half the gain is image-free *on average*, with the image-free share falling as an item's dependence on the image rises.

## 8. Pre-committed branches

**Access matrix:** TrainShare = [Acc(train-blind, test-real) − Acc(base, test-real)] / [Acc(A1, test-real) − Acc(base, test-real)], per seed with paired item-level CIs. ≥0.35 → headline at full strength; 0.15–0.35 → "a substantial minority of the gain is image-free"; <0.15 → training-time access dominates and F1 becomes a secondary ablation-practice finding.
**X2 ladder (fired, bottom branch):** golds-only 0.9067 is predominantly candidate-set structure; the realization gap ships as a measurement-methods finding; "already perceived/understood" stays hypothesis language.
**Mini-A5:** CP moves held-out FlipTrack while matched same-data GRPO does not → trainability established, Paper 2 proceeds; both flat → reported as-is and the Paper-2 gate is reconsidered.
**M7:** stratum recovery tracks stratum blind-opportunity → dose-response confirmed at R3.

## 9. Language locks

"Latent preference for the correct answer," never "already perceived" as result language. "Candidate-evidence ranking" / "open-form realization." "Mass sharpening within observed support" / "support-expansion candidate." "Conservative contamination candidates." "Cued chart point-value reading." "Marginal answer-frequency shortcuts are excluded," never "prior exploitation ruled out." Registered endpoints appear as pivots, findings, or robustness evidence.

## 10. Positioning

Inference-time ablation is the axis this literature does not report; we supply it with matched arms, three seeds, and a certified instrument. Novelty is argued through the X6 nine-column comparison table on the integrated combination: paired counterfactual interventions × controlled information channels at train and test × ranking/generation decomposition × RLVR dynamics × trainability validation.

## 11. Relation to Paper 2

Paper 1 diagnoses; Paper 2 repairs. The boundary: the access matrix, the mechanism, the instrument, and the audit belong here; Paper 2 cites them and contributes method. Paper 2's charter — *Reward What the Image Changes: Intervention-Group Policy Optimization for Multimodal RLVR* — is in `PAPER2_RESEARCH_DOC.md`, gated on Mini-A5. Paper 1 timestamps the repair direction by releasing the Mini-A5 protocol; Paper 2 inherits Paper 1's evaluation as its success criterion, which is why no Paper-2 result can be another utilization gain in disguise.

## 12. Writing plan

Writable now: introduction (problem → the unreported axis → the matrix → the exchange rate), instrument, mechanism, corrosion, calibration, methods. Frozen slots: F1 completion, F7, R3, R4. Every figure has a named argumentative role; results without one go to the appendix.

## 13. Launch doctrine (binding)

The paper is a launch, not a log. Strengths first; no chronology; no volunteered self-attack; compete only on dimensions we win and that matter; state advantages explicitly; experiments are arguments. Unfavorable material: remove if off-claim → narrow the claim → choose the dimension that reflects the value → cast as trade-off → reorganize so the advantage is central → rebuild the story → explain only if it touches the core conclusion. **Integrity anchor:** every registered endpoint appears, cast as pivot, finding, or robustness evidence; claim strength follows the pre-committed ladders; registration governs content, launch framing governs prose.
