# L0 Storage Preflight

Status:

- `blocked`. The guards and retention implementation pass focused tests, but neither compute node exposes a writable persistent local path that satisfies the 40 GiB floor. The required pilot dry save/read/merge therefore has not been performed.
- This report does not declare a compute or scientific gate passed.

Evidence:

## Capacity and writability

Measured 2026-07-11. Byte-exact `df -B1` outputs and mount metadata were collected over SSH; GiB values below are binary GiB.

| Node | Path/mount | Capacity GiB | Free GiB | User writable | Eligible use |
| --- | --- | ---: | ---: | --- | --- |
| `an12` | `/tmp` and `/var/tmp` (`/dev/loop0`, XFS) | 31.98 | 18.47 | `/tmp`: yes; `/var/tmp`: no | no: below 40 GiB floor even before a write |
| `an12` | `/dev/shm` (tmpfs) | 503.76 | 499.13 | yes | staging only; process-survival checkpoints prohibited |
| `an12` | `/run/user/22847` (tmpfs) | 100.75 | 100.75 | yes | staging only; process-survival checkpoints prohibited |
| `an12` | `/logdir` (XFS) | 99.95 | 96.29 | no, root-owned | unavailable |
| `an12` | `/var/lib/containerd` (XFS) | 399.80 | 392.77 | no, root-owned | unavailable and reserved for system use |
| `an29` | `/tmp` and `/var/tmp` (`/dev/loop0`, XFS) | 31.98 | 1.14 | `/tmp`: yes; `/var/tmp`: no | no: below 40 GiB floor even before a write |
| `an29` | `/dev/shm` (tmpfs) | 503.76 | 350.06 | yes | staging only; process-survival checkpoints prohibited |
| `an29` | `/run/user/22847` (tmpfs) | 100.75 | 100.75 | yes | staging only; process-survival checkpoints prohibited |
| `an29` | `/logdir` (XFS) | 99.95 | 57.79 | no, root-owned | unavailable |
| `an29` | `/var/lib/containerd` (XFS) | 399.80 | 81.13 | no, root-owned | unavailable and reserved for system use |
| login | `/tmp` (ext4) | 814.62 | 339.11 at initial probe | yes | Tier T archival path already used for anchor state; not visible as node-local pilot storage |
| login | `/HOME/paratera_xy/pxy1289` | 100.00 | 31.51 | yes | Tier S2; project cap 15 GiB, small archives only |

The supplied reference claim of approximately 339 GiB free under compute-node `/tmp` is not true inside either current SSH environment. The 339 GiB figure applies to login-node `/tmp`.

## Shared quota accounting

Bare `df` is rejected because it reports the whole Lustre filesystem. `lfs quota` is permission-restricted and returns explicitly inaccurate zero values. The quota-aware measurement command is:

```bash
.venv/bin/python scripts/measure_storage_usage.py \
  --root /XYFS02/HDD_POOL/paratera_xy/pxy1289 \
  --output reports/storage_usage_snapshot.json
```

It runs `du -sx --block-size=1` concurrently over every direct child of the quota root, verifies that the child set remains stable, and atomically publishes the sum. The 2026-07-11T04:48:50Z measurement took 541 seconds:

| Quantity | Bytes | GiB |
| --- | ---: | ---: |
| documented conservative quota | 536,870,912,000 | 500.000 |
| allocated | 446,513,242,112 | 415.848 |
| remaining | 90,357,669,888 | 84.152 |
| guard floor | 21,474,836,480 | 20.000 |

The pre-brief baseline was 92.7 GiB free. This first live allocated-byte measurement was 8.55 GiB lower and guarded the step-60 merge. A snapshot fails closed after six hours or if its quota root/status is invalid.

After verified step-60 raw and merged relocation, the same command completed at 2026-07-11T05:12:41Z in 201.073 seconds:

| Post-relocation quantity | Bytes | GiB |
| --- | ---: | ---: |
| allocated | 400,215,797,760 | 372.730 |
| remaining | 136,655,114,240 | 127.270 |

The exact snapshots are retained as `reports/storage_usage_snapshot_20260711T044850Z.json` and `reports/storage_usage_snapshot_20260711T051241Z.json`; `reports/storage_usage_snapshot.json` contains the newest measured values for guard consumption.

## Project footprint

| Project path/store | Allocated bytes | GiB |
| --- | ---: | ---: |
| `checkpoints/` | 70,764,924,928 | 65.905 |
| `experiments/runs/` | 4,147,412,992 | 3.863 |
| `artifacts/models/` | 39,761,457,152 | 37.031 |
| `data/` | 8,621,109,248 | 8.029 |
| caption-named JSONL/image manifests under `data/` and `experiments/` | 410,744,186 | 0.383 |
| `logs/` before old-log archive | 4,501,504 | 0.004 |

## Guards and retention

- `src/ops/storage_guard.py` implements the Tier-S 20 GiB quota-headroom floor and Tier-T 40 GiB free-space floor. It rejects `tmpfs`/`ramfs` for process-survival artifacts.
- `scripts/storage_guard.py` records append-only JSONL decisions. Real zero-byte probes refused both compute-node `/tmp` paths with exit 75.
- `src/ops/easyr1_checkpoint_guard.py` and `docs/easyr1_storage_guard_patch.diff` provide a pilot-only pre-save hook. The patch is prepared but deliberately not applied while the native anchor is running.
- Merge and download launchers now require guards; downloads require a positive conservative byte budget.
- `scripts/relocate_easyr1_raw_checkpoint.py` verifies the newer merged checkpoint and every older raw-state checksum before latest-only deletion. It records paths, byte counts, hashes, and deletion status in both a report and the anchor run manifest.
- `scripts/relocate_merged_checkpoint.py` copies to a partial directory, rehashes every file, commits a shared marker, and only then removes the shared merged source.
- Focused verification at 2026-07-11T04:50Z: `25 passed` across storage guards, raw/merged relocation, merge launcher, download launchers, and EasyR1 pilot hook.

## Reclamation

- The preregistered list is `reports/storage_preflight_reclamation.md`.
- `logs/setup/`, `logs/downloads/`, and `logs/gpu_jobs/` were archived to `/HOME/paratera_xy/pxy1289/blind-gains-s2/log_archives/prelaunch_wave0_logs_20260711T045259Z.tar.gz`.
- Archive size: 38,444 bytes. Source and extracted per-file SHA256 manifests were identical before source removal. Run record: `experiments/runs/storage_log_archive_login_20260711T045259Z/`.
- Tier-S2 Blind Gains use after archival: 124,460 bytes, below the 15 GiB cap.
- Anchor step-60 merge completed on `an12` at 2026-07-11T04:55:20Z. Raw relocation completed at 05:06:18Z under `experiments/runs/easyr1_raw_relocation_anchor_a0_step60_login_retry_20260711T045723Z/`; the raw manifest SHA256 is `fff8f83e3a8275d511a3a7d51c79f4345eae9501c78fbabf7a8c08b1e546a6a3`.
- Steps 20 and 40 raw states were checksum-verified, listed in `reports/raw_checkpoint_retention.md`, recorded in the anchor run manifest, and then deleted. Step 60 is the sole retained raw state for that run.
- The step-60 merged checkpoint relocation completed at 05:08:05Z under `experiments/runs/easyr1_merged_relocation_anchor_a0_step60_login_20260711T050714Z/`. Its archive is 8,147,616,341 bytes with manifest SHA256 `f1ca68d3c356fe10587a771c04b39c3e55dc7cb7a3450f51506e77cc44c1def5`; only shared relocation metadata remains.

Problems:

- **Blocking resource question:** which writable persistent node-local directories should be used on `an12` and `an29`? The paths must support at least one approximately 46 GiB raw pilot checkpoint while preserving 40 GiB free. Provisioning user-owned subdirectories on a sufficiently large local disk, or supplying an approved equivalent, is required.
- The 1-step EasyR1 save/read/merge dry run is blocked by that missing path. Using `/dev/shm` would violate the explicit storage contract.
- Pilot checkpoint configs remain unmodified until a valid per-node path is known. No pilot optimizer step has been launched.

Decision:

- Keep L0 `blocked`; do not reinterpret tmpfs capacity as eligible scratch.
- Select the L9 strong captioner as **32B**, because no eligible writable serving-node scratch has at least 200 GiB free after accounting. This is a size decision only; the download remains blocked until approved scratch exists.
- Continue the native anchor untouched. Use login `/tmp` only for the already-practiced, checksummed anchor archive flow.

Next actions:

- Refresh the shared usage snapshot before its six-hour freshness window expires or before the next large shared write, whichever comes first.
- Obtain the two approved writable persistent local paths.
- Configure pilot save roots, apply the explicit pilot-only EasyR1 hook, and run the required 1-step save/read/merge dry test.
- Only after those checks pass may L0 be reconsidered and Wave 1 begin.
