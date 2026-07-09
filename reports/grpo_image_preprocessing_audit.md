# GRPO Image Preprocessing Audit

Status:
- EasyR1 image preprocessing path was inspected.
- Recovery config uses the official Geometry3K `images` column and Qwen processor path.
- Arm-specific real/gray/noise transforms for Blind Gains are not part of the GRPO recovery anchor yet.

Evidence:
- Dataset code: `artifacts/repos/EasyR1/verl/utils/dataset.py`
- `process_image` converts file/dict/bytes images to PIL, resizes above `max_pixels`, upsizes below `min_pixels`, and converts to RGB.
- Recovery config:
  - `image_key: images`
  - `min_pixels: 262144`
  - `max_pixels: 4194304`
  - `filter_overlong_prompts: true`

Risks:
- Resizing can affect small visual details; this is acceptable for Geometry3K recovery but must be audited for FlipTrack and A1/A2 arms.
- Gray/noise transforms are implemented in `scripts/eval_qwen_vl_fliptrack.py`, not in the EasyR1 dataset path.

Decision:
- Pass for Geometry3K recovery launch.
- Partial for proposal arms until real/gray/noise preprocessing is integrated and tested in the training dataset path.

Next actions:
- Add an explicit training-time image transform wrapper for A1/A2.
- Create visual checksum manifests for transformed training examples before Stage 2.
