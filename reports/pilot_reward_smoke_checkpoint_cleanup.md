# Pilot Reward Smoke Checkpoint Cleanup

Status:
- `complete`. The completed five-step L3 smoke unexpectedly emitted a raw EasyR1 checkpoint even though the launch override set `trainer.save_freq=-1`; the listed retention-expired checkpoint has now been checksum-verified and removed.
- The checkpoint is classified `retention-expired`: it is not a registered pilot checkpoint, is not needed to resume the completed smoke, and occupies the same shared arm root reserved for the later A1 pilot.

Evidence:
- Smoke run: `experiments/runs/pilot_reward_smoke_an29_20260711T114247Z` (`status=complete`, `exit_code=0`).
- Retention-expired path: `checkpoints/pilot/mech_a1_real/global_step_5`.
- Exact allocated payload from `du -sb`: `40,970,253,322` bytes (`39G` human-readable).
- File count: `24`, including four model shards and four optimizer shards.
- The scientifically required smoke outputs remain in the immutable run directory and are audited by `reports/pilot_reward_smoke_audit_v2.json`.
- Inventory run: `experiments/runs/pilot_reward_smoke_checkpoint_hash_login_20260711T145008Z` (`status=complete`, exit 0).
- Preserved checksum manifest: `experiments/runs/pilot_reward_smoke_an29_20260711T114247Z/global_step_5_retention_expired.sha256`, 24 entries, SHA256 `7c3bfff6aadcfb22c9c2c2da2bc9d94833f8030fb2f001e01fc204e12174f02d`.
- Revalidation/deletion run: `experiments/runs/pilot_reward_smoke_checkpoint_delete_login_20260711T145353Z` (`status=complete`, exit 0); its log contains 24 `OK` records.
- Deletion completed at `2026-07-11T14:57:10Z`; `checkpoints/pilot/mech_a1_real/global_step_5` is absent and `40,970,253,322` bytes were reclaimed.

Problems:
- The launcher deviation text assumed that `save_freq=-1` suppresses all saves. EasyR1 performs an unconditional final save; this checkpoint is the resulting unregistered artifact.
- Before cleanup, it consumed shared quota and risked a namespace collision with the registered `mech_a1_real` pilot.

Decision:
- A SHA256 manifest for all 24 files is retained under the completed smoke run.
- After full revalidation, only `checkpoints/pilot/mech_a1_real/global_step_5` was deleted from shared storage.
- Preserve this report and the hash manifest as the deletion record. Do not archive the 39G payload because the smoke is complete and the checkpoint is neither a registered evaluation endpoint nor the latest resumable state of an active run.

Next actions:
- Keep the real `mech_a1_real` checkpoint namespace empty until L12 authorizes L13 optimization.
