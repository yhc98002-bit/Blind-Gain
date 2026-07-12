# Geometry3K Blind-Solvability V2 Independent Audit

Status:
- Machine audit status: `pass`.
- Machine status JSON: `reports/blind_solvability_geo3k_v2_audited.json`.

Evidence:
- `all_run_manifests_complete_and_registered`: `true`.
- `source_and_filter_contract_shared`: `true`.
- `source_selection_exact`: `true`.
- `row_counts_match_filtered_train_plus_untouched_test`: `true`.
- `row_identity_unique`: `true`.
- `row_identity_equal_across_conditions`: `true`.
- `scientific_item_contract_equal`: `true`.
- `row_version_contract_valid`: `true`.
- `decoding_parameters_locked`: `true`.
- `prompt_parser_reward_versions_locked`: `true`.
- `symbolic_grader_guard_locked`: `true`.
- `recomputed_scores_match`: `true`.
- `output_hashes_recorded`: `true`.
- Row counts: `{'real': 1889, 'gray': 1889, 'noise': 1889, 'none': 1889, 'caption': 1889}`; expected `1889` per condition.
- Recomputed score mismatches: `0`.
- Decoding: `{'greedy': {'temperature': 0.0, 'top_p': 1.0, 'n': 1}, 'sampled': {'temperature': 1.0, 'top_p': 1.0, 'n': 16}, 'max_tokens': 2048, 'seed': 20260710}`.

Problems:
- A failed sub-check makes the logical-AND audit status fail; no exception is waived in this artifact.

Decision:
- This is a measurement-integrity audit only. It does not declare L7 or any PI gate passed.

Next actions:
- Use the audited outputs only when machine status is pass and the ledger has the named report.
