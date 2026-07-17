# M7 ViRL39K OCR Login Launch V1

Status:
- The eight-shard RapidOCR extraction retry is active on the login node.
- The job is CPU-only and consumes no GPU allocation.
- This advances one M7 data-readiness layer; it does not authorize M7 training.

Evidence:
- Completed source record run:
  `experiments/runs/decon_virl39k_layer1_hash_text_login_20260716T193506Z`.
- Retry run:
  `experiments/runs/decon_ocr_virl39k_layer1_full_v2_login_20260717T090247Z`.
- Retry Git hash: `9adda436a9cbbd7039b05c16e37d02d3142d31b4`.
- Retry config hash:
  `a3daa778cfae39508484fb23afaf05726fa6c6b2f464e0f240dcb67c93ca5945`.
- Input manifest hash:
  `216b37d9db472c772b90c455dd33c014ce0950c3c1fb1bec3c1e347dd025cc62`.
- Placement: node `login`, GPU IDs `[]`, TP width `0`, replica count `0`;
  eight CPU shards with two BLAS/OpenMP threads each.
- Named tmux session:
  `decon_ocr_virl39k_layer1_full_v2_login_20260717T090247Z`.
- Startup check observed all eight `extract_decon_ocr.py` processes and eight
  shard files.
- Launcher checks: `bash -n` pass and `3 passed` in
  `tests/test_decon_launcher_manifests.py`.

Problems:
- The first login-node attempt at
  `experiments/runs/decon_ocr_virl39k_layer1_full_v1_login_20260717T085739Z`
  used local `nohup`; the wrapper exited before spawning a child. It produced
  zero shard artifacts and is finalized `fail` with exit 75 and an explicit
  non-scientific detachment deviation.
- OCR completion, coverage auditing, and comparison with the calibrated hash,
  text, DINOv2, and BGE layers remain outstanding.

Decision:
- Preserve the failed empty lifecycle and use the named-tmux retry.
- Keep all contamination language at `conservative contamination candidates`;
  no current row is called a confirmed duplicate.
