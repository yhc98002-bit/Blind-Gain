# Seed-2 Archive Preservation, 2026-07-22

Status:
- Complete. Two finished seed-2 training-state archives were copied from login `/tmp` to shared persistent storage and the old source paths became verified symlinks.

Evidence:
- Plan: `experiments/runs/seed2_archive_preservation_plan_login_20260722T055905Z`.
- Execution: `experiments/runs/seed2_archive_preservation_execute_login_20260722T143937Z`.
- Preserved: 138 files, 147,089,537,640 bytes.
- A1: 69 files, 73,544,768,700 bytes.
- A3: 69 files, 73,544,768,940 bytes.
- Persistent root: `/XYFS02/HDD_POOL/paratera_xy/pxy1289/blindgain_archive/login_tmp_checkpoint_archive`.
- Both relocation manifests report unchanged source hashes, verified target hashes, atomic target publication, and source symlinks resolving to their exact destinations.
- Post-copy Lustre project-quota measurement at `2026-07-22T15:14:06Z`: 1,358,134,267,904 bytes used and 252,478,468,096 bytes free under the conservative 1,500-GiB allocation.
- Login `/tmp` free space after preservation: 226,209,181,696 bytes.

Problems:
- The operation itself completed, but its older wrapper exited before publishing terminal status. The immutable operation result already proved both entries complete; the run manifest was reconciled from `running` to `complete` with this discrepancy recorded in `runner_error`.

Decision:
- Retain the persistent copies and the compatibility symlinks. No checkpoint or evaluation output was deleted.
- Use the released Tier-T capacity for the current M5 resume chain; the 40-GiB scratch guard remains mandatory.

Next actions:
- Re-measure quota before every restore/save cycle.
- Keep latest-raw-only retention active after each new M5 merge is hash-verified.
