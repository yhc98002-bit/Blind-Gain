# Blind Gains Continuation Status - 2026-07-10 16:38 UTC

Status:
- Gate 2 is not passed and has not been declared passed. The current machine check remains false on the unfinished anchor, unrun three-arm mechanical pilot, externally dirty worktree, and full-window idle audit.
- The frozen R19 FlipTrack package passed its automated controls, but its status is `automated_pass_human_audit_pending`. Final human audit is still a scientific gate.
- The recipe-scale Geometry3K anchor is healthy through step 40/100 on `an12` GPUs 0-3.
- The 4,096-item ViRL39K blind-solvability extension is complete for 3B `none` and `caption`, complete for 7B `none`, and active for the remaining seven model-condition cells.
- Both `/tmp`-capacity failures were recovered through strict immutable prefix resume; neither partial result was discarded or silently mixed.

## Gate Picture

| Area | Current state | Evidence |
| --- | --- | --- |
| Measurement repair P0.1-P0.5 | complete | `reports/gate2_progress.md` |
| Anchor P1.1 | blocked on normal completion, 40/100 | `reports/anchor_recipe_report.md` |
| Layer-1 base evaluation P1.2 | complete | `reports/base_external_benchmarks.md` |
| Two-node smoke P1.3 | prepared, execution blocked by occupied GPUs | `reports/multinode_smoke.md` |
| FlipTrack P1.4-P1.8 | automated controls complete; human audit pending | `reports/fliptrack_v02r19_exact_package.md` |
| Dataset/license/decon P1.9-P1.10 | complete | `reports/gate2_progress.md` |
| Git hygiene P1.11 | blocked by external `CLAUDE.md` deletion and untracked `AGENTS.md` | `git status --short` |
| Mechanical pilot P2.1 | code/config ready; waits only for P1.1 | `reports/stage2_pilot_readiness.md` |
| Geometry3K blind audit P2.2 | complete and V3 integrity-audited | `reports/blind_solvability_geo3k_v3_audited.md` |

Machine checklist: `reports/gate2_machine_check.json`. Human audit form: `reports/fliptrack_v02r19_human_audit.md`.

## R19 Result

Frozen package:
- Manifest: `data/fliptrack_v02r19_artifact_expanded/manifest.jsonl`, 1,200 pairs.
- Exact package report: `reports/fliptrack_v02r19_exact_package.md`.
- Machine summary: `reports/fliptrack_v02r19_exact_package.json`.
- Release composition: 300 document, 600 geometry, 300 chart pairs.

| Model/mode | Pair accuracy | Strict pair accuracy | Member accuracy | Collapse rate |
| --- | ---: | ---: | ---: | ---: |
| 3B real | 0.5617 | 0.3717 | 0.7129 | 0.0958 |
| 3B caption | 0.0125 | 0.0125 | 0.0954 | 0.4392 |
| 3B gray | 0.0000 | 0.0000 | not headline | 1.0000 |
| 3B noise | 0.0000 | 0.0000 | not headline | 1.0000 |
| 7B real | 0.8092 | 0.8067 | 0.8900 | 0.0167 |
| 7B caption | 0.0208 | 0.0208 | 0.0954 | 0.3817 |
| 7B gray | 0.0000 | 0.0000 | not headline | 1.0000 |
| 7B noise | 0.0000 | 0.0000 | not headline | 1.0000 |

Interpretation boundaries:
- Real-image scale gain is +0.2475 pair accuracy; paired McNemar p = 1.84e-53.
- Caption scale gain is +0.0083 overall and is not significant at the aggregate level (p = 0.1433).
- Document captions rise from 0.01 to 0.06 and are significant within that template (p = 0.0007286). Caption compressibility is therefore low, not absent.
- The 3B document format-valid rate is only 0.4483, so its high final-answer accuracy must not be presented as strict formatted accuracy.
- These are base-model instrument controls, not an RLVR causal result.

## Anchor

Run: `experiments/runs/anchor_a0_recipe_3b_geo3k_20260709T224852Z`.

| Step | Validation overall | Validation format | Validation accuracy | Mean response length |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 0.0774 | 0.1015 | 0.0532 | 378.64 |
| 10 | 0.6231 | 0.9750 | 0.2712 | 292.44 |
| 20 | 0.6398 | 0.9750 | 0.3045 | 312.08 |
| 30 | 0.6581 | 0.9684 | 0.3478 | 340.18 |
| 40 | 0.6697 | 0.9784 | 0.3611 | 322.38 |

Step-40 checkpoint controls:
- Merge run: `experiments/runs/easyr1_checkpoint_merge_anchor_a0_step40_an12_20260710T161553Z`, status `complete`.
- Verification: 825 indexed tensors, 14 files, 8,147,616,341 total bytes; all file SHA256 values are in `merged_checkpoint_verification.json`.
- Eight raw FSDP/optimizer shards were re-read, checksum-matched, and moved to `/tmp/blindgain_checkpoint_archive/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_40/actor`.
- Shared step-40 actor retains the merged checkpoint, extra state, and `RAW_STATE_RELOCATED.json`; raw source-shard count is zero.

## ViRL39K Audit

Snapshot at 2026-07-10 16:38 UTC. Each condition targets the same deterministic 4,096-item audit manifest, greedy plus 16 sampled responses, group size 5.

| Model | Condition | Rows | State | Node/GPU | Run |
| --- | --- | ---: | --- | --- | --- |
| 3B | real | 3,090/4,096 | running | an29/1 | `blind_solvability_virl39k4096_real_an29_20260710T115307Z` |
| 3B | gray | 3,098/4,096 | running | an12/7 | `blind_solvability_virl39k4096_retry_gray_an12_20260710T120007Z` |
| 3B | noise | 2,810/4,096 | resumed/running | an29/5 | `blind_solvability_virl39k4096_3b_resume_noise_an29_20260710T161010Z` |
| 3B | none | 4,096/4,096 | complete | an29/0 | `blind_solvability_virl39k4096_none_an29_20260710T094154Z` |
| 3B | caption | 4,096/4,096 | complete | an29/6 | `blind_solvability_virl39k4096_caption_an29_20260710T115310Z` |
| 7B | real | 684/4,096 | running | an12/5 | `blind_solvability_virl39k4096_7b_retry_real_an12_20260710T150508Z` |
| 7B | gray | 484/4,096 | resumed/running | an29/6 | `blind_solvability_virl39k4096_7b_resume_gray_an29_20260710T161021Z` |
| 7B | noise | 586/4,096 | running | an12/6 | `blind_solvability_virl39k4096_7b_retry_noise_an12_20260710T152149Z` |
| 7B | none | 4,096/4,096 | complete | an29/7 | `blind_solvability_virl39k4096_7b_none_an29_20260710T115323Z` |
| 7B | caption from fixed 3B store | 1,976/4,096 | running | an12/4 | `blind_solvability_virl39k4096_7b_retry_caption_an12_20260710T150505Z` |

Recovery details:
- Original 3B-noise run failed at 2,504 rows because `an29:/tmp` was full.
- Original 7B-gray retry failed at 260 rows for the same reason.
- `scripts/run_blind_solvability.py` now proves a source JSONL is the current manifest's canonical, duplicate-free, batch-aligned prefix and checks condition, answers, image hashes, metadata, score fields, and the complete decoding contract before copying any row.
- New run manifests hash the resume JSONL and source manifest, record `resume_from`, and use `/dev/shm/blind-gains` for deterministic condition caches.
- Both real partials passed validation exactly before relaunch; current output files include the validated prefix plus new rows.
- The fixed ViRL 3B caption source separately passes exact 4,297-image coverage plus schema, literal question-blind prompt, prompt hash, 384-token, greedy-decoding, and single-model checks in `reports/caption_store_contract_virl39k4096_3b.json`.

Supplemental caption sensitivity:
- A model-matched 7B question-blind caption store is being generated on `an29` GPU 7 under `experiments/runs/virl39k_sample4096_qwen25vl7b_captionstore384_retry_20260710T163500Z`.
- The first attempt accidentally started two writers after an operator retried during the long input-hash preflight. It is explicitly marked `fail`, and its output is quarantined as `store_shard_0.invalid_concurrent_writers.jsonl`.
- The launcher now takes an atomic run-directory lock before hashing and refuses initialized run directories. The retry has exactly one worker.

## Cluster Snapshot

At 16:38 UTC:
- `an12` GPUs 0-3: anchor training; GPUs 4-7: 7B-caption, 7B-real, 7B-noise, and 3B-gray ViRL audits.
- `an29` GPU 1: 3B-real; GPU 5: resumed 3B-noise; GPU 6: resumed 7B-gray; GPU 7: supplemental 7B caption store.
- `an29` GPUs 0,2,3,4 hold an unrelated Qwen3-Omni service at about 66 GB each. It was not started or modified by this project.
- A full 2x8 P1.3 window is therefore unavailable without terminating active scientific jobs and the unrelated service. The measured all-reduce and actual-model FSDP launchers are prepared, not falsely reported as executed.

## Code And Tests

New recovery commits:
- `f31fb32`: strict blind-evaluation prefix resume and `/dev/shm` cache default.
- `e937a1a`: verified raw checkpoint relocation utility and adversarial tests.
- `4412cf7`: caption-store launch lock and duplicate-launch regression tests.

Verification:
- Full suite after relocation and launch-lock changes: 183 passed in 316.41 seconds.
- Resume/launcher/scoring target: 14 passed.
- Checkpoint relocation target: 4 passed.
- Caption launch-lock target: 3 passed.
- Caption contract/audit targets: 20 passed with exact Geometry3K and ViRL manifest coverage.
- Blind-summary integrity target: 11 passed; the new V3 aggregator also validated all 2,702 existing Geometry3K rows across five conditions.
- GitHub branch: `agent/gate2-recovery`; draft PR: `https://github.com/yhc98002-bit/Blind-Gain/pull/1`.

## Storage

- Shared project: 58 GB measured after step-40 rotation.
- Shared checkpoints: 23 GB; experiment records: 3.0 GB.
- Login checkpoint archive: 173 GB; `/tmp` has about 371 GB free.
- Reproducible inactive image caches: 25 GB under `/tmp/blind-gains/noise_image_cache_archive_20260710`, with original paths preserved as symlinks.
- Login `/tmp` is temporary, not durable storage. Raw optimizer resume state must move to canonical project storage before node/login maintenance.

Problems:
- P1.1 needs 60 more optimizer steps at roughly 25-30 minutes per step.
- The three-arm mechanical pilot cannot start before P1.1 completes under the registered dependency.
- Final R19 human audit is pending and cannot be substituted by model scoring.
- The worktree is externally dirty due only to `CLAUDE.md` deletion and untracked `AGENTS.md`; these were not touched or staged.
- The historical full-window idle audit remains false even though the recent corrective window had no >30-minute project-idle violations. The official window was not narrowed to game the gate.

Decision:
- Keep the anchor and all active audits unchanged.
- Use strict resumable outputs and `/dev/shm` for future conditioned-image caches.
- Require exact item, decoding, manifest, and recomputed-score agreement across all five conditions before publishing a blind-solvability aggregate.
- Preserve the failed duplicate caption run as explicit negative provenance; never score or merge it.
- Do not launch P2.1 early and do not declare Gate 2.

Next actions:
- Finish and aggregate the 3B ViRL conditions first, then publish the five-condition blind-solvability report with bootstrap intervals and real-vs-blind quadrants.
- Finish the 7B supplemental audit and compare fixed-3B-caption versus model-matched-7B-caption sensitivity.
- Continue anchor validation at step 50; merge, verify, and relocate the next raw checkpoint at step 60.
- Ask the PI/team to complete `reports/fliptrack_v02r19_human_audit.md` when they are ready to exercise the explicit scientific gate.
