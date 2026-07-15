# Chart V08 Calibration Plumbing V1

Status:
- M12 remains `blocked`.
- Frozen calibration construction, diagnostic-manifest conversion, and portable human-audit packaging are complete.
- No model result is interpreted here, and no PI gate is declared.

Evidence:
- Frozen source: `data/fliptrack_chart_v08_calibration_v1_manifest.jsonl`, 100 pairs, SHA256 `d90f3f13c1f3304669c8ca6c717ae58eaa7cfe4e785fab3bae8520e15065c292`.
- Existing mechanical audit: `reports/chart_v08_mechanical_audit_v2.md` and `.json`; all 12 registered CPU checks pass.
- Necessity evaluation manifest: `data/fliptrack_chart_v08_calibration_v1_necessity_eval_manifest_v1.jsonl`, 200 rows, SHA256 `797f8545a283563921469976c716805f288f36062b369fb6f1b6d1e79b5f56cb`.
- Necessity conversion metadata: `reports/chart_v08_necessity_eval_manifest_v1.json`; 50 rows for each subfamily x intervention cell.
- Necessity scoring is fixed to each member's original answer. Random-star implied answers are required to disagree with those targets.
- Human package linter: `reports/chart_v08_human_package_lint_v1.json`; 100 pairs, 200 members, 51/49 AB/BA order, all checks true, no errors.
- Portable human package: `reports/review_packages/blind_gains_chart_v08_calibration_human_audit_20260715_v1.zip`, 8,794,408 bytes, SHA256 `ea4473d3148121d87f50bde36c8417cf22875472af166fd714b87904b483bf24`.
- Bundle registry: `reports/chart_v08_human_audit_bundle_v1.json`.
- Offline viewer V2: `reports/human_audit_viewer_v2.md`; no model-performance field or display path.
- Tests: 21 focused chart-v08/viewer/bundle tests pass.

Problems:
- Human legibility without zoom is not yet audited.
- The complete 3B/7B real and caption calibration table is not yet available.
- No-star/random-star necessity images have not yet been model-scored.
- Caption gates, attacker gates, and strong-captioner stress are pending.
- Template freeze and the one-shot confirmatory split are therefore not authorized.

Decision:
- Audit all 100 calibration pairs rather than selecting a smaller post-generation sample.
- Human reviewers use Fit mode; zoom is disallowed for the registered legibility check.
- Preserve the frozen source and sidecar. Diagnostic rows are separate evaluation inputs and never replace source rows.

Next actions:
- Complete and export the 100-pair human review.
- Run the declared real/caption/necessity/attacker cells on free permanent-node capacity.
- Publish `reports/chart_v08_calibration.md` only after every declared calibration cell is present; then decide whether a freeze candidate exists without inspecting a confirmatory split.
