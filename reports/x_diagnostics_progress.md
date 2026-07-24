# X diagnostics + Track B ledger — dispatch 2026-07-24

One line per task. States: pass | fail | blocked | in-progress | pending.

- X1: pass — 50 cells verified (25 candidate-evidence ranking incl. 15 pinned audited cells; 25 open-form realization); registered readings computed: mismatched-real margin inflation is statistically zero for every arm (all CIs span zero, |mean| <= 0.0004) while correct-image inflation is far from zero for every arm; the mechanical ratio labels split (A2/A2b: reading b; A1/A3: outside-bands) solely because the near-zero mismatched denominator carries an arbitrary sign; twin-condition twin-gold-preferred rate ~0.948-0.953 for every model including base; open-form pair-correct <= 0.0058 under mismatched and exactly 0 under twin/gray/no-image for all models; 32-token budget stands per guard; reports/x1_image_condition_matrix_v1.{md,json} + x1_image_condition_audit_v1.json.
- X2: in-progress — ladder registered pre-scoring; structured negative sets FROZEN (data/fliptrack_r19_hard_negative_candidates_v2.jsonl, sha 666f0347, 600 pairs, set sizes 4-8 mean 6.4, all 600 seeded scene replays verified against recorded pair_id/verifier/swap/frozen answers); three candidate-evidence ranking cells (base, a1_step60, a1_step100 x real) running on an29 GPUs 4-7 (x2_ranking_matrix_queue_login_20260724T172219Z); ladder metric = pair-success against the structured set (golds-only margin is candidate-set-invariant by construction and reported alongside); finalizer + mechanical ladder application on completion.
- X3: pending — CPU forensics from cached seed-1/2 geometry predictions; starts parallel to X1 GPU work.
- X4: pending — EXPLORATORY calibration endpoint; requires X1 dumps.
- X5: blocked — registered as blocked until X1 completes (seed-2 checkpoint matrix).
- B1: pending — UNBLOCKED: docs/EXPERIMENT_TODO.md committed verbatim from the PI-provided file (e252bf9); generator prototype queued behind X2/X3 per dispatch order.
