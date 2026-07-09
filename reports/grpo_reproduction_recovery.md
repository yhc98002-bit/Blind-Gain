# GRPO Reproduction Recovery

Status:
- A 30-step Qwen2.5-VL-3B Geometry3K GRPO engineering anchor is launched on `an12`.
- This is not yet a published reproduction.

Active run:
- Run directory: `experiments/runs/easyr1_geo3k_recovery30_20260708T043244Z`
- Node/GPU allocation: `an12`, GPUs `0,1`
- Config: `configs/train/easyr1_qwen25vl3b_geo3k_recovery30.yaml`
- Config hash: recorded in `run_manifest.json`
- Data manifest: `hiyouga/geometry3k@train|hiyouga/geometry3k@test[:32]`
- Expected checkpoint: `checkpoints/stage0_repro/easyr1_geo3k_recovery30/global_step_30/actor`
- Log: `experiments/runs/easyr1_geo3k_recovery30_20260708T043244Z/logs/an12.log`

Current evidence:
- The process launched and started Ray.
- As of the first recovery report, completion is pending.

Minimum acceptance for this recovery anchor:
- Reaches `global_step_30`, or fails with a concrete root cause and an implemented fix.
- Produces `experiment_log.jsonl` with reward curve, KL curve if available, throughput, and response-length metrics.
- Produces checkpoint tracker and actor checkpoint.
- Follow-up fixed validation eval compares base vs trained checkpoint on a small held-out slice.

Decision:
- Count this as a recovery job in progress, not a completed reproduction.
