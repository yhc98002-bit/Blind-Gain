# Storage Archive Sweep, 2026-07-16 V2

Status:
- In progress. One additional explicitly superseded archive is approved for a preservation move from login scratch to shared persistent storage.
- No active archive, foreign path, or unrelated `/tmp` content is in scope.

Evidence:
- Source: `/tmp/blindgain_checkpoint_archive/mech_a1_real_an12_20260713T031454Z`.
- Source size before relocation: 57,249,533,660 bytes (39 files; approximately 53.3 GiB).
- Classification: failed seed-1 A1 source run, superseded by completed run `mech_a1_real_resume60_an12_20260714T080855Z`, whose step-100 R19 marker is complete and whose registered readout is published.
- Destination: `/XYFS02/HDD_POOL/paratera_xy/pxy1289/blindgain_archive/login_tmp_checkpoint_archive/mech_a1_real_an12_20260713T031454Z`.
- Quota-aware snapshot at `2026-07-16T13:55:49Z`: 752,405,004,288 bytes free before the move.
- Login `/tmp` before the move: approximately 241 GiB free.

Problems:
- None. The active anchor archive, active M5 integrity state, active seed-2 run, and all foreign paths are excluded.

Decision:
- Generate and fsync a complete source SHA256 inventory before copying.
- Apply the Tier-S storage guard, copy to a new destination, hash every destination file, and verify the source is unchanged.
- Remove source bytes only after exact inventory equality, then leave a symlink at the original path so immutable manifests and markers continue to resolve.
- On any mismatch, retain the source and partial copy and fail closed.

Next actions:
- Record the immutable relocation run, source manifest, relocation JSON, final free-space measurement, and exact reclaimed bytes here after completion.
