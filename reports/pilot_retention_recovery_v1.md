# Pilot Retention Recovery V1

Status:
- M2 remains `blocked`.
- Original A2b and A3 retention watchers are retained as failed after both
  completed their step-80 merges and then hit transient quota-scan errors.
- A serialized A2b recovery is running; A3 and A1 recovery remain queued.

Evidence:
- A2b failed watcher:
  `pilot_checkpoint_watch_mech_a2b_noimage_retry4_login_20260713T113639Z`.
- A3 failed watcher:
  `pilot_resume_checkpoint_watch_mech_a3_caption_resume20_login_20260713T144302Z`.
- Both failures occurred at `2026-07-15T17:53Z`; each post-merge `du` traversal
  returned exit 1 for the changing `HaocunYe` tree.
- Both step-80 merge subjobs completed and their merged checkpoints remain on
  shared storage; no raw or merged checkpoint was deleted by the failure.
- Recovery run:
  `experiments/runs/pilot_retention_recovery_mech_a2b_noimage_retry4_login_20260715T180830Z`.
- Recovery git/config: `866366bfdba2010bb220708ff9f7038a5d1e3b33` /
  `28637bae72e4d4d311e41ec1c42f61b01edde5f146568a9ac7208e1ce61b43eb`.
- Shared snapshot before recovery: 635,792,375,808 bytes free.
- Login `/tmp` before recovery: 114,904,879,104 bytes free, above the 40-GiB
  guard floor.

Problem:
- Two retention workers traversed and modified the same quota tree concurrently.
  The measurement failed closed on transient file disappearance and the parent
  workers exited before raw-state relocation.
- Replaying the original workers would repeat already-complete steps 20/40/60
  and recreate unnecessary scan concurrency.

Decision:
- Use a new recovery worker that calls the unchanged, hash-pinned retention
  primitives only for steps 80 and 100.
- Permit exactly one active recovery globally; A2b, then A3, then A1.
- Do not alter `measure_storage_usage.py` or any active A2 watcher bundle file.
  The active A2 expected/actual bundle hash remains exactly
  `eb8642643abb2edf3f0ac00bbbab84bc488cf39380d746e0e4d81c49c7fe17d7`.

Next actions:
- Let A2b recovery finish or fail closed.
- Start A3 recovery only after A2b reaches a terminal state.
- Reassess login scratch before A1 recovery; reclaim only artifacts first listed
  as retention-expired or superseded if the 40-GiB floor would be threatened.
