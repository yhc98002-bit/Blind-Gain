# Main-Phase Storage Reclamation Register

Status:
- `listed-before-relocation` on 2026-07-12.
- The quota-aware snapshot at `2026-07-12T20:02:07Z` measured 532,899,221,504 allocated bytes and only 3,971,690,496 bytes of conservative 500-GiB quota headroom.
- No listed payload has been removed at the time this register is committed.

Scope:
- Relocate only deterministic condition-image caches from completed evaluation runs to login-node Tier-T storage, preserving original paths as symlinks after copy/hash verification.
- Relocate the superseded 30-step merged Hugging Face checkpoint to its existing checksummed recovery archive. The completed 100-step anchor supersedes this checkpoint for main-phase work.
- Preserve every prediction shard, metric, run manifest, source manifest, report, dataset, current 100-step checkpoint, and foreign/unrelated file on its current persistent tier.

Eligible completed-run caches:

| Source path | Apparent bytes | Classification |
| --- | ---: | --- |
| `experiments/runs/fliptrack_r20_qwen25vl7b_noise_an12_20260711T130239Z/noise_image_cache` | 4,760,006,682 | deterministic/re-derivable cache; run complete |
| `experiments/runs/fliptrack_r20_qwen25vl3b_noise_an12_20260711T133319Z/noise_image_cache` | 4,760,006,682 | deterministic/re-derivable cache; run complete |
| `experiments/runs/fliptrack_v02r19_anchor_step100_noise_an12_20260712T094200Z/noise_image_cache` | 4,760,006,457 | deterministic/re-derivable cache; run complete |
| `experiments/runs/fliptrack_r20_qwen25vl3b_severe_an12_20260711T135944Z/severe_image_cache` | 374,085,955 | deterministic/re-derivable cache; run complete |
| `experiments/runs/fliptrack_r20_qwen25vl3b_mild_an12_20260711T134432Z/mild_image_cache` | 356,884,850 | deterministic/re-derivable cache; run complete |
| `experiments/runs/fliptrack_r20_qwen25vl3b_medium_an12_20260711T135139Z/medium_image_cache` | 347,502,786 | deterministic/re-derivable cache; run complete |
| `experiments/runs/fliptrack_v02r16_qwen25vl3b_severe_20260710T091837Z/severe_image_cache` | 158,180,815 | deterministic/re-derivable cache; run complete |
| `experiments/runs/fliptrack_v02r16_qwen25vl3b_mild_20260710T091837Z/mild_image_cache` | 157,962,137 | deterministic/re-derivable cache; run complete |
| `experiments/runs/fliptrack_v02r16_qwen25vl3b_medium_20260710T091837Z/medium_image_cache` | 148,567,112 | deterministic/re-derivable cache; run complete |
| `experiments/runs/fliptrack_v02r10_qwen25vl3b_severe_20260710T022300Z/severe_image_cache` | 71,392,801 | deterministic/re-derivable cache; run complete |
| `experiments/runs/fliptrack_v02r10_qwen25vl3b_medium_20260710T022300Z/medium_image_cache` | 64,863,454 | deterministic/re-derivable cache; run complete |
| `experiments/runs/fliptrack_v02r10_qwen25vl3b_mild_20260710T022300Z/mild_image_cache` | 62,319,176 | deterministic/re-derivable cache; run complete |
| `experiments/runs/fliptrack_r20_qwen25vl3b_gray_an12_20260711T132513Z/gray_image_cache` | 14,847,616 | deterministic/re-derivable cache; run complete |
| `experiments/runs/fliptrack_r20_qwen25vl7b_gray_an12_20260711T125104Z/gray_image_cache` | 14,843,520 | deterministic/re-derivable cache; run complete |
| `experiments/runs/fliptrack_v02r19_packaged_qwen25vl7b_gray_an29_20260710T145136Z/gray_image_cache` | 14,814,848 | deterministic/re-derivable cache; run complete |
| `experiments/runs/fliptrack_v02r19_packaged_qwen25vl3b_gray_an12_20260710T145116Z/gray_image_cache` | 14,814,848 | deterministic/re-derivable cache; run complete |
| `experiments/runs/fliptrack_v02r19_anchor_step100_gray_an12_20260712T091721Z/gray_image_cache` | 14,814,848 | deterministic/re-derivable cache; run complete |
| `experiments/runs/fliptrack_v02r10_qwen25vl3b_gray_20260710T021200Z/gray_image_cache` | 4,840,256 | deterministic/re-derivable cache; run complete |
| `experiments/runs/fliptrack_v02_qwen25vl3b_gray_20260709T223401Z/gray_image_cache` | 4,816,120 | deterministic/re-derivable cache; run complete |
| `experiments/runs/fliptrack_v02r5_qwen25vl3b_gray_20260710T000548Z/gray_image_cache` | 3,803,232 | deterministic/re-derivable cache; run complete |
| `experiments/runs/fliptrack_v02r7_qwen25vl3b_gray_20260710T010800Z/gray_image_cache` | 3,192,656 | deterministic/re-derivable cache; run complete |
| `experiments/runs/fliptrack_v02r16_qwen25vl3b_gray_20260710T091837Z/gray_image_cache` | 2,656,960 | deterministic/re-derivable cache; run complete |

Cache subtotal: 16,115,223,811 apparent bytes across 22 directories.

Eligible superseded checkpoint:

| Source path | Apparent bytes | Classification |
| --- | ---: | --- |
| `checkpoints/stage0_repro/easyr1_geo3k_recovery30/global_step_30/actor/huggingface` | 8,147,620,485 | superseded 30-step merged engineering checkpoint; 100-step anchor retained |

- Checkpoint index pre-relocation SHA256: `6506676495f63b3469e869c858ad249b241b62b7d682393312eba638534a59e8`.
- Intended checkpoint destination: `/tmp/blindgain_checkpoint_archive/easyr1_geo3k_recovery30/global_step_30/actor/huggingface`.

Guard and verification procedure:
1. Require at least 40 GiB Tier-T free space before each archive operation.
2. Copy to a new partial destination; hash every source and destination file; verify byte counts and stable source metadata.
3. Atomically publish the Tier-T archive and its SHA256 manifest.
4. Remove only the verified source payload, then leave a symlink or relocation marker at the original path.
5. Refresh `reports/storage_usage_snapshot.json`; commit the resulting relocation manifest and actual reclaimed-byte accounting.

Problems:
- Tier T is volatile. These artifacts are either deterministic caches or superseded checkpoint weights; canonical metrics and the current final checkpoint remain persistent.
- Even this relocation may not provide the roughly 75 GiB headroom needed for a guarded 55-GB pilot checkpoint save plus the 20-GiB floor. M2 remains storage-blocked until the post-relocation measurement proves sufficient capacity.

Decision:
- Proceed only with the listed paths. Do not touch unlisted or foreign data.
