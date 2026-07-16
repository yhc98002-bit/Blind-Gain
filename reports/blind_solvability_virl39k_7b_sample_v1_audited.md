# ViRL39K Blind-Solvability V1 Independent Audit

Status:
- Machine audit status: `pass`.
- Machine status JSON: `reports/blind_solvability_virl39k_7b_sample_v1_audited.json`.

Evidence:
- `all_run_manifests_complete_and_registered`: `true`.
- `source_manifest_and_sample_spec_hashes_exact`: `true`.
- `sample_spec_recomputes_exactly`: `true`.
- `source_images_present_and_hash_verified`: `true`.
- `row_count_exact_4096`: `true`.
- `row_identity_unique`: `true`.
- `row_identity_equal_to_frozen_sample`: `true`.
- `scientific_item_contract_equal`: `true`.
- `multi_image_distribution_exact`: `true`.
- `row_version_contract_valid`: `true`.
- `decoding_parameters_locked`: `true`.
- `caption_store_question_blind_contract_pinned`: `true`.
- `symbolic_grader_guard_locked`: `true`.
- `recomputed_scores_match`: `true`.
- `output_hashes_recorded`: `true`.
- Row counts: `{'real': 4096, 'gray': 4096, 'noise': 4096, 'none': 4096, 'caption': 4096}`.
- Recomputed score mismatches: `0`.
- Missing/hash-mismatched source images: `0` / `0`.

Problems:
- Any false sub-check makes the logical-AND audit fail; no waiver is encoded here.

Decision:
- This artifact certifies measurement integrity only and does not declare M8 or a PI gate passed.

Next actions:
- Use the summary only when this machine status is pass and the M8 ledger has its named reports.
