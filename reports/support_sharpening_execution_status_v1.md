# M10 Support-Sharpening Execution Status V1

Status:
- The fixed V3 draw registration is merged and unchanged.
- A3 caption completed all 1,152 registered rows with exit 0 on an12 GPU 7.
- A1 real remains active on an12 GPU 4.
- The remaining-arm queue launched A2 gray on an12 GPU 7; A2b no-image remains queued.
- No follow-up response value has been opened by the scheduler.

Evidence:
- A1: `experiments/runs/m10_support_seed1_a1_real_an12_gpu4_20260717T073205Z`.
- A3: `experiments/runs/m10_support_seed1_a3_caption_an12_gpu7_20260717T073450Z`.
- A2 gray: `experiments/runs/m10_support_seed1_a2_gray_an12_gpu7_20260717T081241Z`.
- Remaining-arm queue:
  `experiments/runs/m10_support_seed1_remaining_queue_login_20260717T074237Z`.
- Empty superseded queue:
  `experiments/runs/m10_support_seed1_queue_login_20260717T072835Z`.
- The superseded queue launched zero child jobs, had
  `performance_values_opened=false`, and was finalized with exit `143` after
  GPUs 4 and 7 became free. Its manifest records the capacity-supersession
  deviation.
- Remaining-arm launcher:
  `scripts/launch_support_sharpening_remaining_queue.sh`.

Problems:
- The first queue encoded the earlier capacity snapshot too narrowly (GPUs
  5-6 only). It was stopped before launching anything rather than leaving two
  newly free GPUs idle.

Decision:
- Preserve the failed empty queue as lifecycle evidence.
- Continue A1 and A2 untouched, retain completed A3, and let the replacement queue
  launch only A2b after a permitted GPU becomes free.
- Finalize the M10 readout only after all four immutable child manifests and
  exact per-draw contracts pass.
