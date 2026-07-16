# Mini-A5 Answer-Preserving Catch Set V1

Status:
- Independent mechanical audit: `pass`.
- This result establishes catch-set data readiness only. It does not authorize an M6 optimizer step and is not a PI gate decision.

Evidence:
- Machine audit: `reports/mini_a5_catch_audit_v1.json`.
- Catch set: `data/mini_a5_catch_v1`.
- Generation manifest: `experiments/runs/mini_a5_catch_v1_login_20260716T185633Z/run_manifest.json`.
- Counts: `{"images": 600, "masks": 600, "pairs": 300, "side_assignment": {"False": 147, "True": 153}, "templates": {"mini_a5_catch_distractor_matrix_v1": 100, "mini_a5_catch_distractor_scatter_v1": 100, "mini_a5_catch_distractor_trajectory_v1": 100}}`.
- Hashes: `{"decontamination_json": "19ed9a833665aead2aee1f4494279a26055c4f531fed68d3e3340af8a1a16bda", "pairs_jsonl": "fbd83d52fa01103bfb839fa2572eb9164c532f8c3a3431da6ca8f6033d6a9728"}`.
- Recomputed overlaps: `{"evaluation": {"image_hashes": [], "pair_ids": [], "template_ids": []}, "training": {"image_hashes": [], "pair_ids": [], "template_ids": []}}`.

Checks:
| Check | Result |
| --- | --- |
| `generation_manifest_complete_exit0` | `pass` |
| `generation_manifest_identity` | `pass` |
| `generation_artifacts_registered` | `pass` |
| `pair_count_exact` | `pass` |
| `pair_ids_unique_nonempty` | `pass` |
| `image_hashes_unique_nonempty` | `pass` |
| `template_counts_exact` | `pass` |
| `pair_semantics_files_masks_and_target_regions_exact` | `pass` |
| `image_file_count_exact` | `pass` |
| `mask_file_count_exact` | `pass` |
| `decontamination_status_pass` | `pass` |
| `decontamination_templates_and_counts_exact` | `pass` |
| `source_generator_hash_exact` | `pass` |
| `training_manifest_hash_exact` | `pass` |
| `evaluation_manifest_hashes_exact` | `pass` |
| `recorded_zero_overlap` | `pass` |
| `disjointness_recomputed_zero` | `pass` |
| `no_model_performance_selection` | `pass` |

Problems:
- Errors: `[]`.

Decision:
- Freeze these 300 held-out-template catch pairs. Both members retain the answer while a nonqueried visual nuisance changes.
- No pair was selected or replaced using model performance.

Next actions:
- Bind these artifact hashes into the Mini-A5 registration marker.
- Run the separately registered real EasyR1 plumbing smoke before either main M6 arm is launched.
