# Artifact Gate V0.2

Status:
- The corrected attacker implementation is complete and DINOv2 ran successfully.
- The first broad V0.2 candidate failed as documented below.
- The 300-pair retained package also fails the unchanged gate narrowly on frequency/metadata probes. P1.5 remains open and the required expansion is in progress.

Evidence:
- Run: `experiments/runs/artifact_gate_v02_an12_gpu4_20260709T225131Z`, exit code 0, `an12` GPU 4.
- Machine output: `reports/artifact_gate_v02.json`.
- Protocol: five-fold grouped CV by pair, direction selected only on train folds, out-of-fold AUC, `max(AUC, 1-AUC)`, and 1,000 pair-bootstrap resamples.
- Attackers: frequency/statistical, metadata/PNG encoder, and locally cached `facebook/dinov2-small`.
- Historical diagnosis repeats the old split with 10 seeds rather than interpreting one shared sub-0.5 split.

Pooled results:
| Attacker | Gate statistic | 95% pair-bootstrap CI | Point rule <= 0.55 |
| --- | ---: | ---: | --- |
| Frequency/statistical | 0.5653 | [0.5431, 0.5881] | fail |
| Metadata/encoder | 0.5194 | [0.5012, 0.5504] | pass |
| DINOv2 | 0.6252 | [0.5989, 0.6493] | fail |

Critical per-template findings:
| Template / attacker | Gate statistic | 95% CI | Diagnosis |
| --- | ---: | ---: | --- |
| Parallel / frequency | 1.0000 | [1.0000, 1.0000] | deterministic semantic A/B assignment |
| Parallel / DINOv2 | 1.0000 | [1.0000, 1.0000] | same root cause |
| Triangle / DINOv2 | 0.5850 | [0.5083, 0.6655] | side-conditioned geometry distribution |
| Dense table / metadata | 0.5809 | [0.5091, 0.6545] | replacement/encoding distribution differs by side |

Problems:
- The first generator always assigned one semantic state to A and the counterfactual state to B. An attacker can therefore learn intended visual semantics, not only rendering artifacts.
- The gate's purpose requires directionally balanced sibling edits. Randomized release member order alone is insufficient because private source side remains predictable.

Decision:
- Reject the first candidate for artifact robustness.
- Keep all thresholds and corrected statistics unchanged.
- R2 randomizes semantic side assignment independently for every pair and template before packaging; rerun all attackers on that actual package.

Next actions:
- Add 200 fresh pairs each for coordinate register and header table, preserving template logic and balanced semantic-side randomization.
- Re-score expanded pairs, repackage with a new salt, and rerun all three attackers without changing thresholds.

Retained-package attempt:
- Run: `experiments/runs/artifact_gate_v02_an29_gpu0_20260709T235532Z`.
- Machine output: `reports/artifact_gate_v02_retained.json`.
- Package: `data/fliptrack_v02_retained`, 300 pairs, 100 per retained template.

| Scope / attacker | Gate statistic | 95% pair-bootstrap CI | Result |
| --- | ---: | ---: | --- |
| Pooled frequency/statistical | 0.5201 | [0.5026, 0.5369] | pass |
| Pooled metadata | 0.5142 | [0.5009, 0.5589] | pass |
| Pooled DINOv2 | 0.5078 | [0.5005, 0.5351] | pass |
| Coordinate / frequency | 0.5728 | [0.5388, 0.6091] | point fail |
| Coordinate / metadata | 0.5715 | [0.5084, 0.6470] | point fail; expansion required |
| Header / metadata | 0.5654 | [0.5057, 0.6394] | point fail; expansion required |

Diagnosis:
- DINOv2 passes pooled and per template; the retained package no longer has the deterministic semantic-side leak seen in parallel geometry.
- The failing coordinate frequency and header metadata OOF AUCs are below 0.5 before applying `max(AUC, 1-AUC)`, while every train fold selects the positive direction. This is unstable direction inversion, not evidence of a stable deployable classifier.
- The pre-registered statistic intentionally treats either direction as leakage, so this diagnosis does not override the failure. The CI rule requires more pairs for coordinate and header.

## R8 Expanded Candidate

Status:
- Run `experiments/runs/artifact_gate_v02_an29_gpu4_20260710T012945Z` completed with all three attackers available.
- Machine output: `reports/artifact_gate_v02_r8.json`.
- The unchanged gate fails only for chart metadata; P1.5 remains open.

| Scope / attacker | Gate statistic | 95% pair-bootstrap CI | Result |
| --- | ---: | ---: | --- |
| Pooled DINOv2 | 0.5019 | [0.5003, 0.5187] | pass |
| Pooled frequency | 0.5068 | [0.5003, 0.5205] | pass |
| Pooled metadata | 0.5031 | [0.5007, 0.5347] | pass |
| R7 geometry / metadata | 0.5144 | [0.5008, 0.5559] | pass |
| Document / metadata | 0.5326 | [0.5015, 0.5814] | pass |
| Chart / DINOv2 | 0.5365 | [0.5029, 0.5861] | pass |
| Chart / frequency | 0.5221 | [0.5012, 0.5574] | pass |
| Chart / metadata | 0.5840 | [0.5105, 0.6585] | point fail; expansion required |

Decision:
- Do not relax either threshold.
- Preserve R8 and generate one independent 300-pair R9 chart batch. Re-score the new batch before repackaging chart 400 + document 300 + geometry 300.
