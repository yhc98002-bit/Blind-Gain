# Decontamination Calibration

Status:
- Hash, DINOv2, word-5-gram, BGE, and OCR thresholds have planted-duplicate calibration results.
- OCR uses an isolated RapidOCR environment and a corroboration-only removal policy.
- The first calibration is preserved as a methodology failure; the corrected R2 calibration is authoritative.

Evidence:
- Corrected run: `experiments/runs/decon_calibration_planted64r2_an29_20260710T030039Z`.
- Superseded run: `experiments/runs/decon_calibration_planted64_an29_20260710T024927Z`.
- Image positive: 75% downsample/upscale, JPEG quality 85, then PNG re-encode.
- Text positive: the same question with a semantically neutral solve-carefully suffix.
- Corrected negatives require a different image hash, different normalized question, word-5-gram Jaccard below 0.3, and minimum pHash/dHash Hamming above 10.
- Seed: `20260710`; sample size: 64.
- OCR plan: `experiments/runs/decon_ocr_calibration_plan_login_20260710T082249Z`.
- OCR transformed extraction: `experiments/runs/decon_ocr_calibration_transforms_an29_20260710T082439Z`.
- OCR summary: `experiments/runs/decon_ocr_calibration_summary_login_20260710T085432Z`.

Calibration results:
| Signal | Remove threshold | Positive remove recall | Negative remove FPR | Inspect threshold | Positive inspect recall | Negative inspect FPR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| min(pHash, dHash) Hamming | <= 6 | 1.0000 | 0.0000 | <= 10 | 1.0000 | 0.0000 |
| DINOv2 cosine | >= 0.95 | 1.0000 | 0.0000 | >= 0.90 | 1.0000 | 0.1094 |
| word-5-gram Jaccard | >= 0.80 | 0.0312 | 0.0000 | >= 0.70 | 0.1094 | 0.0000 |
| BGE question cosine | >= 0.95 | 0.8906 | 0.0000 | >= 0.90 | 1.0000 | 0.0312 |
| RapidOCR char-5 Jaccard | >= 0.90 | 0.6667 | 0.0000 | >= 0.75 | 0.6667 | 0.0000 |

Problems:
- The first negative sampler used a fixed half-sample rotation. Several rotated records had identical generic questions such as `Find x`, creating a spurious 9.4% BGE/Jaccard negative rate.
- The corrected sampler has a regression test in `tests/test_decon_calibration.py` and excludes those accidental positives.
- Word 5-grams intentionally have low recall for suffix-modified questions. BGE covers this semantic case; lowering Jaccard alone would broaden lexical false positives.
- The real hash pass began before calibration completed. No filtering decision was made from it until the corrected calibration passed; this ordering deviation is recorded rather than hidden.
- OCR text eligibility retained 30/64 transformed positives and 18/64 constrained negatives. The remaining images lacked at least eight compact characters and two tokens/lines on both sides.
- OCR's zero observed FPR is based on only 18 eligible negatives. OCR-only matches therefore remain inspection-only; removal requires independent SHA/hash/DINO corroboration.

Decision:
- Keep the proposal thresholds unchanged.
- Automatic removal uses the remove thresholds only.
- Inspect-band candidates remain review candidates because calibrated DINO/BGE inspect false-positive rates are nonzero.
- Keep OCR thresholds at 0.90 remove / 0.75 inspect, but use the remove threshold only as corroborating evidence.
- Treat the zero observed remove FPR as limited evidence from 64 negatives, not a proof of zero population FPR.

Next actions:
- Expand OCR calibration with a deliberately OCR-rich document/chart stratum from the now-local HallusionBench/MMVP/MathVista assets.
- Revisit independent OCR removal only if that expanded negative set supports it.
