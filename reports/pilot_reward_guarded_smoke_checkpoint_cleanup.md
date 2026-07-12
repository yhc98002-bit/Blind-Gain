# Guarded Pilot Reward Smoke Checkpoint Cleanup

Status:
- `complete`. The completed guarded five-step L3 smoke again triggered EasyR1's unconditional final save despite `trainer.save_freq=-1`; the listed retention-expired payload was fully revalidated and removed.
- The exact path below is classified `retention-expired` before removal: it is not a registered pilot checkpoint, is not needed to resume the completed smoke, and conflicts with the future L13 A1 checkpoint namespace.

Evidence:
- Smoke run: `experiments/runs/pilot_reward_smoke_an29_20260711T165700Z` (`status=complete`, `exit_code=0`).
- Retention-expired path: `checkpoints/pilot/mech_a1_real/global_step_5`.
- Exact allocated payload from `du -sb`: `40,970,253,322` bytes (`39G` human-readable).
- File count: `24`, including four model shards and four optimizer shards.
- The scientific smoke outputs remain in the immutable run directory and are audited by `reports/pilot_reward_smoke_audit_v3.json`.
- Shared quota was already below the 20 GiB floor after the anchor step-100 save; removing this unregistered payload is the immediate recovery action.
- Inventory run: `experiments/runs/pilot_reward_guarded_smoke_checkpoint_hash_login_20260712T043034Z` (`status=complete`, `exit_code=0`).
- Preserved checksum manifest: `experiments/runs/pilot_reward_smoke_an29_20260711T165700Z/global_step_5_guarded_retention_expired.sha256`, 24 entries, SHA256 `808aa0407276521eb9c1a450c5fa98fa795aea78f91073c5f8bbccfe17da2360`.
- Revalidation/deletion run: `experiments/runs/pilot_reward_guarded_smoke_checkpoint_delete_login_20260712T043418Z` (`status=complete`, `exit_code=0`); its log contains 24 `OK` records.
- Deletion completed at `2026-07-12T04:37:35Z`; `checkpoints/pilot/mech_a1_real/global_step_5` is absent and `40,970,253,322` bytes were reclaimed.

Problems:
- EasyR1 performs an unconditional final save, so a no-save smoke still writes `global_step_5` into the configured pilot checkpoint root.
- No new shared-output job may start until this retention-expired payload is checksum-inventoried, revalidated, removed, and quota headroom is remeasured.

Decision:
- Preserve a SHA256 manifest for every file under the completed smoke run.
- Revalidate the complete checksum manifest immediately before deleting only the exact listed path.
- Do not archive the 39G payload because it is neither a registered endpoint nor resumable state for an active run.

Next actions:
- Refresh the quota-aware storage snapshot before the anchor step-100 merge.
