# Layer-1 Canonical-v2 Legacy Rescore

Status:
- Complete for the ten historical real-image Layer-1 base cells. This is an L10 input artifact, not completion of L10.
- Every final rescore run is immutable, uses code commit `45a18bbcb43961964b697400c8cca169a6d3939b`, and resolves the prompt contract from the source run's hash-pinned config.

Evidence:
- Resolved contract SHA256: `44e40bc8372dc7b007f27a68f9705dce026bfd8e1b7937584ed18a30313ff5b4`.
- Parser: `canonical-v2`; contract resolution: `legacy-hash-pinned-run-config`.
- `Acc_final` exactly matches every predecessor table value. `Acc_strict` is recomputed as `contract_valid AND Acc_final`.

| Model | Benchmark | n | `Acc_final` | `Acc_strict` | Extractor valid | Contract valid | Scoring error |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen2.5-VL-3B | MMStar | 1,500 | 0.5540 | 0.0013 | 0.0013 | 0.0013 | 0.0013 |
| Qwen2.5-VL-7B | MMStar | 1,500 | 0.6320 | 0.0293 | 0.0440 | 0.0440 | 0.0013 |
| Qwen2.5-VL-3B | MathVista-testmini | 999 | 0.6236 | 0.1592 | 0.3183 | 0.3023 | 0.0000 |
| Qwen2.5-VL-7B | MathVista-testmini | 999 | 0.6627 | 0.3233 | 0.5546 | 0.5546 | 0.0000 |
| Qwen2.5-VL-3B | BLINK | 1,901 | 0.4929 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Qwen2.5-VL-7B | BLINK | 1,901 | 0.5565 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Qwen2.5-VL-3B | HallusionBench | 1,129 | 0.5979 | 0.3880 | 0.6678 | 0.6678 | 0.0000 |
| Qwen2.5-VL-7B | HallusionBench | 1,129 | 0.6829 | 0.3729 | 0.5686 | 0.5686 | 0.0000 |
| Qwen2.5-VL-3B | MMVP | 300 | 0.6600 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Qwen2.5-VL-7B | MMVP | 300 | 0.7433 | 0.0000 | 0.0033 | 0.0033 | 0.0000 |

Final run directories:
- `experiments/runs/vlmevalkit_postprocess_l10_mmstar{3b,7b}_canonicalv2_final_20260711T132325Z`
- `experiments/runs/vlmevalkit_postprocess_l10_blink{3b,7b}_canonicalv2_final_20260711T132325Z`
- `experiments/runs/vlmevalkit_postprocess_l10_mathvista{3b,7b}_canonicalv2_final_20260711T132325Z`
- `experiments/runs/vlmevalkit_postprocess_l10_hallusion{3b,7b}_canonicalv2_final_20260711T132325Z`
- `experiments/runs/vlmevalkit_postprocess_l10_mmvp3b_canonicalv2_final_20260711T132326Z`
- `experiments/runs/vlmevalkit_postprocess_l10_mmvp7b_canonicalv2_final_20260711T132326Z`

Problems:
- MMStar rows `268` and `273` have gold label `A` but no option `A`. They remain in the 1,500-row denominator as incorrect and are marked `gold_label_missing_from_options`; they are not silently discarded.
- Initial MMStar rescoring runs at `20260711T131815Z` failed closed on those malformed rows. The `canonicalv2_retry` runs at `20260711T132018Z` exposed an MCQ-label precedence regression and are superseded. All four runs remain preserved.
- Historical source manifests predate embedded prompt-contract fields. The opt-in resolver verifies each manifest's `config_hash`, requires exactly one nonempty system prompt, and rejects a prompt without explicit answer tags.

Decision:
- Use only the `canonicalv2_final` runs above in the L10 successor table.
- Keep native benchmark metrics separate from canonical-v2 scores. MathVerse will not be labeled with its official judged metric unless a calibrated judge is run.

Next actions:
- Run MathVerse and MMMU for 3B and 7B under the embedded-contract L10 configs.
- Build the versioned full Layer-1 successor table after those four cells complete.
