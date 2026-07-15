# Chart V08 Calibration Execution Status V4

Status:
- M12 remains `blocked`; no calibration, freeze, or scientific gate is declared.
- V4 supersedes the operational snapshot in V3 without modifying earlier versions.
- In addition to the V3 real/caption/necessity/attacker lifecycles, all four local
  gray/noise floor lifecycles are structurally complete and aggregated.
- Model-performance, floor, attacker, and necessity values remain unopened in this
  snapshot.

Evidence:
- Full prior lifecycle evidence is preserved in
  `reports/chart_v08_calibration_execution_status_v3.md` and its machine JSON.

| Floor cell | Node / placement | Rows | Run | Aggregate |
| --- | --- | ---: | --- | --- |
| Qwen2.5-VL-3B gray | `an29:5`, TP1 | 100 | `experiments/runs/chart_v08_calibration_qwen25vl3b_gray_an29_20260715T203000Z` | `experiments/runs/fliptrack_aggregate_chart_v08_qwen25vl3b_gray_20260715t203000z_20260715T203331Z` |
| Qwen2.5-VL-3B noise | `an29:6`, TP1 | 100 | `experiments/runs/chart_v08_calibration_qwen25vl3b_noise_an29_20260715T203000Z` | `experiments/runs/fliptrack_aggregate_chart_v08_qwen25vl3b_noise_20260715t203000z_20260715T203337Z` |
| Qwen2.5-VL-7B gray | `an29:7`, TP1 | 100 | `experiments/runs/chart_v08_calibration_qwen25vl7b_gray_an29_20260715T203000Z` | `experiments/runs/fliptrack_aggregate_chart_v08_qwen25vl7b_gray_20260715t203000z_20260715T203342Z` |
| Qwen2.5-VL-7B noise | `an29:5`, TP1 | 100 | `experiments/runs/chart_v08_calibration_qwen25vl7b_noise_an29_20260715T203315Z` | `experiments/runs/fliptrack_aggregate_chart_v08_qwen25vl7b_noise_20260715t203315z_20260715T203610Z` |

- Every run used the same frozen 100-pair manifest, locked prompt contract, greedy
  decoding, 32-token cap, and fixed seed as the real-image cells.
- Every run and aggregate completed with all expected artifacts present.

Problems:
- The 100-pair no-zoom human-legibility audit is pending.
- The 72B strong-captioner stress is pending and requires a four-GPU serving window.
- Calibration values, attacker values, and the necessity effect remain intentionally
  uninterpreted until the human-audit record lands.
- Freeze and one-shot confirmatory generation remain prohibited.

Decision:
- Preserve the four floor runs and aggregates unchanged.
- Do not add no-image cells post hoc; the declared local floor controls are gray and
  noise.
- Keep any four-GPU strong-caption window subordinate to M2 checkpoint evaluation.

Next actions:
- Complete the no-zoom human audit.
- Run the 72B strong-caption stress when four GPUs can be reserved without delaying
  M2.
- Publish registered calibration readouts only after the human-audit record lands.
- Freeze v08 only if every registered criterion holds; otherwise preserve the failed
  calibration and do not mint a confirmatory split.

Machine-readable companion:
- `reports/chart_v08_calibration_execution_status_v4.json`.
