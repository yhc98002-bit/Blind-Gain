# Paper 1 Pipeline Status V7

Status:
- M13 reusable-pipeline and result-slot control status: `pass`.
- The two requested seed-1 values are carried without mechanism interpretation.
- Chart-delta rendering is now bound to the audited registered null.
- Machine status JSON: `reports/paper1_pipeline_status_v7.json`.

Checks:
| Check | Result |
| --- | --- |
| V6 evidence retained and machine status pass | `true` |
| A2-gray R19 geometry delta is exactly `-0.045` | `true` |
| `D_caption^final` is exactly `-0.108` | `true` |
| Both values use `registered seed-1 result; confirmation pending seeds 2–3` | `true` |
| R19 null has 36 complete cells and independent audit pass | `true` |
| Dissociation spec pins the null SHA256 | `true` |
| Builder rejects any chart-delta figure lacking that input | `true` |
| Scientific interpretation made | `false` |

Evidence:
- Seed-1 slots: `docs/paper1/master_result_table.md`, SHA256
  `c3f4cb4577032ed7f781fc9d92a8f2dab8e4247b8d0587bc182fda996ef3e164`.
- Figure spec: `docs/paper1/figure_specs.json`, SHA256
  `501742cfe79c9c96ef3a38fe592585bbae2d3784333c4f58f73e8557ac301059`.
- Registered null: `reports/pilot_4arm_seed1_r19_null_v1.json`, SHA256
  `5c8bb51bfca8a9175c8ad7f4efd9d8d8f80e56d3595f3f1c9f30645a7d9c4f78`.
- Independent null audit:
  `reports/pilot_4arm_seed1_r19_null_v1_audit.json`, SHA256
  `cb9be5b4fd2b8caa7492e2921775c93e9916cf0054dedda371056609526661cc`.

Decision:
- V7 supersedes V6 only as the current pipeline-status artifact; V6 remains
  immutable.
- Multi-seed result slots remain unresolved. The two seed-1 values are not
  converted into final mechanism claims.
