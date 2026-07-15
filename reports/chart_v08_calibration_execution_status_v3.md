# Chart V08 Calibration Execution Status V3

Status:
- M12 remains `blocked`; no calibration, freeze, or scientific gate is declared.
- V3 supersedes the operational snapshot in V2 without modifying V1 or V2.
- The local 3B/7B real, local 3B/7B question-blind-caption, 7B necessity,
  and grouped artifact-attacker lifecycles are structurally complete.
- Model-performance and attacker-value fields remain unopened in this snapshot.

Evidence:
- The full local model-cell matrix is preserved in
  `reports/chart_v08_calibration_execution_status_v2.md` and its machine JSON.
- Artifact attacker run:
  `experiments/runs/chart_v08_artifact_gate_an12_gpu4_20260715T201107Z`.
- Placement: `an12:4`, one TP1 replica; DINOv2 revision
  `ed25f3a31f01632728cabb09d1542f84ab7b0056`.
- The run completed with exit code 0 and all expected artifacts present.
- Run-manifest SHA256:
  `0f17a4a5a0d144e560ac934cc536ff4728c2dfbd3fd7a876aa8e6cbf81fbaf49`.
- Metrics-artifact SHA256:
  `cd0afcc2f00d399cf0e02012901ddce6fbd2caf872ecfe8479e9dbd49a40bbaa`.
- The attacker launcher and adversarial permanent-node fixture are committed at
  `a305781ac191410d397521815bfe08d22c67473e`; seven focused tests passed.

Problems:
- The 100-pair no-zoom human-legibility audit is pending.
- The strong-captioner stress is pending.
- Artifact-gate values and the necessity-effect values are intentionally not
  interpreted before the human-audit record lands.
- Freeze and one-shot confirmatory generation remain prohibited.

Decision:
- Preserve all completed lifecycle artifacts unchanged.
- Keep remaining GPU work subordinate to M2 retention and registered checkpoint
  evaluations.
- Do not turn a structurally complete attacker job into a scientific pass claim;
  PIs audit the eventual gate readout.

Next actions:
- Complete the no-zoom human audit using the portable package.
- Run the strong-captioner stress in a window that cannot delay M2.
- Publish the registered local-cell, attacker, and necessity readouts only after
  the human-audit record lands.
- Freeze v08 only if all registered criteria hold; otherwise preserve the failed
  calibration and do not mint a confirmatory split.

Machine-readable companion:
- `reports/chart_v08_calibration_execution_status_v3.json`.
