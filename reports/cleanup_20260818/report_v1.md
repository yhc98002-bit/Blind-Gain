# Cleanup 2026-08-18 — RAM-side reclamation, plus repo-root clutter

Requested as "clean up old and redundant files to reduce the occurrence of
OutOfMemoryError (OOM) or other memory/storage overflow issues."

## 0. The distinction that decides where the effort goes

**Disk cleanup cannot prevent the OOM this project actually hit.** The ST3-7B
arm-1 failure was host RAM: 8 ranks each materialized ~95-99 GB (~770 GB) inside
`_save_checkpoint` on a 1007-GiB node. It was fixed by `save_model_only: true`
(verified: the step-20 save then succeeded and training continued). Disk sat at
1.30 TB of a 2.5 TiB quota throughout and was never the constraint.

There is, however, one real memory-side target: **`/dev/shm` is RAM-backed
tmpfs**, so bytes parked there are host memory whether or not any process holds
them open. That is what this pass reclaims. Disk cleanup is a separate concern —
it guards against the *storage-guard wedge* (an over-quota project raises a
terminal error and silently wedges trainers; cost 2.5 days of idle GPUs on
2026-08-12), not against OOM.

## 1. an12 `/dev/shm` — 19.789 GiB of host RAM returned

Tool: `scripts/blindgain_cleanup_20260727.py` (dry-run is its default; every
target must clear allowlisted-root, deny-path, uid-ownership, not-held-open, and
post-realpath re-checks). Targets built from its own enumerator
(`blindgain_enumerate_scratch_20260727.py`), filtered to `/dev/shm/bg-ray-*`.

| field | value |
|---|---|
| mode | execute |
| node | an12 |
| accepted | 10 paths |
| **accepted_bytes** | **21,248,780,784 (19.789 GiB)** |
| removed | 10 / 10 |
| failures | none |
| rejected | 1 |
| generated | 2026-08-18T17:18:27Z |

Removed: stale Ray spill dirs dated 2026-07-26 → 08-10 —
`bg-ray-c9182a4ad554` (5.12 GiB), `1cea6313ad3d` (3.02), `67e178370dbc` (2.80),
`70c81420c1e2` (2.43), `3a4558f03f5e` (2.41), `58517dc9be1b` (2.13),
`1e57d119ca89` (1.04), `83c2c0fdbf4d` (0.83), `66de229ef2d2`, `297564c43bdb`.

Measured effect on an12: `/dev/shm` 63 G → 43 G (13% → 9%); host *available*
650 → 669 GiB; `free -g` shared column 234 → 214 GiB.

Manifests: `manifest_an12_devshm_dryrun.json`, `manifest_an12_devshm_execute.json`,
inventory `scratch_an12_devshm.json` + `.sizes.txt`, targets
`targets_an12_devshm.json`.

## 2. Deliberately refused / not touched

| path | why |
|---|---|
| `/dev/shm/bg-ray-868dafa61268` (1.06 GiB) | on the tool's DENY list (it was a live job's tmpdir when that list was written). Refused by the tool, not by me. Recoverable later if the deny entry is retired. |
| `/dev/shm/bgray` (3.09 GiB) | **live**: `RAY_TMPDIR` of the running LH2 stage-1 trainer |
| `/dev/shm/blind-gains` (35.6 GiB) | DENY-listed; holds `gpu_claims/` (the occupancy guard's state) and 33 GB of model checkouts. Policy-protected — not overridden. |
| `psm_02835a62`, `psm_c0cb3580`, `nccl-*`, `sem.*`, `torch_*` | held open by live processes |
| 7 × `blind_gains_an12_*.lock` | 0 bytes each; a stale guard lock might gate a future launch, and removing them frees nothing. No benefit, nonzero risk. |
| `tmp/` (30 MB, git-tracked) | active analysis scripts. Distinct from the `tmp<random>` junk below — removal used explicit names, never a `tmp*` glob. |
| an29 `/dev/shm` | already at 1% (752 MB). Nothing to reclaim. |

## 3. Repo-root clutter — 142,121 bytes, 21 directories

All dated 2026-07-27, all untracked, each either empty or containing only torch
RPC stubs (`_remote_module_non_scriptable.py` + `__pycache__`), none referenced
by any live process cwd: 8 × `pymp-*`, and `tmp3cs8jox2wandb-media`,
`tmp7x7wat9l`, `tmpccmr2iw4`, `tmpfwggwqzdwandb-media`, `tmpimt82o_1`,
`tmpliz9m47bwandb-artifacts`, `tmpmyx_7j6u`, `tmpqgzkgtfhwandb-artifacts`,
`tmpsmov6vv2wandb-artifacts`, `tmpusqcb7h_wandb-media`, `tmpv0fr5oux`,
`tmpw50m166g`, `tmpyhqdwjf0`.

Removed in two batches (93,500 + 48,621 bytes) with a per-directory
`git ls-files --error-unmatch` refusal guard. Space value is negligible; the
point is that the repo root no longer carries 21 stray directories. Something
still creates these in the cwd (torch RPC / wandb temp dirs), so they will
reaccumulate — worth a `TMPDIR` fix in the launchers if it becomes annoying.

Also removed earlier the same day: one 12 KB empty run-dir skeleton
(`easyr1_checkpoint_merge_st3_std_step20_an12_20260818T162402Z`) left by a failed
launch, whose 0-byte `run_manifest.json` breaks `json.load` scans over
`experiments/runs/*`.

## 4. NOT done — needs a PI decision

The large disk pools are policy-protected, and this pass did not override them:

| pool | size | why untouched |
|---|---|---|
| `checkpoints/m7` | 388 G | `apply_storage_retention_rule_20260816.py` **hard-aborts** on `/m7/` (`FORBIDDEN_MARKERS`); m7 feeds the pending two-seed R3 readout |
| `checkpoints/mini_a5` | 267 G | in the rule's scope, but its dry-run plans **0 deletions** — the step-20 dirs are retained as `best_global_step`, so deleting them would violate the registered keep = best ∪ terminal ∪ §21 |
| `checkpoints/lh2_anchor_seed2_3b_geo3k` | 87 G | hard-abort marker `lh2`; stage 1 is live |
| `checkpoints/pilot` | 152 G | real research output, not a mechanical intermediate; its readouts should be confirmed archived first |

Roughly 290 GB sits in superseded intermediate steps whose terminal step is
retained in the same directory (m7 seed-2 arms, mini_a5 step-20s). Reclaiming it
requires either retiring a `FORBIDDEN_MARKERS` entry or relaxing "keep best" —
both are policy changes to a ratified retention rule, not config tweaks.
**Flagged, not taken.** Note also that a 2 TB quota top-up is expected, which
makes this moot for the current plan.

## 5. Verification

- LH2 stage 1 undisturbed: GPUs 0-3 on an12 at 73-77% before and after.
- The two ST3 step-20 readouts on an12 GPUs 4-5 continued across the cleanup.
- The cleanup tool re-scanned 2,742 open handles immediately before deleting and
  reported 0 failures.
- `tmp/` still present at 30 MB; repo root now contains only the 16 expected
  directories.
