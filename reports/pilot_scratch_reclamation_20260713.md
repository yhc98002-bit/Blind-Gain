# Pilot Scratch Reclamation, 2026-07-13

Status:
- Two Stage-0 raw-state archives are approved for deletion from login-node `/tmp` before the next pilot checkpoint wave.
- Their scientific successors and the active pilot archives are retained.

Evidence:

| Archive | Allocated bytes | Classification | Preserved checksum-manifest SHA256 |
|---|---:|---|---|
| `/tmp/blindgain_checkpoint_archive/easyr1_geo3k_smoke` | 46,318,469,120 | superseded 2-step smoke state | `afff3dffba3e77d7aeaacfae6c9af7d969021b1b0fd634d20646402ec587e039` |
| `/tmp/blindgain_checkpoint_archive/easyr1_geo3k_recovery30` | 46,302,494,720 | retention-expired 30-step engineering state | `e31c0c10b0dd9adb9ff72dfd66e4c19dc58a658af74b74aab85732ffe31fe6fc` |

- Total planned reclamation: 92,620,963,840 allocated bytes (86.26 GiB).
- The completed 100-step recipe anchor remains available as the scientific successor: final merged checkpoint at `checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_100/actor/huggingface/` and latest resumable raw state under `/tmp/blindgain_checkpoint_archive/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_100/actor/`.
- Active A1, A2, A2b, and A3 pilot checkpoint/archive namespaces are excluded from reclamation.

Problems:
- Login `/tmp` had approximately 151 GiB free before reclamation. Concurrent 4-GPU pilot checkpoint merge/relocation peaks could approach the 40 GiB guard floor.

Decision:
- Delete only the two paths listed above after this report is committed. They are failed/superseded or retention-expired, re-derivable, and are not resume sources for any active or registered run.

Next actions:
- Record post-delete free space and deletion time below without changing the pre-deletion evidence.
- Continue enforcing latest-raw-only retention for active pilot runs.

Deletion record:
- Pending execution.
