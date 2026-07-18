# M7 ViRL39K Embedding Launch V1

Status:
- The BGE text-embedding layer completed on `an12` GPU 5 with exit code 0.
- The DINOv2 image-embedding layer is active on `an12` GPU 4.
- Both jobs are single-node TP1 feature-extraction jobs over the same frozen
  55,591-entity ViRL39K/Layer-1 record set.
- M7 remains `blocked`; these jobs do not authorize an optimizer step.

Evidence:
- Frozen train records:
  `experiments/runs/decon_virl39k_layer1_hash_text_login_20260716T193506Z/virl39k_train_records.jsonl`,
  SHA256 `f32ac9321bc1f3476285999427544c449583e951f71572a36f4a391b4a5dfdac`.
- Frozen evaluation records:
  `experiments/runs/decon_virl39k_layer1_hash_text_login_20260716T193506Z/layer1_eval_records.jsonl`,
  SHA256 `fffd7caa5dc9b6dc29ae0d8785de4c9a0bdbfa0747c15e78ad789e00dceedbac`.
- Combined data-manifest hash:
  `1c5d71d1b3b536807b11aaddbb33e3f371a55900516cdb5fca58c51d1ba3457a`.
- Launch Git hash: `24a44a6c7fadf04b24fe3c40f7edc8fd14680ee4`.
- BGE run:
  `experiments/runs/decon_bge_virl39k_layer1_full_v1_an12_20260718T055632Z`.
- BGE placement: node `an12`, GPU `5`, TP width `1`, replica count `1`;
  the encoder fits on one GPU and no wider tensor parallelism is required.
- BGE config hash:
  `e32801d515c5ea6e99c8891fc9059efd92875bd9ac90e016be8ac8bb254e2050`.
- BGE lifecycle: `2026-07-18T05:56:54Z` to
  `2026-07-18T05:58:26Z`, status `complete`, exit code `0`.
- BGE output: 55,591 entities, 384 dimensions, float16; embedding SHA256
  `911ea1c7ad7ec9e9252728a070b06d874df1dd51a8f52e60efc68eca2861be99`.
- DINOv2 run:
  `experiments/runs/decon_dinov2_virl39k_layer1_full_v1_an12_20260718T055634Z`.
- DINOv2 placement: node `an12`, GPU `4`, TP width `1`, replica count `1`;
  the encoder fits on one GPU and no wider tensor parallelism is required.
- DINOv2 config hash:
  `872b192bfbdb8b243b3fdb833788002d5f6578d2194e47216263e7dec984be15`.
- DINOv2 start: `2026-07-18T05:57:08Z`; its immutable run manifest remains
  `running` while image decoding and feature extraction proceed.
- At the launch health check, A2-gray seed 2 remained isolated on `an12`
  GPUs 0-3. The embedding jobs used only newly free GPUs 4-5.
- No model-performance value or pilot training metric was opened.

Problems:
- DINOv2 output and checksum do not exist until the active run completes.
- RapidOCR, calibrated signal merge, whole-item freeze, full-subset caption
  coverage, and hashed four-arm configs remain independent M7 prerequisites.

Decision:
- Preserve the completed BGE lifecycle and let DINOv2 finish without
  disturbing A2-gray seed 2.
- Start calibrated embedding comparison only after the DINOv2 manifest is
  complete and both embedding metadata files pass identity/hash checks.
- Continue to describe retained rows only as `conservative contamination
  candidates`; no current record is a confirmed duplicate.

Next actions:
- Audit the completed DINOv2 artifact and record its SHA256.
- Run the registered DINOv2/BGE comparison against the completed hash/text
  baseline.
- Merge the independently completed OCR layer only after all shard and
  coverage checks pass.
