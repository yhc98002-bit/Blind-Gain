# Superseded Archive Retirement Preflight, 2026-07-22

Status:
- Ready for hash-validation only. No archive has been deleted by this preflight.
- The machine allowlist is `reports/storage_retirement_plan_20260722.json`.

Evidence:
- Candidate A1: `/XYFS02/HDD_POOL/paratera_xy/pxy1289/blindgain_archive/login_tmp_checkpoint_archive/mech_a1_real_an12_20260713T031454Z`; 39 files; 57,249,533,660 bytes.
- Its source run is recorded `fail`, exit 1. The same seed/arm replacement `mech_a1_real_resume60_an12_20260714T080855Z` is recorded `complete`, exit 0.
- Candidate A3: `/XYFS02/HDD_POOL/paratera_xy/pxy1289/blindgain_archive/login_tmp_checkpoint_archive/mech_a3_caption_an29_20260713T033039Z`; 24 files; 49,101,916,160 bytes.
- Its source run is recorded `fail`, exit -6. The same seed/arm replacement `mech_a3_caption_resume20_an29_20260713T144233Z` is recorded `complete`, exit 0.
- Both candidates were previously copied from login scratch and byte-verified in `reports/storage_archive_sweep_20260716_v3.md` and `reports/storage_archive_sweep_20260716.md`.
- Historical per-file SHA256 lists are under `reports/storage_relocations/20260716/`.
- Exact retirement total: 63 files, 106,351,449,820 bytes (99.0475 GiB).
- Safety implementation: `scripts/retire_superseded_archives.py`; focused tests cover dry-run, exact execution, extra-file rejection, incomplete-replacement rejection, and nested-path rejection.

Problems:
- Login `/tmp` has about 171 GiB free. The deletion itself frees shared quota, not login scratch; completed seed-2 archives must subsequently be relocated under the shared guard to release scratch.
- Shared quota currently has about 288.4 GiB free before this retirement. No capacity estimate substitutes for per-file hash validation.

Decision:
- Permit deletion only if the tool recomputes all 63 hashes, finds an exact file-set match, confirms both failed/replacement manifest pairs, and confirms each login source is a symlink to the allowlisted shared destination.
- The tool rejects any extra file, hash mismatch, path outside the direct-child allowlist, symlink inside an archive, or incomplete replacement.
- Active M5, seed-3 A1, seed-2 final checkpoints, models, datasets, and evaluation outputs are outside the allowlist and cannot be reached by this plan.

Next actions:
- Run the tool once without `--execute` and retain its machine output.
- Review the dry-run output, then run a fresh output path with explicit `--execute`.
- Remeasure Lustre quota and login scratch before relocating any completed seed-2 archive.
