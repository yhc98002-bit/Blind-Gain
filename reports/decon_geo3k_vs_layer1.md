# Geometry3K vs Layer-1 Decontamination

Status:
- Geometry3K train has been compared against the available Layer-1 images from MMStar, MathVista-testmini, and BLINK.
- The machine filter manifest is intentionally incomplete because OCR, HallusionBench, and MMVP are pending.
- P1.10 remains blocked; the available comparison already shows substantial Geometry3K overlap with MathVista.

Evidence:
- Record build: `experiments/runs/decon_geo3k_layer1_hash_text_20260710T023646Z`.
- DINO features: `experiments/runs/decon_dinov2_an29_20260710T024927Z`, 7,516 unique images, 384 dimensions.
- BGE features: `experiments/runs/decon_bge_an29_20260710T024927Z`, 8,275 questions, 384 dimensions.
- Merged comparison: `experiments/runs/decon_embedding_compare_geo3k_layer1_an29_20260710T025840Z`.
- Machine filter manifest: `experiments/manifests/decon_geo3k_vs_layer1.json`.
- Calibration: `reports/decon_calibration.md`.

Coverage:
| Side | Dataset | Records/images |
| --- | --- | ---: |
| train | Geometry3K train | 2,101 |
| eval | MMStar | 1,500 |
| eval | MathVista-testmini | 999 |
| eval | BLINK validation | 3,675 |
| eval | total | 6,174 |

Candidate results:
| Result | Edges | Unique Geometry3K train records | Unique eval records |
| --- | ---: | ---: | ---: |
| automatic remove | 670 | 457 | 76 |
| inspect | 11,471 | 1,285 inspect-only | 250 |

Automatic-removal overlap:
| Eval dataset | Remove edges | Unique train records | Unique eval records |
| --- | ---: | ---: | ---: |
| MathVista-testmini | 594 | 455 | 56 |
| MMStar | 76 | 74 | 20 |
| BLINK | 0 | 0 | 0 |

Signal counts:
| Signal | Candidate edges |
| --- | ---: |
| DINOv2 cosine >= 0.90 | 11,962 |
| min pHash/dHash Hamming <= 10 | 339 |
| BGE question cosine >= 0.90 | 18 |
| exact normalized question/question-answer or word-5-gram >= 0.70 | 0 |

- Of 670 removal edges, 120 are corroborated by at least two signal families.
- Removal composition: 547 DINO-only, 103 DINO+hash, 17 DINO+hash+BGE, and 3 hash-only.
- Multiple pairs have DINO cosine approximately 1.0 and pHash/dHash distance 0 despite different file SHA256 values, consistent with re-encoded copies rather than merely similar diagram style.
- The 457 automatic-removal records are 21.75% of Geometry3K train. Some records overlap both MathVista and MMStar, so per-dataset unique counts do not sum to 457.

Problems:
- DINO's inspect band is broad on diagrams; calibration measured a 10.9% negative inspect rate. Inspect candidates are not automatic removals.
- OCR text overlap is absent because no local OCR model is installed.
- HallusionBench and MMVP acquisition remains blocked by upstream HTTP 429 responses, so this is not the full Layer-1 suite.
- Geometry3K and MathVista share source material. Any Geometry3K-trained checkpoint row on MathVista must retain the label `contamination: geo3k-source` even after filtering.

Decision:
- Drop every Geometry3K train record listed in `remove_train_record_ids` before any result intended to claim external-benchmark transfer.
- Keep `inspect_only_train_record_ids` out of automatic filtering until review because the inspect threshold is calibrated for recall, not precision.
- Engineering anchor and mechanical-pilot results on unfiltered Geometry3K remain usable for stack validation only, not clean MathVista transfer claims.
- Future CP training template IDs must be disjoint from all FlipTrack evaluation template IDs; the rule is recorded in the machine manifest.

Next actions:
- Add OCR overlap and rerun the merged comparison.
- Resume HallusionBench/MMVP acquisition and append their records without changing existing thresholds.
- Queue ViRL39K/MMK12 against the same Layer-1 records after this Geometry3K audit closes.
