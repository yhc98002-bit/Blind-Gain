# R19 Portable Human-Audit Bundle

Status:
- Ready for reviewer download. This report does not assert the human audit has passed.
- The review artifact contains the exact frozen R19 contact-sheet selection: 20 source-order pairs from each of three templates, 60 pairs and 120 images total.
- The guide-complete v3 artifact includes a full Markdown guidebook and a concise guide embedded in the viewer.

Evidence:
- Archive: `reports/review_packages/blind_gains_r19_human_audit_20260712_v3.zip`.
- Absolute path: `/HOME/paratera_xy/pxy1289/HDD_POOL/HaocunYe/Research/BlindGain/reports/review_packages/blind_gains_r19_human_audit_20260712_v3.zip`.
- Size: 4,892,311 bytes (4.67 MiB).
- SHA256: `e455de54c4d00d024cc8eea18c98141ff326ba4188844e3661dc1025e0fcd25a`.
- `unzip -tq` reports no compressed-data errors.
- A direct audit confirms `contact_sheet_ids_exact=true`, `pair_count=60`, `image_count=120`, and that both embedded viewer and guide hashes equal their repository sources.
- Template counts: geometry 20, document 20, chart 20.
- The archive contains `README.txt`, `REVIEWER_GUIDE.md`, `bundle_manifest.json`, `human_audit_viewer.html`, `package/manifest.jsonl`, `package/images/`, and `private/answer_key.jsonl`.
- Reproducible builder: `scripts/build_human_audit_bundle.py`; adversarial tests: `tests/test_human_audit_bundle.py`.

Problems:
- A browser opened on Windows cannot select files from the remote Linux cluster, even when VS Code Live Server serves the HTML. Browser file inputs always refer to the browser computer's filesystem.
- The full 1,200-pair release manifest is in randomized opaque-ID order. Its first 20 rows per template are not the frozen contact-sheet sample. The bundle maps source-order selections to opaque release IDs through the private `source_pair_id` field.
- The unversioned and `_v2.zip` builds are retained as superseded artifacts. Use only `_v3.zip`, which adds the reviewer guidebook without changing the frozen 60-pair selection.

Decision:
- Download only the 4.67 MiB `_v3.zip` archive, not the 112 MiB full R19 package and not the project repository.
- Keep the private key and exported failure record within the research team.
- In the extracted viewer, audit **All loaded pairs**. The portable package contains only the exact registered 60-pair sample.

Next actions:
- In VS Code Explorer, locate `reports/review_packages/blind_gains_r19_human_audit_20260712_v3.zip`, right-click it, and select **Download**.
- Extract it on Windows and read `REVIEWER_GUIDE.md` before beginning. The same concise rubric is available from **Reviewer guide** inside the viewer.
- Open `human_audit_viewer.html`, choose `package/`, then choose `private/answer_key.jsonl`.
- Complete all six checks for all 60 pairs and return the exported failures JSON.
