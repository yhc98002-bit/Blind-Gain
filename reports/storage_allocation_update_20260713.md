# Storage Allocation Update, 2026-07-13

Status:
- Supersedes the 500-GiB quota assumption used by the prelaunch storage guard.
- PI-reported persistent allocation is 1.5 TiB for
  `/XYFS02/HDD_POOL/paratera_xy/pxy1289`.
- Guard default is conservatively set to 1,500 GiB
  (1,610,612,736,000 bytes), retaining the 20-GiB floor.

Evidence:
| Tier | Used | Capacity | Available |
| --- | ---: | ---: | ---: |
| HDD_POOL persistent | 474.1 G reported | 1.5 T | approximately 1.0 T |
| HOME persistent | 70 G | 100 G | approximately 31 G |
| login `/tmp` | n/a | local | approximately 329 G |
| login `/dev/shm` | n/a | ephemeral | approximately 126 G |

Conservative cross-check:
- The latest project-side allocated-byte snapshot measured
  532,899,221,504 bytes across the quota root.
- Against the updated 1,500-GiB guard capacity, that leaves
  1,077,713,514,496 bytes before new writes, far above the 20-GiB floor.
- The measurement script now imports the same quota constant as the guard,
  eliminating the prior duplicated 500-GiB literal.

Reclamation stop:
- The previously registered completed-evaluation cache relocation was stopped
  after 12 of 22 trees.
- All 12 completed relocations have per-file SHA256 manifests under
  `reports/storage_relocations/20260712/`.
- The interrupted 13th source remains intact; no partial destination remains.
- No further cache, model, dataset, or checkpoint relocation is needed for M2.
- Already relocated caches remain re-derivable Tier-T artifacts as allowed by
  the earlier PI instruction; their canonical predictions and metrics remain
  persistent.

Decision:
- Shared storage is not an M2 blocker.
- Checkpoint saves continue to invoke the 20-GiB floor guard with the updated
  allocation.
