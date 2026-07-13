# M2 Seed-1 Launch Status V2

Status:
- M2 remains `blocked` until all four runs, registered checkpoint evaluations,
  and the registered result table are complete.
- All four arms are now running under the merged preregistration. This report
  records mechanical launch state only; it contains no pilot performance result.

Registration and authorization:
- Final preregistration: `reports/preregistration_pilot_v1.md`.
- Registration introduction commit:
  `2782815cc057d85a302af8bac232cac2b0e1ec75`.
- Each arm has a preserved `status=authorized` machine artifact under
  `reports/pilot_launch_authorization_<arm>_<timestamp>.json`.
- The launcher checked merged-at-HEAD registration before creating each selected
  checkpoint namespace.

Active runs:

| Arm | Immutable run | Node | GPUs | TP | Replicas | Config SHA256 | Git | Operational state |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| A1 real | `mech_a1_real_an12_20260713T031454Z` | an12 | 0,1,2,3 | 1 | 4 | `abf9e9d9...` | `1210c54d...` | optimizing; shadow log populated |
| A2 gray | `mech_a2_gray_an12_20260713T033946Z` | an12 | 4,5,6,7 | 1 | 4 | `c36f24f6...` | `df3f59ef...` | step-0 evaluation/rollout active; shadow log populated |
| A2b no-image | `mech_a2b_noimage_an29_20260713T031525Z` | an29 | 0,1,2,3 | 1 | 4 | `0ead558c...` | `1210c54d...` | optimizing; shadow log populated |
| A3 caption | `mech_a3_caption_an29_20260713T033039Z` | an29 | 4,5,6,7 | 1 | 4 | `573b1ca7...` | `8c904154...` | optimizing; shadow log populated |

Placement:
- Every arm is synchronous and single-node.
- Four independent TP1 rollout replicas shard requests within the arm's node;
  rollout and FSDP training remain colocated.
- The two arms on each node use disjoint GPU sets. No job spans `an12` and `an29`.

Checkpoint discipline:
- Each active arm has exactly one active login-node checkpoint watcher.
- Saves land under `checkpoints/pilot/<arm>` on shared persistent storage.
- The 20-GiB shared quota-headroom guard is configured against the corrected
  1,500-GiB conservative quota and passed a 55-GiB save probe.
- Watchers enforce hash-verified sweep to login `/tmp`, latest-raw-only retention,
  and step-60 FlipTrack scoring before intermediate cleanup.
- Only the step-100 merged checkpoint is designated for final shared retention.

Deviations:
1. The first A3 run, `mech_a3_caption_an29_20260713T031557Z`, failed before
   model allocation and before an optimizer step because validation supplied
   in-memory PIL images to a path-only caption lookup. The normalized-pixel hash
   fix and adversarial fixture are documented in
   `reports/a3_caption_validation_fix.md`; the retry audited all 601 validation
   image references with zero caption misses.
2. One duplicate A2b recovery watcher was stopped before any checkpoint existed.
   The original watcher remained active; both manifests are retained.
3. M8's four resumable 7B inference jobs were gracefully preempted to free an12
   GPUs 4-7 for A2 gray. Preserved prefixes and resume commands are recorded in
   `reports/m8_7b_prep_launch_status_v2.md`.

Evidence:
- Run manifests: `experiments/runs/mech_<arm>_<node>_<timestamp>/run_manifest.json`.
- Native stdout/stderr: each run's `logs/<node>.log`.
- Per-rollout shadows: each run's `reward_shadow.jsonl`.
- Watcher manifests:
  `experiments/runs/pilot_checkpoint_watch_<run>_login_<timestamp>/run_manifest.json`.

Next actions:
- Monitor completion and checkpoint retention without interpreting unregistered
  analyses.
- Run locked geo3k-test and FlipTrack R19 evaluations at registered checkpoints.
- Publish only the registered estimands in
  `reports/pilot_4arm_seed1_results_v1.md`.
