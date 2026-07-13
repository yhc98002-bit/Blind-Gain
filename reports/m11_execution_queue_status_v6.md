# M11 Generalization Execution Queue Status V6

Status:
- M11 remains `blocked` and queued behind the pilot as directed.
- The live queue is `waiting_pilot_release`; all 24 cells are pending and no
  capacity poll or child evaluation has run.

Evidence:
- Queue:
  `experiments/runs/m11_generalization_queue_login_20260713T111601Z`.
- Start: `2026-07-13T11:16:01Z`; node: login; GPU allocation: none.
- Git: `e940994953877f151494574de306c9e38fe7d6fd`.
- Config SHA256:
  `e867fe1c0cfffb64d02f4e9fc755aff8333f3d5041b3cab64456d02796cbba26`.
- Runtime-audit SHA256:
  `44aa1074580a9994b2e4aebb9167d9f1b09f49e1f15f21035253d457018da0cc`.
- Runtime-freeze SHA256:
  `d845a9db2e5e27acc3878a648510961ce4df3375c071666d976455fdbe48cb14`.
- Release checks at `2026-07-13T11:16:01Z` and `2026-07-13T11:21:01Z` see A2b
  retry 2 and A3 caption as `running`, so `pilot_release_ready=false`,
  `capacity_poll_count=0`, and all six smoke plus 18 full cells remain `pending`.
- The prior queue opened during the retry-1 failure was stopped after one poll,
  before the two-poll threshold and before any cell launch. Its retained state
  has all 24 cells pending.
- Repository verification after the release-gate change: 562 tests passed in
  438.58 seconds.

Decision:
- Both `a2b_noimage` and `a3_caption` on an29 must have a successful `complete`
  manifest before GPU vacancy is inspected.
- After release, each GPU must still satisfy the 1,024-MiB and 10% ceilings for
  two consecutive 300-second polls.
- A failed pilot manifest keeps the queue dormant; it is not treated as a GPU
  release.
- InternVL3-9B and Gemma-3-12B-IT remain TP1, one independent cell per eligible
  GPU, in the isolated audited runtime.

Next actions:
- Leave the queue running without intervention while the blind arms train.
- After both release conditions are true, require all six one-row smoke cells to
  complete before opening the 18-cell full matrix.
