# Artifact Gate V0.1

Status:
- First artifact attacker gate is implemented at `src/fliptrack/artifact_attackers.py`.
- Gate result is `fail` for metadata/path leakage and `partial` for DINOv2, pending model cache/download.

Evidence:
- Run: `experiments/runs/artifact_gate_v01_20260708T044741Z`
- Metrics: `experiments/runs/artifact_gate_v01_20260708T044741Z/metrics.json`

Metrics:
- `n_pairs`: 300
- `n_members`: 600
- split: by pair/template group
- frequency/statistical AUC: `0.4208`
- metadata/path AUC: `1.0000`
- DINOv2 status: unavailable in first run
- best attacker AUC: `1.0000`

Interpretation:
- The metadata probe trivially detects pair member side because filenames end in `_a.png` and `_b.png`.
- This is not acceptable for a frozen benchmark, even if models never see paths during normal evaluation.
- Frequency/statistical features are near/below chance on this split, but the metadata leak dominates.

Decision:
- Do not claim artifact robustness.
- V0.1 is acceptable as a recovery hardness instrument, not as a release candidate.

Next actions:
- Randomize image and mask filenames independent of pair side.
- Rerun metadata/frequency/DINOv2 attacker after DINOv2 is cached.
