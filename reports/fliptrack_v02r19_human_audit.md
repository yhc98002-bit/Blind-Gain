# FlipTrack R19 Human Audit

Status:
- `verdict=accepted`.
- Richard accepted all three templates: 60/60 representative pairs passed all six registered checks on 2026-07-12.
- Automated hardness, leakage lint, positive controls, grouped artifact attackers, and the required human audit are complete.
- Exact-package 3B/7B real, caption, gray, and noise cells are complete; their results did not alter the frozen content.
- This human outcome does not approve L12, authorize L13, or substitute for both PI signatures on the revised preregistration.

Evidence:
- Release: `data/fliptrack_v02r19_artifact_expanded/manifest.jsonl`.
- Private audit key: `.private/fliptrack_v02r19_key.jsonl`.
- Source selection: `data/fliptrack_v02r19_artifact_expanded_source_manifest.jsonl`.
- Linter: `reports/fliptrack_v02r19_lint.json`, machine `status=true`.
- Artifact gate: `reports/artifact_gate_v02_r19.json`, machine `status=true`.
- Hardness and controls: `reports/fliptrack_v02_hardness.md` and `reports/positive_controls_v02.md`.
- Exact-package metrics and paired scale tests: `reports/fliptrack_v02r19_exact_package.md` and `reports/fliptrack_v02r19_exact_package.json`.
- Auditor: Richard; scope: exactly 20 source-order pairs per template, mapped to the 60 opaque release IDs in the portable audit package.
- Portable audit package provenance: `reports/human_audit_portable_bundle.md`.

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
| Document | 20 | 0 | 0 | 0 | yes |
| Geometry | 20 | 0 | 0 | 0 | yes |
| Chart v07: cued point-value reading | 20 | 0 | 0 | 0 | yes |

Auditor construct notes for chart v07:
- The circle at the queried plot point reduces the construct to **cued point-value reading**. It bypasses the first intended hop from starred legend entry to series localization.
- The in-image caption text `"The black star marks the queried point at x=N"` is incorrect: the star marks the legend entry, while the circle marks the queried plot point.
- Color discriminability across nine series is marginal.
- These observations constrain the construct description but did not produce a pair-level failure under the six registered checks.

Problems:
- Automated gates cannot establish that wording is natural or that every visual operation is semantically unambiguous to a human reader.
- Document caption-only accuracy rises from 1% at 3B to 6% at 7B; reviewers should specifically check whether document questions or layout cues are answerable without reading the target cell.
- The audit is a scientific gate, not a request to redesign templates after viewing model scores.
- Chart v07 does not certify the intended two-hop legend-to-series-to-value construct; paper and preregistration language must call it `cued point-value reading`.

Decision:
- Accept the frozen R19 representative human audit with 60/60 pairs passing all six checks.
- Make no edits, replacements, or regenerations in R19. Preserve its content, thresholds, and hashes.
- Treat chart v08 as a new-template development line with a new calibration history, not an R19 iteration.

Next actions:
- Carry the chart construct notes and R20 certification caveat into the revised pilot preregistration.
- Obtain both PI signatures on the revised preregistration before changing L12 or authorizing L13.
