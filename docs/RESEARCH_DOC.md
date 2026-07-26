# Blind Gains — Research & Paper Strategy
Living document; guides Paper-1 writing and directs experiments. PIs own §1–§9; Codex updates §4–§5 with each ledger pass. Operational detail lives in briefs/ledgers. Updated 2026-07-17 (post seed-1, post null/M10, post co-PI review).

## 1. Canonical claim and the claim ladder

**Canonical (current scope):** *On Geometry3K (seed-1), standard multimodal RLVR obtains large in-domain gains that require visual access — yet certified counterfactual geometry performance remains unchanged.* Zero-visual-bit training recovers only ~8–12% of the gain; frozen captions recover ~43%; the pixel-dependent remainder produces no measurable gain in the registered geometry FlipTrack endpoint.

**Claim ladder** (each rung broadens the sentence when its evidence lands; scope tags drop mechanically, never rhetorically):
R1 seed-1 geo3k (current) → R2 +seeds 2–3: "replicated" → R3 +step-400: "not a horizon artifact" → R4 +ViRL 3B stratified: "recovery tracks corpus blind-opportunity" (registered dose-response) → R5 +7B ×3 seeds: field-scale → R6 +non-Qwen audits: audit generalizes beyond one family.

**Retired claims (falsified/overbroad — keep visible):** "gains are mostly blind" (registered 30–70% blind-recovery interval falsified: 7.9%/11.8%); "prior-exploitation ruled out" (only marginal-frequency shortcuts are); "57% is pixel-perception gain" (it is: not recovered by A3); "images are retrieval keys" (mechanism hypothesis, untested).

## 2. Narrative arc (section = claim = figure)

1. **The dissociation** (F1): A1 +25.3pp [21.0,29.5] on geo3k; geometry FlipTrack −0.2pp [−2.8,+2.5], equivalence supported; frozen tower — plus the unfrozen anchor showing the same shape. Open here.
2. **The falsified prediction** (T1, main text): preregistered blind recovery 30–70% vs observed 7.9% [−0.7,16.8] / 11.8% [3.4,20.4]. Presented as a scientific result that forced the information-ladder account — not as credibility theater.
3. **The information ladder** (F2): nothing ~12% → frozen captions ~43% → pixels 100%; D_caption^final = −0.108 (training inverted the baseline caption>real advantage); gray≡none equivalence supported.
4. **Where in the pipeline does RL act?** (F4, new): perception / decision / emission separation. Chart rose in blind arms; registered key-shuffle null flat (~1.3%) → marginal-frequency shortcuts excluded; invalid-answer rate fell 17.2%→~10–11% in every arm including blind → consistent with improved answer emission or utilization of existing visual representations (hypothesis, not proven). The layer-3 forced-choice diagnostic (§6) adjudicates.
5. **Mechanism** (F: hurdle): gains concentrate on above-floor blind-opportunity items where estimable (A1 +0.23; A2b +0.10 CI>0; A3 +0.11); format accounting: blind arms recover 58–74% of A1's format gain; gray's total gain is 81% format.
6. **The map and the dose-response** (F3, pending M7): H-mixed ViRL39K; registered cross-corpus prediction merged pre-launch: higher blind opportunity → higher blind recovery, stratum-tracking.
7. **Controls** (F5): unfrozen anchor; step-400 (running); mini-A5 RL positive control (queued); SFT; scale/degradation; nulls; seeds.
8. **Prescription:** audit before you train; the instrument + generator + audit toolkit release.

## 3. Contributions

C1 dissociation + information ladder (causal, matched arms, two corpora, two scales when complete). C2 FlipTrack instrument + generator + validity dossier, now extended by the three-layer measurement (free-gen / strict-contract / forced-choice ranking) — the first RLVR evaluation stack that separates perception from decision from emission. C3 blind reward-opportunity audit + H-mixed map + registered dose-response. C4 caption-mediated accessibility at baseline and its training inversion. C5 exact StrictGain = AnswerGain + G_format accounting. Falsified-prediction table as a first-class result.

## 4. Evidence in hand

| Evidence | Result |
|---|---|
| Seed-1 RQ1 | ΔA1 +25.3pp [21.0,29.5]; ΔA2 +2.0 [−0.2,4.2]; ΔA2b +3.0 [0.8,5.2]; ΔA3 +11.0 [7.3,14.5]; recoveries 7.9%/11.8%/43.4%; gray≡none supported |
| Seed-1 RQ2 | A1 geometry FlipTrack flat (−0.0017, eq. supported, both checkpoints); A2-gray geometry −4.5pp [−7.3,−1.8] decline; overall/table always per-category |
| Registered null | key-shuffle ~1.3% flat across all 36 cells → marginal-frequency shortcut excluded for chart rises |
| Emission diagnostics (chart) | invalid/other rate 17.2% → 9.7/9.7/11.3/10.5% (A1/A2/A2b/A3); value-level asymmetries (answer "10" −40pp under gray) |
| M10 (80-draw) | A1 16/47 expansion candidates vs 31/47 sharpening; A2 1/8; A2b 5/7; A3 2/18; 0/80 Jeffreys upper 3.08%; language locked |
| Anchor | +28.6pp benchmark, FlipTrack flat, unfrozen tower; prior observation, disclosed |
| Audits | geo3k v2 (caption 0.175 > real 0.154 at base); ViRL 3B & 7B five-condition; 7B: caption 0.162 < none 0.182 < gray 0.246 < real 0.358; gray≠none fork row fired → A2 retained at 7B |
| Instrument dossier | R19 + one-shot R20 + 72B caption ≤0.062 + human audit 60/60 + attacker CIs |
| X1/X5 image-condition matrix (seeds 1–2) | Margin inflation is content-bound: mismatched-real inflation statistically zero for every arm in both seeds (|mean| ≤ 0.0006, CIs span zero) while correct-image inflation is far from zero (A1 +0.150/+0.129; A3 +0.090/+0.076; A2b +0.035/+0.058; A2 +0.036/+0.037). Twin-image condition: the twin's gold is preferred for 0.948–0.955 of members in every model including base |
| X2 hard-negative ranking (registered ladder) | Golds-only margin pair-success is candidate-set-invariant and reproduces at exactly 0.9067; against the structured negative sets base pair-success is 0.5167 [0.4750, 0.5567] (A1 step-60 0.5267, step-100 0.5133) → registered bottom branch: the 0.9067 is predominantly candidate-set structure and the realization gap is a measurement-methods finding |
| X3 A2-gray degradation forensics | The −4.5pp geometry decline is item-identifiable and answer-deterministic across seeds: correct→wrong sets 51/49 with 42 shared (Jaccard 0.724 vs permutation null 0.098, p = 1e-4), same extracted wrong answer in 41/42 shared slots; dominant taxon nearest-gridline off-by-one (19/20) |
| X4 calibration (EXPLORATORY) | Under real images all models are underconfident (confidence ~0.18–0.20 vs accuracy ~0.75); under twin-counterfactual images confidence is unchanged by construction while accuracy collapses to ~0.012 (overconfidence gap +0.17–0.19) |
| B1 renderable geometry track (declared batch) | Base pair-correct: fact-read 0.600, style-twin invariance 0.643, distractor invariance 0.438, binding swap 0.188, prior-conflict 0.143, chained two-hop 0.000 (member 0.150); blind 0.03, caption 0.04 overall |
| D2 test-time image access (registered) | The Geometry3K gain is image-mediated at test time in both seeds: RetainedGainBlind 0.158 (seed 1) / 0.122 (seed 2), registered band (a); reproduction check reproduced published step-100 exactly. Secondary: A2b evaluated **with** images reaches 0.3195/0.2962 vs its published blind 0.0982/0.1231 (test-time image benefit +0.221/+0.173) |

## 5. Pending → what each buys

Seed-3 four-arm endpoints + three-seed summary and pooled equivalence verdict (replication rung R2; evaluation lifecycle armed, cohort release on A3 completion) · M5 step-400 terminal readout (horizon rung R3; segments self-driving, step-300 boundary recovered and merged checkpoint regenerated on quota) · M6 mini-A5 two-arm (Paper-2 gate + RL positive control; registered, launcher and checkpoint watcher built, launches when an29 clears the seed-3 evaluations) · M7 ViRL 3B stratified (dose-response rung R4; frozen subset and audited caption store complete, image-disjoint held-out split registered and built, eight matched arm configs and the amendment-bound launcher committed — awaiting a free node) · M8/M9 7B ×3 seeds, 4 arms (scale rung R5) · M11 non-Qwen (family rung R6) · X6 related-work audit table (PI-owned) · human passes: chart-v08 no-zoom audit, 24 expansion candidates, R19/R20 audit samples · merge-back readouts.

## 6. Pre-committed interpretation branches

**Layer-3 forced-choice (register before running; chart AND geometry; all arms + base, steps 0/100):**
- B1: free-gen up, ranking flat → emission/decision account supported; geometry headline untouched.
- B2: ranking up on chart only → improved utilization of existing visual features; still non-perceptual for geometry; headline scope-tightened to "certified counterfactual sensitivity."
- B3: ranking up on GEOMETRY under A1 → masked perception gain (perception improved, expression degraded); the dissociation partially dissolves into a measurement finding; thesis revises to "RLVR improves visual evidence-ranking while degrading its expression" — a different but equally publishable paper. Written down now so no outcome is spun.
**X2 hard-negative ladder (registered):** base geometry ranking pair-success ≥0.75 → latent-competence co-headline at full strength; 0.55–0.75 → mid-form with the measured number; <0.55 → measurement-methods finding. "Already perceived/understood" = hypothesis language always; result language on the top branch + premise-probe convergence.
**M6 mini-A5:** trainability → Paper-2 proceeds per merge-back; failure → cancel rather than manufacture; success measured at the candidate-evidence ranking layer, not free generation.
**M7:** recovery tracks stratum q̄ → dose-response confirmed; flat → shortcut-availability is necessary-not-sufficient; both write into R4.

## 7. Framing rules (binding; additions from co-PI review)

"Marginal answer-frequency shortcuts are excluded" — never "prior-exploitation ruled out." "Consistent with improved answer emission or utilization of existing visual representations" — never "emission unlock is proven." "Not recovered by A3" — never "pixel-perception gain." "No improvement in measured end-to-end counterfactual visual sensitivity" — never "perception unchanged internally." Scope tags (corpus, seed count, endpoint) stay on every claim until the ladder rung removes them. Falsified predictions presented as results that forced the better account. All prior rules (caption-mediated accessibility; support-sharpening language; cued point-value reading; conservative candidates) remain.

## 8. Reviewer-attack map (delta)

"Offsetting cancellation could hide perception gains" → layer-3 diagnostic (B3 pre-committed). "Emission confound contaminates FlipTrack deltas" → three-layer stack + nulls; geometry primary unaffected either way. "Blind recovery so low that shortcuts don't matter" → the ladder: captions recover 43%; and the registered ViRL prediction tests where shortcuts do dominate. Everything else as before (tower, horizon, seeds, corpora, families, contamination).

## 9. Paper 2 — upgraded charter

**Two repair levers, one instrument:** reward-side (CP-GRPO) and data-side (audit-guided curation: train on high-visual-necessity strata), plus their combination. **Success criterion inherited from Paper 1: a repair must move the perception layer (forced-choice ranking on held-out templates), not merely free-generation scores** — no emission-unlock mirages. Gate unchanged: M6 trainability → 7B CP pilot → transfer readout → pre-committed keep/merge/cancel. Paper 1 timestamps both levers and releases the mini-A5 protocol.

## 10. Writing plan

Now writable with results: F1, T1 (falsified prediction), F2 ladder, hurdle/format panels; intro reframed on the canonical claim; three-layer measurement section drafted pending the diagnostic. Frozen slots: F3 (M7), scale table (M9), controls completions. Venue: ICLR 2027 preferred, not binding; the ladder decides the claim, the claim decides the paper.

## 11. Launch doctrine (binding for all paper text)

The paper is an academic launch, not a project log. Organize every section around the strengths that genuinely hold: the dissociation, the information ladder, the falsification-turned-mechanism, the three-gap framework, the instrument. No chronology of attempts; only the final logic that stands. Never volunteer self-attack: the words "unfortunately," "only," "fails to," "significantly behind" do not appear; unfavorable material is handled by the ladder — remove if off-claim → narrow the claim → change the evaluation dimension to one that reflects the work's value → cast as objective/trade-off difference → reorganize so the advantage is the visual center → rebuild the story → explain only if it genuinely touches the core conclusion. Compete only on dimensions we win and that matter; state advantages explicitly rather than hoping tables speak. Experiments are arguments — each result in the paper has a named argumentative role or it moves to the appendix. Abstract and introduction open with problem-gap-solution-result; limitations never precede contributions; the conclusion reinforces the central memory and introduces nothing new. The story serves the strongest evidence and may be rebuilt without loyalty to prior plans.

**Integrity anchor (non-negotiable within the doctrine):** every registered endpoint appears in the paper — cast as a pivot, a finding, or robustness evidence, never as confession. Falsified predictions are presented as the results that forced the better account. Claim strength follows the pre-committed ladders (§6), with hypothesis language always free and result language gated by the branches. Launch framing governs prose; registration governs content; the two never trade against each other.
