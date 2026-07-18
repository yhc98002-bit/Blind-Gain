# M11 Finalization V1

Status:
- All 18 registered M11 inference cells are complete: 12 FlipTrack cells and
  six ViRL39K blind-sample cells.
- The fail-closed finalizer verified every metric artifact, runtime placement,
  fixed decoding contract, parser version, and model-stage manifest.
- `reports/generalization_audits_v2.md` is the current human-facing report;
  `reports/generalization_audits_v2.json` retains internal template IDs for
  artifact compatibility.

Evidence:
- Reconciled queue:
  `experiments/runs/m11_reconciled_backfill_v2_login_20260717T075457Z`,
  complete, exit code 0, `performance_values_opened=false` before finalization.
- Successful V2 report run:
  `experiments/runs/m11_reconciled_final_report_login_20260718T153539Z`,
  complete, exit code 0.
- Current reports: `reports/generalization_audits_v2.md` and
  `reports/generalization_audits_v2.json`.
- All six evidence-conjunction checks are true.
- Human-facing chart rows use `cued chart point-value reading`; the old
  `starred_series_value_nine_v07` identifier appears only in machine artifacts.
- Focused regression suites: 10 tests passed across the generalization builder
  and reconciled finalizer.

Problems:
- The first post-fix finalization lifecycle omitted the `an12` InternVL stage
  manifest. It failed closed with no output publication and is preserved at
  `experiments/runs/m11_reconciled_final_report_login_20260718T151122Z`.
- V1 reports were then generated with correct values but an internal chart ID
  in the Markdown. They remain immutable; V2 corrects only the human-facing
  construct label. V1 and V2 machine JSON are intentionally byte-identical
  because internal identifiers and numeric evidence did not change.

Decision:
- Treat M11 as an inference-only generalization audit, not evidence of a
  training effect.
- Report InternVL3 and Gemma-3 separately; do not pool architectures.
- Use V2 for all human-facing references and retain V1 for provenance.
