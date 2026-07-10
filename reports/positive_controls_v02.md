# FlipTrack V0.2 Positive Controls

Status:
- P1.7 is blocked because no three-template retained set exists.
- Controls identify the exact R7 failure: real-image accuracy scales up, but 7B caption-only also rises above the certification ceiling.

Control A, 3B degradation pair accuracy:
| Template | Original | Mild | Medium | Severe | Gray | Result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| R3 chart | 0.460 | 0.150 | 0.140 | 0.000 | 0.000 | pass |
| R3 document | 0.850 | 0.670 | 0.650 | 0.180 | 0.000 | pass |
| R4 coordinate register | 0.420 | 0.410 | 0.250 | 0.000 | 0.000 | pass |
| R7 eight-point geometry | 0.4267 | 0.4533 | 0.2633 | 0.000 | 0.000 | pass as strongly downward; mild +0.0266 is sampling variation |
| R6 coordinate calibration | 0.350 | 0.420 | 0.150 | 0.000 | 0.000 | fail: original below floor and mild improves materially |

Control B, model/caption scale:
| Template | 3B real | 7B real | 3B caption | 7B caption | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| R3 chart | 0.460 | 0.670 | 0.000 | 0.010 | pass, but R9 expansion fails visual floor |
| R3 document | 0.850 | 0.990 | 0.010 | 0.030 | pass |
| R4 coordinate register | 0.420 | 0.750 | 0.000 | 0.060 | provisional pass; R5 expansion fails visual floor |
| R7 eight-point geometry | 0.4267 | 0.740 | 0.0167 | 0.170 | fail: 7B caption exceeds 0.15 |

Evidence:
- Transform implementation and fixtures: `src/eval/image_conditions.py`, `tests/test_eval_image_conditions.py`.
- R7 degradation runs: `experiments/runs/fliptrack_v02r7_qwen25vl3b_{mild,medium,severe}_20260710T011200Z`.
- R7 gray/noise runs: `...gray_20260710T010800Z` and `...noise_20260710T011700Z`.
- R3/R4/R5 caption aggregates are under their corresponding immutable run directories.
- R7 160-token 7B caption QA: `experiments/runs/fliptrack_v02r7_qwen25vl7b_captionqa160_20260710T020500Z`; pair accuracy is 0.1633 versus 0.1700 at 384 tokens.

Problems:
- A positive degradation curve does not rescue caption-compressibility.
- Tightening the R7 caption budget from 384 to 160 tokens does not rescue it: both results exceed 0.15.
- R8 was packaged before the R7 7B-caption cell completed; it is retained only as a failed candidate.

Decision:
- Reject R7 under Control B and retain its Control A curve as instrument-sensitivity evidence.
- Do not mark P1.7 complete until every template in a final package passes both controls.

Next actions:
- Run the same controls on the next high-entropy geometry design.
- Recompute this table only from the final selected package.
