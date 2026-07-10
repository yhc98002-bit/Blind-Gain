# Storage Quota Recovery - 2026-07-10

Status:
- Shared-project usage fell from approximately 166 GB to 76 GB.
- Approximately 130 GB of raw FSDP/optimizer state is preserved under `/tmp/blindgain_checkpoint_archive` on the login host.
- Another 25 GB of reproducible noise-image caches is temporarily stored under `/tmp/blind-gains/noise_image_cache_archive_20260710`.
- The active anchor is healthy past step 20; its merged step-20 Hugging Face checkpoint remains on shared storage.

Evidence:
- Shared filesystem capacity itself is healthy (`/XYFS02` was 23% used), but user writes returned `EDQUOT`; `lfs quota` details are permission-restricted.
- The quota first appeared when pytest tried to update `.pytest_cache`, then terminated the first R14 evaluation after 207/300 rows.
- A 16 MB write probe failed before relocation and passed after filesystem accounting synchronized.
- Current top-level scan: `artifacts/` 42 GB, `checkpoints/` 16 GB, `data/` 8.1 GB, `.venv/` 7.6 GB, `experiments/` 2.9 GB, `.venv-ocr/` 428 MB; total 76 GB.
- Login `/tmp` has 815 GB capacity and approximately 414 GB free after relocation.

Relocated artifacts:
| Artifact | Temporary path | Approx. size | Verification | Shared survivor |
| --- | --- | ---: | --- | --- |
| obsolete 2-step smoke checkpoint | `/tmp/blindgain_checkpoint_archive/easyr1_geo3k_smoke` | 44 GB | all 22 files passed source SHA256 manifest | relocation marker only |
| recovery step-30 raw model/optimizer shards | `/tmp/blindgain_checkpoint_archive/easyr1_geo3k_recovery30/global_step_30/actor` | 44 GB | source bytes streamed through SHA256 while copying; sizes checked before removal | merged Hugging Face checkpoint, 7.6 GB |
| active anchor step-20 raw model/optimizer shards | `/tmp/blindgain_checkpoint_archive/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_20/actor` | 44 GB | source bytes streamed through SHA256 while copying; sizes checked before removal | merged Hugging Face checkpoint, 7.6 GB |
| 14 inactive noise-evaluation caches | `/tmp/blind-gains/noise_image_cache_archive_20260710` | 25 GB | 10,700 files and 26,079,397,607 file bytes verified after copy; zero broken links | predictions, metrics, manifests, and original-path symlinks |

Restore metadata:
- Smoke checksum manifest: `/tmp/blindgain_checkpoint_archive/easyr1_geo3k_smoke/source.sha256`.
- Recovery checksum manifest: `/tmp/blindgain_checkpoint_archive/easyr1_geo3k_recovery30/global_step_30/actor/raw_training_state.source.sha256`.
- Anchor step-20 checksum manifest: `/tmp/blindgain_checkpoint_archive/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_20/actor/raw_training_state.source.sha256`.
- Shared actor directories contain `RELOCATED.json` or `RAW_STATE_RELOCATED.json` with exact restore locations.
- Historical `eval_image_*_path` values remain usable through absolute symlinks from each original `noise_image_cache` path to its temporary target.

Problems:
- `/tmp` is node-local and may be cleared by host maintenance or account cleanup. It is a temporary preservation layer, not canonical archival storage.
- Noise images are deterministic intermediate caches rather than result artifacts, but their symlinks will break if login-node `/tmp` is cleared; regenerate them from the recorded run inputs when needed.
- Optimizer-state resume from recovery step 30 or anchor step 20 requires restoring the listed raw shards to their original actor directories.
- The anchor is configured for checkpoints every 20 steps. Keeping every raw checkpoint on shared storage would consume roughly 44 GB per checkpoint and hit quota again.

Decision:
- Preserve every merged Hugging Face checkpoint on shared storage for deterministic evaluation.
- After each anchor checkpoint is merged and verified, move only raw FSDP/optimizer shards to checksummed `/tmp` storage.
- Preserve run manifests, validation outputs, logs, dataloader state, extra state, and relocation markers in their immutable shared run/checkpoint directories.
- Move only inactive, reproducible condition caches to temporary storage; preserve per-item predictions and aggregate metrics on shared storage.
- Do not delete model downloads, datasets, generated manifests, evaluation results, or user-authored files.

Next actions:
- Merge and rotate anchor steps 40, 60, 80, and 100 using the same procedure.
- Move `/tmp/blindgain_checkpoint_archive` to canonical multi-TB project storage when the PI supplies it.
- Before releasing either node, copy all temporary checkpoint archives to durable storage and verify their checksum manifests.
