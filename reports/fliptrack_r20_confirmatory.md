# FlipTrack R20 Confirmatory Instrument

Status:
- The one-shot R20 pipeline is complete; this report records automated criterion outcomes and does not declare a PI gate passed.
- Generator-level automated outcome: `one-or-more-templates-downgraded-to-R19-selected`.
- Machine status JSON: `reports/fliptrack_r20_confirmatory.json`.

Interpretation rule:
- R20 is confirmatory. A template failing here has its certification downgraded to R19-selected; we do not mint R21. Generator-level pass = R20 meets the pre-frozen criteria without selection.

Evidence:
- Release manifest: `data/fliptrack_r20/manifest.jsonl`, SHA256 `be033f67bd78d6207fb6dd1a3156810f3515416203b48fc65ae59334308255b4`.
- Linter: `reports/fliptrack_r20_lint.json`; grouped attackers: `reports/artifact_gate_r20.json`.
- Every cell covers the same 1,200 opaque pair IDs: document 300, geometry 600, chart 300.
- Caption stores are question-blind, greedy, fixed at 384 tokens; QA is greedy with 32 output tokens.

Hardness cells:
| Template | 3B real | 7B real | 3B gray | 7B gray | 3B noise | 7B noise | 3B caption | 7B caption | Outcome |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| document | 0.8667 | 0.9967 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0200 | 0.0633 | generator-level-pass |
| geometry | 0.3967 | 0.7567 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0117 | 0.0100 | downgrade-to-R19-selected |
| chart | 0.3900 | 0.6233 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0067 | downgrade-to-R19-selected |

3B degradation control:
| Template | Real | Mild | Medium | Severe | Gray | Nonincreasing |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| document | 0.8667 | 0.6767 | 0.6533 | 0.2033 | 0.0000 | true |
| geometry | 0.3967 | 0.3450 | 0.2417 | 0.0050 | 0.0000 | true |
| chart | 0.3900 | 0.1933 | 0.1533 | 0.0000 | 0.0000 | true |

Problems:
- Automated checks cannot establish legibility, naturalness, or semantic uniqueness; the second human contact-sheet audit is separate.
- R20 is one-shot confirmatory evidence. No failed template is regenerated or replaced in this round.

Decision:
- Preserve the per-template automated outcomes exactly as reported. No R21 is authorized by this workflow.
- Treat final human acceptance and any prelaunch gate decision as PI responsibilities.

Next actions:
- Complete the representative R20 human contact-sheet audit and record pair IDs for any semantic or legibility failures.
