# Mini-A5 Advantage and Config Audit V2

Status:
- Audit status: `pass`.
- This is prerequisite evidence only. It authorizes zero optimizer steps and makes no PI gate decision.

Evidence:
- Machine artifact: `reports/mini_a5_advantage_equivalence_v2.json`.
- Fixed budget: `{"batches_per_corpus_pass": 15, "exact_corpus_passes": 8, "max_response_tokens": 2048, "maximum_generated_tokens_per_arm": 491520000, "optimizer_steps": 120, "rollout_source_prompts_per_step": 400, "rollouts_per_prompt": 5, "training_rows": 6000}`.
- Allowed config differences: `["algorithm.pair_group_mode", "trainer.experiment_name", "trainer.save_checkpoint_path", "worker.reward.reward_function"]`.
- Observed config differences: `{"algorithm.pair_group_mode": ["joint", "member"], "trainer.experiment_name": ["mini_a5_cp_seed1", "mini_a5_same_data_seed1"], "trainer.save_checkpoint_path": ["/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/checkpoints/mini_a5/mini_a5_cp_seed1", "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/checkpoints/mini_a5/mini_a5_same_data_seed1"], "worker.reward.reward_function": ["/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/src/rewards/cp_grpo_reward.py:compute_score", "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/src/rewards/cp_grpo_reward.py:compute_member_score"]}`.
- Advantage evidence: `{"g": 5, "max_abs_cp_vs_independent_reference": 0.0, "max_abs_cp_vs_member_when_rewards_equal": 0.0, "max_abs_standard_member_vs_old_shared_2g_bug": 0.06644964218139648, "member_group_uids": ["member:[\"pair-1\",\"a\"]", "member:[\"pair-1\",\"b\"]"], "mixed_joint_scores": [0.0, 1.0, 1.0, 0.0, 1.0]}`.
- Step-0 and catch audit inputs: `reports/mini_a5_step0_reward_audit_v1.json`, `reports/mini_a5_catch_audit_v1.json`.

Checks:
| Check | Result |
| --- | --- |
| `g_is_exactly_five` | `pass` |
| `cp_matches_independent_unique_pair_grpo` | `pass` |
| `constant_zero_vector_is_finite_zero` | `pass` |
| `constant_one_vector_is_finite_zero` | `pass` |
| `paths_equal_when_reward_assignment_is_equal` | `pass` |
| `member_control_has_distinct_prompt_groups` | `pass` |
| `old_shared_2g_control_fixture_is_detected` | `pass` |
| `malformed_pair_metadata_is_rejected` | `pass` |
| `member_fixture_has_ten_rollout_rows` | `pass` |
| `only_registered_arm_fields_differ` | `pass` |
| `cp_mode_is_joint` | `pass` |
| `control_mode_is_member` | `pass` |
| `cp_reward_callback_exact` | `pass` |
| `control_reward_callback_exact` | `pass` |
| `pre_shuffled_order_preserved` | `pass` |
| `online_filtering_disabled` | `pass` |
| `kl_is_loss_not_reward_shaping` | `pass` |
| `vision_tower_frozen` | `pass` |
| `real_images_used` | `pass` |
| `single_node_eight_gpu_tp1` | `pass` |
| `duration_fixed_at_120_steps` | `pass` |
| `rollout_group_size_is_five` | `pass` |
| `all_corpus_rows_consumed_per_epoch` | `pass` |
| `duration_is_eight_exact_corpus_passes` | `pass` |
| `plumbing_val_hash_exact` | `pass` |
| `training_parquet_hash_exact` | `pass` |
| `corpus_independent_audit_passed` | `pass` |
| `fixed_subset_manifest_passed` | `pass` |
| `step0_reward_audit_passed` | `pass` |
| `catch_set_independent_audit_passed` | `pass` |
| `runtime_advantage_marker_present` | `pass` |

Problems:
- A real EasyR1 GPU plumbing smoke and its post-smoke main-arm registration marker remain pending.

Decision:
- Supersede the draft shared-UID control behavior. Standard member-level GRPO uses one UID per source prompt; CP alone uses the shared pair UID.
- Keep M6 fail-closed until the remaining diagnostics and merged registration marker exist.
