# Document V-Next Calibration

Status:
- The single declared 100-pair L11 batch and all three registered cells are complete.
- Calibration verdict: `too-easy`. The 7B-real target was [0.50, 0.90] and the observed pair accuracy was 1.0000.
- This is a calibration outcome, not a PI gate declaration.

Evidence:
- Source manifest: `data/fliptrack_document_vnext_calibration_manifest.jsonl`, SHA256 `8b7cb91f54af62092197b4c9f2eb8d785e3f9cebe60c7ef6f0cd58ed77cc7dc6`.
- Machine report: `reports/document_v_next_calibration.json`.
- Template: `dense_control_register_code_v01`; seed `20261101`; pairs `100`.

| Cell | Pair accuracy | Member accuracy | Collapse rate |
|---|---:|---:|---:|
| Qwen2.5-VL-3B real | 0.6900 | 0.7250 | 0.2000 |
| Qwen2.5-VL-7B real | 1.0000 | 1.0000 | 0.0000 |
| Qwen2.5-VL-7B caption | 0.0400 | 0.0750 | 0.5800 |

Problems:
- A result outside the target range means this declared family did not achieve the intended 7B difficulty. It is reported as observed and is not repaired by selection.

Decision:
- Preserve the one-shot result. Iteration policy: `one declared batch; no regeneration or threshold change in this round`.
- Do not generate a second L11 batch in this round.

Next actions:
- Carry this calibration result into instrument limitations and defer any redesign to a separately preregistered round.
