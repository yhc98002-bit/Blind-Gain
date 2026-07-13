# M2 Seed-1 Launch Status V1

Status:
- M2 is running; no task or scientific gate is declared complete.
- A1 real, A2b no-image, and A3 caption are launched under the merged
  preregistration.
- A2 gray is queued for `an12` GPUs 4-7 after the active M8 jobs release
  those GPUs.
- No pilot training or validation result is reported here.

Registration:
- Final preregistration: `reports/preregistration_pilot_v1.md`.
- Introduction commit pinned in registration:
  `2782815cc057d85a302af8bac232cac2b0e1ec75`.
- M0 finalization commit: `4f9c1b2`.
- Every arm received `status=authorized` from
  `scripts/check_pilot_launch_authorization.py` before run-directory creation.

Active runs:
| Arm | Run | Node | GPUs | TP | Replicas | Git | State |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| A1 real | `mech_a1_real_an12_20260713T031454Z` | an12 | 0,1,2,3 | 1 | 4 | `1210c54d...` | running |
| A2b no-image | `mech_a2b_noimage_an29_20260713T031525Z` | an29 | 0,1,2,3 | 1 | 4 | `1210c54d...` | running |
| A3 caption retry | `mech_a3_caption_an29_20260713T033039Z` | an29 | 4,5,6,7 | 1 | 4 | `8c904154...` | running |

Queued run:
| Arm | Registered placement | Reason not launched |
| --- | --- | --- |
| A2 gray | an12 GPUs 4,5,6,7 | occupied by four proposal-critical M8 TP1 evaluations |

Operational deviations:
1. The combined launch shell reached its foreground orchestration limit after
   process creation. The normal A2b watcher already existed, and a duplicate
   recovery watcher was briefly attached. The duplicate was terminated before
   any checkpoint existed; the original watcher remains active. Both watcher
   manifests and the A2b run-manifest deviation line are preserved.
2. Initial A3 run `mech_a3_caption_an29_20260713T031557Z` failed during
   validation data preparation before model allocation and before any optimizer
   step. Root cause and fix are in
   `reports/a3_caption_validation_fix.md`.
3. A3 retry uses the unchanged registered config/data and the committed
   normalized-pixel caption lookup at `8c904154...`. Failed and retry
   manifests cross-reference each other.

Checkpoint discipline:
- Each active arm has exactly one active login-node watcher.
- Save path is `checkpoints/pilot/<arm>`.
- The shared 55-GB write probe passed under the updated 1,500-GiB quota guard.
- Latest-raw-only retention and hash-verified relocation remain enabled.
- Step 60 FlipTrack evaluation remains a watcher prerequisite before cleanup.

Next actions:
- Verify A3 reaches normal rollout without another data-path error.
- Launch A2 gray when M8 releases an12 GPUs 4-7.
- Continue mechanical monitoring only; publish registered analyses in
  `reports/pilot_4arm_seed1_results_v1.md` after all four runs and evaluations
  complete.
