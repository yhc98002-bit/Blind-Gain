# Stage 2 Pilot Readiness

Status:
- A1/A2 pilot config stubs are prepared but not ready to launch as long runs.
- Do not launch full Stage 2 until GRPO recovery checkpoint finalizes and the training-time image transform path is audited.

Prepared:
- `configs/train/a1_real_3b_pilot.yaml`
- `configs/train/a2_gray_3b_pilot.yaml`

Still required:
- Training-time gray/noise image transformation implementation.
- Matched compute audit across A1/A2.
- Seed manifest.
- Checkpoint cadence choice from recovery throughput.
- Base and trained checkpoint deterministic eval scripts.

Decision:
- Stage 2 is prepared conceptually, not cleared for execution.
