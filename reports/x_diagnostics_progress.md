# X diagnostics + Track B ledger — dispatch 2026-07-24

One line per task. States: pass | fail | blocked | in-progress | pending.

- X1: in-progress — registration at HEAD pre-inference; derangement fixture data/x1_mismatched_derangement_v1.json (sha 4fe9c293, seed 20260724); 12-case adversarial source-selection fixture pass; candidate-evidence ranking cells (5 models x mismatched_real/twin_counterfactual) running on an29 GPUs 4-7 (x1_ranking_matrix_queue_login_20260724T085613Z); open-form realization cells (5 models x 5 conditions, greedy, 32 tokens) running on an12 GPUs 4-7 (x1_openform_queue_login_20260724T085613Z); correct/gray/no-image ranking cells are pinned from the audited seed-1 and calibration matrices per the configuration scope note, not re-measured.
- X2: pending — structured negative-set generator not started; scheduled after X1 cells occupy free GPUs.
- X3: pending — CPU forensics from cached seed-1/2 geometry predictions; starts parallel to X1 GPU work.
- X4: pending — EXPLORATORY calibration endpoint; requires X1 dumps.
- X5: blocked — registered as blocked until X1 completes (seed-2 checkpoint matrix).
- B1: pending — generator prototype proceeds from dispatch text; NOTE: experiment-todo.md not found in repo, local workspace, or dispatch attachments, so docs/EXPERIMENT_TODO.md cannot be committed and Track-B details beyond the dispatch text are unavailable (blocked sub-item, flagged to PI).
