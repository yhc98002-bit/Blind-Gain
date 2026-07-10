# FlipTrack V0.2 Hardness Calibration

Status:
- P1.6 implementation is complete with three retained templates: document 300, high-entropy geometry 600, and R16 chart 300.
- All three satisfy the unchanged hardness contract, and R10 supplies the required Track-b geometry family.
- The 1,200-pair R19 package passes P1.4 leakage lint and P1.5 grouped artifact attacks; the required human contact-sheet audit is pending.

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
| R15 five-series chart | 300 | 0.5733 | 0.3967 | 0.0033 | 0.0000 | 0.0000 | 0.0000 | reject: 7B real does not improve over 3B |
| R16 nine-series chart | 300 | 0.4367 | 0.6733 | 0.0000 | 0.0067 | 0.0000 | 0.0000 | retain: all registered hardness cells pass |
| R18 geometry expansion | 300 | 0.4933 | not rerun | same template | same template | same template | same template | retain for artifact expansion after fixed 3B spot check |

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

R15 diagnostics:
- Source manifest: `data/fliptrack_v02r15_source_manifest.jsonl`, one fixed 300-pair batch.
- 3B real: `experiments/runs/fliptrack_v02r15_qwen25vl3b_real_20260710T075114Z`; final pair accuracy 0.5733 and strict pair accuracy 0.3933.
- 7B real: `experiments/runs/fliptrack_v02r15_qwen25vl7b_real_20260710T075919Z`; final/strict pair accuracy 0.3967.
- Control A is monotone: 0.5733 real, 0.3733 mild, 0.2167 medium, 0 severe, and 0 gray; pair-shared noise is also 0 with collapse 1.0.
- R15 fails Control B. The 7B final score falls by 0.1766; strict accuracy is effectively flat (+0.0034), so there is no substantive scale gain under either score.
- Caption-only pair accuracy is 0.0033 for 3B and 0 for 7B. This rules out caption leakage as the failure cause but cannot repair the failed real-image scale control.

R16 diagnostics:
- Source manifest: `data/fliptrack_v02r16_source_manifest.jsonl`, one fixed 300-pair batch, SHA256 `8a0ec164c68adb131860e9ca7da802492d9cec22f390ba6c5960cb8ec69225a4`.
- 3B real: `experiments/runs/fliptrack_v02r16_qwen25vl3b_real_20260710T090950Z`; final pair accuracy 0.4367 and strict pair accuracy 0.4200.
- 7B real: `experiments/runs/fliptrack_v02r16_qwen25vl7b_real_20260710T091837Z`; final and strict pair accuracy 0.6733.
- Gray and pair-shared noise pair accuracy are 0 with collapse 1.0.
- The degradation curve is monotone: 0.4367 real, 0.1733 mild, 0.1333 medium, 0 severe, and 0 gray.
- Question-blind 384-token caption QA is `experiments/runs/fliptrack_v02r16_qwen25vl3b_captionqa384_retry_an12_20260710T120300Z` and `experiments/runs/fliptrack_v02r16_qwen25vl7b_captionqa384_retry_an12_20260710T120300Z`; pair accuracy is 0/0.0067.
- Initial caption-QA attempts on `an29` are preserved as failed because an unrelated TP=4 service occupied their registered GPUs; see `reports/gpu_allocation_conflict_20260710.md`.

R18 expansion diagnostics:
- Source manifest: `data/fliptrack_v02r18_source_manifest.jsonl`, SHA256 `932632a8720601ad2c87a78dcb29c8e167b9a718c09aa934801e7d1643e5fe33`.
- R18 uses the unchanged R10 generator with independent seed `20260919`; all 300 pairs are retained in addition to the original R10 batch.
- Fixed 3B real-image spot check: `experiments/runs/fliptrack_v02r18_qwen25vl3b_real_an12_20260710T123900Z`; pair accuracy 0.4933, strict pair accuracy 0.4767, format-valid rate 0.98.
- Other mode/model cells are not rerun because this is an instance expansion of the already accepted template, not a template redesign.

R19 exact-package caption diagnostic:
- The exact 3B store covers all 2,400 packaged image hashes with no missing, extra, duplicate, mixed-contract, or empty-caption rows.
- Full-package 3B caption-only pair accuracy is 0.0125 with 95% bootstrap CI [0.0067, 0.0192]. Per-template pair accuracy is 0.0100 document, 0.0200 geometry, and 0 chart.
- The within-template key-shuffle null mean is 0.00681 (`p=0.01598`), so the small nonzero caption signal is reported rather than rounded away.
- Runs: `experiments/runs/caption_store_merge_fliptrack_v02r19_qwen25vl3b_384_20260710T134825Z`, `experiments/runs/fliptrack_v02r19_qwen25vl3b_captionqa384_an29_20260710T140850Z`, and `experiments/runs/fliptrack_aggregate_v02r19_qwen25vl3b_caption384_20260710T142221Z`.

Format caveat:
- R3 document 3B final pair accuracy is 0.85 but strict pair accuracy is 0.19 because format-valid rate is 0.425.
- The shared prompt contract is unchanged; final and strict metrics remain separate.

Contact sheets:
- R3: `reports/contact_sheets/fliptrack_v02r3/`.
- R5: `reports/contact_sheets/fliptrack_v02r5/`.
- R7: `reports/contact_sheets/fliptrack_v02r7/coordinate_register_eight_point_v02.png`.
- R9: `reports/contact_sheets/fliptrack_v02r9/starred_series_value_v02.png`.
- R10: `reports/contact_sheets/fliptrack_v02r10/coordinate_register_twenty_point_x_v02.png`.
- R16: `reports/contact_sheets/fliptrack_v02r16/starred_series_value_nine_v07.png`.

Problems:
- The R8 package passed its linter but is scientifically invalid as a freeze candidate because R7's 7B caption check was pending when packaged.
- Generic 7B captions can enumerate enough of an eight-point coordinate plot to recover 17% of R7 pairs; increasing R10 to twenty randomized bindings reduces this to 0.67%.
- The independent R9 chart expansion misses the 3B visual floor.
- Removing all direct target emphasis while increasing R12 to eight series overcorrects the R11 upper-bound failure.
- R13's six-series intermediate design improves over R12 but remains below the visual floor; the chart family is not yet retained.
- R14's unhighlighted 12-row ledger saturates the 3B visual ceiling and therefore cannot serve as the third retained template.
- R15 passes the 3B hardness and degradation gates but fails the registered 3B-to-7B real-image scale control.
- R19 passes the automated package and artifact gates, but automated checks cannot replace the pending human legibility/semantic audit.

Decision:
- Preserve R8/R9 as failed calibration evidence.
- Retain 300 document, all 600 R10/R18 geometry, and 300 R16 chart pairs in the R19 freeze candidate.
- Keep every rejected calibration batch out of the candidate; no failed batch is pooled to cross a threshold.

Next actions:
- Finish the exact-package 7B caption store and scale-control score.
- Complete `reports/fliptrack_v02r19_human_audit.md` before declaring the candidate frozen for scientific use.
