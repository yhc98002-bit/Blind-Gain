# Offline Human Audit Viewer V2

Status:
- Viewer implementation: `pass`.
- This is a software status only; it is not a human-audit or scientific gate decision.
- Visible setup and completion wording is package-generic rather than hardcoded to R19 or 60 pairs.

Evidence:
- Viewer: `tools/human_audit_viewer.html`, SHA256 `9b5245893a22e60528552ae73214670a0f5cdd2e6fe95adda251714556ac7122`.
- Portable-bundle builder: `scripts/build_human_audit_bundle.py`, SHA256 `656d3271d853a9bc11ca0dbca017461f94a1b565bc0dd7a7c44361030aa98e08`.
- Focused viewer/bundle tests: `14 passed` when run together with the chart-v08 necessity-manifest tests; the broader chart-v08 set reports `21 passed`.
- The occupied setup state no longer says R19 when a reviewer is opening R20 or chart-v08.
- Bundle README pair counts are derived from the selected rows; the adversarial two-pair fixture must say `portable 2-pair package` and must not say `portable 60-pair package`.
- The viewer still has no evaluation-result input and displays no model performance.

Problems:
- Browser decisions remain local to the exact browser profile and manifest/key hashes until exported.
- The chart-v08 human outcome is pending; software readiness does not substitute for review.

Decision:
- Reuse one offline viewer for R19, R20, and chart-v08 packages.
- Keep package-specific instructions in each ZIP's `REVIEWER_GUIDE.md`.

Next actions:
- Open the chart-v08 ZIP named in `reports/chart_v08_human_audit_bundle_v1.json` on the reviewer's computer.
- Review all 100 pairs in Fit mode and return an export with an empty `unreviewed_pair_ids` list.
