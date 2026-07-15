# M11 Generalization Execution Queue Status V8

Status:
- M11 remains `blocked`.
- The V7 claim that the queue was live and waiting is superseded: that queue
  subsequently opened after both blind arms completed, ran six smoke cells,
  and finalized `fail` because three InternVL cells failed.
- Runtime V2 now passes; fresh InternVL smoke runs are next. No full cell has
  run.

Evidence:
- Retained failed queue:
  `experiments/runs/m11_generalization_queue_login_20260713T111601Z`.
- Queue start/end: `2026-07-13T11:16:01Z` /
  `2026-07-14T16:58:10Z`; exit `1`.
- Final state: three Gemma smoke cells `complete`, three InternVL smoke cells
  `fail`, and all 18 full cells `pending`.
- Queue manifest/state SHA256:
  `457e3bc020246e616c2949a0a87929383d037ec61df50b94a095f9a21449e60c` /
  `c46cf9e5c258d2c0b2bea4ebabce5b3e7f07e98bf1d69423d2103d6192efc1d7`.
- Root cause and repaired runtime evidence:
  `reports/m11_runtime_environment_v2.md`.

Problem:
- InternVL's trusted local model code imports `einops`; the V1 environment did
  not provide it, and V1's machine audit did not import that model class.

Decision:
- Preserve every V1 smoke run and queue outcome.
- Do not reinterpret the three successful Gemma smoke cells as a six-cell
  barrier pass.
- Run fresh InternVL smoke cells against the V2 audit/freeze, then decide the
  full-matrix launch mechanically while preserving M2 evaluation priority.

Next actions:
- Launch InternVL real, no-image, and fixed-caption one-pair cells on separate
  free `an29` GPUs with TP1.
- Publish `reports/m11_smoke_recovery_v1.md` from manifest/artifact validity,
  without reporting smoke-item performance.
