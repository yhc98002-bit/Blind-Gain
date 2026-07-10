# FlipTrack V0.2 Positive Controls

Status:
- P1.7 implementation is complete for the three-template R17 candidate.
- The retained document, R10 geometry, and R16 chart templates pass both registered controls; R7 and R15 remain explicit negative calibration outcomes.

Control A, 3B degradation pair accuracy:
| Template | Original | Mild | Medium | Severe | Gray | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| R3 chart | 0.460 | 0.150 | 0.140 | 0.000 | 0.000 | pass |
| R3 document | 0.850 | 0.670 | 0.650 | 0.180 | 0.000 | pass |
| R4 coordinate register | 0.420 | 0.410 | 0.250 | 0.000 | 0.000 | pass |
| R7 eight-point geometry | 0.4267 | 0.4533 | 0.2633 | 0.000 | 0.000 | pass as strongly downward; mild +0.0266 is sampling variation |
| R6 coordinate calibration | 0.350 | 0.420 | 0.150 | 0.000 | 0.000 | fail: original below floor and mild improves materially |
| R10 high-entropy geometry | 0.450 | 0.410 | 0.240 | 0.0067 | 0.000 | pass: strongly downward |
| R15 five-series chart | 0.5733 | 0.3733 | 0.2167 | 0.0000 | 0.0000 | pass: monotone downward |
| R16 nine-series chart | 0.4367 | 0.1733 | 0.1333 | 0.0000 | 0.0000 | pass: monotone downward |

Control B, model/caption scale:
| Template | 3B real | 7B real | 3B caption | 7B caption | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| R3 chart | 0.460 | 0.670 | 0.000 | 0.010 | pass, but R9 expansion fails visual floor |
| R3 document | 0.850 | 0.990 | 0.010 | 0.030 | pass |
| R4 coordinate register | 0.420 | 0.750 | 0.000 | 0.060 | provisional pass; R5 expansion fails visual floor |
| R7 eight-point geometry | 0.4267 | 0.740 | 0.0167 | 0.170 | fail: 7B caption exceeds 0.15 |
| R10 high-entropy geometry | 0.450 | 0.7467 | 0.0167 | 0.0067 | pass: real rises while caption decreases |
| R15 five-series chart | 0.5733 | 0.3967 | 0.0033 | 0.0000 | fail: 7B real does not improve |
| R16 nine-series chart | 0.4367 | 0.6733 | 0.0000 | 0.0067 | pass: real rises strongly while caption remains near floor |

Evidence:
- Transform implementation and fixtures: `src/eval/image_conditions.py`, `tests/test_eval_image_conditions.py`.
- R7 degradation runs: `experiments/runs/fliptrack_v02r7_qwen25vl3b_{mild,medium,severe}_20260710T011200Z`.
- R7 gray/noise runs: `...gray_20260710T010800Z` and `...noise_20260710T011700Z`.
- R3/R4/R5 caption aggregates are under their corresponding immutable run directories.
- R7 160-token 7B caption QA: `experiments/runs/fliptrack_v02r7_qwen25vl7b_captionqa160_20260710T020500Z`; pair accuracy is 0.1633 versus 0.1700 at 384 tokens.
- R10 real/blind/caption/degradation runs share `data/fliptrack_v02r10_source_manifest.jsonl` and are under `experiments/runs/fliptrack_v02r10_*`.
- R15 real/blind/degradation and completed caption diagnostics share `data/fliptrack_v02r15_source_manifest.jsonl`.
- R16 runs share `data/fliptrack_v02r16_source_manifest.jsonl`; caption-QA retries on `an12` are complete and immutable.

Problems:
- A positive degradation curve does not rescue caption-compressibility.
- A positive degradation curve also does not rescue a template whose visual score fails to improve with model scale, as R15 demonstrates.
- Tightening the R7 caption budget from 384 to 160 tokens does not rescue it: both results exceed 0.15.
- R8 was packaged before the R7 7B-caption cell completed; it is retained only as a failed candidate.

Decision:
- Reject R7 under Control B and retain its Control A curve as instrument-sensitivity evidence.
- Retain R10 as the geometry candidate under both controls.
- Reject R15 under Control B even though it passes Control A.
- Retain R16 under both controls and use document/R10/R16 as the R17 candidate set.

Next actions:
- Confirm the same template identities in the opaque R17 answer key after packaging.
- Keep P1.7 results separate from P1.5 artifact robustness; one does not substitute for the other.
