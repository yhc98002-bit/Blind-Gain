# Storage Cleanup, 2026-07-19

Status:
- Complete. The cleanup recovered shared quota and login-node scratch without deleting an active BlindGain resume state, model, dataset, or evaluation output.
- SoundDecisions was declared abandoned by the user. Its seven roots disappeared concurrently after the retirement bundle was verified and before this agent began deletion; deletion ownership is therefore recorded as external/unknown, not attributed to this cleanup process.

Evidence:
- Retirement package: `/HOME/paratera_xy/pxy1289/retired_projects/SoundDecisions_20260719` (18 MiB).
- The package contains a verified all-refs Git bundle, the local-only `arc4-wpA` ref, the dirty binary patch, `arc4_wpA2_verify.py`, remote/worktree snapshots, and SHA256 checksums.
- Preflight measurements placed the seven SoundDecisions roots under Lustre project ID `2228473301`, totaling 389,039,439,872 bytes (362.321 GiB).
- A 64-MiB shared-storage write, double SHA256 readback, and deletion probe passed after those roots disappeared.
- Invalid checkpoint selected for deletion: `checkpoints/pilot/mech_a2_gray_seed2/global_step_40`, 21,832,908,800 bytes (20.333 GiB), eight shard files.
- Its optimizer shards are truncated to 1,049,624,576--1,588,592,640 bytes; the verified step-20 optimizer shards are 6,172,412,241 bytes each.
- The run tracker states `last_global_step=20` and `best_global_step=20`; step-40 is not a recovery point.
- Pre-delete SHA256 inventory: `/HOME/paratera_xy/pxy1289/retired_projects/SoundDecisions_20260719/a2_gray_seed2_invalid_step40.sha256`, inventory SHA256 `ab488e4ccf1ba268ab1c97fc21b14dc385e6f44f92413d5375953d36e906e142`.
- The invalid step-40 path was removed after the checks above; the valid step-20 archive and tracker remain intact.
- Seed-1 cleanup evidence package: `/HOME/paratera_xy/pxy1289/storage_cleanup_20260719`.
- Four retention-expired login-node archives are allowlisted for deletion, totaling 245,294,313,472 bytes (228.448 GiB):
  - `/tmp/blindgain_checkpoint_archive/mech_a1_real_resume60_an12_20260714T080855Z`
  - `/tmp/blindgain_checkpoint_archive/mech_a2_gray_an12_20260713T033946Z`
  - `/tmp/blindgain_checkpoint_archive/mech_a3_caption_resume20_an29_20260713T144233Z`
  - `/tmp/blindgain_checkpoint_archive/mech_a2b_noimage_retry4_an29_20260713T113556Z`
- Their relocation SHA256 manifests were copied into the evidence package. A new 56-file SHA256 inventory covers all four persistent step-100 Hugging Face checkpoints before deletion.
- `reports/pilot_4arm_seed1_results_v1.json` reports `status=complete`; all four trackers report `last_global_step=100` and all persistent final model indexes and shards are present.
- All four allowlisted login-node archives were deleted, releasing exactly 245,294,313,472 bytes (228.448 GiB). `/tmp` now reports 415,348,269,056 bytes (386.823 GiB) available.
- The protected A2 seed-2 step-20, M5, and anchor archives remain present. The archive root now occupies 223,404,568,576 bytes.
- Every file in the 56-file persistent final-model inventory passed a post-delete SHA256 check. The seed-1 Markdown and machine readout hashes also passed.
- A 1-GiB shared-storage write with `fsync`, two matching SHA256 reads, full readback, and cleanup passed. Probe SHA256: `49bc20df15e412a64472421e13fe86ff1c5165e18b2afccf160d4dc19fe68a14`.
- Sound retirement package checksum-list SHA256: `efe4194ff910b4c84380afc4c9b86a124ce22f8c0ab82477fa0a0b68617489b8`.
- BlindGain cleanup evidence checksum-list SHA256: `deb22e47b8e218371eb5f07e2a77644e37145442fa02e14d5eb4b282f6e844fb`.

Problems:
- Project quota reporting was stale during the failed save. The runtime guard began reporting 217,992,568,832 bytes of headroom after the concurrent SoundDecisions removal, but direct write probes remain the authoritative operational check.
- The SoundDecisions per-file count was not completed because the roots disappeared during inventory. Previously completed byte measurements and the verified retirement package are retained.
- The later recursive `du` snapshot reports more allocated bytes than the configured 1.5-TiB capacity and conflicts with successful direct writes. It is unsuitable for authorizing the next checkpoint save; a fresh conservative snapshot or administrator quota reading is still required before relaunch.

Decision:
- The exact invalid step-40 path was deleted after this report and its hash inventory existed. The valid archived step-20 state, run manifest, tracker, logs, and hash inventory were preserved.
- Only the explicitly retention-expired seed-1 raw archives were removed from login `/tmp`. All seed-2 resume states and M5 state were retained.
- Do not touch models, datasets, evaluation outputs, final merged checkpoints, or unrelated projects.
- The optional `.uv_cache` and shared `blindgain_archive` cleanup was not needed and was not performed.

Next actions:
- Publish a fresh guard-compatible quota snapshot before the next training checkpoint save; do not use the contradictory recursive snapshot as authorization.
- Resume A2 seed-2 only from the verified archived step-20 state. Keep A2b seed-2 and M5 recovery paths unchanged.
