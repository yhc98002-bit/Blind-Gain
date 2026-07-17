# Paper 1 Pipeline Status V8

Status:
- Paper-artifact integration status: `pass`.
- The post-seed-1 visual-evidence ranking diagnostic now occupies a versioned
  result slot and is explicitly separated from the original pilot endpoints.
- This is not a scientific gate decision and does not assign B1/B2/B3.

Checks:
| Check | Result |
| --- | --- |
| V7 evidence retained and machine status pass | `true` |
| Diagnostic label says post-seed-1 and not an original endpoint | `true` |
| Geometry primary margin is exactly `+0.1501417384828839` | `true` |
| Geometry pair-success effect is exactly `0.0` | `true` |
| Geometry candidate top-1 effect is exactly `+0.008333333333333333` | `true` |
| Input-integrity, builder, and independent audits pass | `true` |
| Branch assignment remains null | `true` |
| Internal-perception claim made | `false` |

Evidence:
- Machine status: `reports/paper1_pipeline_status_v8.json`.
- Master slot: `docs/paper1/master_result_table.md`, SHA256
  `75508789c5ee0b0b50c6779f2985e4156144eb58968857b6f429874445cd713b`.
- Diagnostic machine result: SHA256
  `f73792c0a5d670419b5e8d0f90fdb333b48a0491d691cc1bccb619d79533594b`.
- Independent audit: SHA256
  `9e9f797ddf16e9fa8cca49e83f3bb46abba9b8081c22ffa2f33f212022c0e477`.

Decision:
- V8 supersedes V7 only as the current Paper-1 pipeline-status artifact; all prior
  versions remain immutable.
- Carry both the positive geometry margin and the nearly unchanged discrete
  candidate outcomes. Do not collapse them into one mechanism claim.
