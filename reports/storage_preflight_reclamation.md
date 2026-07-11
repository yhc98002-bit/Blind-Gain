# Storage Preflight Reclamation Register

Recorded UTC: 2026-07-11T04:52:03Z

This register is written before any listed bytes are removed. Checkpoint rows may be deleted only after the newer merged checkpoint is hash-verified. Active logs, generated data, evaluation outputs, model weights, and foreign-process files are excluded.

| Path | Size bytes | Classification | Prerequisite | Intended action |
| --- | ---: | --- | --- | --- |
| `/tmp/blindgain_checkpoint_archive/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_20/actor` | 46,304,799,760 | retention-expired raw FSDP/optimizer state | step-60 merge hash verification | delete through latest-only retention code; preserve hashes and deletion event in the run manifest |
| `/tmp/blindgain_checkpoint_archive/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_40/actor` | 46,304,799,760 | retention-expired raw FSDP/optimizer state | step-60 merge hash verification | delete through latest-only retention code; preserve hashes and deletion event in the run manifest |
| `logs/setup/` | 91,283 | old setup logs from 2026-07-07 | S2 archive hash and extraction verification | compress to Tier S2, then remove source directory |
| `logs/downloads/` | 387,060 | old completed download logs from 2026-07-07 | S2 archive hash and extraction verification | compress to Tier S2, then remove source directory |
| `logs/gpu_jobs/` | 7,217 | old completed synthetic-profile logs from 2026-07-07 | S2 archive hash and extraction verification | compress to Tier S2, then remove source directory |

Explicitly retained:

- `/tmp/blindgain_checkpoint_archive/easyr1_geo3k_recovery30` (46,302,468,896 bytes) is the latest raw state for the completed engineering-anchor run.
- `/tmp/blindgain_checkpoint_archive/easyr1_geo3k_smoke` (46,318,401,427 bytes) is superseded, but is not deleted in this preflight because no durable raw-state archive exists yet.
- `logs/tunnels/` may describe active proxy processes and is not reclaimed.
- `logs/gpu_util_an12.jsonl` and `logs/gpu_util_an29.jsonl` are active utilization records and are not reclaimed.
