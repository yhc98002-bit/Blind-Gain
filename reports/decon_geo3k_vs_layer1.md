# Geometry3K vs Layer-1 Decontamination

Status:
- P1.10 is complete for Geometry3K train against the frozen Gate-2 Layer-1 subset.
- SHA/provenance, pHash/dHash, DINOv2, exact/5-gram text, BGE, and OCR layers have complete coverage for that subset.
- The filter marks 463/2,101 Geometry3K train records for automatic removal and 1,285 additional records for inspection only.

Evidence:
- Full record build: `experiments/runs/decon_geo3k_layer1_hash_text_20260710T033444Z`.
- DINOv2 extraction: `experiments/runs/decon_dinov2_full_layer1_an29_20260710T072713Z`, 8,154 unique applicable images, 384 dimensions.
- BGE extraction: `experiments/runs/decon_bge_full_layer1_retry_an29_20260710T073821Z`, 9,704 questions, 384 dimensions.
- Embedding merge: `experiments/runs/decon_embedding_compare_full_layer1_an29_20260710T074847Z`.
- RapidOCR extraction: `experiments/runs/decon_ocr_full_layer1_retry_an29_20260710T080747Z`, 8,154/8,154 images and zero errors.
- Final merge: `experiments/runs/decon_ocr_merge_full_layer1_login_20260710T085608Z`.
- Complete machine filter: `experiments/manifests/decon_geo3k_vs_layer1_v2.json`.
- Threshold calibration: `reports/decon_calibration.md`.

Coverage:
| Side | Dataset | Records |
| --- | --- | ---: |
| train | Geometry3K train | 2,101 |
| eval | MMStar | 1,500 |
| eval | MathVista-testmini | 999 |
| eval | BLINK validation | 3,675 |
| eval | MMVP | 300 |
| eval | HallusionBench | 1,129 |
| eval | total | 7,603 |

Candidate results:
| Result | Edges | Unique Geometry3K train records |
| --- | ---: | ---: |
| automatic remove | 697 | 463 |
| inspect | 11,932 | 1,285 inspect-only |

Automatic-removal overlap:
| Eval dataset | Remove edges | Unique train records | Unique eval records |
| --- | ---: | ---: | ---: |
| MathVista-testmini | 594 | 455 | 56 |
| MMStar | 76 | 74 | 20 |
| HallusionBench | 27 | 7 | 21 |
| BLINK | 0 | 0 | 0 |
| MMVP | 0 | 0 | 0 |

Signal counts:
| Signal | Candidate edges |
| --- | ---: |
| DINOv2 cosine >= 0.90 | 12,146 |
| min pHash/dHash Hamming <= 10 | 632 |
| RapidOCR char-5 Jaccard >= 0.75 | 42 |
| BGE question cosine >= 0.90 | 18 |
| exact normalized question/question-answer or word-5-gram >= 0.70 | 0 |

- Of 697 removal edges, 121 have at least two signal families.
- Removal composition is 569 DINO-only, 69 DINO+hash, 33 DINO+OCR+hash, 10 DINO+hash+BGE, 7 DINO+OCR+hash+BGE, 7 hash-only, and 2 DINO+OCR.
- All 42 OCR edges were already removal edges under independent image evidence; OCR did not create a new automatic-removal decision.
- OCR coverage: 5,452 images produced nonempty text and 2,735 passed the minimum eight-character/two-token-or-line eligibility rule.

Problems:
- DINO's inspect band is broad on diagrams; calibration measured a 10.9% negative inspect rate. Inspect candidates are not automatic removals.
- OCR planted calibration has only 30 eligible positives and 18 eligible negatives. It observed zero negative FPR but is too small to establish population-level specificity.
- Geometry3K and MathVista share source material. Every Geometry3K-trained MathVista result remains labeled `contamination: geo3k-source` even after filtering.
- HallusionBench's 178 true text-only rows were included for text overlap and excluded from image/OCR signals by construction.

Decision:
- Drop every Geometry3K train record in `remove_train_record_ids` before any run claiming clean external-benchmark transfer.
- Keep `inspect_only_train_record_ids` out of automatic filtering until review; inspect thresholds are calibrated for recall rather than precision.
- Engineering anchor and mechanical-pilot results on unfiltered Geometry3K remain stack-validation evidence only.
- Future CP training template IDs must remain disjoint from every FlipTrack evaluation template ID, as recorded in the machine manifest.

Next actions:
- Queue ViRL39K and MMK12 against the same complete Layer-1 records.
- Expand OCR calibration with an OCR-rich document/chart stratum before treating OCR as an independent removal signal.
- Add MathVerse and MMMU in L10 and publish a versioned expanded decontamination report rather than changing this Gate-2 subset result.
