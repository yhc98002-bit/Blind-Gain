# Geometry3K Train-vs-Test Decontamination

Status:
- The calibrated hash, text, DINOv2, BGE, and OCR pipeline is complete over 2,101 train and 601 held-out test records.
- The final precision-oriented policy marks 498 train rows as conservative contamination candidates and 1,576 additional rows as inspect-only candidates.
- All seven registered signal layers have complete coverage; OCR has zero missing and zero error images.

Evidence:
- Final comparison: `experiments/runs/decon_ocr_compare_geo3k_train_test_v4_an29_20260711T105035Z/comparison_v3.json`, SHA256 `75cb5076fc824b67e919ef170c4fe84effc93eb9b7bf0f745531668badfc5336`.
- Final filter manifest: `experiments/runs/decon_summary_geo3k_train_test_v4_login_20260711T105057Z/filter_manifest.json`, SHA256 `cf6affe7d74af2f52daaf03d561e41031d60f03f29ad341d1410740a2883eddc`.
- Extraction jobs: DINOv2 `experiments/runs/decon_geo3k_train_test_dinov2_an29_20260711T102338Z`, BGE `experiments/runs/decon_geo3k_train_test_bge_an29_20260711T102338Z`, and eight-shard RapidOCR `experiments/runs/decon_ocr_geo3k_train_test_an29_20260711T102644Z`; all completed with exit code 0.
- Visual false-positive audit: `reports/contact_sheets/decon_geo3k_train_test_v4/dinov2_false_positive_audit.png`, SHA256 `fe9dacd9571a596d05bb28340a75357c592386f6e5294528f2e3fbb88331002f`.
- Focused decontamination suite: 17 tests pass, including adversarial generic-prompt BGE and same-renderer DINO fixtures.

| Pipeline state | Candidate edges | Remove edges | Unique train candidates | Disposition |
| --- | ---: | ---: | ---: | --- |
| V1 hash/text | 21,604 | 20,880 | not used | invalid: short generic prompts were treated as exact 5-grams |
| V2 corrected hash/text | 21,604 | 1,978 | 928 | intermediate; embedding/OCR layers absent |
| V2 full merge | 42,747 | 13,181 | 1,789 | superseded: BGE bypassed the generic-prompt guard and same-renderer DINO acted alone |
| V3 embedding guards | 42,747 | 3,399 | 1,023 | superseded: same-dataset template similarity still acted as removal evidence |
| V4 final policy | 42,747 | 653 | 498 | final conservative contamination-candidate set |

Final signal accounting:
| Policy outcome | Edges |
| --- | ---: |
| Exact image SHA256 preserved as removal | 635 |
| Distinctive exact question+answer preserved as removal | 12 |
| Joint pHash+DINOv2+OCR preserved as removal | 6 |
| Unsupported same-dataset removal downgraded to inspection | 2,746 |

OCR coverage:
| Measure | Count |
| --- | ---: |
| Expected/present unique images | 1,736 / 1,736 |
| Nonempty OCR text | 1,731 |
| Eligible OCR text | 889 |
| Missing/error images | 0 / 0 |

Problems:
- The cross-dataset planted-duplicate calibration did not transfer directly to train-vs-test data rendered by one source. Near-threshold DINO pairs were usually distinct problems with similar styling, and BGE linked repeated task wording with different images and answers.
- The V4 policy prioritizes precision: a same-dataset edge can remove only through exact image identity, distinctive exact question+answer, or joint pHash+DINOv2+OCR corroboration. This may leave re-rendered contamination candidates in the inspect-only set.
- Counts are conservative contamination candidates, never confirmed duplicates.

Decision:
- Use only the V4 498-row removal set in the pilot-corpus union.
- Preserve V1-V3 outputs as failure evidence; do not reinterpret their larger counts as valid filters.
- Keep all inspect-only records in training because their evidence is calibrated for recall, not sufficient removal precision.

Next actions:
- Recompute the exact L7 blind-solvability audit on the frozen union-filtered corpus.
- Audit a stratified inspect-only sample before any later claim that the filter has high recall.
