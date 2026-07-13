# A3 Caption Validation Data-Path Fix

Status:
- The first A3 process failed before model allocation and before any optimizer
  step.
- Root cause is fixed and covered by an adversarial in-memory validation-image
  fixture.
- A1 and A2b were not modified or restarted.

Failed run:
- Run: `experiments/runs/mech_a3_caption_an29_20260713T031557Z`.
- Git: `1210c54d0134ebc4ff9c3829c78977cdb0a080ca`.
- Exit code: 1.
- Failure location: validation-dataset overlength filtering, before FSDP/model
  allocation and before step 0 rollout.
- Exact error: `TypeError: caption condition requires content-addressable image paths`.

Root cause:
- The filtered training JSONL stores image filesystem paths.
- The cached `hiyouga/geometry3k@test` validation dataset exposes decoded
  in-memory PIL images.
- The frozen caption store covers all 1,736 Geometry3K train/test image hashes,
  but the prior loader only computed a hash from a path string.
- Re-encoding a decoded PNG does not reproduce its original compressed-file
  SHA256, so a naive PIL-to-PNG hash would still miss valid captions.

Fix:
- Preserve original file/bytes SHA256 lookup when available.
- Add a normalized pixel-content index keyed by width, height, and RGBA bytes.
- Build that index only from the frozen caption store's recorded source image
  paths.
- Cache the index by the SHA256 fingerprints of all caption-store shards.
- Fail closed on missing source images, pixel-hash caption conflicts, and
  missing lookup entries.
- Caption text, prompt hash, model identity, insertion template, and training
  config remain unchanged.

Reproducibility:
- Incremental patch: `docs/easyr1_caption_pil_hash_patch.diff`.
- Installer: `scripts/apply_easyr1_caption_pil_hash_patch.sh`.
- Runtime EasyR1 worktree remains pinned at
  `dd71bbd252694f5f850213eec15795b6b88d9fea`; each run snapshots its full
  worktree diff.

Tests:
- Filesystem-path caption lookup: pass.
- In-memory PIL validation lookup by normalized pixels: pass.
- Missing raw and pixel hashes fail loudly: pass.
- Caption batches still contain no image tensor or multimodal payload: pass.
- Full cached validation audit: 601 rows and 601 image references checked
  against the 1,736-entry normalized pixel index; missing captions: 0.

Decision:
- Retry A3 in a new immutable run directory after committing this patch.
- Record the failed pre-step run and retry relationship in both run manifests.
