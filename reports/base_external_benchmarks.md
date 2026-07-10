# Base External Benchmarks

Status:
- MMStar and BLINK are complete for Qwen2.5-VL-3B and 7B.
- MathVista-testmini inference is active with the local Qwen2.5-7B judge.
- Remaining Layer-1 cells are prepared or blocked as listed; P1.2 is not complete.

Evidence:
| Model | Benchmark | n | Harness metric | `Acc_final` | `Acc_strict` | Format valid | Ambiguous | Infer failures |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen2.5-VL-3B | MMStar | 1,500 | 0.5387 | 0.5540 | 0.0013 | 0.0013 | 0.0000 | 0 |
| Qwen2.5-VL-7B | MMStar | 1,500 | 0.6080 | 0.6320 | 0.0293 | 0.0440 | 0.0000 | 0 |
| Qwen2.5-VL-3B | MathVista-testmini | 999 | pending | pending | pending | pending | pending | pending |
| Qwen2.5-VL-7B | MathVista-testmini | 999 | pending | pending | pending | pending | pending | pending |
| Qwen2.5-VL-3B | BLINK | 1,901 | 0.4929 | 0.4929 | 0.0000 | 0.0000 | 0.0000 | 0 |
| Qwen2.5-VL-7B | BLINK | 1,901 | 0.5565 | 0.5565 | 0.0000 | 0.0000 | 0.0000 | 0 |
| Qwen2.5-VL-3B/7B | HallusionBench | pending | blocked | blocked | blocked | blocked | blocked | blocked |
| Qwen2.5-VL-3B/7B | MMVP | pending | blocked | blocked | blocked | blocked | blocked | blocked |

Run evidence:
- 3B: `experiments/runs/vlmevalkit_mmstar3b_adapted_an29_20260710T004416Z`; unified output `postprocessed_v2/metrics.json`.
- 7B: `experiments/runs/vlmevalkit_mmstar7b_adapted_an29_20260710T005355Z`; unified output `postprocessed_v2/metrics.json`.
- Both validation manifests report zero inference failures across all 1,500 rows.
- MathVista adapter: `experiments/runs/prepare_layer1_mathvista_retry_20260710T012824Z`.
- BLINK adapter: `experiments/runs/prepare_layer1_blink_20260710T012324Z`.
- BLINK 3B: `experiments/runs/vlmevalkit_blink3b_an29_20260710T015012Z`; unified output `postprocessed_v2/metrics.json`.
- BLINK 7B: `experiments/runs/vlmevalkit_blink7b_an29_20260710T015014Z`; unified output `postprocessed_v2/metrics.json`.
- Both BLINK validation manifests report zero inference and judge failures across all 1,901 rows.
- Active MathVista runs: `experiments/runs/vlmevalkit_mathvista3b_an29_20260710T021019Z` and `experiments/runs/vlmevalkit_mathvista7b_an29_20260710T021019Z`.
- Local judge: `experiments/runs/local_judge_an29_gpu2_20260710T020845Z`; deterministic smoke response is `<answer>4</answer>`.

Problems:
- `Acc_strict` is much lower than benchmark accuracy because the base checkpoints usually ignore the requested `<answer>` wrapper. BLINK predictions omit it on every row. This is the intended format decomposition, not a substitute benchmark score.
- Blind deltas are not reported yet. A gray image is not equivalent to image removal, so no gray result will be mislabeled as the registered blind protocol.
- MathVista item 781 is excluded because two options have identical text and the authoritative annotation has no answer-option label.

Decision:
- Preserve both scoring contracts and never mix them in one headline column.
- Mark missing cells as pending/blocked rather than treating them as zero.
- Label any later Geometry3K-trained checkpoint MathVista row `contamination: geo3k-source`.

Next actions:
- Fill MathVista cells from the active frozen-config runs.
- Acquire and adapt HallusionBench/MMVP.
- Run image-removed MMStar and MathVista after the blind prompt path passes fixtures.
