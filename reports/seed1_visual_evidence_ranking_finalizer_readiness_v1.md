# Seed-1 Visual-Evidence Ranking Finalizer Readiness V1

Status:
- CPU-only watcher is ready and remains fail-closed until the authoritative matrix
  queue publishes exactly nine completed child runs.
- No scientific value is opened while waiting.

Evidence:
- Watcher: `scripts/wait_finalize_visual_evidence_ranking.py`.
- Frozen finalizer: `scripts/finalize_visual_evidence_ranking.py`.
- Independent audit: `scripts/audit_visual_evidence_ranking.py`.
- Expected versioned outputs:
  `reports/seed1_visual_evidence_ranking_results_v1.{md,json}`,
  `reports/seed1_visual_evidence_ranking_builder_audit_v1.json`, and
  `reports/seed1_visual_evidence_ranking_audit_v1.json`.
- The full-shape synthetic finalizer dry run completed before result opening.

Problems:
- The watcher cannot make a PI scientific decision and never assigns B1/B2/B3.

Decision:
- Open values only after exact nine-cell lifecycle completion, then require both the
  builder checks and independent raw-score audit before ledger completion.

Next actions:
- Start the watcher in a named login-node tmux session and monitor lifecycle state.
