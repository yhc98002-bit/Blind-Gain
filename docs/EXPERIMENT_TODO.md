# Experiment To-Do — Engineering Implementation
Companion to `PAPER1_RESEARCH_DOC.md` and `PAPER2_RESEARCH_DOC.md`. Those define *what claim* each experiment serves; this file defines *what the code must do* so the two never diverge. Updated 2026-07-27.

**How to use.** Every row names the claim it serves and the implementation requirement that makes the result mean what the claim says. If an implementation detail here conflicts with a merged registration, the registration wins and this file is corrected. Status snapshot is from the 2026-07-27 consolidated results; **verify against `reports/main_progress.md` at HEAD before acting** — the ledger is authoritative, this file is a plan.

---

## PART 0 — Implementation invariants (each exists because violating it silently changes the result)

| # | Invariant | Failure it prevents |
|---|---|---|
| I1 | Per-item constants must never be applied as reward scaling under group-normalized GRPO. Necessity weighting is **sampling probability**; the post-normalization loss-weight form is the ablation. | Δq weighting cancels exactly in `(r−mean)/std`; the arm trains identically to baseline and looks like a null result. |
| I2 | Relational rewards must vary **across rollouts within a group**, not across items. | Any per-item reward transform is scrubbed by normalization (this is why the blind-likelihood discount was removed). |
| I3 | Intervention-group members are scored **jointly**; negative-control conditions live inside the group. | Scoring members separately reduces the objective to ordinary answer reward and destroys attribution. |
| I4 | Member presentation order is randomized per rollout. | A positional policy satisfies causal groups without reading the image. |
| I5 | Causal groups are never trained without invariance groups. | Change-detector heuristic: notice a difference, flip the answer, collect reward. |
| I6 | Train/eval disjointness is enforced at the **scene-program** level, not the item level; R19+R20 are never trained on. | Template leakage turns a transfer claim into an in-domain claim. |
| I7 | Evaluation decoding is locked (greedy, fixed contract, fixed max tokens) and identical for base and all checkpoints; both lenient and contract-strict scoring are reported. | The Paper-1 FlipTrack correction happened because one scoring convention was reported alone. |
| I8 | Image-dependence is never a sole success criterion; competence and attribution are co-primary. | `Acc_real − Acc_blind` grows when blind accuracy merely degrades. |
| I9 | Registration merges before the first optimizer step of any training unit; launchers fail closed on merged-at-HEAD. | Post-hoc analysis choices. |
| I10 | Every fix ships an adversarial fixture the old code fails; `*_audited` artifacts are never byte-identical to their source. | Both previously-caught Goodhart patterns. |
| I11 | R19/R20 are never modified, regenerated, or trained on. New capability tasks are added alongside; they never replace a frozen task. | Editing a frozen benchmark after seeing results destroys the preregistration value and invalidates every Paper-1 comparison. |
| I12 | Cue-ladder rungs render from the **same scene program**, with only the annotation layer changing between rungs. Decoy gold follows the **question**, never the cue. | If no-cue images differ from exact-cue images by anything beyond the cue, the ladder measures rendering differences instead of localization. |
| I13 | Causal sensitivity and invariance specificity are always reported separately; no aggregate combines tasks that hold different scientific roles. | A unified average across a saturated control, an oracle-localized control, and the primary anchor is uninterpretable — and causal-only reward is gameable without the invariance control. |
| I14 | Every new track passes acceptance gates (caption stress, blind floor, attacker check, difficulty band) before it is used for training or reporting. | Blind-solvability as a schema field is not a gate; an unaudited track can leak. |
| I15 | The intervention-group schema is versioned and validated by the training loader with a fixture. | Silent schema drift changes what a group contains, and therefore what the reward means. |
| I16 | If a premise warm start is used, an SFT-warm-start + standard-GRPO comparator is trained alongside. | Without it, every gain is attributable to the SFT rather than to IGPO. |

---

## PART 1 — Paper 1

### 1A. Complete
| ID | Experiment | Serves | Status |
|---|---|---|---|
| C1 | Pilot seeds 1–3, four arms (A1 real / A2 gray / A2b no-image / A3 caption), geo3k, 100 steps | F1, F2, ladder R1 | ✅ |
| D2 | Test-time access, three seeds | F1 (access matrix) | ✅ |
| X1/X5 | Image-condition matrix, seeds 1–2 (correct / mismatched-real / twin / gray / no-image × both layers) | F3 | ✅ |
| X2 | Hard-negative ranking v2, registered ladder fired (bottom branch) | F4, candidate-set correction | ✅ |
| X3 | A2 −0.045 item forensics (Jaccard 0.724 vs null 0.098) | F5 | ✅ |
| X4 | Calibration, exploratory | F6 | ✅ |
| B1 | Geometry track declared batch + trained-checkpoint scoring | F4, benchmark §5 | ✅ |
| — | Instrument dossier: R19, one-shot R20, 72B caption stress, attackers, human audit, cross-family | C3 | ✅ |

### 1B. In flight
| ID | Experiment | Serves | Implementation requirement |
|---|---|---|---|
| D3 | Train×test grid (19/36 cells at snapshot) | **completes F1** | All four training arms × {real, gray, no-image, caption} test conditions × 3 seeds. Export one tidy CSV keyed for F1. Registered estimand: TrainShare with paired item-level CIs per seed — register before reading remaining cells (I9). |
| M5 | Long-horizon to step 400 (step 354 at snapshot) | ladder R2 | Terminal rule already merged: 400-vs-100 primary, SESOI ±0.05, no extension under any outcome. Evaluate at 150/200/300/400. |
| A5 | Mini-A5: CP arm vs matched same-data standard GRPO | **F7**, and Paper-2 Gate 1 | Same corpus, prompts, G, steps, token budget for both arms. Advantage-tensor equivalence test must pass. Success read on held-out-template pair accuracy, not margins. |

### 1C. Remaining
| ID | Experiment | Serves | Implementation requirement |
|---|---|---|---|
| M7 | ViRL39K stratified decomposition (built, awaiting node) | ladder R3 | Strata = source × category with stratum-level q̄ attached; per-stratum estimands registered; pooled reported secondary. Prediction (merged pre-launch): recovery tracks stratum blind-opportunity. |
| C5 | 7B access pair | ladder R4 | **A1 and A2b only, one seed** — the test side is inference, so the headline replicates for two training runs, not twelve. |
| M11 | Cross-family completion | ladder R5 | Inference only. Confirm current state in the ledger; snapshot is ambiguous between "validity confirmed" and "full matrix pending." |
| X6 | Related-work nine-column table | positioning | **PI-owned, not a cluster task.** |
| G0 | Gate-0 stratification (see Part 2) | freezes the title claim | Cached predictions; also serves Paper 2. |
| CL | **Cue ladder on existing checkpoints** | **F4b** — does RLVR improve oracle-localized readout while leaving search and binding flat? | Generate four rungs (exact / region / no cue / decoy) from the nine-series scene family; score base + 4 arms × 3 seeds, inference only. Register the analysis before scoring; label a post-hoc decomposition. Invariants I12, I13. Generation is CPU; scoring is one eval pass per checkpoint. |
| F2d | Template decomposition of the overall-R19 movement | **sharpens F2** | Split the +0.0283/+0.0208/+0.0267 overall delta by template. Expectation from role analysis: the saturated table contributes zero and the movement concentrates on the oracle-localized readout control. Cached predictions, no new inference. |

---

## PART 2 — Paper 2

### 2A. Gate 0 — no GPUs, run first
| ID | Analysis | Decides |
|---|---|---|
| G0.1 | Do A1's per-item gains concentrate on high-Δq items? | H1; whether C1 belongs in the method |
| G0.2 | Does A2b's image-present gain concentrate on low blind-solvability items? | whether the image-free gain is visual utilization or generic text-side improvement — **freezes Paper 1's title claim** |
| G0.3 | Overlap of A1 / A2b newly-correct sets (Jaccard + permutation null) | same policy or different policies |
| G0.4 | Answer-gain vs format-gain split of A2b's image-present gain | that the access-matrix result is not a formatting artifact |

### 2B. Phase 0 — no GPU training; blocking
| ID | Task | Why blocking / requirement |
|---|---|---|
| P0.1 | Measure **premise-probe accuracy separately** on the B1 batch, all models | If premises are at floor, C3 supplies no gradient and IGPO cannot learn on chained items. Determines whether the paper's most valuable result is reachable. Report premise accuracy, reasoning-given-correct-premise, member accuracy, pair accuracy, and premise-transition accuracy as five separate numbers. |
| P0.2 | Fix the **equal-gold invariance scorer** (two-gold ambiguity guard structurally fails equal-gold items) | Invariance is the anti-gaming component (I5, I13); it cannot rest on single-gold workaround scoring. Ships with an adversarial fixture. |
| P0.3 | Freeze and version the **intervention-group schema**; add loader validation fixture | I15. |
| P0.4 | Fix task **roles** in all reports and text | Primary visual anchor / saturated positive control + retention canary / oracle-localized readout control. No aggregate across roles (I13). |

### 2C. Phase 1 — minimum capability extension (development scale only)
| ID | Task | Requirement |
|---|---|---|
| P1.1 | Cue ladder track | Shared scene program across rungs; decoy gold follows the question (I12). Doubles as Paper-1 task CL. |
| P1.2 | Binding and distractor track | **Scales B1's existing `binding_swap` / `distractor_only` types — not a new build.** Add similar-label interference, same-abscissa/ordinate distractors, position exchange, question-cue conflict. |
| P1.3 | Causal / invariance groups | Both present in every group; reported separately (I13). Scales B1's `style_twin` and `fact_read` types. |
| P1.4 | Generate **100–300 development groups only** | Check difficulty band, blind-solvability, scorer behaviour, and whether IGPO produces non-zero training signal. **Do not generate tens of thousands of items before Mini-A5 prints a positive signal.** |
| P1.5 | Acceptance gates on every new track | Caption stress, blind floor, attacker check, difficulty band (I14). |
| P1.6 | Per-item Δq metadata | C1 sampling has nothing to sample on otherwise. |
| P1.7 | Program-level three-way split registration | Training / development (~300–600) / confirmatory (~600–1,200), split by scene program and template family, never random item split (I6). R19+R20 excluded from all three. |

### 2C-bis. Phase 2+ — gated expansion
Phase 2 (premise curriculum) expands only if P0.1 shows learnable signal; if premise accuracy is near zero, build a simpler premise curriculum or a small verified warm start — and if a warm start is used, train the SFT+standard-GRPO comparator alongside (I16). Phase 3: full development and confirmatory sets, human sampling audit, frozen metrics and scorer, then 3B and 7B runs. Phase 4: external transfer, each benchmark reported with image-present **and** blind conditions.

### 2D. Method implementation
| Component | Implementation requirement | Invariant |
|---|---|---|
| C1 necessity sampling | Sampling probability ∝ f(Δq_i). Ablation only: post-normalization loss weighting. **Never reward scaling.** | I1 |
| C2 intervention groups | Group = one scene's members; reward on the relation (R_causal, R_inv); members scored jointly; order randomized. Reuse Mini-A5's shared-group-uid broadcast-reward path and its advantage-tensor equivalence test. | I2, I3, I4, I5 |
| C3 premise-verified reward | Hierarchical: premise · reasoning-given-premise · answer · synchronized change. Programmatic verification, no model judge. | — |
| C4 twin-contrastive loss | Pre-registered fallback; engaged only on the "attribution moves, competence flat" branch. | — |
| — | Blind-likelihood discount **removed** — no-op under GRPO normalization. Do not implement. | I1, I2 |

### 2E. Training stages
| Stage | Arms | Notes |
|---|---|---|
| Gate 1 | standard GRPO · paired-data + answer-only · necessity + answer-only · full IGPO | Small. Answers data / selection / relational-reward in sequence. |
| Stage 2 (3B) | standard · paired-data · necessity-only · relation-only · full IGPO | Ablations: drop causal / drop invariance / drop premise / drop necessity; C1 sampling-vs-loss-weight form. |
| Stage 3 (7B) | standard · full IGPO · minimal blind control | Three runs, not a matrix. |
| Efficiency ablation | blind-first curriculum at matched total compute | Registered probe: Paper-1's 42-item corrosion set. Not headline. |

### 2F. Evaluation harness (must exist before Stage 2)
Co-primary A — competence: counterfactual pair accuracy, hard negatives, binding, prior-conflict, premise extraction, chained reasoning, invariance specificity, held-out-template transfer.
Co-primary B — attribution: VAG = ΔAcc(method, real) − ΔAcc(matched same-data blind control, real), with constraints (real up, blind not significantly down, A rises jointly). **Requires training a same-data blind control per method arm** — budget it explicitly (I8).
Supporting: external benchmarks with blind variants at matched compute; corrosion probe; calibration.

---

## PART 3 — Human items (Richard)
- [ ] Chart-v08 no-zoom audit (~1–2 h; package ready) — blocks chart-v08 freeze and P2 of the benchmark build.
- [ ] 24-candidate support-expansion review (~30 min; viewer ready) — A2b's five are the qualitative window into what image-free training installed.
- [ ] R20 human audit sample (~30 min).
- [ ] Cue-ladder legibility spot-check when Phase-1 rungs render (~20 min) — confirm the region-cue rung is genuinely ambiguous about the exact point and the no-cue rung is answerable by a careful human.
- [ ] Merges as sign-offs: D3 estimand registration, P1.2 split registration, Gate-1 registration.

## PART 4 — Conventions
Ledger `reports/main_progress.md`, one line per task, `pass | fail | blocked` with a note; honest `blocked` always beats a thin pass. Registration merges before first optimizer step (I9). Reports carry numbers, checks, and provenance — never interpretation. Language locks per `PAPER1_RESEARCH_DOC.md` §9 apply to every report and ledger note.
