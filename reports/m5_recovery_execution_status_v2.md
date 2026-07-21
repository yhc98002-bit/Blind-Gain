# M5 Recovery Execution Status V2

Status:
- `blocked`. The fixed step-400 long-horizon recovery is actively training; terminal step 400 and its registered evaluations are not yet complete.
- The replacement launch passed the fresh Ray startup preflight and uses `an12:0-3`. No gate is declared passed.

Evidence:
- Failed-safe preflight: `experiments/runs/m5_ray_startup_preflight_an12_20260721T160012Z`; the only failure was an overlong AF_UNIX socket path, before any optimizer step.
- Corrected preflight: `experiments/runs/m5_ray_startup_preflight_an12_20260721T160149Z`; both fresh Ray sessions, runtime-env task, and four unique one-GPU CUDA actors passed.
- Active training run: `experiments/runs/m5_anchor_longhorizon_400_resume150_an12_20260721T160431Z`, Git-bound launch after commits `c06085c` and `91fa0e1`.
- Placement: one synchronous four-GPU job on `an12:0-3`; GPUs 4-7 are not required by M5.
- Checkpoint watcher: `experiments/runs/m5_checkpoint_watch_login_20260721T161055Z`.
- Merged-relocation watcher: `experiments/runs/m5_merged_relocation_watch_login_20260721T161055Z`.
- Registered evaluation queue: `experiments/runs/m5_checkpoint_evaluation_queue_login_20260721T160434Z`.
- Current process snapshot shows all four assigned GPUs computing. No post-resume registered checkpoint has yet materialized; step 150 remains the verified resume source.

Problems:
- Steps 200, 300, and terminal 400 remain pending.
- Registered Geometry3K and R19 evaluations must complete before the fixed terminal verdict can be computed.

Decision:
- Do not modify the run, config, target, or stopping rule.
- Keep new high-host-memory or second-Ray workloads off `an12` while M5 is active. The unused four GPUs do not imply an eight-GPU M5 requirement.

Next actions:
- Allow the run to continue to fixed step 400.
- Let checkpoint, retention, and evaluation queues process each registered endpoint without coupling evaluation readiness to archive relocation.
- Compute the registered flat/rising/falling/indeterminate rule only after terminal artifacts complete.
