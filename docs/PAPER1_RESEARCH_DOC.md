# Paper 1 — Research Document
*Learning Without Looking: Image-Dependent Gains from Image-Free RLVR*

Living document. PIs own all sections except §6–§7, which the executor updates with each ledger pass. Engineering detail lives in `EXPERIMENT_TODO.md`; the method sequel in `PAPER2_RESEARCH_DOC.md`. Updated 2026-07-27 after D3 completion.

## 1. Title and framing guard

**Title (current):** *Learning Without Looking: Image-Dependent Gains from Image-Free RLVR.*
**Conditional upgrade, pending M5b only:** if geo3k task accuracy rises across steps 100→400 while the primary anchor falls below the frozen base, the title becomes *Learning Without Looking: Image-Dependent Gains and Visual Grounding Corrosion in Multimodal RLVR*, and the abstract carries both headline results. Do not adopt it before M5b resolves.

**Guard:** the title omits the model class, so the abstract's first sentence and the introduction's first paragraph must establish that this is an RLVR stage applied to a *pretrained vision-language model*. "Image-free" refers to the RL stage only, never to pretraining. Same guard on talk titles and slides.

## 2. Canonical claim

Multimodal RLVR needs images at inference, not at training. **Under blind evaluation the training condition is irrelevant** — every arm, including one trained on full real images, gains the same small amount. **Under image-present evaluation the arms order themselves along an information ladder**, and training with no visual information whatsoever recovers roughly half the gain of full-image training. What RLVR learns is a *readout policy* over pretrained visual evidence: learnable largely without images, expressible only with them.

**The unifying statement.** RLVR strengthens the decision pathways that most cheaply produce reward. When benchmark reward does not require exact grounding, evidence-readout and shortcut policies improve while grounded visual distinctions stay flat or deteriorate.

**The mechanism, stated precisely.** RLVR can learn a transferable evidence-readout policy *without access to the evidence channel that will later supply the task-critical content*.

**Three findings.** (1) Blind reward opportunity varies across benchmarks and must be audited — visual necessity is measurable, not assumed. (2) Image-dependent gains can be learned without images: the access matrix plus the 84%/42% stratification. (3) Reward optimization can corrode visual grounding: replicated structured attractors, extended by the long-horizon anchor.

**On multimodality.** Multimodality is both the empirical setting and the **causal instrument** that makes a more general RLVR phenomenon identifiable. The visual channel can be removed, replaced, mismatched, captioned, or counterfactually altered while the textual task stays intact; that intervention structure is what separates access during optimization, acquisition of new distinctions, and utilization of pretrained evidence at inference. The caption result establishes evidence-generality, and the paper remains fundamentally multimodal because this decomposition has no equivalent in text-only RLVR.

**Ladder:** R1 three seeds on geo3k (in hand) → R2 long-horizon step-400 (complete, FALLING) → R3 second corpus, ViRL39K stratified (launched) → R4 scale, 7B access pair → R5 cross-family (complete).

## 3. Narrative arc (section = claim = figure)

**F0 — Visual necessity is a measurable property of a benchmark, not something guaranteed by the word "multimodal."** The frozen base evaluated on public benchmarks with and without the image, two scales, locked contract.

*Reporting requirement, every benchmark:* image-present accuracy · blind accuracy · the null appropriate to the answer format · chance-corrected retention · item-level bootstrap CIs (retention is a ratio of differences, so naive intervals do not apply).

*Null rule, by format — closed-form, not an invented empirical null:* multiple-choice subsets take 1/k; free-form numeric subsets take ≈0 and no correction, since nothing can be guessed; **mixed benchmarks are split and reported separately** rather than taking one global baseline.

*What we know now:* MMStar, curated specifically against image-free solving, sits at essentially four-way chance blind (0.2607 at 3B, 0.2880 at 7B against 0.25) — chance-corrected retention ≈3.5%. Its design works, and our measurement confirms it. **Whether other benchmarks retain materially more above-null opportunity follows the split analysis and is not asserted in advance** — MathVista is roughly half multiple-choice, so its correction may also be substantial. If its free-form subset retains high blind accuracy, that is the stronger result, because no guessing explains it.

Against this, FlipTrack scores exactly 0.0000 with collapse 1.0 for every model and family tested: image-necessary by construction, not merely harder. The instrument answers a demonstrated measurement gap rather than adding a leaderboard.

**F1 — The access matrix: two regimes.** Gain over base, mean of three seeds (base: real 0.1747, gray 0.0899, none 0.0682):

| trained ↓ / tested → | real | gray | none |
|---|---|---|---|
| A1 real | **+0.2435** | +0.019 | +0.036 |
| A3 caption | **+0.1747** | +0.024 | +0.037 |
| A2b no-image | **+0.1287** | +0.017 | +0.046 |
| A2 gray | **+0.1187** | +0.016 | +0.033 |

Tested blind, every arm lands between +0.016 and +0.046 with no ordering: A1, trained on real images for 100 steps, gains +0.036; A2-gray, which saw only uniform gray rectangles, gains +0.033. Tested with images, the arms separate and order themselves by training-time information. The same gray arm reports **6.6% recovery under matched evaluation and 48.6% under crossed evaluation** — a seven-fold difference in the scientific conclusion, produced by the evaluation protocol alone. Registered branch (a) obtains: ratio > 2 for both blind arms in all three seeds. Strict-scoring control reproduces direction and rough magnitude (ratios 1.95–2.69), qualifying rather than overturning the claim. **This is the central figure.**

**F1b — The policy is evidence-general, not pixel-specific (preregistered, passed).** D4's registered primary, filed before any cell ran: ρ(caption, real) = +0.800 against a ≥+0.70 threshold, and the caption column's spread is 4.0× the larger blind spread against a ≥2× threshold. Given frozen textual descriptions instead of pixels, the arms re-order as they do with images. *Registration record, stated in this order:* the primary branch passed; the A3 protocol-effect secondary **missed** its registered 2× threshold at 1.67; the explanation — that A3's matched condition is evidence-bearing rather than evidence-free — is **post hoc**, offered as mechanism refinement, not as a passed test.

**F2 — The information ladder on one common test condition.** Measured with images at test, over base: gray +0.119 (49% of A1) → no-image +0.129 (53%) → caption +0.175 (72%) → real +0.244 (100%). So **49% of the gain requires no visual information during training at all; a further 23% is transmissible through frozen textual descriptions; 28% requires actual pixels during optimization.** Gray ≡ no-image as registered. The caption inversion replicates 3/3: A3 starts above A1 at step 0 and ends below it.

**F3 — The exchange rate, and where it lands.** +24.4 benchmark points buy +2.5 points of overall certified counterfactual pair accuracy (CIs excluding zero, 3/3 seeds); on the registered geometry primary, +0.006. The instrument moves — it is not a dead ruler — which is what makes the asymmetry a measurement rather than a failure to detect. Decomposed by template, the movement sharpens into a mechanism: the saturated header table sits at 1.000 for every model and contributes nothing to any delta, so the gain concentrates on the oracle-localized readout control — the template where localization is supplied by the cue — while the primary anchor requiring search, binding, and read stays flat. **The gain lands exactly where the visual work has been done for the model.**

**F4 — Content-bound sharpening (mechanism).** Margin inflation vs base under the correct image: A1 +0.150, caption +0.090, no-image +0.035, gray +0.036 — the same information ordering as F2. Under a same-template mismatched image: statistically zero for every arm, both seeds. Under the twin's image, every model including the frozen base prefers the twin's gold (0.948–0.955). Blind-condition entropy stays at 0.998, so this is not a global temperature change.

**F5 — What the residual does not buy.** Structured hard-negative discrimination: base 0.517, A1 0.513–0.527. Chained premise-to-reasoning at floor for every model. Binding swap flat. Fact-read unimproved. The 28% that requires training-time pixels is more readout policy, tuned against real evidence — not new visual distinctions.

**F6 — Visual grounding corrosion (principal finding; formal term).** *Definition:* the progressive replacement of grounded visual behaviour by cheaper reward-compatible decision rules. The evidence is reported as an explicit three-tier ladder, and no tier claims more than it holds.

**Tier 1 — Established.** Evidence-poor optimization produces replicated, structured, item-specific corrosion. Gray's −0.0450 reproduces exactly across the **two analyzed seeds** (SEED3γ pending for the third), resolving to 42 shared pairs — Jaccard 0.724 against a permutation null of 0.098, p=1e-4 — with the identical extracted wrong answer on 41/42 and a dominant nearest-gridline off-by-one taxon (19/20). Errors move toward structured attractors, not random noise.

**Tier 2 — Observed in the long-horizon anchor.** With images available and the vision encoder trainable, grounding declines progressively along one prolonged trajectory and falls below the frozen base: primary anchor 0.4800 → 0.4133 against base 0.4717, monotone from step 100 (overall R19 0.5633 → 0.5600 → 0.5433 → 0.5383 → 0.5167), strict ≡ lenient so not a scoring artifact, blind floor still 0.0 with collapse 1.0.

*Attribution, required in every mention:* this extends the **anchor** configuration — unfrozen vision tower, native r1v reward, unfiltered corpus — never pilot A1. The unfrozen tower is what makes it consequential: corrosion occurs with gradients reaching the visual encoder. The unfiltered corpus is named as part of the configuration because abundant cheap reward is mechanistically relevant, not incidental. *Scope:* one trajectory; intervals quantify evaluation uncertainty, not run-to-run RL variance.

**Tier 3 — Upgrade condition.** If a second long-horizon seed reproduces the direction, prolonged proxy optimization is presented as a systematic source of visual grounding corrosion. Until then, Tier 2 stands as observed rather than systematic.

**F7 — Confidence tracks image presence, not correctness.** Underconfident when right (≈0.19 vs 0.75 accuracy, ECE 0.57); identical confidence under twin images where accuracy is 0.012 (+0.17–0.19 overconfidence gap).

**F8 — Trainability (Mini-A5).** CP-GRPO vs matched same-data standard GRPO on held-out templates.

**Prescription.** Ablate at inference, not only at training; report the exchange rate; audit the corpus before spending compute.

### The mechanism paragraph (surviving account)

RLVR learns a readout policy — how to commit to a value, structure the answer, avoid degenerate output, convert available evidence into a scored response. That policy is learnable almost entirely from text-side reward variance, which is why gray training captures half of it; it is worthless without evidence to read, which is why the blind-test column is flat for every arm; and it is content-sensitive rather than presence-triggered, which is why mismatched images buy exactly zero sharpening while correct images buy +0.15. Presence-gating, global temperature change, and pure formatting are each excluded by direct measurement.

### The pivot (how the falsified preregistration is presented)

We registered that blind training would recover 30–70% of the gain, measured 7–23% under matched evaluation, and then found that the prediction had been testing the evaluation protocol rather than the training condition. Under crossed evaluation the recovery is 43–53% — inside the interval we originally registered. **The preregistered interval was right; the evaluation protocol was wrong.** The falsification is what located the protocol error.

### The broader claim (discussion, one paragraph)

If RLVR learns a readout policy over a frozen encoder, the ceiling on RL-driven multimodal improvement is set by what the pretrained representation already encodes: RL cannot teach the model to see what the encoder does not represent, only to ask better questions of what is there. That predicts exactly the measured pattern — flat discrimination, floor-level chained reasoning, flat binding, large readout gains — and it predicts the same phenomenon in any RLVR setting with a frozen non-text encoder: audio, video, structured data.

## 4. Contributions

**C1** the access matrix and the ablation-protocol correction. **C2** the information-ladder decomposition (49 / 23 / 28). **C3** the mechanism: a readout policy, content-bound and information-ordered, with flat competence layers. **C4** FlipTrack — instrument, generator, validity dossier, multi-layer readout — released as protocol (§5). **C5** the blind reward-opportunity audit and corpus shortcut map. **C6** blind-reward corrosion as a measured, item-identifiable harm. **C7** Mini-A5 as published trainability validation.

## 5. The benchmark (C4)

**Construction.** Render-twice counterfactual minimal pairs: both members generated from one scene program, differing in exactly one answer-changing fact, identical question text, success requiring both members correct. Blind answering is capped by construction, and there is no original-versus-edited artifact channel because neither member is an edit of the other.

**R19 (frozen, 1,200 pairs) — three tasks, three scientific roles.** Reported separately; no aggregate is computed across roles.
- *Coordinate survey register* (600) — locate the label, bind it to the point, read the coordinate. The **primary visual anchor**; base pair accuracy 0.4717. The only R19 task requiring search and binding.
- *Header-cued verification table* (300) — saturated at 1.000 for every model. A **saturated positive control and retention canary**: it cannot show improvement, but any drop signals damage to simple readout or to the scoring pipeline. Excluded from every capability aggregate.
- *Nine-series calibration trace* (300) — the circle marks the queried point, supplying localization. The certified construct is **oracle-localized visual readout**: given a located target, can the model read the local value, and does that reading track image content? A control condition, never chart reasoning.

**R20.** One-shot private twin from fresh seeds under the frozen generator; failures downgrade certification rather than triggering a retry.

**Validity dossier.** 72B question-blind caption stress ≤0.062; artifact-attacker gates with CIs; blind conditions at exactly 0.000 with answer collapse 1.0; monotone degradation and scale controls; 60/60 human audit with construct notes; cross-family confirmation (InternVL3-9B, Gemma-3) with no-image collapse and caption ≤0.013.

**Multi-layer readout on identical pairs.** Open-form realization · candidate-evidence ranking · structured hard negatives · calibration. This decomposition is what separated the utilization result from an apparent competence result.

**Release form.** Instrument + generator + dossier as a protocol rather than a static leaderboard — regeneration from fresh seeds makes it contamination-resistant — plus the blind reward-opportunity audit as a corpus-side tool.

**Status for Paper 1: finalize, do not extend.** Three tasks with distinct, honest roles are a coherent instrument, and Paper 1's claims rest on the access matrix, the ladder, and the competence layers rather than on benchmark breadth. Remaining work is scoring and documentation only — roles fixed in every report, no cross-role aggregates, the equal-gold invariance scorer repaired, premise accuracy measured. New capability tracks belong to Paper 2 and are gated on Mini-A5.

## 6. Evidence in hand

Three-seed task gains: A1 +0.2435, A3 +0.1048, A2b +0.0460, A2 +0.0161 under matched evaluation; strict-format gain larger (+0.3583), so the reported lenient figure is conservative. D2 access verdict image-mediated-at-inference, 3/3 seeds. D3 complete, 36 cells, registered branch (a). X1/X5 sharpening. X2 hard negatives (bottom branch). X3 corrosion forensics. X4 calibration (exploratory). B1 declared batch. Instrument dossier per §5.

## 7. Pending

*(Executor update 2026-07-30.)* **Landed since the last pass:** caption column (D4, branch (a) evidence-general); M5 step-400 (R2, FALLING) plus the M5b/M5c trajectory and turnover analyses; Mini-A5 both arms (F8 — gate PASS, endpoints read, branch 2 fired; the primary anchor is flat on three of four measurements and the layer-selectivity of F3 reproduces under the counterfactual-group objective); E1a/E1b/E1c external columns; CHANCE null-corrected retention across seven benchmarks.

**Landed 2026-08-04: R3 complete (seed 1).** The registered secondary passes with stable margins — ViRL39K matched-evaluation recovery **0.7174 (A2-gray) / 0.7449 (A2b)** against the geo3k anchors 0.0789/0.1184 — so blind arms recover 72–88% of A1's gain on the second corpus under the same matched protocol that yields 8–12% on geo3k, exactly as the blind-opportunity audit predicted in advance. ρ_gain fails in direction for all three blind arms (gains track headroom); ρ_recovery is point-positive for the blind arms. Every number carries the one-seed tag; seed 2 in progress. `reports/m7_r3_readout_v1.*`.

**Still pending:** 7B access pair (R4) — both arms training under `docs/registered_c5_7b_access_pair_v1.md` (A2-gray ~2026-08-06, A1-real ~2026-08-07); both 7B base cells already banked; readout follows the locked 6-cell access-matrix spec. M7 seed 2 (upgrade to the two-seed estimator) queued behind the C5 pair. Human gates; X6 related-work table (PI-owned).

## 8. Pre-committed branches

**D3 (fired, branch a):** the low blind recovery substantially reflects the matched evaluation condition; the canonical claim carries the scope tag "under matched evaluation" with the crossed figure reported alongside.
**X2 (fired, bottom branch):** golds-only 0.9067 is predominantly candidate-set structure; the realization gap ships as a measurement-methods finding; "already perceived" stays hypothesis language.
**Mini-A5:** CP moves held-out FlipTrack while matched same-data GRPO does not → trainability established, Paper 2 proceeds; both flat → reported as-is and the Paper-2 gate is reconsidered.
**M7:** stratum recovery tracks stratum blind-opportunity → dose-response confirmed at R3.

## 9. Language locks

"Latent preference for the correct answer," never "already perceived" as result language. "Candidate-evidence ranking" / "open-form realization." "Mass sharpening within observed support" / "support-expansion candidate." "Conservative contamination candidates." "Oracle-localized visual readout." "Marginal answer-frequency shortcuts are excluded," never "prior exploitation ruled out." Registered endpoints appear as pivots, findings, or robustness evidence.

## 10. Positioning

Inference-time ablation is the axis this literature does not report; we supply it with matched arms, three seeds, and a certified instrument, and we show the standard matched-condition protocol understates image-free training by a factor of two to thirteen. Novelty is argued through the X6 nine-column table on the integrated combination: paired counterfactual interventions × controlled information channels at train and test × ranking/generation decomposition × RLVR dynamics × trainability validation.

## 11. Relation to Paper 2

Paper 1 diagnoses; Paper 2 repairs. The access matrix, the mechanism, the instrument, and the audit belong here; Paper 2 cites them and contributes method. The representational-ceiling argument (§3) is what gives Paper 2 its thesis: improving multimodal RL requires reward variance resolvable only through distinctions the encoder can make but the policy does not yet use. Charter in `PAPER2_RESEARCH_DOC.md`, gated on Mini-A5.

## 12. Writing plan

Writable now: introduction (problem → the unreported axis → the two-regime matrix → the ladder), instrument, mechanism, corrosion, calibration, methods. Frozen slots: caption column, F8, R3, R4. Every figure has a named argumentative role; results without one go to the appendix.

## 13. Launch doctrine (binding)

The paper is a launch, not a log. Strengths first; no chronology; no volunteered self-attack; compete only on dimensions we win and that matter; state advantages explicitly; experiments are arguments. Unfavorable material: remove if off-claim → narrow the claim → choose the dimension that reflects the value → cast as trade-off → reorganize so the advantage is central → rebuild the story → explain only if it touches the core conclusion. **Integrity anchor:** every registered endpoint appears, cast as pivot, finding, or robustness evidence; claim strength follows the pre-committed ladders; registration governs content, launch framing governs prose.
