# FlipTrack R19 Human Audit

Status:
- The 1,200-pair R19 candidate is ready for the required PI/team representative audit.
- Automated hardness, leakage lint, positive controls, and grouped artifact attackers pass; human acceptance is intentionally still pending.
- Exact-package 3B/7B real, caption, gray, and noise cells are complete; their results did not alter the frozen content.

Evidence:
- Release: `data/fliptrack_v02r19_artifact_expanded/manifest.jsonl`.
- Private audit key: `.private/fliptrack_v02r19_key.jsonl`.
- Source selection: `data/fliptrack_v02r19_artifact_expanded_source_manifest.jsonl`.
- Linter: `reports/fliptrack_v02r19_lint.json`, machine `status=true`.
- Artifact gate: `reports/artifact_gate_v02_r19.json`, machine `status=true`.
- Hardness and controls: `reports/fliptrack_v02_hardness.md` and `reports/positive_controls_v02.md`.
- Exact-package metrics and paired scale tests: `reports/fliptrack_v02r19_exact_package.md` and `reports/fliptrack_v02r19_exact_package.json`.

Representative sheets (20 pairs per template):
- Document: `reports/contact_sheets/fliptrack_v02r19/header_cued_table_code_v02.png`.
- Geometry: `reports/contact_sheets/fliptrack_v02r19/coordinate_register_twenty_point_x_v02.png`.
- Chart: `reports/contact_sheets/fliptrack_v02r19/starred_series_value_nine_v07.png`.

Audit checklist:
1. Could I answer the question without seeing the image?
2. Is the marked visual change the only answer-changing difference between pair members?
3. Is the changed fact legible at normal viewing size without being an artificial pop-out cue?
4. Are labels, legends, axes, row/column headers, and question wording unambiguous?
5. Is either member visibly more compressed, clipped, crowded, or otherwise artifact-prone?
6. Does the answer key match both members exactly?

Calibration failures retained for comparison:
- R7 geometry failed because 7B question-blind caption pair accuracy reached 0.1700.
- R15 chart failed because 7B real accuracy fell below 3B despite a valid degradation curve.
- R17 failed the metadata point rule at 0.5526; R19 retains every R17 pair and adds the fixed R18 expansion.

Human findings:

| Template | Pairs reviewed | Answerable blind | Non-visual answer change | Legibility/artifact failures | Accept |
| --- | ---: | ---: | ---: | ---: | --- |
| Document | pending | pending | pending | pending | pending |
| Geometry | pending | pending | pending | pending | pending |
| Chart | pending | pending | pending | pending | pending |

Problems:
- Automated gates cannot establish that wording is natural or that every visual operation is semantically unambiguous to a human reader.
- Document caption-only accuracy rises from 1% at 3B to 6% at 7B; reviewers should specifically check whether document questions or layout cues are answerable without reading the target cell.
- The audit is a scientific gate, not a request to redesign templates after viewing model scores.

Decision:
- Freeze R19 content and thresholds while human review is pending. Do not regenerate, replace, or remove pairs in response to model performance.

Next actions:
- PI/team reviews the three sheets and records counts plus concrete pair IDs for any failure.
- If accepted, record approval and freeze hashes. If rejected, preserve R19 and open a separately versioned repair batch with the stated human failure mode.
