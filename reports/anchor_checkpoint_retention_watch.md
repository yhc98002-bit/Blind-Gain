# Anchor Checkpoint Retention Watch

Status:

- Prepared for the native `anchor_a0_recipe_3b_geo3k_20260709T224852Z` steps 80 and 100. This is checkpoint lifecycle automation only; it does not inspect training or validation metrics.

Evidence:

- `scripts/watch_anchor_checkpoints.py` waits for `checkpoint_tracker.json` to reach the target and requires two identical complete model/optimizer shard signatures one minute apart.
- Every quota refresh, merge, raw relocation, and merged relocation receives its own immutable run directory and `run_manifest.json`.
- Shared usage is measured before merge, after merge, and after relocation. The shared and scratch guards remain fail-closed.
- Step 80: merge, archive latest raw state, preserve merged checkpoint in Tier T.
- Step 100: merge, archive latest raw state, retain final merged checkpoint on Tier S.
- The watcher reads no metric or generation log. Pilot metrics remain inaccessible before preregistration.

Problems:

- Login-node Tier T remains volatile. The watcher preserves SHA256 manifests on Tier S, but a durable multi-TB archive path is still owed.

Decision:

- Run the watcher in a detached `tmux` session after its fixtures pass and its code is committed.

Next actions:

- Record the watcher run directory and terminal step-80/100 subruns here as they occur.
