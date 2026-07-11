# Anchor Checkpoint Retention Watch

Status:

- Running for the native `anchor_a0_recipe_3b_geo3k_20260709T224852Z` steps 80 and 100. This is checkpoint lifecycle automation only; it does not inspect training or validation metrics.

Evidence:

- `scripts/watch_anchor_checkpoints.py` waits for `checkpoint_tracker.json` to reach the target and requires two identical complete model/optimizer shard signatures one minute apart.
- Every quota refresh, merge, raw relocation, and merged relocation receives its own immutable run directory and `run_manifest.json`.
- The launcher pins a SHA256 over the watcher, guards, merger, and relocation code; the watcher rechecks that bundle immediately before each future operation and fails if it changed.
- Shared usage is measured before merge, after merge, and after relocation. The shared and scratch guards remain fail-closed.
- Step 80: merge, archive latest raw state, preserve merged checkpoint in Tier T.
- Step 100: merge, archive latest raw state, retain final merged checkpoint on Tier S.
- The watcher reads no metric or generation log. Pilot metrics remain inaccessible before preregistration.
- Active run: `experiments/runs/anchor_checkpoint_retention_watch_login_20260711T052335Z/`; git `4c31687280e039e47922ce886d83fa86fdcf3cb1`; code bundle `855e48f6d552357573782586205b9420be6ec1223d568deb4236e05e9e58b3a7`; tmux session `anchor_checkpoint_retention_watch`; start `2026-07-11T05:23:36Z`.
- The earlier waiting-only run `anchor_checkpoint_retention_watch_login_20260711T052047Z` was preserved as `fail/superseded` at 05:23:35Z before step 80 arrived; no checkpoint subjob had started.

Problems:

- Login-node Tier T remains volatile. The watcher preserves SHA256 manifests on Tier S, but a durable multi-TB archive path is still owed.

Decision:

- Keep the detached watcher running; a nonzero subjob or storage refusal terminates it with a failed manifest instead of continuing unsafely.

Next actions:

- Record the watcher run directory and terminal step-80/100 subruns here as they occur.
