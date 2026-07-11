# Pilot Reward Smoke Checkpoint Cleanup

Status:
- `pending cleanup`. The completed five-step L3 smoke unexpectedly emitted a raw EasyR1 checkpoint even though the launch override set `trainer.save_freq=-1`.
- The checkpoint is classified `retention-expired`: it is not a registered pilot checkpoint, is not needed to resume the completed smoke, and occupies the same shared arm root reserved for the later A1 pilot.

Evidence:
- Smoke run: `experiments/runs/pilot_reward_smoke_an29_20260711T114247Z` (`status=complete`, `exit_code=0`).
- Retention-expired path: `checkpoints/pilot/mech_a1_real/global_step_5`.
- Exact allocated payload from `du -sb`: `40,970,253,322` bytes (`39G` human-readable).
- File count: `24`, including four model shards and four optimizer shards.
- The scientifically required smoke outputs remain in the immutable run directory and are audited by `reports/pilot_reward_smoke_audit_v2.json`.

Problems:
- The launcher deviation text assumed that `save_freq=-1` suppresses all saves. EasyR1 performs an unconditional final save; this checkpoint is the resulting unregistered artifact.
- Leaving it in place consumes shared quota and risks a namespace collision with the registered `mech_a1_real` pilot.

Decision:
- Compute a SHA256 manifest for all 24 files and retain that small manifest under the completed smoke run.
- After the manifest is complete and validated, delete only `checkpoints/pilot/mech_a1_real/global_step_5` from shared storage.
- Preserve this report and the hash manifest as the deletion record. Do not archive the 39G payload because the smoke is complete and the checkpoint is neither a registered evaluation endpoint nor the latest resumable state of an active run.

Next actions:
- Hash, validate, and remove the listed checkpoint; then version this report with completion time, reclaimed bytes, and manifest hash.
