# Artifact Gate V0.2

Status:
- The corrected attacker implementation is complete and DINOv2 ran successfully.
- The first V0.2 candidate fails the pre-registered gate. P1.5 remains open pending R2 repackaging and rerun.

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
- Finish R2 hardness calibration and select candidate templates.
- Package the retained R2 set with a new salt and rerun metadata, frequency, and DINOv2 attacks.
- Expand any template whose CI upper bound remains above 0.62.
