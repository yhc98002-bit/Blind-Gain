# X diagnostics + Track B ledger — dispatch 2026-07-24

One line per task. States: pass | fail | blocked | in-progress | pending.

- X1: in-progress — both campaigns COMPLETE (10/10 ranking cells, 25/25 open-form cells, zero failures; an12 4-7 and an29 4-7 released); truncation guard pass: 0/250 sampled rows truncated in every condition, 32-token budget stands (reports/x1_openform_truncation_guard_v1.json); registered readings + report remain to be computed.
- X2: in-progress — interpretation ladder registered pre-scoring (docs/registered_x2_ladder_v1.md, e252bf9); recon complete: per-pair provenance records generator/pair_seed/render_variant, so scene registers reconstruct exactly with byte-level image-hash verification; negative-set builder next, ranking re-runs take the freed GPU blocks.
- X3: pending — CPU forensics from cached seed-1/2 geometry predictions; starts parallel to X1 GPU work.
- X4: pending — EXPLORATORY calibration endpoint; requires X1 dumps.
- X5: blocked — registered as blocked until X1 completes (seed-2 checkpoint matrix).
- B1: pending — UNBLOCKED: docs/EXPERIMENT_TODO.md committed verbatim from the PI-provided file (e252bf9); generator prototype queued behind X2/X3 per dispatch order.
