# Anchor A0 Recipe Config Diff

Status:
- Prepared recipe-scale 3B Geometry3K anchor config from resolved EasyR1 reference.
- This report covers config intent before the run completes.

Evidence:
- Config: `configs/train/anchor_a0_recipe_3b_geo3k.yaml`
- Resolved reference: `reports/easyr1_geo3k_reference_resolved.yaml`
- Machine diff: `reports/anchor_a0_recipe_config_diff.json`

| Field | Reference | Anchor | Match |
| --- | --- | --- | --- |
| `rollout.n` | `5` | `5` | yes |
| `rollout_batch_size` | `512` | `512` | yes |
| `global_batch_size` | `128` | `128` | yes |
| `max_response_length` | `2048` | `2048` | yes |
| `val_batch_size` | `1024` | `32` | no |
| `validation.temperature` | `0.6` | `0.0` | no |
| `validation.top_p` | `0.95` | `1.0` | no |
| `validation.n` | `1` | `1` | yes |
| `freeze_vision_tower` | `False` | `False` | yes |
| `actor.padding_free` | `True` | `False` | no |
| `ref.padding_free` | `True` | `False` | no |
| `KL.disable_kl` | `False` | `False` | yes |
| `KL.use_kl_loss` | `True` | `True` | yes |
| `KL.kl_penalty` | `low_var_kl` | `low_var_kl` | yes |
| `KL.kl_coef` | `0.01` | `0.01` | yes |
| `val_before_train` | `True` | `True` | yes |
| `val_freq` | `5` | `10` | no |
| `save_freq` | `5` | `20` | no |
| `save_limit` | `3` | `-1` | no |
| `max_steps` | `None` | `100` | no |
| `n_gpus_per_node` | `2` | `4` | no |

Decision:
- Intentional divergences are validation decoding (`temperature=0`, `top_p=1.0`), checkpoint cadence, run length (`max_steps=100`), local model/reward/prompt paths, and 4-GPU allocation.
- `actor.padding_free=false` and `ref.padding_free=false` are required by the documented SDPA fallback. EasyR1's padding-free branch imports `unpad_input` from FlashAttention; with FlashAttention absent, the recipe value fails before the first optimizer step.
- `val_batch_size=32` retains the full 302-example test split but bounds each multimodal `all_gather_object`; the recipe batch of 1024 caused a worker abort in `all_gather_data_proto` before step 0 completed.
- Recipe-scale fields retained: `rollout_batch_size=512`, `global_batch_size=128`, `rollout.n=5`, `max_response_length=2048`, and `freeze_vision_tower=False`.
