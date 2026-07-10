# FlipTrack V0.2 Hardness Calibration

Status:
- P1.6 is blocked. The earlier 300-pair “retained” claim was provisional and is superseded.
- The expanded document family and R10 high-entropy geometry pass. Existing chart expansion fails unchanged acceptance thresholds.
- No FlipTrack V0.2 eval split is frozen and no PI audit is requested yet.

Acceptance contract:
- 7B question-blind caption pair accuracy <= 0.15.
- 3B real pair accuracy in [0.40, 0.90].
- Gray and pair-shared-noise pair accuracy <= 0.05 with collapse near 1.
- One declared batch is evaluated without adding rescue examples until it passes.

Current evidence:
| Batch / template | Pairs | 3B real | 7B real | 3B caption | 7B caption | Gray | Noise | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| R3 chart | 100 | 0.460 | 0.670 | 0.000 | 0.010 | 0.000 | 0.000 | provisional pass; expansion required by artifact CI |
| R3 document | 100 | 0.850 | 0.990 | 0.010 | 0.030 | 0.000 | 0.000 | pass; format caveat below |
| R4 coordinate register | 100 | 0.420 | 0.750 | 0.000 | 0.060 | 0.000 | 0.000 | provisional pass; expansion required by artifact CI |
| R5 document expansion | 200 | 0.875 | 0.995 | 0.010 | 0.075 | 0.000 | 0.000 | pass |
| R5 coordinate expansion | 200 | 0.375 | 0.795 | 0.000 | 0.045 | 0.000 | 0.000 | reject: 3B real below 0.40 |
| R6 coordinate calibration | 100 | 0.350 | 0.650 | 0.000 | 0.080 | 0.000 | not run | reject: 3B real and degradation control fail |
| R7 eight-point geometry | 300 | 0.4267 | 0.740 | 0.0167 | 0.170 | 0.000 | 0.000 | reject: 7B caption exceeds 0.15 |
| R9 chart expansion | 300 | 0.370 | 0.6067 | 0.000 | 0.0033 | not run | not run | reject: 3B real below 0.40 |
| R10 high-entropy geometry | 300 | 0.450 | 0.7467 | 0.0167 | 0.0067 | 0.000 | 0.000 | retain candidate: all registered hardness cells pass |
| R11 legible chart | 300 | 0.980 | not run | not run | not run | not run | not run | reject: 3B real exceeds 0.90 upper bound |
| R12 balanced chart | 300 | 0.2533 | not run | not run | not run | not run | not run | reject: 3B real below 0.40 lower bound |
| R13 guided chart | 300 | 0.3767 | not run | not run | not run | not run | not run | reject: 3B real below 0.40 lower bound |
| R14 inspection ledger | 300 | 0.9900 | not run | not run | not run | not run | not run | reject: 3B real exceeds 0.90 upper bound |

R7 diagnostics:
- Source manifest: `data/fliptrack_v02r7_source_manifest.jsonl`, SHA256 `1640e682a765257d220dab83e66b248f79cebd2b0382d5c55d0bf9867bbb1dc3`.
- 3B real: `experiments/runs/fliptrack_v02r7_qwen25vl3b_real_20260710T010100Z`; pair-accuracy 95% bootstrap CI [0.370, 0.483].
- 3B gray/noise collapse is 1.0 and pair accuracy is 0.
- 3B caption QA: `experiments/runs/fliptrack_v02r7_qwen25vl3b_captionqa384_20260710T013700Z`.
- 7B caption QA: `experiments/runs/fliptrack_v02r7_qwen25vl7b_captionqa384_20260710T014100Z`.
- The scale-dependent caption increase shows that eight labeled points fit inside a stronger model's generic 384-token caption often enough to violate certification.

R9 diagnostics:
- Source manifest: `data/fliptrack_v02r9_source_manifest.jsonl`, 300 pairs, SHA256 `bfc60bd6c81beea7a30e0f1d6bd2ecd431ec9d4972060f1991f68d754a980534`.
- 3B real: `experiments/runs/fliptrack_v02r9_qwen25vl3b_real_20260710T013700Z`.
- Final pair accuracy is 0.370; strict pair accuracy is 0.3667; format-valid rate is 0.995.
- The diagnostic 7B real-image run reaches 0.6067; this does not rescue the failed registered 3B floor.
- R9 is excluded rather than pooled opportunistically with the favorable R3 batch.

R10 diagnostics:
- Source manifest: `data/fliptrack_v02r10_source_manifest.jsonl`, 300 pairs generated in one declared batch.
- 3B real: `experiments/runs/fliptrack_v02r10_qwen25vl3b_real_20260710T020600Z`.
- Pair accuracy is 0.450; strict pair accuracy is 0.410; format-valid rate is 0.970.
- 7B real pair accuracy is 0.7467; 3B/7B caption-only pair accuracy is 0.0167/0.0067.
- Gray and pair-shared-noise pair accuracy are both 0 with collapse 1.0.
- Degradation is strongly downward: 0.450 original, 0.410 mild, 0.240 medium, 0.0067 severe, 0 gray.
- R10 is a retained template candidate. It does not by itself satisfy the three-template P1.6 requirement.

R11 diagnostics:
- Source manifest: `data/fliptrack_v02r11_source_manifest.jsonl`, one fixed 300-pair batch.
- 3B real: `experiments/runs/fliptrack_v02r11_qwen25vl3b_real_20260710T030100Z`.
- Pair accuracy is 0.980 and strict pair accuracy is 0.830. The direct point ring and target-line emphasis made the template too easy.
- R11 is excluded without running blind/caption cells; an upper-bound failure cannot be rescued by those cells.

R12 diagnostics:
- Source manifest: `data/fliptrack_v02r12_source_manifest.jsonl`, one fixed 300-pair batch.
- 3B real: `experiments/runs/fliptrack_v02r12_qwen25vl3b_real_20260710T031345Z`.
- Pair accuracy is 0.2533, strict pair accuracy is 0.1933, and format-valid rate is 0.915.
- R12 is excluded without running blind/caption cells; a lower-bound failure is not repaired by threshold changes or favorable follow-on modes.

R13 diagnostics:
- Source manifest: `data/fliptrack_v02r13_source_manifest.jsonl`, one fixed 300-pair batch.
- 3B real: `experiments/runs/fliptrack_v02r13_qwen25vl3b_real_20260710T033515Z`.
- Pair accuracy is 0.3767, strict pair accuracy is 0.3033, and format-valid rate is 0.9217.
- R13 is excluded without running blind/caption cells because it misses the preregistered 0.40 visual floor.

R14 diagnostics:
- Source manifest: `data/fliptrack_v02r14_source_manifest.jsonl`, one fixed 300-pair batch, SHA256 `60bc4b2a40b189d402eb6eb379dac86a16c6404ad4072d8ee75b305afacf5abf`.
- The first evaluation, `experiments/runs/fliptrack_v02r14_qwen25vl3b_real_20260710T065652Z`, was terminated by shared-storage quota after 207 rows and is preserved as a failed run.
- The clean retry is `experiments/runs/fliptrack_v02r14_qwen25vl3b_real_retry_20260710T072648Z`.
- Pair accuracy is 0.9900, strict pair accuracy is 0.9833, and format-valid rate is 0.9950.
- R14 is excluded without blind/caption cells. Removing row highlighting did not make exact record-ID lookup difficult enough for the 3B model.

Format caveat:
- R3 document 3B final pair accuracy is 0.85 but strict pair accuracy is 0.19 because format-valid rate is 0.425.
- The shared prompt contract is unchanged; final and strict metrics remain separate.

Contact sheets:
- R3: `reports/contact_sheets/fliptrack_v02r3/`.
- R5: `reports/contact_sheets/fliptrack_v02r5/`.
- R7: `reports/contact_sheets/fliptrack_v02r7/coordinate_register_eight_point_v02.png`.
- R9: `reports/contact_sheets/fliptrack_v02r9/starred_series_value_v02.png`.

Problems:
- The R8 package passed its linter but is scientifically invalid as a freeze candidate because R7's 7B caption check was pending when packaged.
- Generic 7B captions can enumerate enough of an eight-point coordinate plot to recover 17% of R7 pairs; increasing R10 to twenty randomized bindings reduces this to 0.67%.
- The independent R9 chart expansion misses the 3B visual floor.
- Removing all direct target emphasis while increasing R12 to eight series overcorrects the R11 upper-bound failure.
- R13's six-series intermediate design improves over R12 but remains below the visual floor; the chart family is not yet retained.
- R14's unhighlighted 12-row ledger saturates the 3B visual ceiling and therefore cannot serve as the third retained template.

Decision:
- Preserve R8/R9 as failed calibration evidence.
- Keep the 300-pair document family.
- Retain R10 high-entropy geometry and the expanded document family as the two current candidates.
- Continue with independently declared template revisions; never pool failed batches to cross the visual floor.

Next actions:
- Predeclare one five-series chart revision between R13's six-series lower-bound miss and R11's directly highlighted upper-bound failure; retain the no-ring/no-thick-line contract.
- Package and attack only after three families independently meet all acceptance checks.
