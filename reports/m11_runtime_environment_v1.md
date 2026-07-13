# M11 Runtime Environment V1

Status:
- Isolated M11 inference runtime: `pass`.
- This closes environment preparation only. M11 remains `blocked` until six
  smoke cells, 18 full cells, and the registered final report complete.
- The active EasyR1 pilot `.venv` was not modified.

Evidence:
- Successful setup run:
  `experiments/runs/m11_runtime_setup_login_20260713T102407Z`.
- Start: `2026-07-13T10:24:07Z`; end: `2026-07-13T11:00:44Z`; exit code: 0.
- Setup Git: `c26ac320a9e8660dc4f3c15ab81711ec2071c5bc`.
- Setup config hash:
  `5f37f31a4ee997c3a33698a6665aaf5bcc6962de3f8beae6839e262bbdf16829`.
- Machine audit: `reports/m11_runtime_audit_v1.json`, SHA256
  `44aa1074580a9994b2e4aebb9167d9f1b09f49e1f15f21035253d457018da0cc`.
- Exact freeze: `reports/m11_runtime_freeze_v1.txt`, SHA256
  `d845a9db2e5e27acc3878a648510961ce4df3375c071666d976455fdbe48cb14`.
- Top-level requirements SHA256:
  `f5f0ab9e8d39f65c619f9fb5ab9fc33d4e7cc1dd64655b7e21a0a9b627b1675b`.
- Environment path: `.venv-m11`; allocated size: 5,738,835,968 bytes.

Machine checks:
| Check | Result |
| --- | --- |
| exact pinned versions | pass |
| CUDA runtime is 11.8 | pass |
| Torch mask combinators available | pass |
| Gemma3 conditional-generation class importable | pass |

Node read-back:
- an29 imported Torch, Torchvision, Transformers, Accelerate, timm, Torch mask
  combinators, and `Gemma3ForConditionalGeneration` from `.venv-m11` with
  `CUDA_VISIBLE_DEVICES` empty.
- Observed versions exactly matched the table below and
  `torch.cuda.is_available()` was false, confirming the read-back allocated no GPU.

Pinned runtime:
| Package | Version |
| --- | --- |
| Torch | `2.6.0+cu118` |
| Torchvision | `0.21.0+cu118` |
| Transformers | `4.56.2` |
| Accelerate | `1.14.0` |
| timm | `0.9.12` |

Failure retention:
- The first setup run failed before download because system `venv` lacked
  `ensurepip`; see `reports/m11_runtime_setup_failure_v1.md`.
- The successful retry used the explicit user `virtualenv` executable.
- The setup encountered one transient SSL EOF while fetching metadata; pip's
  bounded retry recovered without manual mutation.

Scratch cleanup:
- Disposable pip cache: `/tmp/blind-gains-m11-pip-cache`.
- Allocated size before deletion: 2,938,847,232 bytes.
- Classification: setup-complete and retention-expired; exact installed state is
  preserved by the freeze and environment, so this cache is not an artifact.
- This report lists the cache before deletion.
- Deletion completed at `2026-07-13T11:02:21Z`; the cache path was absent on the
  immediate read-back check.

Decision:
- Require the machine audit and freeze hashes in the queue and every child run.
- Keep M11 capacity-gated behind the pilot; do not run a smoke cell while an29 is
  pilot-owned.

Next actions:
- Delete the retention-expired pip cache.
- Commit the audit, freeze, and this report.
- Launch a fresh immutable M11 queue, which should remain in capacity-wait state.
