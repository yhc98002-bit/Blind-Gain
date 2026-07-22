# Pilot Seed-2 Execution Status V4

Status:
- `blocked`. All four seed-2 training arms reached step 100, but the sealed evaluation lifecycle failed closed because the step-60 merged checkpoints were relocated after R19 and before all Geometry3K audits completed.
- No seed-2 performance value has been opened. This is an evaluation-lifecycle race, not a failed optimizer trajectory or a damaged checkpoint.
- No PI gate decision is made.

Evidence:
- A3-caption training run `experiments/runs/mech_a3_caption_seed2_an29_20260720T125144Z` is `complete`; checkpoints 20/40/60/80/100 materialized and the parent exited zero.
- M5 remains independently active on `an12:0-3`; seed-2 recovery uses no M5 process or checkpoint.
- Original sealed lifecycle: `experiments/runs/pilot_seed2_locked_eval_lifecycle_login_20260721T163341Z`; status `fail`, `performance_values_opened=false`.
- All eight R19 arm/checkpoint queues completed. All four step-100 Geometry3K queues and their 601-row audits completed and pass the structural lifecycle validator.
- Step-60 Geometry3K outcomes before recovery: A2-gray, A2b-no-image, and A3-caption could not launch because the checkpoint index had already been relocated; A1 evaluation completed, but its audit failed when the same index disappeared before audit recomputation.
- Timestamp ordering is consistent across all four arms: `step60_fliptrack_complete.json` was published first, followed 1-3 minutes later by `MERGED_CHECKPOINT_RELOCATED.json`; the Geometry3K queue either had not launched or had not completed its audit.
- Four archived step-60 merged checkpoints remain under `/tmp/blindgain_checkpoint_archive/<run-id>/global_step_60/actor/huggingface`. Every archived file passes `merged_checkpoint.source.sha256`.
- Each archived index SHA256 exactly matches its frozen R19 completion marker: A1 `dc2d2c...`, A2-gray `4df707...`, A2b `9e399d...`, A3 `d435bf...`.
- The source archives total approximately 32.5 GB for the four step-60 merged checkpoints and remain untouched. The latest quota snapshot records 374,858,334,208 bytes of project headroom before recovery; login `/tmp` has approximately 171 GiB free.
- Regression coverage adds a two-marker relocation barrier: R19 completion alone is insufficient; a hash-bound 601-row Geometry3K audit marker is also required. It also rejects a changed audit after marker publication.
- Restore coverage requires an absent destination, exact relocation/R19 bindings, the shared-storage guard, source stability during copy, destination re-hashing, immutable output, and preservation of the archive.
- Focused validation: 29 queue/audit tests, 22 barrier/restore tests, and 19 final recovery tests passed; Python compilation, shell syntax, and `git diff --check` passed.
- Full repository regression suite: `910 passed in 571.83s`; the dedicated `/tmp` test cache was listed and removed afterward.

Problems:
- The four step-60 Geometry3K endpoints must be recovered in fresh immutable run directories.
- The original lifecycle and failed child runs are immutable failure evidence and cannot be reused as successful runs.
- M6 and seed 3 correctly observed the lifecycle failure and stopped fail-closed; their old queue instances must not be reinterpreted as pending.

Decision:
- Commit the dual-marker barrier before any restore or new evaluation launch.
- Restore one checkpoint at a time from the verified archive to the original shared checkpoint path. Preserve the source archive until the new endpoint audit and lifecycle complete.
- Launch four new step-60 Geometry3K queues against the already completed, hash-bound R19 markers. Do not rerun R19 or any training arm.
- Build a new lifecycle manifest using the original successful R19 queues, the original successful step-100 Geometry3K queues, and only the four fresh step-60 Geometry3K queues.
- Keep all values sealed until that replacement lifecycle reports eight complete endpoints. Only then generate the unified seed-2 four-arm readout.

Next actions:
- Commit and push the race fix, adversarial fixtures, and guarded restore tooling.
- Execute sequential restore jobs, verify their immutable restore manifests, then launch the four TP1 Geometry3K endpoints on free `an29:4-7`.
- Reconcile a replacement sealed lifecycle and readout queue.
- After seed-2 sealing, launch a fresh M6 eight-GPU smoke queue on a fully free node; only a passing smoke audit may release the seed-3 scheduler.
