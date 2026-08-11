# Paper 2 — Research Document
*Reward What the Image Changes: Intervention-Group Policy Optimization for Multimodal RLVR*

Method paper; sequel to *Learning Without Looking* (`PAPER1_RESEARCH_DOC.md`). PI-owned. Consolidated 2026-07-27 after co-PI review. Supersedes the v1 charter: the blind-likelihood discount is removed, necessity weighting is re-specified, the curriculum is demoted, metrics are co-primary, and the intervention group becomes the training unit.

**Method name:** IGPO — Intervention-Group Policy Optimization (alternative: CIPO, Counterfactual Intervention Policy Optimization). **Not VAPO**: taken by ByteDance Seed's Value-based Augmented PPO (arXiv 2504.05118), an RL-for-reasoning framework positioned against GRPO/DAPO — same field, unacceptable collision. Check the chosen acronym against the literature before freezing.

## 1. The problem inherited

Paper 1 establishes that RLVR improves *utilization* of pretrained visual evidence while leaving acquisition flat (hard negatives 0.517→0.513–0.527; chained premise 0.000 for every model; binding flat), with roughly half the gain obtainable without training-time pixels. Two mechanisms:

- **H1 (data):** most items carry reward opportunity attainable blind, so no gradient pressure points at the visual pathway.
- **H2 (signal):** a scalar answer reward cannot separate *correct because it read the image* from *correct anyway*; credit flows to whichever pathway supplies cheap variance, which is text sampling.

**The corrosion argument (inherited from Paper 1's F6).** Continued optimization of a proxy satisfiable without precise evidence consultation does not merely fail to build grounding — it displaces grounding that was already present, even with gradients reaching the vision encoder. A repair method therefore has two jobs, not one: install acquisition, and prevent displacement. Paper 2's evaluation must show both, which is why the corrosion probe sits in the co-primary constraint set rather than in an appendix.

**The ceiling argument (inherited from Paper 1's D3 result).** RLVR learns a *readout policy* over a frozen encoder: half the gain is obtainable with no visual information at all, and under blind evaluation the training condition is irrelevant entirely. If the policy only queries what the encoder already represents, then the ceiling on RL-driven multimodal improvement is representational — and improving it requires reward variance that is **resolvable only through distinctions the encoder can make but the policy does not yet use.** That is the precise job description for intervention groups, and it is why scalar answer rewards cannot do it.

**Thesis.** Standard answer-level RLVR cannot identify whether reward was earned through visual evidence. IGPO makes visual credit identifiable by combining necessity-aware sampling with verified counterfactual intervention rewards, converting benchmark improvements into newly acquired visual distinctions.

## 2. Method

### C1 — Visual-necessity sampling (data side; addresses H1)
Per item, Δq_i = q_i^real − q_i^blind from the Paper-1 audit: the reward opportunity attributable to the image. Prefer items with low blind solvability, real-image solvability above blind, non-zero base visual ability, and an available verifiable intervention.

**Implementation (critical).** Apply as **sampling probability**, not reward scaling. Naive r'_ij = Δq_i·r_ij is cancelled exactly by GRPO's within-group normalization, because Δq_i is constant across the group. Ablation form: post-normalization loss weighting L_i = −Δq_i Σ_j A_ij log π(o_ij | x_i), which survives normalization but raises gradient variance — hence secondary.

### C2 — Counterfactual intervention-group optimization (signal side; addresses H2; core contribution)
The training unit is a group of controlled interventions on one scene, not a single sample.
- *Causal group:* image I → y, counterfactual I' → y'. R_causal = 1[ŷ(I)=y ∧ ŷ(I')=y'].
- *Invariance group:* style twin or distractor-only change. R_inv = 1[ŷ(I)=y ∧ ŷ(I^s)=y].
- *Negative controls inside the group:* mismatched real, gray, no-image, caption.

**Why it works.** The same question text maps to different answers across members, so a text-prior policy scores exactly zero on causal groups — the reward is structurally unsatisfiable without reading the image, rather than merely correlated with reading it. And the reward varies across rollouts within the group without being a per-item constant, so it survives normalization.

**Why invariance is required, not optional.** Causal-only reward is satisfiable by a change-detector heuristic: notice that something differs, flip to the other plausible value. Invariance groups forbid that and supply the specificity axis reported alongside sensitivity.

**Guards.** Randomize member presentation order across rollouts (positional policies can otherwise fake the relation); keep negative controls inside the group so they contribute to the relation rather than being scored separately.

### C3 — Premise-verified hierarchical reward (enabling component)
Decompose reward into visual-premise correctness, reasoning given a correct premise, final answer, and synchronized premise/answer change under the counterfactual. Premises are render-derived and exactly verifiable — not model-judged descriptions.

**Why it is not optional.** Pair-product rewards are sparse. On chained-premise items, base pair accuracy is 0.000 and member accuracy 0.150, so R_causal ≈ 0 for nearly every rollout: zero variance, zero gradient, no learning on precisely the construct the paper most wants to move. C3 is the only source of signal there. **The components are a dependency chain, not a menu:** C1 selects the items, C3 makes them trainable, C2 makes the credit unfakeable.

### C4 — Twin-contrastive auxiliary loss (pre-registered fallback)
Representation-level separation of twin members in a direction predictive of the answer difference; engaged only if reward shaping alone leaves competence flat.

### Removed: blind-likelihood-discounted reward
r_i = 1{correct}·(1 − λ·P_blind(y_i)) is a no-op. For unique-answer tasks every correct rollout extracts the same y*, so the discount is a per-item constant and std-normalization cancels it exactly (A_correct = (1−ρ)/√(ρ(1−ρ)) regardless of the constant). Under mean-only normalization it survives but reduces to C1's item weighting. It is never an independent component, and its response-level variant rewards unusual phrasing rather than visual grounding. Retain at most as a one-paragraph negative note.

## 3. Evaluation — two co-primary criteria

**A. Certified visual competence must rise:** counterfactual pair accuracy, structured hard-negative discrimination, binding swap, prior-conflict, premise extraction, chained reasoning, invariance specificity, held-out-template transfer. *The capability evidence.*

**B. Visually attributable gain must be positive:** VAG = ΔAcc(method, real-image test) − ΔAcc(matched same-data blind control, real-image test), with all constraints required — real-image accuracy rises, blind accuracy does not significantly fall, and criterion A rises jointly. *The attribution evidence.*

**Rationale.** Image-dependence alone is gameable: Acc_real − Acc_blind grows if blind accuracy merely degrades. Attribution without competence is not acquisition; competence without attribution is not ours.

**Supporting.** External benchmarks at matched compute (MathVista, MathVerse, MMStar, MMMU), each reported with its blind variant. Paper-1's 42-item corrosion probe. Calibration: does the method fix underconfident-when-right and equally-confident-under-twins?

## 4. Benchmark architecture — three layers, one principle

**Principle: do not replace the existing benchmark; add the missing capability layers around it.** R19/R20 derive their value from being frozen and validated. Editing them because we later judged a task too easy would destroy the property that makes Paper 1's null results credible, and would force re-running every Paper-1 arm.

### Layer A — Frozen historical anchor (unchanged, never trained on)
R19's three tasks, R20's private twin, the existing open-form / candidate-ranking / hard-negative / calibration readouts, and the correct / twin / mismatched / gray / no-image / caption conditions. Purpose: direct Paper-1-to-Paper-2 comparability, the access matrix, and one-shot private confirmation. Never used for training, tuning, or checkpoint selection. Each task keeps its Paper-1 role — primary visual anchor, saturated positive control, oracle-localized readout control — and no aggregate is computed across roles.

### Layer B — Capability suite (new; FlipTrack-C, not "R21"; R-numbers are reserved for regenerations of the frozen family)

**Track 1 — Cue ladder.** Exact cue → region cue → no cue → decoy cue over the nine-series scene family. Rung differences localize the bottleneck to local readout, search, binding, or distractor suppression. Cheapest new track (reuses existing scene generation) and highest information per unit cost. Decoy cue is a stress condition, never averaged with the ordinary rungs. *Scope note: this track belongs to Paper 2. Paper 1's claims are already carried by the access matrix and the competence layers, so building it for Paper 1 would be accumulation rather than argument.*

**Track 2 — Binding and distractor control.** Label swap, similar-label interference, same-abscissa and same-ordinate distractors, inserted neighbours, target/distractor position exchange, question-cue conflict. Scales B1's existing `binding_swap` and `distractor_only` types rather than building new ones. B1's prototype already shows fact reading (0.600) far above binding (0.188) and prior conflict (0.143), so binding is a separate capability layer, not an extension of reading.

**Track 3 — Causal change and invariance.** Every group carries both: causal interventions where the answer must change (move the target, swap labels, change a key value or relation) and invariance interventions where it must not (colour, font, background, irrelevant objects, layout perturbation, distractor position). **Causal sensitivity and invariance specificity are reported separately and never combined into one score** — causal-only training is satisfiable by a change-detector heuristic, and invariance is the control that forbids it.

**Track 4 — Premise-to-reasoning. STATUS: construct redesign required before any claim.** P0.1 returned branch (b): the chained-premise floor is **uninformative**, so it is removed from Paper 1's affirmative evidence and cannot yet support a Paper-2 claim. Its role is now methodological — it establishes that this track needs a redesigned construct **and independently measurable premise competence** before hierarchical reward (C3) can be justified. Building C3 on an uninformative floor would produce an unfalsifiable method.

**Track 4 (design target).** Programmatically verifiable visual premise, intermediate relation, final answer, and the counterfactual premise transition. Reports premise accuracy, reasoning conditional on a correct premise, final member accuracy, full pair accuracy, and premise-transition accuracy — separately. B1's chained premise is 0.000 at pair level but 0.150 at member level, so the construct is not impossible; the pair conjunction is brutal. **Premise accuracy must be measured on its own before any training config is written.**

### Layer C — Intervention-group training engine (isolated from A and B)
Each training group carries: original image, causal twin, one or more invariance twins, mismatched image, no-image/gray control, premise labels, final answers, hard negatives, blind-solvability metadata, scene-program ID, intervention type, difficulty metadata. Schema versioned and validated by the training loader with a fixture, so schema drift cannot silently change what a group contains.

### Splits — at the scene-program level, never by random item split
*Training programs*: bulk generation for intervention groups; share no scene program with Layer A or the confirmatory set. *Development programs* (~300–600 groups): checkpoint selection, reward debugging, curriculum design, method ablations; B1's 100-pair batch serves as calibration seed only. *Confirmatory programs* (~600–1,200 groups): frozen until method and hyperparameters are frozen, covering the cue ladder, binding, causal sensitivity, invariance specificity, prior conflict, premise, chained reasoning, and structured hard negatives.

### Acceptance gates for new tracks
Every new track ships with the same evidence R19 cleared before it is used for training or reporting: caption stress, blind floors, attacker checks, and a difficulty band placing the base model in the learnable zone. Blind-solvability metadata is an acceptance gate, not merely a field in the schema.

**Status of the first track to run them — premise-v2 dev batch, 160 groups, 2026-08-11.** The gates did their job: they caught a real defect before a single training step was spent, and they located it precisely.

- **E4 attacker check — PASS.** DINOv2, pixel-frequency and metadata attackers over the packaged 160-pair / 320-member release, 5-fold grouped CV by pair; largest folded statistic 0.546, largest CI upper 0.576, against the instrument's ≤0.55 / ≤0.62 criterion. DINOv2 hits train AUC 1.0 on every fold and still lands at OOF 0.529 — it memorises folds and transfers nothing across pairs, which is what an artifact-free release looks like. *Wording debt:* the registration's prose says "CI includes 0.5", but the instrument folds to max(AUC, 1−AUC), so that interval cannot include 0.5 by construction; reconcile the prose to the folded statistic at the next revision — no number changes.
- **E2 blind floor — the premise clause PASSES everywhere, the final clause FAILS everywhere.** Blind premise member accuracy is exactly **0.000** for all four premise-bearing types against ceilings 0.105 (n=20) and 0.286 (n=8): the new construct is blind-unsolvable as designed, which is the thing Track 4 was built to establish. Blind *final* member accuracy clears the 0.133 ceiling for all five types (0.1375–0.250), but blind *pair* accuracy is 0.000 and blind collapse rate 1.000 in every failing cell — the model emits one constant for both members and is never right about a pair. The leak is a **generator** property (final-answer balance over the 15 offsets), not a visual one. Registered consequence binds: the failing types are excluded from training use until the answer distribution is balanced. No regeneration of the premise construct is indicated.
- **E1 difficulty band — FAIL, branch (c) "still too hard".** Carrier `chained_premise_easy` premise member accuracy 0.2875 against the [0.40, 0.60] band, both contracts agreeing; the pre-committed step to `n=5` fires. *Diagnosis worth more than the number:* dropping the coordinate register from n=20 to n=8 — a 2.5× smaller search — moved premise solvability from the P0.1 anchor 0.275 to 0.2875. Candidate-set size is **not** what makes this premise hard, so `n=5` is a weak lever and the redesign should look elsewhere.
- **E3 caption stress — COMPLETE, and the batch is not caption-leaky.** 7B captioner over all 480 distinct dev images, QA build restricted to the 320-member causal release, 3B caption-QA eval. The quantity E3 exists to bound is what a caption *buys* over blindness, and that increment is **at or below zero for four of the five types** (`fact_read` −0.125, `premise_transition` −0.025, `chained_premise` −0.025, `premise_transition_easy` −0.0125) and +0.0375 for the fifth — every one far inside the registered 0.10 margin. These renders are coordinate registers: a captioner cannot serialize twenty labelled point positions accurately, and a confidently wrong caption is worse than the prior-driven constant a blind model falls back on. All five types pass against their own measured blind floor + 0.10; one (`chained_premise_easy`, 0.2625) fails against the registered literal 0.133 + 0.10, and that failure is inherited from E2's answer-balance defect rather than from captions. Section 7 does not disambiguate which blind-floor threshold it means, so both readings are reported and the choice is the PI's.

**All four gates have now run.** The construct has two independent clean bills — the premise clause is blind-unsolvable at exactly 0.000, and the items are not caption-solvable — plus a clean attacker check. The single defect is the final-answer distribution, a property of the answer sampler rather than of the construct, and balancing it should clear E2 and E3 together. E1's difficulty band remains the open design problem, and candidate-set size is not its lever.

**What this means for C3.** The hierarchical premise reward was justified on the claim that a programmatically verifiable premise can be measured on its own and is not blind-guessable. E2 now supplies exactly that at 0.000 blind premise accuracy across four types — the dependency C3 was waiting on. What is not yet supplied is a premise the base model solves often enough to learn from: at 0.2875 the carrier sits below the registered learnable band, so C3 remains justified in principle and unbuildable in practice until the difficulty lever is found. Evidence: `reports/track4_premise_v2_gate_readout_v1.{json,md}`, `reports/track4_premise_v2_attacker_gate_v1.json`.

### Phased build — gated, not front-loaded
**Phase 0 (no GPU training):** fix task roles in all text; report tasks separately; measure B1 premise accuracy; fix the equal-gold invariance scorer; freeze and version the intervention-group schema. **Phase 1:** cue ladder, binding, causal/invariance — 100–300 development groups only; check difficulty, blind-solvability, scorer behaviour, and whether IGPO produces non-zero training signal. **Do not generate tens of thousands of items before Mini-A5 prints a positive signal.** **Phase 2 (premise curriculum):** expand only if premise probes show learnable signal; if premise accuracy is near zero, build a simpler premise curriculum or a small verified warm start first — and if a warm start is used, an SFT-warm-start + standard-GRPO comparator is mandatory, or every gain is attributable to the SFT rather than to IGPO. **Phase 3:** full development and confirmatory sets, human sampling audit, frozen metrics and scorer, then the 3B and 7B runs. **Phase 4:** external transfer (MathVista, MathVerse, MMStar, MMMU), each reported with image-present *and* blind conditions, carrying generalization beyond the procedural environment — never the core causal evidence.

### Explicitly not built for v1
Large-scale natural-image counterfactuals; video; open-world VQA; a dozen additional render families; model-judge scoring; large-scale human premise annotation; further tasks resembling coordinate reading. The benchmark's value is construct clarity and causal control, not task count.

### Reporting profile — no single headline accuracy
Oracle-localized readout · search and binding · causal sensitivity · invariance specificity · premise accuracy · reasoning given a correct premise · full chained pair accuracy · structured hard-negative discrimination · ordinary task accuracy · matched blind-control gain.

## 5. Gates and stages

**Gate 0 — no training required.** From cached predictions: do A1's and A2b's gains concentrate on high-Δq items? Does A2b's image-present gain concentrate on low blind-solvability items? Overlap of A1/A2b newly-correct sets. Answer-gain vs format-gain split. Decides whether H1 holds and whether C1 earns a place in the method. *This same analysis freezes Paper 1's title claim.*

**Gate 1 — Mini-A5, four arms.** (1) standard GRPO; (2) same paired data + answer-only reward; (3) necessity sampling + answer-only reward; (4) IGPO. Answers in sequence: is the data enough, is item selection enough, does the relational reward add. Success measured on held-out pair accuracy, hard negatives, chained premise, binding/invariance — not margins.

*Executor result 2026-08-09 (readout: `reports/mini_a5_gate1_endpoint_readout_v1.json`, acceptance audit 9/9 before unseal, one seed/arm):* the sequence answers **no / no / no on content**. No arm moves held-out content on the primary anchor (lenient NOT MOVED, all contrasts and roles; absolute levels vs frozen base flat). Pairing alone is a strict-contract tax (−0.32 on the saturated canary, p=4e−27); necessity sampling refunds part of it (+0.043 [0.018, 0.070] strict, primary); the relational reward's increment over plain GRPO remains format-shaped. **All four recipes move the oracle-localized readout +0.15–0.23 lenient** — the F3 layer selectivity is recipe-independent, which sharpens this paper's thesis: the lever is not reward shape but reward *resolvability* (variance only encoder-level distinctions can resolve — the premise-v2 construct). The §6 branch reading on this result is the PI's.

**Stage 2 — full 3B.** Standard GRPO · paired-data GRPO · necessity-only · relation-reward-only · full IGPO. Ablations: remove causal reward; remove invariance reward; remove premise reward; remove necessity sampling; sampling-vs-loss-weighting form of C1.

**Stage 3 — 7B.** Standard GRPO · full IGPO · minimal blind control. Three runs, not a matrix.

**Efficiency ablation (demoted from headline).** Blind-first curriculum at matched total compute, with Paper 1's 42-item corrosion set as a registered probe. Paper-1 evidence shows blind reward training pushes a reproducible item set toward deterministic wrong attractors, so this answers "is blind-then-sighted cheaper?" — not "how is visual capability acquired?" The reference-policy role goes to a separately trained blind model, never to the target model's own history.

## 6. Pre-committed branches

Mini-A5 CP > matched same-data GRPO → C2 validated, full method proceeds. Mini-A5 flat → premise-first redesign (C3 before C2), C1 retained. Components move attribution but not competence → engage C4; the hybrid becomes the headline and reward-only results become its motivation. Nothing moves competence including C4 → publish as *the limits of outcome-reward RL for visual acquisition*: diagnosis, systematic negative surface, representation-level boundary. C1 alone captures most of the benefit → simplify to the audit-driven recipe rather than defend three components.

## 7. Differentiation

Perception-R1 rewards model-judged visual-description consistency; VPPO reweights tokens by attention-derived visual dependency; process-reward work supervises steps without visual verifiability; the RLVR-capacity literature studies support expansion with no modality decomposition. Ours: the problem is measured before it is treated; necessity is measured per item rather than heuristically inferred; premises are render-verifiable; the training unit is the intervention group, so the reward is structurally unsatisfiable by text priors; and success requires joint competence and attribution evidence.

## 8. Assets already paid for

Blind reward-opportunity audit under five conditions across two corpora and two model families; A2b blind-trained checkpoints across three seeds (blind controls); renderable generator with twins, premise probes, six intervention types; FlipTrack multi-layer evaluation and validity dossier; the access-matrix protocol; Mini-A5's shared-group-uid broadcast-reward implementation with advantage-tensor equivalence tests; decontaminated ViRL39K subset with audited caption store; registration, ledger, and goal machinery.

## 9. Scope and risks

Full intervention groups require twins, hence generated data; C1 requires none and applies to any corpus, so the corpus-agnostic component carries external-transfer claims while generated data carries the mechanism. Reward shaping may trade raw accuracy for attribution — report the Pareto curve and lead with the joint criterion. Change-detector gaming — invariance groups plus order randomization. Scope creep — the access matrix, the diagnosis, and the instrument stay in Paper 1.
