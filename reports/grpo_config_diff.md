# GRPO Config Diff: Resolved EasyR1 Geometry3K Reference vs Recovery30

Status:
- Resolved reference materialized from `artifacts/repos/EasyR1/examples/config.yaml` plus official `examples/qwen2_5_vl_3b_geo3k_grpo.sh` overrides.
- This report is a config audit; it does not claim the recovery run reproduced the recipe.

Evidence:
- Resolved reference: `reports/easyr1_geo3k_reference_resolved.yaml`
- Recovery config: `configs/train/easyr1_qwen25vl3b_geo3k_recovery30.yaml`
- Machine diff: `reports/grpo_config_diff.json`

## Required Field Diff

| Field | Config path | Reference | Ours | Match |
| --- | --- | --- | --- | --- |
| `rollout.n` | `worker.rollout.n` | `5` | `2` | no |
| `rollout_batch_size` | `data.rollout_batch_size` | `512` | `4` | no |
| `global_batch_size` | `worker.actor.global_batch_size` | `128` | `4` | no |
| `max_response_length` | `data.max_response_length` | `2048` | `512` | no |
| `validation.temperature` | `worker.rollout.val_override_config.temperature` | `0.6` | `0.6` | yes |
| `validation.top_p` | `worker.rollout.val_override_config.top_p` | `0.95` | `0.95` | yes |
| `validation.n` | `worker.rollout.val_override_config.n` | `1` | `1` | yes |
| `freeze_vision_tower` | `worker.actor.model.freeze_vision_tower` | `False` | `False` | yes |
| `KL.disable_kl` | `algorithm.disable_kl` | `False` | `False` | yes |
| `KL.use_kl_loss` | `algorithm.use_kl_loss` | `True` | `True` | yes |
| `KL.kl_penalty` | `algorithm.kl_penalty` | `low_var_kl` | `low_var_kl` | yes |
| `KL.kl_coef` | `algorithm.kl_coef` | `0.01` | `0.01` | yes |
| `train_files` | `data.train_files` | `hiyouga/geometry3k@train` | `hiyouga/geometry3k@train` | yes |
| `val_files` | `data.val_files` | `hiyouga/geometry3k@test` | `hiyouga/geometry3k@test[:32]` | no |
| `val_before_train` | `trainer.val_before_train` | `True` | `False` | no |
| `val_freq` | `trainer.val_freq` | `5` | `-1` | no |
| `save_freq` | `trainer.save_freq` | `5` | `-1` | no |
| `max_steps` | `trainer.max_steps` | `None` | `30` | no |
| `n_gpus_per_node` | `trainer.n_gpus_per_node` | `2` | `2` | yes |

## Explicit Deviations
- `rollout.n` differs: reference `5`, ours `2`.
- `rollout_batch_size` differs: reference `512`, ours `4`.
- `global_batch_size` differs: reference `128`, ours `4`.
- `max_response_length` differs: reference `2048`, ours `512`.
- `val_files` differs: reference `hiyouga/geometry3k@test`, ours `hiyouga/geometry3k@test[:32]`.
- `val_before_train` differs: reference `True`, ours `False`.
- `val_freq` differs: reference `5`, ours `-1`.
- `save_freq` differs: reference `5`, ours `-1`.
- `max_steps` differs: reference `None`, ours `30`.

Decision:
- The 30-step recovery config intentionally reduced batch sizes, response length, validation cadence, checkpoint cadence, and run length for engineering recovery.
- P1.1 must create a new recipe-scale anchor config instead of extending this recovery config silently.
