# Experiment To-Do — Engineering Implementation
Companion to `PAPER1_RESEARCH_DOC.md` and `PAPER2_RESEARCH_DOC.md`. Those define *what claim* each experiment serves; this file defines *what the code must do* so the two never diverge. Updated 2026-07-27.

**Benchmark stance (2026-07-27).** For Paper 1: **finalize, do not extend.** Remaining benchmark work is scoring and documentation only — Phase 0 below. New capability tracks are Paper-2 work and stay gated on Mini-A5; if the endpoint proves unmovable, tracks built now would measure something no method can affect.

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
| I18 | Every blind/retention figure is reported against the null appropriate to its answer format (MC → 1/k; free-form → ≈0; mixed → split), with bootstrap CIs. Conclusions about a benchmark's blind opportunity are written after its split is computed, never before. | Raw retention on multiple-choice benchmarks reports the guessing floor as if it were prior exploitation — and asserting a comparison before computing it is how that error arose. |
| I19 | The long-horizon run extends the **anchor** (unfrozen tower, native reward, unfiltered corpus), never pilot A1. Every mention states the configuration and names the unfiltered corpus as a confound. | Misattributing it to A1 claims a controlled result we did not run — and discards the stronger fact that corrosion occurs with gradients reaching the vision encoder. |
| I17 | Baselines are implemented as published. No component of our method is transplanted into a baseline; fairness is secured by matched backbone/data/compute, baseline-specific tuning, and reproducing the baseline's own claimed benefit before reporting. | A baseline carrying our contribution is neither the published method nor a clean ablation, and it hands our novelty to prior work. |
| I20 | Template roles are stated from measured base accuracies, never from an assumed ceiling; no template is described as saturated or zero-contributing without the number that justifies it. | The header table was asserted saturated at 1.000; it is 0.8667 and supplies 18.7% of A1's movement. |
| I21 | Any generator that rewrites question text must recompute gold from scene ground truth and verify gold against the **question-named entity**; any variant family built by replaying existing renders must ship a rendered-diff proof that the annotation layer actually differs across variants. | The cue-ladder builder renamed questions without recomputing golds or re-rendering; its verifier passed by checking the wrong operand. |

---

## PART 1 — Paper 1

### 1A. Complete
| ID | Experiment | Serves | Status |
|---|---|---|---|
| C1 | Pilot seeds 1–3, four arms (A1 real / A2 gray / A2b no-image / A3 caption), geo3k, 100 steps | F1, F2, ladder R1 | ✅ |
| D2 | Test-time access, three seeds | F1 | ✅ |
| D3 | Train×test grid, 36 cells | **F1 — the central figure** | ✅ registered branch (a): ratio > 2 for both blind arms in all three seeds; strict control 1.95–2.69, qualifying not overturning |
| X1/X5 | Image-condition matrix, seeds 1–2 (correct / mismatched-real / twin / gray / no-image × both layers) | F3 | ✅ |
| X2 | Hard-negative ranking v2, registered ladder fired (bottom branch) | F4, candidate-set correction | ✅ |
| X3 | A2 −0.045 item forensics (Jaccard 0.724 vs null 0.098) | F5 | ✅ |
| X4 | Calibration, exploratory | F6 | ✅ |
| B1 | Geometry track declared batch + trained-checkpoint scoring | F5, benchmark §5 | ✅ |
| D4 | Caption test column, 4×3 → 4×4 | F1 | ✅ branch (a) **evidence-general**: ρ(caption,real)=+0.80, caption spread 4.0× blind spread. A3 ratio 1.67 (<2×) — reported as a confirmed prediction, since A3's matched condition is evidence-bearing |
| M5 | Long horizon → step 400 | **R2** | ✅ **verdict FALLING**: geometry pair acc 0.4800 → 0.4133, Δ −0.0667 [−0.0933,−0.0400]; below the frozen base 0.4717; strict ≡ lenient; blind floor holds at 0.0. Terminal — no extension |
| M11 | Cross-family generalization | R5 | ✅ recovered 2026-07-28 |
| G0 | Gate-0 stratification | title claim + Paper-2 C1 | ✅ **G0.2: image-free training recovers 84% of A1's gain on blind-answerable items and 42% on items requiring pixels** |
| E1a | Base external-benchmark blind columns | **motivation / opening** | ✅ **naive figures WITHDRAWN — superseded by CHANCE.** Corrected (I18): MMStar **−0.029 [−0.108, +0.049]** (3B) and **+0.053 [−0.010, +0.117]** (7B) — indistinguishable from the 0.2688 guessing floor, so MMStar is image-necessary, not blind-solvable. MathVista **split**: MC +0.458/+0.464, free-form +0.228/+0.210; its old whole-benchmark 53%/51% was a forbidden cross-format average. Cross-family: **only free-form is reportable** — Gemma-3 0.727 [0.690, 0.765], InternVL3-9B 0.485 [0.439, 0.533]; **both MC ratios withheld** (Gemma-3's with-image MC accuracy 0.1349 is *below* its 0.2679 null → negative denominator, 100% of replicates degenerate). FlipTrack 0.0000 collapse 1.0 for every model — unchanged. |
| CL | Cue ladder v1 | Paper 2 P1.1 | ❌ **INVALID BUILD — 2026-08-11 PI review.** All six rungs reference the byte-identical v07 image (pixel diff = 0; `replayed_from: starred_series_value_nine_v07`); the annotation layer never varied; golds were copied from the starred series while named/none/decoy questions name other series (question–gold mismatch on 4/6 rungs); the verifier's `gold_follows_question` checked gold against the *target*, not the question. The July readout numbers (+0.317 / −0.277) are wrong-gold artifacts. **The "marker is cue and occluder" story and the text-priority micro-result are RETRACTED.** The validity gates correctly detected invalidity; the attached mechanism was unsupported. Arm cells were never scored — nothing propagated to results. |
| — | Instrument dossier: R19, one-shot R20, 72B caption stress, attackers, human audit, cross-family | C3 | ✅ |

### 1B. In flight
| ID | Experiment | Serves | Implementation requirement |
|---|---|---|---|
| A5 | Mini-A5 | **F8**, Paper-2 Gate 1 | ✅ **complete 2026-07-30.** Gate PASS; **branch 2 fired** — primary anchor flat on three of four measurements (ranking lenient/strict, generation lenient); the +0.07 generation-strict gap decomposes exactly to contract validity (residual 1e−17, 85.7% from the member arm falling below base). Content moved only on the oracle-localized readout control, replicated on R20 — F3's layer selectivity reproduced by a method built to breach it. Catch-stability instrument built later reads invariance at ceiling for both arms; strict gaps are format again (4th independent localisation). `reports/f8_mini_a5_endpoint_readout_v1.*`, `f8_secondaries_v1.md`, `mini_a5_catch_stability_readout_v1.*` |
| M7 | ViRL39K stratified, 4 arms seed 1 | R3 | ✅ **complete (seed 1) 2026-08-04.** Registered secondary passes hugely: matched-evaluation recovery **0.7174 (A2-gray) / 0.7449 (A2b)** vs geo3k anchors 0.0789/0.1184 — differences +0.64/+0.63, stable. **Which access regime a corpus sits in is measurable in advance from its blind-opportunity audit.** ρ_gain direction **fails** all three blind arms (gains track headroom, −0.26/−0.26/−0.73); ρ_recovery point-positive for blind arms (A2b +0.504). One-seed tag on every number; seed 2 relaunches after the C5 pair (attempt 1 died in the 08-03 an29 host-OOM cascade, deviations logged). `reports/m7_r3_readout_v1.*` |

### 1B-bis. **Highest priority — completes R2 into a headline figure**
| ID | Experiment | Serves | Implementation requirement |
|---|---|---|---|
| **M5b** | **geo3k benchmark trajectory across the M5 checkpoints** | turns R2 into **the scissors figure** and gates the title upgrade | **Check for existing artifacts first** — the merged extension registered "benchmark + FlipTrack R19 evaluations at steps 150, 200, 300, 400", so these numbers may already exist and this may be a reporting gap rather than an experiment. If absent, evaluate geo3k `Acc_final` at 100/150/200/300/400 on the existing checkpoints, locked contract, paired CIs. Plot benchmark and grounding on identical axes with the frozen-base reference; the divergence in trajectory matters more than the terminal difference. |
| **CHANCE** | **Null correction on every blind-retention figure** | **protects F0, the paper's opening** | ✅ **DONE 2026-07-28** — `reports/chance_corrected_retention_v1.*`. **Coverage is partial and that is a finding, not an omission:** BLINK, HallusionBench, MMVP, MathVerse and MMMU have **no image-removed run anywhere**, so no retention (naive or corrected) exists for them; k is available for future work. Executed spec: Retention = (blind − null)/(with-image − null), with **item-level bootstrap CIs** — it is a ratio of differences, so naive intervals do not apply. **Null rule by answer format:** multiple-choice → 1/k; free-form numeric → ≈0, no correction; **mixed benchmarks split into MC and free-form subsets and reported separately**, never one global null. Report image-present accuracy, blind accuracy, the null, corrected retention, and CI for every benchmark. Known: MMStar is 4-way MC, blind 0.2607/0.2880 vs 0.25 → corrected retention ≈3.5%, not 47%. **Do not assert that any other benchmark retains materially more until its split is computed** — MathVista is roughly half MC and its correction may also be large; if its free-form subset holds up, that is the stronger result since no guessing explains it. Pure arithmetic on existing numbers. |
| **SEED3γ** | Third-seed replication of the A2-gray −0.0450 attractor | **gates Tier-1 wording of the corrosion ladder** | Cached predictions; no GPU. Until it returns, Tier 1 reads "across two analyzed seeds," not "across seeds." A 3/3 structured replication strengthens the formal corrosion concept at essentially zero interpretive cost — run it with CHANCE. |
| LH2 | Second long-horizon seed — **staged, conditional** | Tier-3 upgrade of the corrosion ladder | Do **not** commit a full 400-step run before M5b. Sequence: (1) recover or run M5b; (2) if the scissors pattern appears, register LH2; (3) run the second seed through the intermediate checkpoints only; (4) continue to step 400 **only if** the grounding trajectory reproduces directionally. Each stage is a separate go/no-go. |

### 1C. Remaining
| ID | Experiment | Serves | Implementation requirement |
|---|---|---|---|
| M7 | **ViRL39K stratified decomposition — PROMOTED** (built, awaiting node) | ladder R3; second corpus for a bold claim | Strata = source × category with stratum-level q̄ attached; per-stratum estimands registered; pooled reported secondary. Prediction (merged pre-launch): recovery tracks stratum blind-opportunity. |
| C5 | 7B access pair | ladder R4; second scale | ✅ **complete 2026-08-07 — LADDER R1–R5 CLOSED.** Registered readout `reports/c5_r4_readout_v1.*`, all 18 checks true, 5000/5000 draws. Matched gain A1 **+0.2479** (vs +0.2435 at 3B — recipe transfers); crossed TrainShare A2-gray **0.7785 [0.6418, 0.9214]** canonical / **0.8402 [0.7457, 0.9456]** strict vs 3B pooled 0.487 [0.383, 0.588] (cross-scale descriptive, intervals disjoint) — **the access phenomenon grows with scale**. Matched A2-gray gain still only +0.0516: F1's two-regime structure reproduces at 7B with a wider crossed/matched gap. One seed; A2b not run (registered fired-fork choice). Collected: RESULTS §12e. |
| M11 | Cross-family completion | ladder R5 | Inference only. Confirm current state in the ledger; snapshot is ambiguous between "validity confirmed" and "full matrix pending." |
| X6 | Related-work nine-column table | positioning | **PI-owned, not a cluster task.** |
| **D4** | **Caption test column — completes the D3 matrix** | **F1** — is the readout policy pixel-specific or evidence-general? | The registered matrix is 4×3 because A3's own condition is absent. Score all four arms × 3 seeds under *tested-with-caption* using the frozen 3B caption store, same locked decoding. If caption-at-test reproduces the real-image ordering, the policy reads evidence generally; if not, it is pixel-specific. **Inference only on existing checkpoints — the one addition to Paper 1.** |
| **E1b** | **Trained-arm external-benchmark access columns** | **generalization of F1 beyond geo3k** | 🔄 **blind column DONE 2026-07-28 (24/24), with-image column running.** Registered `docs/registered_e1b_external_access_matrix_v1.md` before any cell ran. **P1 refuted:** no arm beats base blind on either benchmark or any subset — twelve intervals, all containing zero, widest Δ 0.006. **P2 withheld** (not evaluable: it scales by A1's own blind gain, which is null). Strict shows a real gain for A1 (+0.0411 MMStar, +0.0798 MathVista MC) but `Format_valid` tracks it step for step, so **what transfers is output-format compliance, not blind answering**. `reports/e1b_blind_readout_v1.json`. Base rows complete (E1a). Now evaluate all four arms × 3 seeds on the pinned suite **with and without images**, locked decoding. Expected shape if the mechanism holds — blind-trained arms beat base *with* images and match base *without*. **Inference only, no training.** |
| E2 | Anchor as recipe-variation comparison | robustness of the dissociation across configurations | ✅ **complete 2026-08-04** (assembly only, 17 hashed sources, build fails on mismatch). The dissociation reproduces under a recipe differing in **all three** blamable factors: pilot A1 benchmark +0.2435 / grounding +0.0056 [−0.018, +0.029] (3 seeds, equivalence supported) vs anchor +0.2562 / +0.0083 (p 0.64) — nearly identical magnitudes on both axes. Anchor-only 100→400 extension carries the corrosion trajectory with the I19 clause. Caveats: one anchor seed; three coupled factors, robustness not factorial. `reports/e2_recipe_variation_v1.*` | |
| G0 | Gate-0 stratification (see Part 2) | freezes the title claim | Cached predictions; also serves Paper 2. |
| F3d | Template decomposition of the overall-R19 movement | **sharpens F3** | Split the +0.0283/+0.0208/+0.0267 overall delta by template. Expectation from role analysis: the saturated table contributes zero and the movement concentrates on the oracle-localized readout control. Cached predictions, no new inference. |

---

## PART 2 — Paper 2

### 2A. Gate 0 — no GPUs, run first
| ID | Analysis | Decides |
|---|---|---|
| G0.1 | Do A1's per-item gains concentrate on high-Δq items? | H1; whether C1 belongs in the method |
| G0.2 | Does A2b's image-present gain concentrate on low blind-solvability items? | whether the image-free gain is visual utilization or generic text-side improvement — **freezes Paper 1's title claim** |
| G0.3 | Overlap of A1 / A2b newly-correct sets (Jaccard + permutation null) | same policy or different policies |
| G0.4 | Answer-gain vs format-gain split of A2b's image-present gain | that the access-matrix result is not a formatting artifact |

### 2B. Phase 0 — no GPU training; blocking — ✅ **COMPLETE**
| ID | Task | Why blocking / requirement |
|---|---|---|
| P0.1 | Measure **premise-probe accuracy separately** on the B1 batch, all models | ✅ complete — branch (b): the chained-premise floor is **uninformative**, so it is not counted as evidence in F5 and the construct needs redesign before it can carry a Paper-2 claim. |
| P0.2 | Fix the **equal-gold invariance scorer** (two-gold ambiguity guard structurally fails equal-gold items) | Invariance is the anti-gaming component (I5, I13); it cannot rest on single-gold workaround scoring. Ships with an adversarial fixture. |
| P0.3 | Freeze and version the **intervention-group schema**; add loader validation fixture | I15. |
| P0.4 | Fix task **roles** in all reports and text | Primary visual anchor / saturated positive control + retention canary / oracle-localized readout control. No aggregate across roles (I13). |

### 2B-status (2026-08-11). premise-v2: all four acceptance gates run; blind floor 0.000; PI decisions taken — branch (c) step to n=5 **approved**; E2-failing intervention types **excluded from training use** until final-answer distributions are balanced. Chart-v08 calibration + necessity ablations verified clean at PI review (minimal-diff ablations, correct verifier invariants).

### 2C. Phase 1 — minimum capability extension (development scale only)
| ID | Task | Requirement |
|---|---|---|
| P1.1 | ~~Cue ladder v2 rebuild~~ **SUPERSEDED 2026-08-12** by the L1/L2/L3 hierarchy (HB below) | The L1 location-oracle derivation is the exact rung done properly; L2 is the named rung. Region/decoy survive only as optional calibration diagnostics, not built now. The v2 spec's hard requirements (non-occluding cue, gold-follows-question, rendered-diff proofs) transfer into HB's verifier set. |
| P1.1b | **Verifier-operand audit, all generators** — P0 of the hierarchy build | Every named verifier predicate traced to its exact operand; gold recomputed from the question-referenced entity; rendered-diff limited to permitted pixels; oracle variants preserve all non-oracle scene content; one adversarial fixture per generator that fails under the old buggy behavior. Census review packages mandatory before any freeze. |

### 2C-HB. Hierarchical benchmark (Paper-2 core instrument) — Discover → Ground → Read
| ID | Task | Requirement |
|---|---|---|
| HB.0 | **Registration before generation** | `docs/registered_hier_benchmark_v1.md` merges before any item exists: two families (`hier_coord_v1` on the premise-v2 generator; `hier_chart_v1` on the v08 renderer), three layers per mother-item, three pair roles, difficulty-knob grids, informativeness gates, split policy. One-shot dev batches per knob cell. |
| HB.1 | **Mother-item derivation** | Every L3 scene auto-derives L2 (target oracle: correct target identity given) and L1 (location oracle: non-occluding cue at the target). Identical across derivations: scene data, renderer, visual facts, final answer, distractors, scene-program ID. Only oracle information varies. `mother_item_id` links the three. |
| HB.2 | **L3 relations** | Coordinate family: canonical = **extremum discovery** (highest/lowest y, leftmost/rightmost); **nearest-neighbor = labeled hard tier** (premise-v2 full-run gates already forced n=5, so nearest sits near floor at 3B and cannot be canonical). Chart family: argmax-at-x → read same series at another x. |
| HB.3 | **Non-occlusion, operationalized** | L1 cue ink pixel-disjoint from all data ink (mask intersection = ∅, verified per render); cue rendered as offset callout or out-of-data-region pointer, never on-point occlusion (the v07 lesson). |
| HB.4 | **Pair roles** | target-switch (intervention changes which entity is the target) · target-stable (target fixed, downstream value flips) · invariance (irrelevant change; answer must not change). Reported separately, never averaged (I13). Prior-conflict and binding-swap remain in the generator as exploratory cells outside the core taxonomy. |
| HB.5 | **Ranking layer ships with the items** | Registered candidate sets + structured hard negatives per L2/L3 item at generation time, so candidate-evidence ranking and hard-negative discrimination read out on the hierarchy (Paper-2 co-primary A). |
| HB.6 | **Probes, no CoT** | Discovery probe (predicted target identity) + per-layer accuracies + pair successes. Failure patterns per the registered table (L1✓L2✓L3✗ = discovery bottleneck; L1✓L2✗ = grounding bottleneck; L1✗ = readout weak). |
| HB.7 | **P2 development validation — no training** | 150 mother-items per family per knob cell; run base 3B/7B + existing standard-GRPO and CP Gate-1 checkpoints. **Informativeness gates on base 3B:** monotone L1 > L2 > L3; L1 ∈ [0.60, 0.95]; L2 ∈ [0.20, 0.80]; L3 ≥ 0.05 in at least one pre-registered knob cell per family. Chart confirmatory cells keep 9-series density for caption resistance. |
| HB.8 | **P3 freeze** | Only after: human audit (Richard), blind floor, caption stress, attacker checks, difficulty calibration, verifier-operand audit, mother-item matching checks, program-level train/dev/confirmatory split. |
| HB.9 | **R19 mapping recorded** | Header table and chart = L1; coordinate register = L2; premise-v2 = L3. Paper 1's template decomposition becomes a hierarchy statement: standard RLVR moves L1, not L2. Written into both research docs. |
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
| Gate 1 | standard GRPO · paired-data + answer-only · necessity + answer-only · full IGPO | Small. Answers data / selection / relational-reward in sequence. | ✅ **COMPLETE 2026-08-09.** Acceptance audit 9/9 PASS before unseal. **No axis buys held-out content on the primary anchor** (lenient NOT MOVED, every contrast, every role; absolute levels vs base flat). Pairing alone is a format tax (member −0.32 strict on the canary, p=4e−27); necessity refunds part (+0.043 [0.018, 0.070] strict primary); **all four recipes move the oracle-localized readout +0.15–0.23 lenient — F3 layer selectivity is recipe-independent.** Catch: lenient at ceiling ×4; strict cp 0.64 ≈ std 0.62 > necessity 0.49 > member 0.28 (5th format localisation). One seed/arm. `reports/mini_a5_gate1_{acceptance_audit,endpoint_readout}_v1.*`, catch v1 jsons. PI reads the pre-committed branches for the Paper-2 direction. |
| Stage 2 (3B) | standard · paired-data · necessity-only · relation-only · full IGPO | Ablations: drop causal / drop invariance / drop premise / drop necessity; C1 sampling-vs-loss-weight form. |
| Stage 3 (7B) | standard · full IGPO · minimal blind control | Three runs, not a matrix. |
| Efficiency ablation | blind-first curriculum at matched total compute | Registered probe: Paper-1's 42-item corrosion set. Not headline. |

### 2E-bis. Prior-method baselines — implemented as published
| ID | Baseline | Implementation | Argumentative role |
|---|---|---|---|
| B-PR1 | Perception-R1 | **As published**: model-judged visual-description consistency reward. Do **not** substitute our verifiable premises. | Does an existing visual reward fix acquisition? |
| B-VPPO | VPPO | **As published**: attention-derived visual-dependency token reweighting. | Does existing credit reweighting reach the encoder? |

**Baseline integrity rules.**
1. **No component of our method is transplanted into a baseline.** Enhancing a baseline with our contribution produces a hybrid that is neither the published method nor a clean ablation, and it attributes our novelty to prior work. The question "would verified premises improve a description-style reward?" is a design-choice study of ours (below), not a baseline.
2. **Fairness lives on the axes that matter:** identical backbone, data, and compute budget; a baseline-specific hyperparameter search rather than inherited settings; every deviation forced by our setting reported explicitly.
3. **Implementation validation before reporting:** each baseline must reproduce its own claimed benefit on ordinary accuracy. A baseline that works exactly as advertised and still fails our criteria is the strongest possible result; a baseline that underperforms without this check invites "you implemented it badly."
4. **Every baseline is pushed through the access matrix** and scored on the co-primary criteria. If prior methods also show ~50% crossed recovery and flat competence, the field's current answer does not fix the problem either — a second diagnostic result rather than a courtesy comparison.

**Design-choice study (ours, not a baseline):** verified premise reward vs model-judged description reward, both inside IGPO. The win is attributed to our verification mechanism, where it belongs.

**Ablation, not a baseline:** standard GRPO on our generated corpus (Stage-2 arm "paired-data") isolates data volume from signal design and sits in the ablation ladder.

**Scope statement, not an experiment:** the mechanism argument concerns outcome-only rewards under group normalization, hence the GRPO family (GRPO, DAPO, RLOO, variants). PPO with a learned value baseline is a different credit path and belongs in the limitations sentence, not the GPU queue.

### 2F. Evaluation harness (must exist before Stage 2)
Co-primary A — competence: counterfactual pair accuracy, hard negatives, binding, prior-conflict, premise extraction, chained reasoning, invariance specificity, held-out-template transfer.
Co-primary B — attribution: VAG = ΔAcc(method, real) − ΔAcc(matched same-data blind control, real), with constraints (real up, blind not significantly down, A rises jointly). **Requires training a same-data blind control per method arm** — budget it explicitly (I8).
Supporting: external benchmarks with blind variants at matched compute; corrosion probe; calibration.

---

## PART 2-bis — Execution order (2026-07-28)
1. **CHANCE** — recompute every external retention against its format-appropriate null; regenerate the F0 table. No GPU.
2. **M5b** — locate existing benchmark artifacts first (the merged extension registered them); run only what is missing. Plot base + steps 100/150/200/300/400, geo3k accuracy and the R19 primary anchor on identical axes; trajectory divergence matters more than the terminal gap.
3. **SEED3γ** — third-seed structured corrosion; unlocks Tier-1 wording. No GPU.
4. **LH2 decision** — triggered only by a genuine scissors pattern in M5b, then staged per its row.
5. Finish **Mini-A5** and **M7** under their registered endpoints, unaltered.
6. **E1b** — trained-arm external columns, so the public-benchmark result connects to the gain decomposition.
7. **C5 7B configs** — author A1 and A2-gray after the current evidence chain is secured.

## PART 2-ter — Execution status (2026-08-11)

**Closed this round.**
- **C6 mechanism at scale** — six 7B FlipTrack cells (3 models × R19/R20) on banked C5 checkpoints; registration filed pre-read (`docs/registered_c6_mechanism_at_scale_v1.md`); instrument `scripts/build_c6_mechanism_at_scale_readout.py` with 61 adversarial fixtures green before it touched a real cell; all 16 acceptance checks pass. A1-real fires branch (d) (anchor MOVED, readout NOT MOVED) on both instruments and both contracts; A2-gray fires branch (c) everywhere. `reports/c6_mechanism_at_scale_v1.*`.
- **Track-4 E4** — PASS on the instrument's registered folded criterion. Registration wording to reconcile (prose says "CI includes 0.5"; the statistic is folded `max(AUC,1−AUC)` so the interval cannot include 0.5 by construction). No number changes.
- **Track-4 E1/E2 per-type readout** — instrument + 26 fixtures built and run. E1 FAIL branch (c); E2 premise clause PASS at 0.000 blind, final clause FAIL for all five types.

**Running.** E3 caption stress on an29 0–3 (`scripts/run_e3_caption_stress.sh`). M7 seed 2: a2_gray on an12 4–7, a3_caption on an29 4–7; evals auto-chain. LH2 stage 1 relaunches on `scripts/seed2_an12_chain.sh` when a2_gray finishes.

**Next.** (1) Read E3 against its registered per-type criterion. (2) PI go/no-go on the E1 branch-(c) step to n=5 and on rebalancing the premise-v2 final-answer distribution (E2's failing clause); the premise construct itself passes and is not regenerated. (3) Two-seed R3 readout when the last seed-2 eval lands.

## PART 3 — Human items (Richard)
- [ ] Chart-v08 no-zoom audit (~1–2 h; package ready) — blocks chart-v08 freeze and P2 of the benchmark build.
- [ ] 24-candidate support-expansion review (~30 min; viewer ready) — A2b's five are the qualitative window into what image-free training installed.
- [ ] R20 human audit sample (~30 min).
- [ ] Cue-ladder **v2** legibility spot-check when its rungs render (~20 min) — confirm region-cue is genuinely ambiguous about the exact point, the none rung carries no mark/star/caption, and the no-cue image is answerable by a careful human.
- [ ] Merges as sign-offs: D3 estimand registration, P1.2 split registration, Gate-1 registration.

## PART 4 — Conventions
Ledger `reports/main_progress.md`, one line per task, `pass | fail | blocked` with a note; honest `blocked` always beats a thin pass. Registration merges before first optimizer step (I9). Reports carry numbers, checks, and provenance — never interpretation. Language locks per `PAPER1_RESEARCH_DOC.md` §9 apply to every report and ledger note.

## PART 5 — State revision 2026-08-16 (post-ladder-closure; supersedes conflicting rows above)

**Closed with numbers:** R1–R5 ladder (R3 ViRL matched recovery 0.72–0.88 vs 0.08–0.12 geo3k; R4 TrainShare 0.487→0.779 disjoint; R5 ✓) · SEED3γ (3-way Jaccard 0.661 vs null 0.012 — Tier-1 corrosion wording unlocked) · Gate 1 four arms (resolvability, not shape) · C6 (7B real moves primary anchor +0.025/+0.023 both instruments, one seed, tier language, **no replication run ordered**) · E1b/E1c (blind gain corpus-local; MMVP blind 0.000) · E4 PASS · E1 branch (c) executed · M5c turnover 137/601 vs zero noise floor.

**Cancelled:** Paper-2 Stage-2 3B ablation matrix (Gate-1 null at four arms; rationale in PAPER2 §5).

**New decisive experiment (registration before launch):** ST3-7B — two arms on the HB training split, standard GRPO vs necessity-sampled intervention-group reward; pre-committed method-paper / limits-paper branches per PAPER2 §5. Launch order: after the two-seed R3 readout lands and HB P2 gates pass.

**In flight:** M7 seed-2 a2_gray + a3_caption → evals → **two-seed R3 readout (~08-16)** · LH2 stage 1 re-armed (directional read gates the title upgrade) · HB P0–P2 per the 08-12 dispatch.

**Decisions recorded (PI, 2026-08-16):** E3 = both readings reported, type indeterminate pending E2 fix, reading (a) unmodified · E4 = recompute unfolded per-attacker CIs, criterion untouched · storage = rule-based (delete non-terminal steps not referenced in §21; keep terminal + best + §21-referenced; byte-exact record) · Gate-1 §6 branch = resolvability; Stage-3 pilot is the method's make-or-break · GPT hierarchy plan = adopted 08-12 as amended (cue-ladder v2 superseded by L1 derivation).

**Infra fixes ordered (each ships an adversarial fixture, I10):** storage snapshot "pass"-while-over-quota bug · waiter wedged-vs-dead distinction (a stalled-but-alive trainer must not exhaust a deadline silently) · E3 STAGE-B argument-order bug · premise-v2 answer-balance constraint added to the registered design, failing types regenerated one-shot under it.

**Writing phase opens:** Paper-1 drafting begins (intro, F0–F2, instrument, mechanism, corrosion sections writable now; frozen slots: two-seed R3, LH2 direction, C6 tier). X6 related-work table remains PI-owned. Human gates queue unchanged (four delivered packages + chart-v08 no-zoom + R20 sample).
