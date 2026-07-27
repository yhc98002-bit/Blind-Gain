# Main progress ledger

Authoritative task ledger per `docs/EXPERIMENT_TODO.md` Part 4. One line per
task: `pass | fail | blocked` plus a note. An honest `blocked` always beats a
thin `pass`. Reports carry numbers, checks, and provenance — never
interpretation. Language locks per `docs/PAPER1_RESEARCH_DOC.md` §9 apply here.

Supersedes `reports/x_diagnostics_progress.md` (retained, not deleted).
Source of truth for the three guide documents is the PI's local machine; the
`docs/` copies are reference.

Updated 2026-07-27.

## Paper 1

| ID | Task | Status | Note |
|---|---|---|---|
| C1 | Pilot seeds 1–3, four arms, geo3k, 100 steps | pass | Three-seed gains A1 +0.2435, A3 +0.1048, A2b +0.0460, A2 +0.0161. |
| C1b | Pooled item-level equivalence (registered ±0.05 SESOI) | pass | Cluster bootstrap over 600 pair_ids. A1 equivalent (TOST [−0.0150,+0.0256]); A2 gray **not** equivalent; A2b marginal. `reports/pooled_item_equivalence_v1.*`. |
| — | Base FlipTrack endpoint re-measurement | pass | Reproduces pinned 0.4717 lenient / 0.4433 strict exactly under the current harness. Minuend verified, not inherited. |
| D2 | Test-time access, three seeds | pass | Only 12–17% of A1's gain survives image removal. |
| D3 | Train×test grid | pass | **36/36 cells complete.** Registered branch (a): blind arms recover 42–57% when tested with images vs 4–23% matched. |
| D3b | TrainShare estimand + paired item-level CIs | pending | PAPER1 §8 branches. Must be labeled a declared post-hoc recomputation — all 36 cells were read under the ratio-based D3 registration. |
| X1/X5 | Image-condition matrix, seeds 1–2 | pass | Mismatched-image inflation statistically zero in every arm. |
| X2 | Hard-negative ranking v2 | pass | Registered bottom branch fired: 0.9067 is predominantly candidate-set structure. |
| X3 | A2 −0.045 item forensics | pass | Jaccard 0.724 vs null 0.098; 41/42 same wrong answer. |
| X4 | Calibration (exploratory) | pass | Confidence tracks image presence, not correctness. |
| B1 | Geometry track declared batch + trained scoring | pass | Six intervention types; chained premise 0.000 pair / 0.150 member. |
| F2d | Template decomposition of overall R19 movement | pending | Cached predictions, no new inference. |
| M5 | Long-horizon to step 400 | running | Step 366/400 on an12:0–3. Terminal rule merged; no extension under any outcome. |
| A5 | Mini-A5 CP vs matched same-data GRPO | running | CP arm 47/120 on an29:0–7. Matched arm queued; 4-arm Gate-1 registration to be prepared in parallel. |
| M7 | ViRL39K stratified decomposition | blocked | Built; awaiting a full free node (an12 after M5). |
| C5 | 7B access pair | blocked | Re-scoped to A1 and A2b only, one seed. Awaiting a node. |
| M11 | Cross-family completion | blocked | State ambiguous in prior ledgers between "validity confirmed" and "full matrix pending"; must be resolved before any claim. |
| CL | Cue ladder on existing checkpoints (F4b) | pending | Generation CPU; scoring inference-only, fits 4-GPU gaps. Register before scoring; invariants I12, I13. |
| X6 | Related-work nine-column table | blocked | PI-owned, not a cluster task. |

## Paper 2 — Gate 0 (no GPUs, runs first)

| ID | Analysis | Status | Note |
|---|---|---|---|
| G0.1 | A1 gains vs Δq concentration | pending | Δq source = blind-solvability audit (real vs none, 2,702 items). Base step-0 geo3k eval running to supply per-item base under the arm harness. |
| G0.2 | A2b image-present gain vs blind solvability | pending | **Freezes Paper 1's title claim.** |
| G0.3 | A1/A2b newly-correct overlap (Jaccard + permutation null) | pending | |
| G0.4 | Answer-gain vs format-gain split of A2b's gain | pending | Per-arm `strict_gain_accounting` already carries AnswerGain / G_format with `identity_exact`. |

## Paper 2 — Phase 0 (no GPU training; blocking)

| ID | Task | Status | Note |
|---|---|---|---|
| P0.1 | Premise-probe accuracy, five separate numbers | pass | Base premise member 0.275 (95% [0.137,0.413]); registered branch **(b)** fires — construct revised before release. Reasoning\|correct-premise 0.273 at base. `reports/p01_premise_probe_v1.*`. |
| P0.2 | Equal-gold invariance scorer | pass | `acc_final = gold_tier > other_tier` was structurally false on equal-gold pairs. Fixed with an equal-gold branch; 7-case adversarial fixture the pre-fix code fails; R19 rescores to 0.4717/0.4433 unchanged; frozen R20 scorer untouched (I11). |
| P0.3 | Freeze and version intervention-group schema + loader fixture | pending | I15. |
| P0.4 | Fix task roles in all reports and text | pending | Primary visual anchor / saturated positive control + retention canary / oracle-localized readout control. No aggregate across roles (I13). |

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
