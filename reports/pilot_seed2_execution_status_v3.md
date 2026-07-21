# Pilot Seed-2 Execution Status V3

Status:
- `blocked`. A1, A2-gray, and A2b-no-image training are complete; A3-caption remains active with step 80 as the latest materialized checkpoint and target step 100.
- The four-arm evaluation lifecycle is queued but fail-closed behind A3 completion. No seed-2 training, validation, Geometry3K, or FlipTrack performance value has been opened.
- No PI gate decision is made.

Evidence:
- A3 run: `experiments/runs/mech_a3_caption_seed2_an29_20260720T125144Z`; structural state `running`; placement `an29:0-3`.
- M5 runs concurrently on `an12:0-3`; this is a disjoint single-node placement.
- A1 checkpoint recovery queue: `experiments/runs/a1_seed2_checkpoint_recovery_queue_login_20260721T161411Z`; it waits for A3 checkpoint finalization before rebuilding A1 steps 60/100.
- Sealed evaluation lifecycle: `experiments/runs/pilot_seed2_locked_eval_lifecycle_login_20260721T163341Z`, Git `36b18723eb074d4a057dae27f7e4680f14e752cc`.
- Eight R19 queues are at `waiting_cohort_release`; eight Geometry3K queues are at `waiting_r19_marker`.
- R19 children are pinned to `an29:0-3` as four TP1 replicas. Geometry3K children are pinned one per GPU across `an29:4-7`.
- Each arm/checkpoint endpoint is registered at steps 60 and 100. Each Geometry3K endpoint requires an independent 601-row identity/hash/score-recomputation audit.
- Focused regression suite: `43 passed`; shell syntax, Python bytecode compilation, and `git diff --check` also passed before launch.

Problems:
- A3 must reach step 100 and complete its retention lifecycle.
- A1 step-60/100 merged checkpoints must be reconstructed and hash-verified by the queued recovery path.
- The eight R19 and eight Geometry3K endpoints remain unexecuted while the cohort barrier is closed.

Decision:
- Keep A3 uninterrupted to step 100.
- Keep every seed-2 result sealed until all eight checkpoint endpoints and all eight 601-row audits complete. Build the four-arm readout in one action afterward.
- Archive relocation remains operational bookkeeping and cannot block an otherwise complete checkpoint evaluation.

Next actions:
- A3 completion automatically releases A1 checkpoint recovery and the R19 queues.
- Complete step-60/100 R19 and Geometry3K scoring, then validate the sealed lifecycle artifact.
- Produce the unified seed-2 readout only after the lifecycle reports all eight endpoints complete.
