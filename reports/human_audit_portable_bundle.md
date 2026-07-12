# R19 Portable Human-Audit Bundle

Status:
- Ready for reviewer download. This report does not assert the human audit has passed.
- The review artifact contains the exact frozen R19 contact-sheet selection: 20 source-order pairs from each of three templates, 60 pairs and 120 images total.

Evidence:
- Archive: `reports/review_packages/blind_gains_r19_human_audit_20260712_v2.zip`.
- Absolute path: `/HOME/paratera_xy/pxy1289/HDD_POOL/HaocunYe/Research/BlindGain/reports/review_packages/blind_gains_r19_human_audit_20260712_v2.zip`.
- Size: 4,886,711 bytes (4.66 MiB).
- SHA256: `0d2df5810120789a4bb6f74ad9325ea268f4c30e63e0dff99505f4a359a30236`.
- `unzip -tq` reports no compressed-data errors.
- A direct audit confirms `contact_sheet_ids_exact=true`, `pair_count=60`, `image_count=120`, and the embedded viewer hash equals the repository viewer hash.
- Template counts: geometry 20, document 20, chart 20.
- The archive contains `README.txt`, `bundle_manifest.json`, `human_audit_viewer.html`, `package/manifest.jsonl`, `package/images/`, and `private/answer_key.jsonl`.
- Reproducible builder: `scripts/build_human_audit_bundle.py`; adversarial tests: `tests/test_human_audit_bundle.py`.

Problems:
- A browser opened on Windows cannot select files from the remote Linux cluster, even when VS Code Live Server serves the HTML. Browser file inputs always refer to the browser computer's filesystem.
- The full 1,200-pair release manifest is in randomized opaque-ID order. Its first 20 rows per template are not the frozen contact-sheet sample. The bundle maps source-order selections to opaque release IDs through the private `source_pair_id` field.
- `blind_gains_r19_human_audit_20260712.zip` is retained as a superseded 4,886,553-byte build. Use only the `_v2.zip` archive, which contains the corrected viewer labels and instructions.

Decision:
- Download only the 4.66 MiB `_v2.zip` archive, not the 112 MiB full R19 package and not the project repository.
- Keep the private key and exported failure record within the research team.
- In the extracted viewer, audit **All loaded pairs**. The portable package contains only the exact registered 60-pair sample.

Next actions:
- In VS Code Explorer, locate `reports/review_packages/blind_gains_r19_human_audit_20260712_v2.zip`, right-click it, and select **Download**.
- Extract it on Windows, open `human_audit_viewer.html`, choose `package/`, then choose `private/answer_key.jsonl`.
- Complete all six checks for all 60 pairs and return the exported failures JSON.
