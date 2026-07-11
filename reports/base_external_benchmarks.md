# Gate-2 Layer-1 Subset

Status:
- MMStar, MathVista-testmini, BLINK, HallusionBench, and MMVP are complete for Qwen2.5-VL-3B and 7B.
- This is the frozen Gate-2 Layer-1 subset; MathVerse and MMMU rows are owed by prelaunch task L10.
- Unified parser fields and native harness metrics are retained separately.

Evidence:
Registered members: `MMStar`, `MathVista-testmini`, `BLINK`, `HallusionBench`, `MMVP`, `MathVerse`, `MMMU`
Reported members: `MMStar`, `MathVista-testmini`, `BLINK`, `HallusionBench`, `MMVP`

| Model | Benchmark | n | Harness metric | `Acc_final` | `Acc_strict` | Format valid | Ambiguous | Infer failures |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen2.5-VL-3B | MMStar | 1,500 | 0.5387 | 0.5540 | 0.0013 | 0.0013 | 0.0000 | 0 |
| Qwen2.5-VL-7B | MMStar | 1,500 | 0.6080 | 0.6320 | 0.0293 | 0.0440 | 0.0000 | 0 |
| Qwen2.5-VL-3B | MMStar image-removed | 1,500 | n/a | 0.2607 | 0.0153 | 0.0373 | 0.0007 | 0 |
| Qwen2.5-VL-7B | MMStar image-removed | 1,500 | n/a | 0.2880 | 0.2140 | 0.7633 | 0.0007 | 0 |
| Qwen2.5-VL-3B | MathVista-testmini | 999 | 0.6226 | 0.6236 | 0.1672 | 0.3183 | 0.0000 | 0 |
| Qwen2.5-VL-7B | MathVista-testmini | 999 | 0.6607 | 0.6627 | 0.3233 | 0.5546 | 0.0000 | 0 |
| Qwen2.5-VL-3B | MathVista-testmini image-removed | 999 | n/a | 0.3293 | 0.1391 | 0.6186 | 0.0000 | 0 |
| Qwen2.5-VL-7B | MathVista-testmini image-removed | 999 | n/a | 0.3393 | 0.1331 | 0.5295 | 0.0000 | 0 |
| Qwen2.5-VL-3B | BLINK | 1,901 | 0.4929 | 0.4929 | 0.0000 | 0.0000 | 0.0000 | 0 |
| Qwen2.5-VL-7B | BLINK | 1,901 | 0.5565 | 0.5565 | 0.0000 | 0.0000 | 0.0000 | 0 |
| Qwen2.5-VL-3B | HallusionBench | 1,129 | 0.5979 | 0.5979 | 0.3880 | 0.6678 | 0.0000 | 0 |
| Qwen2.5-VL-7B | HallusionBench | 1,129 | 0.6829 | 0.6829 | 0.3729 | 0.5686 | 0.0000 | 0 |
| Qwen2.5-VL-3B | MMVP | 300 | 0.6600 | 0.6600 | 0.0000 | 0.0000 | 0.0000 | 0 |
| Qwen2.5-VL-7B | MMVP | 300 | 0.7433 | 0.7433 | 0.0000 | 0.0033 | 0.0000 | 0 |

Run evidence:
- 3B: `experiments/runs/vlmevalkit_mmstar3b_adapted_an29_20260710T004416Z`; unified output `postprocessed_v2/metrics.json`.
- 7B: `experiments/runs/vlmevalkit_mmstar7b_adapted_an29_20260710T005355Z`; unified output `postprocessed_v2/metrics.json`.
- Both validation manifests report zero inference failures across all 1,500 rows.
- MathVista adapter: `experiments/runs/prepare_layer1_mathvista_retry_20260710T012824Z`.
- BLINK adapter: `experiments/runs/prepare_layer1_blink_20260710T012324Z`.
- BLINK 3B: `experiments/runs/vlmevalkit_blink3b_an29_20260710T015012Z`; unified output `postprocessed_v2/metrics.json`.
- BLINK 7B: `experiments/runs/vlmevalkit_blink7b_an29_20260710T015014Z`; unified output `postprocessed_v2/metrics.json`.
- Both BLINK validation manifests report zero inference and judge failures across all 1,901 rows.
- HallusionBench adapter: `experiments/runs/prepare_layer1_hallusion_local_v2_20260710T032525Z`; 1,129 rows, including 178 text-only controls represented by a deterministic blank placeholder.
- HallusionBench 3B/7B: `experiments/runs/vlmevalkit_hallusion3b_v2_an29_20260710T033006Z` and `experiments/runs/vlmevalkit_hallusion7b_v2_an29_20260710T033007Z`; native `aAcc/fAcc/qAcc` are 59.79/27.66/24.94 and 68.29/36.97/34.03.
- MMVP adapter: `experiments/runs/prepare_layer1_mmvp_local_v2_20260710T032520Z`; 300 rows preserving 150 adjacent official pairs.
- MMVP 3B/7B: `experiments/runs/vlmevalkit_mmvp3b_v2_an29_20260710T033004Z` and `experiments/runs/vlmevalkit_mmvp7b_v2_an29_20260710T033005Z`; native row accuracy is 0.6600/0.7433, while unified paired accuracy is 0.3667/0.5133.
- MathVista inference/evaluation: `experiments/runs/vlmevalkit_mathvista3b_an29_20260710T021019Z` and `experiments/runs/vlmevalkit_mathvista7b_an29_20260710T021019Z`.
- Those parent manifests are preserved as `fail`: inference and local-judge evaluation completed, but the old validator incorrectly required `*_acc.csv`; MathVista emits `*_score.csv`.
- Validator recovery: `experiments/runs/vlmevalkit_validation_recovery_mathvista3b_20260710T021941Z` and `experiments/runs/vlmevalkit_validation_recovery_mathvista7b_20260710T021941Z`.
- Unified MathVista postprocessing: `experiments/runs/vlmevalkit_postprocess_mathvista3b_20260710T022024Z` and `experiments/runs/vlmevalkit_postprocess_mathvista7b_20260710T022024Z`.
- Local judge: `experiments/runs/local_judge_an29_gpu2_20260710T020845Z`; deterministic smoke response is `<answer>4</answer>`. It was stopped after both scoring jobs completed.
- Image-removed runs: `experiments/runs/layer1_blind_{mmstar3b,mmstar7b,mathvista3b,mathvista7b}_an29_20260710T023019Z`.
- Every blind run has a complete manifest, zero missing predictions, and the protocol marker `blind-gains.layer1-image-removed.v1`.

Registered blind deltas:
| Model | Benchmark | Real `Acc_final` | Image-removed `Acc_final` | Blind delta (blind - real) |
| --- | --- | ---: | ---: | ---: |
| Qwen2.5-VL-3B | MMStar | 0.5540 | 0.2607 | -0.2933 |
| Qwen2.5-VL-7B | MMStar | 0.6320 | 0.2880 | -0.3440 |
| Qwen2.5-VL-3B | MathVista-testmini | 0.6236 | 0.3293 | -0.2943 |
| Qwen2.5-VL-7B | MathVista-testmini | 0.6627 | 0.3393 | -0.3233 |

Problems:
- `Acc_strict` is much lower than benchmark accuracy because the base checkpoints usually ignore the requested `<answer>` wrapper. BLINK predictions omit it on every row. This is the intended format decomposition, not a substitute benchmark score.
- The blind path uses the same Qwen checkpoints and vLLM version but a dedicated runner rather than VLMEvalKit's image dataset class. Prompt text, options, system prompt, maximum tokens, and greedy decoding are locked; only the image message/tokens/tensors are absent.
- MathVista item 781 is excluded because two options have identical text and the authoritative annotation has no answer-option label.
- The MathVista harness score uses its local-judge evaluator. `Acc_final` independently applies the unified answer-span matcher to raw predictions; the small difference is retained rather than reconciled away.

Decision:
- Preserve both scoring contracts and never mix them in one headline column.
- Register true image removal, not gray pixels: retain question references to the image verbatim, but send no image message, image token, or image tensor.
- Mark missing cells as pending/blocked rather than treating them as zero.
- Label any later Geometry3K-trained checkpoint MathVista row `contamination: geo3k-source`.

Next actions:
- Add image-removed HallusionBench/MMVP only as a later extension; the proposal's registered blind cells remain MMStar and MathVista.
- Add MathVerse and MMMU for both model sizes in L10 and publish canonical-v2 `extractor_valid` and `contract_valid` columns in a versioned successor table.
