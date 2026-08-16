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

### Layer B — Hierarchical capability suite (Discover → Ground → Read)

**Core abstraction (adopted 2026-08-12, co-PI synthesis).** Three matched layers derived from the **same mother-item**: L3 = Discover + Ground + Read (no target identity or location given) · L2 = Ground + Read (target oracle: identity given) · L1 = Read (location oracle: non-occluding cue). Identical scene data, renderer, answer, distractors, and scene-program ID across the three — only oracle information varies. Controlled capability subtraction: L3−L2 isolates discovery, L2−L1 isolates grounding, L1 isolates readout. Paper 2's success question becomes: **does the method move learning from Read toward Ground and Discover?**

**Two families only.** `hier_coord_v1` on the premise-v2 generator (canonical L3 relation: extremum discovery; nearest-neighbor as the labeled hard tier — its full-run gates already forced n=5, so it cannot carry the canonical tier at 3B) and `hier_chart_v1` on the chart-v08 renderer (L3: argmax-at-x, read the same series elsewhere). Cue-ladder v2 is superseded: L1/L2 absorb its valid purpose; region/decoy survive only as optional calibration diagnostics.

**Three pair roles, reported separately, never averaged:** target-switch (primary L3 causal diagnostic) · target-stable (isolates post-discovery behaviour) · invariance (specificity and anti-gaming). Prior-conflict and binding-swap remain exploratory generator cells outside the core.

**Ranking layer ships with the items:** registered candidate sets and structured hard negatives per L2/L3 item, so candidate-evidence ranking and hard-negative discrimination read out on the hierarchy.

**Diagnosis without chain-of-thought:** discovery probe + per-layer accuracies + pair successes give interpretable bottleneck patterns (L1✓L2✓L3✗ discovery; L1✓L2✗ grounding; L1✗ readout).

**Retroactive mapping.** R19's header table and chart are L1 tasks; the coordinate register is L2; premise-v2 is L3. Paper 1's template decomposition — movement on cued templates, flat on the search template — is the statement *standard RLVR moves L1, not L2*. The hierarchy names the structure the frozen instrument already had.

### Layer C — Intervention-group training engine (isolated from A and B)
Each training group carries: original image, causal twin, one or more invariance twins, mismatched image, no-image/gray control, premise labels, final answers, hard negatives, blind-solvability metadata, scene-program ID, intervention type, difficulty metadata. Schema versioned and validated by the training loader with a fixture, so schema drift cannot silently change what a group contains.

### Splits — at the scene-program level, never by random item split
*Training programs*: bulk generation for intervention groups; share no scene program with Layer A or the confirmatory set. *Development programs* (~300–600 groups): checkpoint selection, reward debugging, curriculum design, method ablations; B1's 100-pair batch serves as calibration seed only. *Confirmatory programs* (~600–1,200 groups): frozen until method and hyperparameters are frozen, covering the cue ladder, binding, causal sensitivity, invariance specificity, prior conflict, premise, chained reasoning, and structured hard negatives.

### Acceptance gates for new tracks
Every new track ships with the same evidence R19 cleared before it is used for training or reporting: caption stress, blind floors, attacker checks, and a difficulty band placing the base model in the learnable zone. Blind-solvability metadata is an acceptance gate, not merely a field in the schema.

### Phased build — gated, not front-loaded
**Phase 0 (no GPU training):** fix task roles in all text; report tasks separately; measure B1 premise accuracy; fix the equal-gold invariance scorer; freeze and version the intervention-group schema. **Phase 1:** cue ladder, binding, causal/invariance — 100–300 development groups only; check difficulty, blind-solvability, scorer behaviour, and whether IGPO produces non-zero training signal. **Do not generate tens of thousands of items before Mini-A5 prints a positive signal.** **Phase 2 (premise curriculum):** expand only if premise probes show learnable signal; if premise accuracy is near zero, build a simpler premise curriculum or a small verified warm start first — and if a warm start is used, an SFT-warm-start + standard-GRPO comparator is mandatory, or every gain is attributable to the SFT rather than to IGPO. **Phase 3:** full development and confirmatory sets, human sampling audit, frozen metrics and scorer, then the 3B and 7B runs. **Phase 4:** external transfer (MathVista, MathVerse, MMStar, MMMU), each reported with image-present *and* blind conditions, carrying generalization beyond the procedural environment — never the core causal evidence.

### Explicitly not built for v1
Large-scale natural-image counterfactuals; video; open-world VQA; a dozen additional render families; model-judge scoring; large-scale human premise annotation; further tasks resembling coordinate reading. The benchmark's value is construct clarity and causal control, not task count.

### Reporting profile — no single headline accuracy
Oracle-localized readout · search and binding · causal sensitivity · invariance specificity · premise accuracy · reasoning given a correct premise · full chained pair accuracy · structured hard-negative discrimination · ordinary task accuracy · matched blind-control gain.

## 5. Gates and stages — REVISED after Gate 1 and C6 (2026-08-16, PI branch decision)

**Gate 0 ✓ · Phase 0 ✓ · Gate 1 ✓ (2026-08-09).** Four arms at 3B: standard · paired-data · necessity · CP. **No arm moves held-out content on the primary anchor**; pairing costs strict-format (−0.32 canary, p=4e−27); necessity refunds +0.043 [0.018, 0.070]; all four move oracle readout +0.15–0.23. **Fired branch: the lever at 3B is reward resolvability, not reward shape.**

**Stage 2 (3B ablation matrix): CANCELLED.** Five arms plus leave-one-outs would re-confirm at scale n a null already established at four arms. C1 (necessity sampling) survives on its measured refund; C2/C3 are not pursued further at 3B.

**Stage 3 — the decisive 7B pilot (registration before launch).** Motivated by C6: 7B real-image standard GRPO moves the primary anchor +0.025 — capacity is implicated where reward shape was not. Two arms on the HB training split: standard GRPO vs necessity-sampled intervention-group reward (C1+C2+C3). Pre-committed: IGPO content gain > standard's on the primary anchor and hierarchy L2/L3 → the method paper proceeds; otherwise → the limits paper ("resolvability and capacity govern; reward shape does not"), published as such. One pilot decides which paper this is.

**Track-4 premise-v2 gate record.** E4 attacker PASS (DINOv2 OOF 0.529; wording resolved by recomputing unfolded per-attacker AUC CIs against the registered "CI includes 0.5" — the criterion is not modified). E1 FAIL branch (c): difficulty is not candidate-set size (n=8 → 0.2875); step to n=5 executed. E2: premise clause passes at exactly 0.000 blind for every type; final clause fails all five via a constant-answer degeneracy meeting non-uniform golds — an answer-balance defect, not a visual leak; failing types excluded from training until the registered balance constraint regenerates them. E3: not caption-leaky (4/5 clean); chained_premise_easy indeterminate pending the E2 fix — both readings reported, reading (a) not relaxed.

## 6. Pre-committed branches

Mini-A5 CP > matched same-data GRPO → C2 validated, full method proceeds. Mini-A5 flat → premise-first redesign (C3 before C2), C1 retained. Components move attribution but not competence → engage C4; the hybrid becomes the headline and reward-only results become its motivation. Nothing moves competence including C4 → publish as *the limits of outcome-reward RL for visual acquisition*: diagnosis, systematic negative surface, representation-level boundary. C1 alone captures most of the benefit → simplify to the audit-driven recipe rather than defend three components.

## 7. Differentiation

Perception-R1 rewards model-judged visual-description consistency; VPPO reweights tokens by attention-derived visual dependency; process-reward work supervises steps without visual verifiability; the RLVR-capacity literature studies support expansion with no modality decomposition. Ours: the problem is measured before it is treated; necessity is measured per item rather than heuristically inferred; premises are render-verifiable; the training unit is the intervention group, so the reward is structurally unsatisfiable by text priors; and success requires joint competence and attribution evidence.

## 8. Assets already paid for

Blind reward-opportunity audit under five conditions across two corpora and two model families; A2b blind-trained checkpoints across three seeds (blind controls); renderable generator with twins, premise probes, six intervention types; FlipTrack multi-layer evaluation and validity dossier; the access-matrix protocol; Mini-A5's shared-group-uid broadcast-reward implementation with advantage-tensor equivalence tests; decontaminated ViRL39K subset with audited caption store; registration, ledger, and goal machinery.

## 9. Scope and risks

Full intervention groups require twins, hence generated data; C1 requires none and applies to any corpus, so the corpus-agnostic component carries external-transfer claims while generated data carries the mechanism. Reward shaping may trade raw accuracy for attribution — report the Pareto curve and lead with the joint criterion. Change-detector gaming — invariance groups plus order randomization. Scope creep — the access matrix, the diagnosis, and the instrument stay in Paper 1.
