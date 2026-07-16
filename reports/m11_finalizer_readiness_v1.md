# M11 Reconciled Finalizer Readiness V1

Status:
- Final-report plumbing is ready; M11 remains blocked while the reconciled 18-cell queue is incomplete.
- No M11 scientific performance value was opened while preparing or testing this finalizer.

Evidence:
- `scripts/finalize_m11_reconciled_report.py` requires a completed, exit-zero reconciled queue manifest and queue state `cells_complete_pending_report` before resolving any metric paths.
- The gate requires exactly 18 complete cells, split into 12 FlipTrack metrics and 6 ViRL39K blind-sample metrics, with every metric under an immutable run directory.
- The existing placement-aware builder still requires verified model-stage evidence for every backend-node placement. The registered launch will supply Gemma on an29 plus InternVL on an12 and an29.
- Failed conjunctions produce no registered report output. Passing JSON and Markdown are staged together and publication rolls back both final names if either atomic rename fails.
- `scripts/launch_m11_reconciled_report.sh` is commit-bound, CPU-only on the login node, storage-guarded, and writes an immutable run manifest.
- `PYTHONPATH=. pytest -q tests/test_finalize_m11_reconciled_report.py tests/test_generalization_audit_builder.py tests/test_m11_reconciled_backfill_queue.py`: `11 passed`.
- The adversarial incomplete-queue fixture traps any attempt to open a metric file before the complete-queue gate.
- A preflight against the live queue refused with `M11 queue run is not complete with exit code zero`; no report path was created.

Problems:
- The live queue still has running and pending cells. The finalizer is therefore intentionally not launched.

Decision:
- Keep queue execution and scientific report publication separate.
- Publish the single registered M11 readout only after the queue wrapper itself is complete with exit code zero.
- Do not create a partial InternVL-only or partial Gemma report.

Next actions:
- Wait for `experiments/runs/m11_reconciled_backfill_login_20260716T172041Z` to reach `cells_complete_pending_report` and for its wrapper manifest to finalize.
- Launch the finalizer with the three verified stage manifests for Gemma/an29 and InternVL/an12+an29.
- Reconcile `reports/main_progress.md` and `docs/RESEARCH_DOC.md` from the final machine artifact without adding architecture-pooled claims.
