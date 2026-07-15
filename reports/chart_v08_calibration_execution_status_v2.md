# Chart V08 Calibration Execution Status V2

Status:
- M12 remains `blocked`; no calibration, freeze, or scientific gate is declared.
- V2 supersedes the operational snapshot in V1 without modifying it.
- The frozen 100-pair calibration manifest now has structurally complete 3B-real,
  7B-real, 3B-caption, and 7B-caption evaluation lifecycles.
- The frozen 200-row no-star/random-star necessity manifest has a structurally
  complete 7B-real lifecycle.
- Model-performance fields were not opened or interpreted while this snapshot was
  assembled.

Evidence:
- Calibration manifest:
  `data/fliptrack_chart_v08_calibration_v1_manifest.jsonl`, 100 pairs, SHA256
  `d90f3f13c1f3304669c8ca6c717ae58eaa7cfe4e785fab3bae8520e15065c292`.
- Necessity manifest:
  `data/fliptrack_chart_v08_calibration_v1_necessity_eval_manifest_v1.jsonl`,
  200 rows, SHA256
  `797f8545a283563921469976c716805f288f36062b369fb6f1b6d1e79b5f56cb`.
- Human package:
  `reports/review_packages/blind_gains_chart_v08_calibration_human_audit_20260715_v1.zip`,
  SHA256
  `ea4473d3148121d87f50bde36c8417cf22875472af166fd714b87904b483bf24`.

| Cell | Node / placement | Rows | Lifecycle evidence |
| --- | --- | ---: | --- |
| Qwen2.5-VL-3B real | `an29:4-7`, 4 x TP1 | 100 | `experiments/runs/chart_v08_calibration_qwen25vl3b_real_an29_20260715T185645Z`; aggregate `experiments/runs/fliptrack_aggregate_chart_v08_qwen25vl3b_real_20260715T190101Z` |
| Qwen2.5-VL-7B real | `an12:4-5`, 2 x TP1 | 100 | `experiments/runs/chart_v08_calibration_qwen25vl7b_real_an12_20260715T192600Z`; aggregate `experiments/runs/fliptrack_aggregate_chart_v08_qwen25vl7b_real_20260715t192600z_20260715T193220Z` |
| Qwen2.5-VL-3B captions | `an12:4-7`, 4 x TP1 | 100 | `experiments/runs/chart_v08_calibration_qwen25vl3b_captions_an12_20260715T195700Z` |
| Qwen2.5-VL-3B caption QA | `an12:4-7`, 4 x TP1 | 100 | `experiments/runs/chart_v08_calibration_qwen25vl3b_caption_qa_an12_20260715T200405Z`; aggregate `experiments/runs/fliptrack_aggregate_chart_v08_qwen25vl3b_caption_qa_20260715t200405z_20260715T200452Z` |
| Qwen2.5-VL-7B captions | `an12:4-7`, 4 x TP1 | 100 | `experiments/runs/chart_v08_calibration_qwen25vl7b_captions_an12_20260715T194147Z` |
| Qwen2.5-VL-7B caption QA | `an12:4-7`, 4 x TP1 | 100 | `experiments/runs/chart_v08_calibration_qwen25vl7b_caption_qa_an12_20260715T194628Z`; aggregate `experiments/runs/fliptrack_aggregate_chart_v08_qwen25vl7b_caption_qa_20260715t194628z_20260715T194847Z` |
| Qwen2.5-VL-7B necessity | `an12:4-7`, 4 x TP1 | 200 | `experiments/runs/chart_v08_necessity_qwen25vl7b_real_an12_20260715T194950Z`; aggregate `experiments/runs/fliptrack_aggregate_chart_v08_necessity_qwen25vl7b_real_20260715t194950z_20260715T195243Z` |

Problems:
- The 100-pair no-zoom human-legibility audit is pending.
- The strong-captioner, attacker, and necessity-effect gates are pending.
- The caption-generation manifests do not stamp the question-blind prompt hash.
  Every caption row preserves the exact prompt text, so this remains an operational
  provenance deviation rather than an in-place repair.
- Calibration cannot freeze and the one-shot confirmatory split cannot be minted
  until all registered gates are evaluated.

Decision:
- Preserve all completed runs and aggregates without opening headline metrics.
- Keep R19 immutable and keep answer-pointing cues prohibited for the v08 two-hop
  construct.
- Give M2 retention and registered checkpoint evaluations priority over remaining
  M12 GPU cells.

Next actions:
- Complete the no-zoom human audit using the portable package.
- Run the strong-captioner and attacker cells on genuinely free permanent-node
  capacity.
- Compute the preregistered star-ablation necessity contrast only after input
  lifecycle and human-audit checks are complete.
- Freeze v08 only if all registered criteria hold; otherwise preserve the failed
  calibration as evidence and do not mint a confirmatory split.

Machine-readable companion:
- `reports/chart_v08_calibration_execution_status_v2.json`.
