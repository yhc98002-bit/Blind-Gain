# Mini-A5 Corpus V1

Status:
- Independent audit status: `pass`.
- This is an M6 data-readiness result, not authorization to train and not a PI gate decision.

Evidence:
- Machine audit: `reports/mini_a5_corpus_audit_v1.json`.
- Corpus: `data/mini_a5_train_v1`.
- Counts: `{"images": 6000, "masks": 6000, "pairs": 3000, "templates": {"mini_a5_train_code_matrix_v1": 1000, "mini_a5_train_labeled_scatter_v1": 1000, "mini_a5_train_named_trajectory_v1": 1000}, "training_rows": 6000}`.
- Artifact hashes: `{"decontamination_json": "6060439b0b2b4b3253fbbc62843ba4307578af36806b3c577a1bb736c290851d", "pairs_jsonl": "c592d8560cf3f5544fea36a12b3b52642d0faf0056c4ef9fddc0dde1f75f34bd", "train_jsonl": "07d785ee6ae4a3b5325e12595f7830c5924e31c49565554f1e88b2abffc5fa5c", "train_parquet": "0b0f0965987d1c340c3ebd78da742c9d99b319b61524b5cb42960519fd9c9b28"}`.
- Semantic side assignment: `{"mini_a5_train_code_matrix_v1:false": 503, "mini_a5_train_code_matrix_v1:true": 497, "mini_a5_train_labeled_scatter_v1:false": 497, "mini_a5_train_labeled_scatter_v1:true": 503, "mini_a5_train_named_trajectory_v1:false": 527, "mini_a5_train_named_trajectory_v1:true": 473}`.
- Recomputed disjointness: `{"evaluation_template_count": 5, "image_hash_overlap": 0, "pair_id_overlap": 0, "template_id_overlap": 0, "training_template_ids": ["mini_a5_train_code_matrix_v1", "mini_a5_train_labeled_scatter_v1", "mini_a5_train_named_trajectory_v1"]}`.

Checks:
| Check | Result |
| --- | --- |
| `run_manifest_complete_exit0` | `pass` |
| `run_manifest_expected_commit` | `pass` |
| `pair_count_exact` | `pass` |
| `training_row_count_exact` | `pass` |
| `pair_ids_unique_nonempty` | `pass` |
| `template_counts_exact` | `pass` |
| `all_pair_semantics_exact` | `pass` |
| `all_file_hashes_and_masks_exact` | `pass` |
| `training_projection_exact` | `pass` |
| `training_pair_adjacency_exact` | `pass` |
| `parquet_jsonl_row_identity_exact` | `pass` |
| `decontamination_status_pass` | `pass` |
| `evaluation_manifest_hashes_exact` | `pass` |
| `disjointness_recomputed_exact` | `pass` |
| `generator_hash_exact` | `pass` |

Problems:
- Audit errors: `[]`.
- Step-0 reward statistics, an immutable advantage-tensor artifact, matched configs, and a GPU smoke remain pending.

Decision:
- Freeze this corpus and its hashes. Do not regenerate or replace failed/hard examples based on model performance.
- Keep M6 blocked until every remaining registered prerequisite is audited.

Next actions:
- Prepare matched CP/member configs against this exact Parquet hash and compute step-0 reward-hit/variance statistics.
- Run the isolated EasyR1 plumbing smoke when an eight-GPU single-node window becomes available.
