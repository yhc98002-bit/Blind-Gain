# Decontamination Calibration

Status:
- Hash, DINOv2, word-5-gram, and BGE thresholds are calibrated on 64 planted near-duplicates plus 64 constrained negatives.
- The calibration is partial because OCR overlap has no local model yet.
- The first calibration is preserved as a methodology failure; the corrected R2 calibration is authoritative.

Evidence:
- Corrected run: `experiments/runs/decon_calibration_planted64r2_an29_20260710T030039Z`.
- Superseded run: `experiments/runs/decon_calibration_planted64_an29_20260710T024927Z`.
- Image positive: 75% downsample/upscale, JPEG quality 85, then PNG re-encode.
- Text positive: the same question with a semantically neutral solve-carefully suffix.
- Corrected negatives require a different image hash, different normalized question, word-5-gram Jaccard below 0.3, and minimum pHash/dHash Hamming above 10.
- Seed: `20260710`; sample size: 64.

Calibration results:
| Signal | Remove threshold | Positive remove recall | Negative remove FPR | Inspect threshold | Positive inspect recall | Negative inspect FPR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| min(pHash, dHash) Hamming | <= 6 | 1.0000 | 0.0000 | <= 10 | 1.0000 | 0.0000 |
| DINOv2 cosine | >= 0.95 | 1.0000 | 0.0000 | >= 0.90 | 1.0000 | 0.1094 |
| word-5-gram Jaccard | >= 0.80 | 0.0312 | 0.0000 | >= 0.70 | 0.1094 | 0.0000 |
| BGE question cosine | >= 0.95 | 0.8906 | 0.0000 | >= 0.90 | 1.0000 | 0.0312 |

Problems:
- The first negative sampler used a fixed half-sample rotation. Several rotated records had identical generic questions such as `Find x`, creating a spurious 9.4% BGE/Jaccard negative rate.
- The corrected sampler has a regression test in `tests/test_decon_calibration.py` and excludes those accidental positives.
- Word 5-grams intentionally have low recall for suffix-modified questions. BGE covers this semantic case; lowering Jaccard alone would broaden lexical false positives.
- The real hash pass began before calibration completed. No filtering decision was made from it until the corrected calibration passed; this ordering deviation is recorded rather than hidden.

Decision:
- Keep the proposal thresholds unchanged.
- Automatic removal uses the remove thresholds only.
- Inspect-band candidates remain review candidates because calibrated DINO/BGE inspect false-positive rates are nonzero.
- Treat the zero observed remove FPR as limited evidence from 64 negatives, not a proof of zero population FPR.

Next actions:
- Add and calibrate OCR overlap when a reproducible local OCR model is installed.
- Expand calibration with document/chart images when HallusionBench and MMVP acquisition is unblocked.
