# ViRL39K 3B Data Readiness V2

Status:
- M7 data readiness remains `blocked`; no M7 optimizer step is authorized.
- The full seven-suite hash/text pass is complete and RapidOCR extraction is
  active on the login node.
- DINOv2, BGE, the calibrated layer merge, whole-item freeze, and caption-store
  coverage remain required.

Evidence:
- V1 baseline and source/license details remain at
  `reports/virl_3b_data_readiness_v1.md`.
- Hash/text run:
  `experiments/runs/decon_virl39k_layer1_hash_text_login_20260716T193506Z`,
  status `complete`, exit 0, all four registered artifacts present.
- Hash/text outputs include 38,870-item ViRL train records, seven-suite Layer-1
  records, a record audit, and the immutable hash/text comparison.
- OCR lifecycle and retry placement:
  `reports/m7_ocr_login_launch_v1.md`.
- Informed mechanism amendment remains merged at
  `docs/registered_m7_amendment_v1.md` before any optimizer step.

Problems:
- No final contamination filter or frozen training ID list exists yet.
- DINOv2/BGE work has not launched because no GPU is free: an12 GPUs 0-3 run
  M5, GPUs 5-6 run M11, and GPUs 4/7 hold foreign processes that are treated as
  normal neighbors; an29 is fully occupied by seed 2 and M11.
- The existing 4,096-item caption store cannot substitute for full filtered
  corpus coverage.

Decision:
- Let CPU-only OCR progress without disturbing GPU priority.
- Launch embedding layers only on genuinely free GPUs and only when their
  expected runtime will not delay the registered seed-two/M11 schedule.
- Keep M7 training fail-closed through final decontamination, whole-item freeze,
  100% caption coverage or enumerated gaps, and hashed four-arm configs.
