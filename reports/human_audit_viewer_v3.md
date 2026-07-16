# Offline Human Audit Viewer V3

Status:
- Chart-v08 viewer readiness: `pass`.
- Chart-v08 human audit outcome: `pending`.
- M12 remains `blocked`; this report makes no template or scientific gate decision.

Evidence:
- Single-file offline viewer: `tools/human_audit_viewer.html`, SHA256
  `e32aaadd4d3e43440204f13dfd582be4b031b4c9091b7d2b8860e9f88d7d29e1`.
- The viewer detects a chart-v08-only package from its frozen template IDs. In that
  mode it fixes each member to `700 x 450` CSS pixels, hides and disables viewer zoom,
  and removes the full-resolution image links from focus and display.
- The existing six registered checks remain unchanged. Chart-v08 mode adds exactly
  `no_zoom_correct` and `series_unambiguous`, for eight explicit decisions per pair.
- Export schema `blind-gains.human-audit-failures.v2` records the audit mode, fixed
  rendering contract, all eight decisions for failed pairs, and unreviewed pair IDs.
- The viewer has no result input and displays no model-performance values.
- Reviewer guide: `docs/CHART_V08_HUMAN_AUDIT_GUIDE.md`, SHA256
  `97f09f7adfd56de7da34377b6e72bf80302cfa65578a550251981dd9d7ad0e0a`.
- Focused viewer and bundle suite: `13 passed`.
- Adversarial fixtures require package detection, disabled zoom controls, hidden
  original-image links, fixed dimensions, both v08 rating IDs, eight-decision bundle
  metadata, and eight-check reviewer instructions. The prior viewer fails these.

Problems:
- Browser-level page magnification cannot be disabled by an offline HTML file. The
  guide explicitly prohibits browser zoom, OS magnification, screenshots, and export;
  all viewer-provided enlargement paths are mechanically disabled.
- Human review must still be performed by Richard after the seed-1 readout.

Decision:
- Preserve the generic R19/R20 behavior with six checks and optional viewer zoom.
- Activate the fixed no-zoom contract only when every loaded template ID starts with
  `chart_v08_`; mixed or non-v08 packages retain standard mode.
- Keep the prior v1 review ZIP immutable. Publish a new v2 ZIP locally because it
  contains the private answer key and must not be committed to the public repository.

Next actions:
- Extract the v2 ZIP, read `REVIEWER_GUIDE.md`, open `human_audit_viewer.html`, select
  `package/` and `private/answer_key.jsonl`, and review all 100 pairs.
- Return the exported JSON with `unreviewed_pair_ids: []` for PI review.

Local review package:
- Absolute path:
  `/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/reports/review_packages/blind_gains_chart_v08_calibration_human_audit_20260716_v2.zip`
- Bytes: `8,799,203`.
- SHA256: `20ab5fea8a674dfcd91d7d671bd9142ecacb2001002ff3e53cce25eb95a6df02`.
