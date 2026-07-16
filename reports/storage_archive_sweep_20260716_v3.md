# Storage Archive Sweep, 2026-07-16 V3

Status:
- Complete. One explicitly superseded seed-1 A1 archive was preserved on shared storage and removed from login-node `/tmp` only after exact hash verification.
- No active archive, foreign path, or unrelated `/tmp` content was read, moved, or deleted.

Evidence:
- Source classification: failed `mech_a1_real_an12_20260713T031454Z`, superseded by completed `mech_a1_real_resume60_an12_20260714T080855Z`.
- Source before relocation: `/tmp/blindgain_checkpoint_archive/mech_a1_real_an12_20260713T031454Z`; 39 files; 57,249,533,660 file bytes (53.318 GiB).
- Destination: `/XYFS02/HDD_POOL/paratera_xy/pxy1289/blindgain_archive/login_tmp_checkpoint_archive/mech_a1_real_an12_20260713T031454Z`.
- Immutable operation: `experiments/runs/storage_sweep_superseded_a1_login_20260716T165326Z`, complete at `2026-07-16T17:08:04Z`.
- Pre-copy SHA256 inventory: `reports/storage_relocations/20260716/login_tmp_mech_a1_real_an12_20260713T031454Z_source.sha256`.
- Relocation manifest: `reports/storage_relocations/20260716/login_tmp_mech_a1_real_an12_20260713T031454Z_relocation.json`.
- Reconciliation: 39 pre-copy entries, 39 copied entries, exact path/hash equality, source unchanged during copy, and `source_replaced_by_symlink=true`.
- The original source path now resolves to the preserved destination, so immutable historical references remain valid without retaining duplicate bytes.
- Final login `/tmp` free space: 315,659,194,368 bytes (294.00 GiB).
- Latest quota-aware measurement completed immediately before the copy at `2026-07-16T17:00:26Z`: 644,412,846,080 bytes free (600.16 GiB). Subtracting the exact copied payload gives 587,163,312,420 bytes (546.84 GiB) estimated free at copy completion, before any concurrent project writes.

Problems:
- The generic relocation helper recorded a Tier-T check even though this destination was shared. The separate, explicit Tier-S preflight ran before the copy and authorized it with hundreds of GiB of headroom, so the completed move did not approach the 20-GiB floor.
- The helper has now been changed to require `--destination-tier S|T`; its Tier-S path uses the quota snapshot and 20-GiB floor. An adversarial fixture verifies that a shared destination cannot be routed through the scratch guard.

Decision:
- Preserve rather than destroy the superseded archive because the shared allocation has ample headroom.
- Retain the source SHA256 list, relocation JSON, and symlink. Do not sweep any additional directory without a new classification, size listing, guard result, and immutable run.

Next actions:
- Let the existing quota-refresh loop publish the next full post-copy measurement; do not start duplicate quota scans.
- Continue latest-raw-only retention for active runs. Evaluation queues remain independent of relocation outcomes.
