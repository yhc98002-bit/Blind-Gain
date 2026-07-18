# M7 Embedding Completion V1

Status:
- The BGE text and DINOv2 image embedding layers are complete.
- Their calibrated comparison against the frozen hash/text baseline completed
  on `an12` GPU 4 with exit code 0.
- M7 remains `blocked`; RapidOCR completion, the final calibrated signal merge,
  whole-item freeze, caption coverage, and hashed training configs are still
  required before any optimizer step.

Evidence:
- Frozen source-manifest hash:
  `1c5d71d1b3b536807b11aaddbb33e3f371a55900516cdb5fca58c51d1ba3457a`.
- DINOv2 run:
  `experiments/runs/decon_dinov2_virl39k_layer1_full_v1_an12_20260718T055634Z`,
  45,302 image entities, output SHA256
  `b3f5fcccbf11c06b1fd9764b51ad74c6867f6bc1ff4e6eda471ee9ee3683230b`.
- BGE run:
  `experiments/runs/decon_bge_virl39k_layer1_full_v1_an12_20260718T055632Z`,
  55,591 text entities, output SHA256
  `911ea1c7ad7ec9e9252728a070b06d874df1dd51a8f52e60efc68eca2861be99`.
- Comparison run:
  `experiments/runs/decon_embedding_compare_virl39k_layer1_full_v1_an12_20260718T145041Z`,
  status `complete`, exit code `0`, TP width `1`, replica count `1`.
- Comparison output SHA256:
  `7ea8bab741485a86cc870d1d65bae8e6abf155dcf38650fe9130ef3d40741f01`.
- The comparison produced 254,154 candidate edges for the registered
  calibration logic; no training subset was frozen from this layer alone.

Problems:
- RapidOCR is still processing eight CPU shards on the login node.
- The current edge actions are intermediate conservative contamination
  candidates and do not constitute a final removal manifest.

Decision:
- Preserve all three immutable embedding lifecycles and their hashes.
- Wait for complete OCR coverage before the registered multimodal signal merge.
- Apply removals at whole-item level only after the final merge and report its
  distribution shift before training.
