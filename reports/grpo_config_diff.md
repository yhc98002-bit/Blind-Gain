# GRPO Config Diff Audit

Status:
- Reference recipe: EasyR1 `examples/qwen2_5_vl_3b_geo3k_grpo.sh`.
- Recovery config: `configs/train/easyr1_qwen25vl3b_geo3k_recovery30.yaml`.
- This is an engineering recovery anchor, not a published reproduction.

Reference:
- Runs `python3 -m verl.trainer.main config=examples/config.yaml`.
- Overrides:
  - `data.train_files=hiyouga/geometry3k@train`
  - `data.val_files=hiyouga/geometry3k@test`
  - `worker.actor.model.model_path=Qwen/Qwen2.5-VL-3B-Instruct`
  - `trainer.experiment_name=qwen2_5_vl_3b_geo_grpo`
  - `trainer.n_gpus_per_node=2`

Recovery deviations:

| Field | Reference | Recovery | Reason |
| --- | --- | --- | --- |
| model path | remote Qwen ID | local ModelScope path | compute nodes cannot download; shared local model is required |
| val split | full `test` | `test[:32]` | avoid full-validation smoke overhead while preserving validation path |
| max steps | upstream default config | `30` | minimum recovery anchor requested |
| logger | upstream default | `file` | local-only structured logging |
| checkpoint path | default | `checkpoints/stage0_repro/easyr1_geo3k_recovery30` | immutable project checkpoint discipline |
| attention implementation | hardcoded FlashAttention2 | SDPA via `EASYR1_ATTN_IMPLEMENTATION=sdpa` patch | current env lacks `flash_attn`; patch is explicit and tracked |
| offline caches | not specified | HF cache/offline env vars | compute-node external network is unreliable |

Risk:
- The SDPA fallback changes attention kernel performance and possibly memory behavior. It should not change the intended GRPO objective, but it is a runtime deviation.
- Tiny validation split is not comparable to published results; it is only for throughput and plumbing.

Decision:
- Accept deviations for a 30-step engineering anchor.
- Do not call this a published reproduction until a published target, full validation protocol, and tolerance are defined.
