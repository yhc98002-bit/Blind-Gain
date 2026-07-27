# Cross-Path Storage Cleanup — 2026-07-27

Scope: the four storage paths specified by the PI — `/XYFS02/HDD_POOL/paratera_xy/pxy1289`,
`/HOME/paratera_xy/pxy1289`, `/tmp` + `/var/tmp`, and `/dev/shm` — across an12, an29
and the login nodes.

Status: **complete.** 230 paths removed, 300.501 GiB apparent. All verification
checks pass. The live M5 training job was not disturbed.

## 1. Authorized scope (PI rulings, 2026-07-27)

1. **XYFS02 — BlindGain only.** Sibling projects (`AudioDiffusion` 310 GB,
   `benchmark_v2_runtime` 129 GB, `AudioDiffusion_envs` 54 GB, `.uv_cache` ~26 GB)
   not touched on shared Lustre.
2. **Both large raw-FSDP blocks held** — the 137 GiB seed-2 archive and the
   38.1 GiB seed-3 A3 step-100 raws.
3. **tmpfs — ADSR staged models dropped** (191 GB); `/dev/shm/blind-gains`
   kept hot for M5-350/400 and the Mini-A5 retry.
4. **/HOME — caches plus the self-labelled quarantined duplicate venv.**

## 2. Shared vs node-local classification (established before any deletion)

| Path | Type | Shared? | Evidence |
| --- | --- | --- | --- |
| `/XYFS02/HDD_POOL/paratera_xy/pxy1289` | Lustre XYFS02 | **shared** | identical `stat %d %i` = `431160220 180144339110885094` from an12 and an29; identical NID source; `df` used agrees to 0.0014% |
| `/HOME/paratera_xy/pxy1289` | Lustre XYFS01 | **shared** | identical `stat %d %i` = `3356821666 144116747383948379` |
| `/tmp`, `/var/tmp` | xfs on `/dev/loop0` | **node-local** | same path different inode (`util_cbb47c8…`: 49711172 on an12 vs 795 on an29); disjoint contents; different `df` used |
| `/dev/shm` | tmpfs, 504 GB/node | **node-local** | independent contents and `df` |

`/tmp` and `/var/tmp` are bind-mounted subdirectories of **the same 32 GB image as `/`** —
one budget shared with the OS root. `/var/tmp` had no pxy1289 entries on either node.

Login-node `/tmp` is a third filesystem (`/dev/sda3`, 815 GB, 9% used) holding ~60 MB
of pxy1289 scratch — not worth sweeping.

> **Recorded trap:** `stat -c '%d' /tmp` returns **1792 on both nodes** because both host
> their root image on `/dev/loop0`. Cross-node device-number equality proves nothing;
> only inode + contents + `df` are valid tests.

## 3. What was removed

| Tier | Node | Paths | Apparent GiB | `df` before → after |
| --- | --- | --- | --- | --- |
| `an29-devshm` | an29 | 69 | 181.170 | 230G → 60G used (445G free) |
| `an12-devshm` | an12 | 42 | 95.107 | 134G → 39G used (465G free) |
| `home` | ln207 | 5 | 17.802 | 100G/**0 free** → 86G/**15G free** |
| `an12-tmp` | an12 | 59 | 5.808 | 15G → 8.8G used (24G free) |
| `xyfs02-blindgain` | ln206 | 8 | 0.614 | quota 1,159,701,254,144 → 1,159,064,731,648 B |
| `an29-tmp` | an29 | 47 | 0.000 (436 KB) | 20K → 456K free (still 100%) |
| **total** | | **230** | **300.501** | |

Categories: ADSR staged model weights and uv/wheelhouse caches in tmpfs (191 GB),
~33 stale Ray session directories, orphaned PSM3/libfabric segments, loky semaphores,
a tmpfs venv untouched since 06-09, pip/whisper caches, a quarantined duplicate venv,
stale scratch and lock files, two incomplete dataset download trees, and one
unreferenced HF hub duplicate.

Per-path manifests with sizes, mtimes and (where applicable) SHA256:
`manifest_{an29,an12}_devshm.json`, `manifest_{an12,an29}_tmp.json`,
`manifest_home.json`, `manifest_xyfs02.json`. Dry-run counterparts retained
alongside. Target lists retained as `targets_*.json`.

## 4. Method

`scripts/blindgain_cleanup_20260727.py` — manifest-first, dry-run-by-default. Each
target must pass **all** of:

1. absolute, normalized, strictly deeper than an allowlisted root;
2. not equal to, inside, or an **ancestor of** any protected path;
3. owned by the invoking uid (`lstat`, symlinks not followed);
4. **not held open by any live process** — `/proc/*/fd` + `/proc/*/maps` +
   `cwd` + `exe` scan, with the kernel's `" (deleted)"` suffix stripped so
   unlinked-but-mapped segments still match;
5. `realpath()` still satisfies (1) and (2).

Live handles are re-scanned immediately before the removal loop, and every path is
re-vetted at that point. Deletion walks bottom-up per item, so one failure cannot
cascade. This makes the 2026-07-26 failure mode — a scope escape beyond the authorized
path list — structurally impossible rather than merely unlikely.

Validated against two adversarial fixture sets (`safety_test2.json` retained):
29 hostile inputs — allowlist roots themselves, protected trees, ancestors of protected
trees, `/tmp/../etc`, `/etc/passwd`, both `/HOME` spellings — **all 29 rejected, 0 accepted.**

## 5. Deviations from the approved plan

Nine, each with its evidence. Five are cases where the plan would have destroyed
something load-bearing.

1. **`.vscode-server` (5.4 GB) held, not deleted.** The plan authorized it as
   "regenerates on next IDE connect", but a live VS Code remote agent host was
   running on ln207 (26 processes). Because `/proc` scans are per-node and `/HOME`
   is shared Lustre, the tool cannot self-protect this from another node. Deleting
   it would have killed an active IDE session. `/HOME` relief came to 17.8 GiB
   instead of ~24 GiB, which still cleared the wall.
2. **`*_retry_no_xet` polarity was inverted in the plan.** The plan proposed
   deleting the `_retry_no_xet` copies as duplicates. In fact the **originals** are
   incomplete — `hf_rayguan_HallusionBench` 56M with **22 `.incomplete` files**,
   `hf_MMVP_MMVP` 4.7M with 6 — and the retries are the complete copies
   (0 incomplete, 1109 vs 423 files). Deleted the incomplete originals instead;
   the retries are retained and verified present.
3. **`data/modelscope/MathVerse/images.zip` (130M) held.** The plan called it a
   duplicate of an extracted form. There is no extracted `images/` directory — the
   zip is the only copy of the MathVerse images.
4. **`artifacts/hf_home/hub/datasets--TIGER-Lab--ViRL39K` (1.7 GB) held.** Not a
   dead cache: `scripts/prepare_virl39k.sh`,
   `scripts/launch_virl39k_decon_hash_text.sh` and
   `scripts/launch_virl39k_decon_finalize.sh` all read
   `snapshots/812ec617…/39Krelease.parquet`, and the M7 ViRL39K decomposition is
   unfinished.
5. **`artifacts/hf_home/hub/datasets--hiyouga--geometry3k` (57M) held — live job
   dependency.** `hiyouga/geometry3k@train|hiyouga/geometry3k@test` is the
   `data_manifest` for the M5 anchor runs including `launch_m5_anchor_longhorizon.sh`,
   which is the **currently running** segment 300→350, executed with
   `TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home`. Deleting this cache
   could have broken the live job and the 350→400 continuation.
6. **`/dev/shm/blind_gains_an12_m5_anchor_longhorizon_400.lock` held.** The plan
   classified `blind_gains_an12_*.lock` as stale; the `/proc` scan found this one
   **open by the live job**. Caught by the tool, not by the plan.
7. **`/HOME` is spelled differently per login node.** ln206 exposes it as a symlink
   into `/XYFS01/HOME/...`; ln207 as a direct mount. The first `/HOME` execute
   attempt ran on ln206 and **fail-closed with 0 of 5 paths accepted**
   (`symlink resolves outside allowlist`). Nothing was deleted. Fixed by adding
   `/XYFS01/HOME/paratera_xy/pxy1289` as an allowlisted root and mirroring every
   `/HOME` protection under that spelling, then re-validating the fixture set.
8. **Repo-root `pymp-*` / `tmp*wandb-*` dirs and non-venv `__pycache__` not swept.**
   The former had mtimes coinciding with live watcher activity; the latter sit under
   `scripts/`, `src/`, `tests/`, which are on the denylist. Combined ~4.4 MB — not
   worth relaxing a protection that guards the record surface.
9. **an29 `/tmp` reclaimed 436 KB, not 32 GB, and remains 100% full.** Confirmed
   pre-existing diagnosis: `du -shx /tmp` on an29 was 7.2 MB; the exhausted resource
   is the node root image (`/var` 25 GB, `/usr` 7.2 GB), largely other users' data.
   See §7.1.

## 6. Held by ruling — considered and deliberately not deleted

| Item | Bytes | Reason |
| --- | --- | --- |
| `blindgain_archive/login_tmp_checkpoint_archive` | 137 GiB (147,089,537,640 B, 138 files) | Rescued **completed** seed-2 A1+A3 raws. `storage_preservation_seed2_20260722.md` records the explicit decision *"Retain the persistent copies."* Ruling 2. Verified present. |
| `checkpoints/pilot/mech_a3_caption_seed3/global_step_100/actor` raws | 38.1 GiB | Seed 3 is complete and recorded, but `scripts/blindgain_raw_checkpoint_cleanup.py:177` guards *"no seed-3 lineage is a candidate"*. Ruling 2. Verified: 12 raw shards present. |
| `checkpoints/m5_anchor_longhorizon_400/global_step_150/actor` raws | 43.1 GiB | `…cleanup.py:178` protects it as *"M5 fallback resume state"*; sole surviving copy after the 07-26 archive loss; M5 has already lost step 250 irrecoverably. Verified: 12 raw shards present. |
| `checkpoints/m5_anchor_longhorizon_400_resume150/global_step_300/actor` | 43.1 GiB raw + 7.6 GiB merged | Active resume source of the running segment. Verified: 12 raw shards present. |
| `/dev/shm/blind-gains` | an29 59.6 GiB, an12 35.6 GiB | Kept hot. Ruling 3. |
| XYFS02 siblings | ~519 GB | Ruling 1 — their record surfaces were not audited. |
| `/HOME/.conda/envs`, `sa3_foundation_runtime` (beyond quarantine), `cuda`, `.local`, `.cache/{modelscope,huggingface,clap,vllm}` | ~71 GB | Ruling 4. |

**No checkpoint byte was removed.** No manifest contains a path under
`checkpoints/`, `blindgain_archive/`, `reports/` or `configs/` — verified by scan
across all six execute manifests. Because nothing in scope was checkpoint state,
no entry was owed to `pilot_raw_checkpoint_retention.md` or
`m5_raw_checkpoint_retention.md`; this report is the record that both raw blocks
were considered and held.

## 7. Verification (`verify.py`, retained) — ALL CHECKS PASS

- **37** `configs/eval/*.json` entries carrying a `checkpoint_path` all resolve; 0 missing.
  (72 files exist in `configs/eval/`; 37 declare a `checkpoint_path`.)
- **20** training-lineage roots scanned; **0** missing `experiment_log.jsonl`,
  `experiment_config.json`, `generations.log` or `checkpoint_tracker.json`.
- The four seed-1 `experiment_log.jsonl` files behind the published *Training Resource
  Accounting* table are present (82,096 / 82,060 / 203,935 / 163,668 bytes).
- All four held raw/merged checkpoint blocks present with 12 raw shards each.
- Kept caches and corpora intact: geometry3k hub cache, ViRL39K hub cache, dinov2
  `hub` copy, MathVerse `images.zip`, both `_retry_no_xet` trees,
  `Qwen2.5-VL-3B-Instruct`, `mini_a5_train_v1/train.parquet`, `data/virl39k/images`.
- `git status`: **0 tracked files deleted.**
- Live M5 run: `run_manifest.json` still `status: running`; tracker at
  `last_global_step: 300`, `best_val_reward_score: 0.7404`;
  `experiment_log.jsonl` actively appended (349,938 bytes at 04:15Z);
  driver PID 2534607 alive at 19h10m with all four GPUs computing.

One item was flagged and cleared as a false positive:
`checkpoints/pilot/pilot_storage_dry_cycle_login_20260711T094144Z` has no training
telemetry. It is a **storage dry-cycle probe** containing only
`RAW_STATE_RELOCATED.json` and `MERGED_CHECKPOINT_RELOCATED.json` — it never was a
training lineage and never had telemetry. The check's lineage heuristic was
tightened to require either an `experiment_log.jsonl` or a real merged checkpoint.

## 8. Open items for the PI (outside cleanup scope)

1. **an29 `/` is 100% full (456 KB free) with other users' data** — the actual blocker
   on Mini-A5 (`mini_a5_cp_main_an29_20260727T023335Z` → `status: fail`, NCCL
   `DistBackendError`). Needs an admin ticket; no cleanup inside the four authorized
   paths can fix it. BlindGain holds only a few MB there.
2. **M5 boundary durability, time-sensitive.** `cleanup_20260726/report_v1.md` §5
   requires the 350/400 merged boundaries to land on shared quota, and step 350 is
   imminent. If the watcher still targets the destroyed `/tmp` archive tier, the 350
   boundary could be relocated into nothing. Worth confirming before the boundary lands.
3. **`reports/pilot_3seed_summary_v1.md`** — the filename `MAIN_TASKS.md` names as M3's
   required evidence — does not exist; `three_seed_summary_v1.{md,json}` does. Naming
   drift or a missing deliverable.
4. **`artifacts/models/Qwen/Qwen2.5-7B-Instruct` (15 GB)** has no reference in any
   config, report or run manifest. Possibly a never-used text-only baseline.
5. **Three FlipTrack r15 retry run dirs (~461 MB)** stuck at `status: running` since
   07-10, superseded by r17/r19 — left untouched.
6. **Further easy relief if needed:** `.vscode-server` 5.4 GB (once the IDE session
   ends) and `.cache/{modelscope,huggingface,clap,vllm}` ~13 GB on `/HOME`.
