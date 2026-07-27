# Main progress ledger

Authoritative task ledger per `docs/EXPERIMENT_TODO.md` Part 4. One line per
task: `pass | fail | blocked` plus a note. An honest `blocked` always beats a
thin `pass`. Reports carry numbers, checks, and provenance — never
interpretation. Language locks per `docs/PAPER1_RESEARCH_DOC.md` §9 apply here.

Supersedes `reports/x_diagnostics_progress.md` (retained, not deleted).
Source of truth for the three guide documents is the PI's local machine; the
`docs/` copies are reference.

Updated 2026-07-27 (Gate 0 and Phase 0 P0.1/P0.2 complete; F2d and TrainShare landed).

## Paper 1

| ID | Task | Status | Note |
|---|---|---|---|
| C1 | Pilot seeds 1–3, four arms, geo3k, 100 steps | pass | Three-seed gains A1 +0.2435, A3 +0.1048, A2b +0.0460, A2 +0.0161. |
| C1b | Pooled item-level equivalence (registered ±0.05 SESOI) | pass | Cluster bootstrap over 600 pair_ids. A1 equivalent (TOST [−0.0150,+0.0256]); A2 gray **not** equivalent; A2b marginal. `reports/pooled_item_equivalence_v1.*`. |
| — | Base FlipTrack endpoint re-measurement | pass | Reproduces pinned 0.4717 lenient / 0.4433 strict exactly under the current harness. Minuend verified, not inherited. |
| D2 | Test-time access, three seeds | pass | Only 12–17% of A1's gain survives image removal. |
| D3 | Train×test grid | pass | **36/36 cells complete.** Registered branch (a): blind arms recover 42–57% when tested with images vs 4–23% matched. |
| D3b | TrainShare estimand + paired item-level CIs | pass | Pooled 0.487 / 0.528 / 0.718, every CI entirely above 0.35 → **headline at full strength**. Labeled a declared post-hoc recomputation (does not satisfy I9). `reports/d3_trainshare_v1.*`. |
| X1/X5 | Image-condition matrix, seeds 1–2 | pass | Mismatched-image inflation statistically zero in every arm. |
| X2 | Hard-negative ranking v2 | pass | Registered bottom branch fired: 0.9067 is predominantly candidate-set structure. |
| X3 | A2 −0.045 item forensics | pass | Jaccard 0.724 vs null 0.098; 41/42 same wrong answer. |
| X4 | Calibration (exploratory) | pass | Confidence tracks image presence, not correctness. |
| B1 | Geometry track declared batch + trained scoring | pass | Six intervention types; chained premise 0.000 pair / 0.150 member. |
| F2d | Template decomposition of overall R19 movement | pass | Movement concentrates on the oracle-localized readout control (70% of A1's overall); primary anchor flat (CI spans zero). **Correction: the header table is not saturated at 1.000 — base 0.8667, contributes 18.7%.** Blind arms decline on the anchor while rising on the cued control. `reports/f2d_template_decomposition_v1.*`. |
| M5 | Long-horizon to step 400 | running | Step 366/400 on an12:0–3. Terminal rule merged; no extension under any outcome. |
| A5 | Mini-A5 CP vs matched same-data GRPO | running | CP arm 47/120 on an29:0–7. Matched arm queued; 4-arm Gate-1 registration to be prepared in parallel. |
| M7 | ViRL39K stratified decomposition | blocked | Built; awaiting a full free node (an12 after M5). |
| C5 | 7B access pair | blocked | Re-scoped to A1 and A2b only, one seed. Awaiting a node. |
| M11 | Cross-family completion | blocked | State ambiguous in prior ledgers between "validity confirmed" and "full matrix pending"; must be resolved before any claim. |
| CL | Cue ladder on existing checkpoints (F4b) | running | Registered `docs/registered_cue_ladder_v1.md` before any scoring. Four rungs replayed from the frozen R19 nine-series `pair_seed`s, so the ladder is item-paired with R19; replay integrity gate passes 300/300. Scoring next on free GPUs. |
| X6 | Related-work nine-column table | blocked | PI-owned, not a cluster task. |

## Paper 2 — Gate 0 (no GPUs, runs first)

| ID | Analysis | Status | Note |
|---|---|---|---|
| G0.1 | A1 gains vs Δq concentration | pass | Monotone across Δq terciles for **both** A1 and A2b (ρ +0.198 / +0.192, perm p ≤ 0.0005). H1 supported; C1 necessity sampling earns its place. |
| G0.2 | A2b image-present gain vs blind solvability | pass | **Opposite of the hypothesis**: concentrates on blind-*answerable* items — 84% of A1's gain there vs 42% where no blind success was observed (91% vs 61% base-wrong control). Title claim survives with a scope qualifier; direct support for H1. |
| G0.3 | A1/A2b newly-correct overlap (Jaccard + permutation null) | pass | Jaccard 0.363–0.423 vs null 0.157–0.177, p ≤ 0.004 all seeds. Overlapping policies, ~60% of the union arm-specific. |
| G0.4 | Answer-gain vs format-gain split of A2b's gain | pass | Format gain **exactly +0.1148 for all four arms** by identity (every trained arm has acc_strict == acc_final, so it collapses to base_final − base_strict). The access matrix is format-free by construction. |

## Paper 2 — Phase 0 (no GPU training; blocking)

| ID | Task | Status | Note |
|---|---|---|---|
| P0.1 | Premise-probe accuracy, five separate numbers | pass | Base premise member 0.275 (95% [0.137,0.413]); registered branch **(b)** fires — construct revised before release. Reasoning\|correct-premise 0.273 at base. `reports/p01_premise_probe_v1.*`. |
| P0.2 | Equal-gold invariance scorer | pass | `acc_final = gold_tier > other_tier` was structurally false on equal-gold pairs. Fixed with an equal-gold branch; 7-case adversarial fixture the pre-fix code fails; R19 rescores to 0.4717/0.4433 unchanged; frozen R20 scorer untouched (I11). |
| P0.3 | Freeze and version intervention-group schema + loader fixture | pass | `src/train/intervention_group_schema.py` pins v1 and fails closed on unknown versions; rejects causal members sharing the original answer, groups without an invariance member (I5), and stale `delta_q`. 13-case fixture. |
| P0.4 | Fix task roles in all reports and text | pass | `src/eval/task_roles.py` + 8-case I13 guard; unknown tasks fail closed. Registered primary endpoint already role-pure; only the `overall` key crosses roles and is now labelled an accounting identity. Registry records `SATURATION_CLAIM_IS_ACCURATE = False`. `reports/p04_task_roles_v1.md`. |

## Human items (Richard)

| Item | Status |
|---|---|
| Chart-v08 no-zoom audit | blocked — package ready |
| 24-candidate support-expansion review | blocked — viewer ready |
| R20 human audit sample | blocked |
| Cue-ladder legibility spot-check | blocked — awaits Phase-1 rungs |
| Sign-off merges (D3 estimand, P1.2 split, Gate-1) | blocked |

## Known defects and integrity notes

- The 9 failing tests in `tests/` at HEAD are orchestration/queue/manifest tests
  and predate the P0.2 change; all 74 scorer-touching tests pass.
- B1 invariance types (`style_twin` 14/14, `distractor_only` 16/16) were scored
  with a single-gold workaround before P0.2 and must be rescored before reuse.
- The B1 premise probe's on-disk `metrics.json` files read 0.000 for every cell
  under the pre-fix scorer and are void; cite the rescored readout instead.
