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
| M5 | Long-horizon to step 400 | running | Step 393/400 on an12:0–3. Terminal readout **tooling built and armed** (`scripts/build_m5_terminal_readout.py`) implementing MAIN_PHASE_RULING R1 exactly: Delta on R19 **geometry** pair accuracy, 400 vs 100, item-paired bootstrap CI, FLAT/RISING/FALLING/INDETERMINATE. Steps 150/200/300 are descriptive and cannot select the endpoint. Step-100 endpoint resolved and verified at 600 geometry rows. **Step 400 is terminal — no extension or rerun under any outcome.** |
| A5 | Mini-A5 CP vs matched same-data GRPO | running | **CP arm complete at 120/120** (`mini_a5_cp_main_an29_20260727T064527Z`, status complete, `global_step_120` written). **Matched member arm launched** on the now-free an29 0–7 (`mini_a5_member_main_an29_20260728T023715Z`); member config sha256 verified against the registration, storage guard pass. The two arms differ only in `pair_group_mode` and the reward callback. Readout on held-out-template pair accuracy, not margins; the advantage-tensor equivalence test must pass first. Gate-1 four-arm registration already merged behind it. |
| M7 | ViRL39K stratified decomposition | blocked | Built; awaiting a full free node (an12 after M5). |
| C5 | 7B access pair | blocked | Re-scoped to A1 and **A2-gray** only, one seed (not A2b: A2-gray is retained by the fired precommitted M8 fork rule, Extension 4 of `docs/registered_extensions_v1.md` — gray 0.2456 vs no-image 0.1824, non-overlapping 95% intervals; a rule-citation, not preference). Authored + registered 2026-07-30: `docs/registered_c5_7b_access_pair_v1.md`, `reports/c5_arm_configs_v1.json`, `scripts/launch_c5_7b_arm.sh`. No 7B base geo3k eval exists yet; required before readout. Launch when M7 frees GPUs (~2026-08-02). |
| M11 | Cross-family completion | **pass** | **Corrected 2026-07-28 — R5 is LANDED.** The full 18-cell matrix completed via `m11_reconciled_backfill_v2_login_20260717T075457Z` (status complete, exit 0): 12 FlipTrack cells (InternVL3-9B, Gemma-3 x {R19,R20} x {real,caption,none}) plus a 6-cell blind-sample matrix. `reports/generalization_audits_v2.json` has status pass, zero errors, all six completeness checks true, and `performance_values_opened_only_after_complete_queue_gate=true`. My 2026-07-27 entry claiming "the 18-cell full matrix never ran" was wrong. |
| CL | Cue ladder on existing checkpoints (F4b) | fail | Gate 1 pass (exact reproduces R19). Gate 2 **fails under both rung designs** (v1 0.4533/0.1367/0.6167; v2 0.3333/0.6100/0.6167), so branches (a)/(b) are void and the 12 arm cells were deliberately **not scored** — F2d's prediction is untested, not refuted. Cause: the on-point annotation is a cue *and* an occluder (+0.317 when it is the sole identifier, −0.277 when the series is named). Instrument findings stand: R19's nine-series marker occludes the datum it localizes; at 3B a correct or misleading visual cue adds ~nothing once text names the series. v3 redesign specified, not attempted this round. `reports/cue_ladder_readout_v1.*`. |
| X6 | Related-work nine-column table | blocked | PI-owned, not a cluster task. |

## Paper 2 — Gate 0 (no GPUs, runs first)

| ID | Analysis | Status | Note |
|---|---|---|---|
| G0.1 | A1 gains vs Δq concentration | pass | Monotone across Δq terciles for **both** A1 and A2b (ρ +0.198 / +0.192, perm p ≤ 0.0005). H1 supported; C1 necessity sampling earns its place. |
| G0.2 | A2b image-present gain vs blind solvability | pass | **Opposite of the hypothesis**: concentrates on blind-*answerable* items — 84% of A1's gain there vs 42% where no blind success was observed (91% vs 61% base-wrong control). Title claim survives with a scope qualifier; direct support for H1. |
| G0.3 | A1/A2b newly-correct overlap (Jaccard + permutation null) | pass | Jaccard 0.363–0.423 vs null 0.157–0.177, p ≤ 0.004 all seeds. Overlapping policies, ~60% of the union arm-specific. |
| G0.4 | Answer-gain vs format-gain split of A2b's gain | pass | Format gain **exactly +0.1148 for all four arms** by identity (every trained arm has acc_strict == acc_final, so it collapses to base_final − base_strict). The access matrix is format-free by construction. |


## Paper 2 — Gate 1 (gated on F7)

| ID | Task | Status | Note |
|---|---|---|---|
| Gate 1 | Four-arm decomposition (standard / paired-data / necessity / IGPO) | blocked | Registered before any optimizer step (I9). Blocked on F7 and on a free node. Success is held-out-template pair accuracy at the scene-program level; margins explicitly excluded (X2 bottom branch), chained premise excluded (P0.1 branch (b)); no branch reads as success unless VAG is positive (I8). |

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
  with a single-gold workaround before P0.2. **Rescored under the fixed scorer:
  0 of 30 cells move** — all differences are 3-dp rounding in the published
  table — so the published B1 numbers stand. The workaround was fragile in
  principle (never validated against the two-gold path; a response matching the
  other member's gold would have been mis-scored) but was equivalent on these
  items. `reports/b1_rescored_p02_v1.json`. **Closed.**
- The B1 premise probe's on-disk `metrics.json` files read 0.000 for every cell
  under the pre-fix scorer and are void; cite the rescored readout instead.
- `reports/m11_execution_queue_status_v10.md` describes its queue as `running` while that
  queue's manifest says `fail`. **Both were stale**: the work was completed two days later by
  `m11_reconciled_backfill_v2`. The real lesson is stronger than "check the manifest, not the
  status report" — a failed run manifest does not mean the work never happened. Search for a
  successor run before recording anything as never-ran.

## Implementation issues (not scientific results)

- **M7 launcher requested 8 GPUs against a 4-GPU registered config.**
  `scripts/launch_m7_virl_arm.sh` exported a visible-device list of 8 while the
  effective config declared `n_gpus_per_node: 4`, so the launcher and the trainer
  disagreed about the job's width. **Fixed**: the launcher now reads
  `n_gpus_per_node` out of the effective config and fails loudly if the exported
  device count does not match it. M7 runs at its registered 4-GPU width on an12
  GPUs 0-3, which is the like-for-like condition for the Geometry3K pilot
  comparison; the width was never widened.
  This is an **implementation defect in the launcher, corrected before the
  registered run produced any reported number** — it is not part of any scientific
  result and no reported value depends on it. Recorded here so the fix is
  traceable and is not mistaken for a design change to R3/M7.
  The four idle GPUs it left behind (an12 4-7) are the resource E1b is registered
  to use; see `docs/registered_e1b_external_access_matrix_v1.md`.

- **E1b preflight counted TSV lines instead of parsed records.** The pinned TSVs
  embed newlines inside question and option text, so `wc -l` reported 2106 rows for
  MMStar and 4421 for MathVista where the parsed record counts are 1500 and 999 —
  exactly the base item counts. The preflight raised a spurious comparability
  failure, and a first index check compounded it by comparing string indices to int
  indices and reporting 0/1500 overlap. Both were **measurement errors in my own
  check, not defects in the data**: with correct parsing and type coercion the base
  item sets are 1500/1500 and 999/999 present. `scripts/preflight_e1b.py` now parses
  the TSV. No data was modified and no E1b cell was affected.

- **E1b MathVista with-image cells recorded `status: fail` while their inference
  had fully succeeded.** VLMEvalKit's *native* MathVista scorer requires an
  OpenAI judge; without one it aborted, and `validate_vlmeval_run.py` then failed
  the run for a missing `*_acc.csv`. The run summary shows the true state:
  `infer_fail_rate 0.00% (0/999)`, `judge_fail_rate 100%`. All 999 predictions
  per cell were on disk the whole time. The project never uses that judge for
  reported numbers — the base MathVista column was scored by
  `postprocess_vlmeval_predictions.py` under canonical-v2 — so all 12 cells were
  recovered by running the canonical scorer over the raw workbooks. No GPU work
  was repeated. **For future MathVista runs pass `MODE=infer`** to
  `launch_vlmevalkit_eval.sh`, which skips the judge stage and the spurious
  failure. Recorded as an implementation issue; no reported number depends on it.
  This is the second instance of the general lesson already in this ledger: a
  `fail` status is a claim about a pipeline stage, not about whether the work
  happened.

- **Two defects in my own E1b image readout, both caught before any number was
  reported.** (1) It ran the postprocess under `.venv/bin/python`, which lacks
  `openpyxl`, so every workbook read failed; the base pipeline uses
  `artifacts/envs/vlmevalkit/bin/python`. (2) It selected `candidates[-1]`, which
  on MMStar is `_exact_matching_result.pkl` rather than the raw prediction
  workbook — MathVista only worked because it happened to have no pickle. Both
  fixed in `scripts/e1b_image_readout.py`; the second is the more dangerous kind,
  since a wrong-but-readable input would have produced plausible numbers.
