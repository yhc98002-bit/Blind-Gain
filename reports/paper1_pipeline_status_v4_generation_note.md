# Paper 1 Pipeline V4 Generation Note

Status:
- The V4 machine JSON is valid and records a passing structural pipeline audit.
- The V4 Markdown generator incorrectly hardcoded the heading `V3`; this is a report-version labeling defect, not a scientific-result change.
- V4 is retained unchanged as superseded generation evidence.

Evidence:
- Affected artifact: `reports/paper1_pipeline_status_v4.md`.
- Machine artifact: `reports/paper1_pipeline_status_v4.json`.
- Regression test: `tests/test_paper1_pipeline_audit.py::test_versioned_markdown_title_uses_requested_report_version`.

Decision:
- Use `reports/paper1_pipeline_status_v5.md` and its JSON as the current M13 pipeline audit.
- Never cite the V4 Markdown heading as a version identifier.
