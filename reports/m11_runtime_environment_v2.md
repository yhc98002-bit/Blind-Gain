# M11 Runtime Environment V2

Status:
- Runtime repair: `pass`; M11 remains `blocked` pending smoke and full-matrix execution.
- The isolated `.venv-m11` was repaired in place without modifying the EasyR1
  pilot environment.
- V1 evidence is retained. V2 adds the dependency and model-class import check
  that V1 omitted.

Evidence:
- Repair run:
  `experiments/runs/m11_runtime_repair_v2_login_20260715T174847Z`.
- Start/end: `2026-07-15T17:48:47Z` / `2026-07-15T17:52:27Z`; exit `0`.
- Git/config: `c1a548f05c6a9ee82e618e05a464c6a63a6c6649` /
  `16c39e5a8aa9bf89ddadb3a80e9d4366dba2b9d3902e660d52d82ffad5c3c2df`.
- Machine audit: `reports/m11_runtime_audit_v2.json`, SHA256
  `c562ae15883427aede5e0ae879c6a17f06eb68de21ddf52b002998a1b1232c8a`.
- Exact freeze: `reports/m11_runtime_freeze_v2.txt`, SHA256
  `fd37c92bbb8338175b613e0d4e2d973781ab3388f573804ae135ea2465a6f00d`.
- V2 requirements SHA256:
  `60b77c6e5fd3725131a1440408a001cb76118a3c1297b9e0b22dd2a8a92bd2c0`.
- Environment allocated size after repair: `5,672,059,694` bytes.

Checks:
| Check | Result |
| --- | --- |
| exact pinned versions | pass |
| CUDA runtime 11.8 | pass |
| Torch mask combinators import | pass |
| Gemma-3 conditional-generation class import | pass |
| local InternVL `InternVLChatModel` dynamic-class import | pass |

Problem:
- The failed V1 queue exposed `ModuleNotFoundError: No module named 'einops'`
  in InternVL's local `modeling_intern_vit.py`.
- The V1 verifier imported Gemma and common runtime packages but did not import
  InternVL's trusted local dynamic model class, so its pass status was too weak
  for the two-backend matrix.

Decision:
- Pin `einops==0.8.1` alongside the existing `timm==0.9.12` dependency.
- Require launchers to accept only schema
  `blind-gains.m11-runtime-audit.v2` and its exact freeze hash.
- Import the staged model class without loading weights as a mandatory runtime
  check. The import ran CPU-only on `an29`; it allocated no GPU memory.
- Retain the 156,998-byte v2 pip cache until smoke recovery is recorded; it is
  not a storage concern.

Next actions:
- Rerun only the three failed InternVL one-pair smoke cells in new immutable run
  directories.
- Keep the 18-cell full matrix closed until all six smoke outcomes are accepted
  mechanically and M2 checkpoint evaluations have capacity priority.
