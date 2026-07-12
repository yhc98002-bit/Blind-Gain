# Anchor Step-100 OOM Recovery V2

Status:
- `complete` as an engineering recovery. The native-reward anchor continuation loaded the verified step-80 model, optimizer, dataloader, and extra state and completed steps 81-100 without changing the anchor config or reward.
- Step 100 is merged and hash-verified; only the final merged checkpoint remains on shared storage, and only the latest raw state remains in the login-node scratch archive.
- This report does not declare a PI scientific or compute gate.

Evidence:
- Original failed attempt: `experiments/runs/anchor_a0_recipe_3b_geo3k_20260709T224852Z`; root cause was Ray host-memory OOM after step 80.
- Successful continuation: `experiments/runs/anchor_a0_recipe_3b_geo3k_resume80_20260711T150633Z`; `status=complete`, `exit_code=0`, end `2026-07-11T23:48:25Z`.
- Placement: `an12` GPUs `0,1,2,3`, TP1 workers in one synchronous EasyR1 job; no cross-node rollout or training.
- Step-100 merge: `experiments/runs/easyr1_checkpoint_merge_anchor_a0_step100_an12_20260712T045914Z`; `status=complete`, `exit_code=0`.
- Final merged checkpoint: `checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_100/actor/huggingface`, approximately `7.6G`.
- Merged-checkpoint digest: `0653b7a428b19d99b1be9f1efece0cbcaf8156cacb49c44e6238f7c65b28d004`.
- Merged shards: `model-00001-of-00002.safetensors` SHA256 `e94f8b8c012144138762cc0833b2e9654f8de778ef166d7acaf791c714674fa7`; `model-00002-of-00002.safetensors` SHA256 `0b85dd28b543c87e36ba83d49a87caf5b1680d4d73db2f77a2b6c1ebefdba8c2`.
- Step-100 raw relocation: `experiments/runs/easyr1_raw_relocation_anchor_a0_step100_login_20260712T050611Z`; eight shards, `46,304,794,904` bytes, checksum-manifest SHA256 `b843071ebba161bb9257c61cd302082f7ca3baf5a9f4464ce863e6bb35d9f2c1`.
- Latest raw archive: `/tmp/blindgain_checkpoint_archive/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_100/actor`.
- Restored step-80 shared copy cleanup: `experiments/runs/anchor_restored_raw_retention_cleanup_step80_login_20260712T051740Z`; all eight files were rehashed before `46,304,794,904` bytes were removed.
- Retention evidence: `reports/raw_checkpoint_retention.md` and the anchor run manifest's step-100 `storage_retention_events` entry both record the scratch archive and restored shared-copy deletions.
- Watcher: `experiments/runs/anchor_checkpoint_retention_watch_login_20260712T043809Z`; `status=complete`, `exit_code=0`.
- Final quota-aware snapshot at `2026-07-12T05:18:46Z`: `135,071,206,912` bytes free on Tier S.

Problems:
- The original anchor process exceeded Ray's 95% host-memory threshold while several project evaluators shared host RAM.
- EasyR1's unconditional final save recreated an unregistered five-step smoke checkpoint; it was independently hashed and removed before the final anchor merge.
- The original retention code expired the step-80 scratch raw state but did not recognize its restored shared resume copy. The new adversarial fixture covers that case, and 48 storage/checkpoint tests pass.

Decision:
- Preserve the failed parent attempt, successful continuation, final merged checkpoint, latest raw archive, checksum manifests, and deletion records.
- Keep the anchor's native `r1v.py` reward path untouched; the custom pilot reward remains limited to pilot-arm configs.
- Use restored-copy-aware retention for subsequent pilot checkpoints so an older resume copy cannot survive after a newer merged checkpoint is verified.

Next actions:
- Use the final merged checkpoint for the registered anchor evaluation path.
- Continue L7/L9 measurement jobs and keep L13 blocked until the L12 preregistration is PI-approved and merged.
