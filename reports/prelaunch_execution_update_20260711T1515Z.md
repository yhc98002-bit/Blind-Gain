# Blind Gains Prelaunch Execution Update

Report time: 2026-07-11 15:15 UTC (23:15 Asia/Shanghai)

Status:
- This is an operational engineering/research status report. It does not declare a PI scientific or compute gate passed.
- Ledger tasks L0-L6 and L8 are recorded `pass`; L7 and L9-L13 remain `blocked` in `reports/prelaunch_progress.md`.
- No L13 pilot optimizer step has occurred. L12 preregistration does not exist and has not been merged.
- Branch `agent/gate2-recovery` was pushed through commit `b7a6d93`; the worktree also contains watcher-owned storage files and unrelated user changes that were not staged or reverted.

## Task Matrix

| Task | Ledger | Current evidence | Remaining work |
| --- | --- | --- | --- |
| L0 | pass | Approved shared-save/login-archive dry cycle, guards, retention tests | Refresh quota snapshot before the next large save |
| L1 | pass | canonical-v2 fixtures; 320-row agreement report | Agreement is 0.915625, below 0.95; retained for PI review |
| L2 | pass | `extractor_valid`/`contract_valid`; strict accounting fixtures | None for task scope |
| L3 | pass | Five-step pilot reward smoke; 12,800 train and 601 validation shadows | Scientific efficacy not claimed from smoke |
| L4 | pass | Caption condition path; no image tensors; 100% fixed-store coverage | None for task scope |
| L5 | pass | Frozen 1,288-row filtered Geometry3K train subset | None for task scope |
| L6 | pass | Consistency auditor/report repairs; GPU-hours is descriptive | None for task scope |
| L7 | blocked | Five conditions launched; four active, caption prefix preserved | Finish all conditions, summarize, produce distinct audited MD/JSON |
| L8 | pass | One-shot R20 report with all 11 cells | Human contact-sheet audit remains separate for L12 |
| L9 | blocked | 72B choice remains registered | No safe serving window yet; TP2/TP4 only, node-local ephemeral weights |
| L10 | blocked | MathVerse/MMMU 3B/7B base rows now complete | Five-condition ViRL39K sample audit remains |
| L11 | blocked | One-shot 100-pair harder-document batch generated | 3B/7B real and 7B caption scoring remains |
| L12 | blocked | Dependencies not complete | L7 outputs, human R19 audit, two-PI sign-off |
| L13 | blocked | Configs prepared; launch prohibited | Requires merged L12 first |

## Node Placement

The PI placement policy is committed in `docs/PRELAUNCH_BRIEF.md` and implemented by `src/ops/run_placement.py`.

| Node | GPUs | Project job | Placement |
| --- | --- | --- | --- |
| an12 | 0-3 | Anchor continuation from step 80 | One synchronous EasyR1/FSDP job, TP1, one replica |
| an12 | 4-7 | Free at report time | Deliberately left free during anchor host-memory peak characterization |
| an29 | 1 | L7 real | Independent TP1 replica |
| an29 | 5 | L7 gray | Independent TP1 replica |
| an29 | 6 | L7 noise | Independent TP1 replica |
| an29 | 7 | L7 no-image | Independent TP1 replica |
| an29 | 0,2,3,4 | Researcher/foreign neighbors | Normal neighbors; untouched |

Every newly launched run records `node`, normalized `gpu_ids`, `tensor_parallel_width`, `replica_count`, and `placement_justification`. No current training or serving job spans nodes.

## Anchor Recovery

The original anchor did not reach step 100. It failed after step 80 when Ray observed 957.61/1007.52 GB host memory and killed a worker at its 0.95 threshold. Four anchor workers each used approximately 209 GB; project evaluators on disjoint GPUs contributed enough additional host memory to cross the threshold.

Preserved source attempt:
- `experiments/runs/anchor_a0_recipe_3b_geo3k_20260709T224852Z`
- Final status: `fail`, exit 1.
- Original config and native r1v reward remain unchanged.

Recovery evidence:
- Source verification: `experiments/runs/anchor_step80_verify_login_20260711T143511Z`; all eight raw model/optimizer shards passed SHA256.
- Guarded restore: `experiments/runs/anchor_step80_restore_login_20260711T144238Z`; 46,304,794,904 bytes restored and reverified.
- Restore marker SHA256 chain: `checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_80/actor/RAW_STATE_RESTORED_FOR_RESUME.json`.
- Failed import-path startup is preserved at `...resume80_20260711T150253Z`; no trainer import or GPU allocation occurred.
- Failed overlong-Ray-socket startup is preserved at `...resume80_20260711T150357Z`; no GPU allocation occurred.
- Active continuation: `experiments/runs/anchor_a0_recipe_3b_geo3k_resume80_20260711T150633Z`.

The active continuation has loaded model, optimizer, scheduler/RNG extra-state on ranks 0-3 from `global_step_80` and entered registered validation. A one-minute host-memory trace is running at `experiments/runs/anchor_resume_host_memory_watch_20260711T151344Z`.

## L7 Blind Solvability

Registered contract for every condition:
- filtered Geometry3K train plus untouched test: 1,889 rows;
- greedy pass plus 16 samples/item;
- temperature 1.0 for samples, top_p 1.0, max tokens 2,048;
- canonical-v2 and pilot-reward-v1;
- group size G=5 and fixed answer-tag prompt contract.

Progress at report time:

| Condition | Run | Status | Durable rows |
| --- | --- | --- | ---: |
| real | `...real_an29_20260711T141452Z` | running | 700 |
| gray | `...gray_an29_20260711T141458Z` | running | 928 |
| noise | `...noise_an29_20260711T141503Z` | running | 864 |
| no-image | `...none_an29_20260711T141514Z` | running | 100 |
| caption | `...caption_an12_20260711T142842Z` | paused/fail | 332 |

Caption was deliberately paused to isolate anchor host memory. Its 332-row prefix is batch-aligned and passes the registered resume validator. Prefix SHA256: `9ca0ae90cff47b30d68a427e855ebadf31714eb01d7ef41cd860df9b3bfe76ee`. Details are in `reports/l7_caption_pause_for_anchor.md`.

## R20 Confirmatory Result

`reports/fliptrack_r20_confirmatory.{md,json}` covers 1,200 one-shot pairs and all eight hardness plus three degradation cells.

| Template | 3B real | 7B real | 3B caption | 7B caption | Automated outcome |
| --- | ---: | ---: | ---: | ---: | --- |
| document | 0.8667 | 0.9967 | 0.0200 | 0.0633 | generator-level-pass |
| geometry | 0.3967 | 0.7567 | 0.0117 | 0.0100 | downgrade-to-R19-selected |
| chart | 0.3900 | 0.6233 | 0.0000 | 0.0067 | downgrade-to-R19-selected |

Geometry and chart miss only the pre-frozen 3B-real lower bound of 0.40. No R21 is authorized or generated. This is an automated template outcome, not a PI gate declaration.

## L10 Base Rows

MathVerse inference completed for all 3,940 rows/model. The original wrappers were preserved `fail` because the old validator missed timestamp-nested workbooks; versioned recovery validated and hashed the existing outputs without rerunning inference.

MMMU v1 was preserved after a real adapter failure: a lone carriage return inside LaTeX split one TSV record. `MMMU_LOCAL_V2` escapes the byte and round-trips as exactly 1,050 unique rows with zero null image paths.

| Model | Benchmark | `Acc_final` | `Acc_strict` | extractor valid | contract valid |
| --- | --- | ---: | ---: | ---: | ---: |
| 3B | MathVerse | 0.2817 | 0.0173 | 0.3662 | 0.3662 |
| 7B | MathVerse | 0.3406 | 0.0632 | 0.4906 | 0.4906 |
| 3B | MMMU | 0.4819 | 0.0067 | 0.0590 | 0.0590 |
| 7B | MMMU | 0.5133 | 0.2114 | 0.4829 | 0.4829 |

The source runs and native MMMU scores are documented in the appended v2 section of `reports/base_external_benchmarks.md`. L10 remains blocked because ViRL39K has not run.

## Storage

- The unexpected L3 `global_step_5` checkpoint was listed before deletion, hashed twice, and removed only after all 24 files passed verification.
- Reclaimed bytes: 40,970,253,322.
- Preserved checksum manifest: `experiments/runs/pilot_reward_smoke_an29_20260711T114247Z/global_step_5_retention_expired.sha256`.
- Step-80 anchor raw state is currently restored on shared storage for resume and remains independently archived in login `/tmp`.
- Storage guards passed the restore operation. A fresh quota-aware usage measurement is still required before the next large checkpoint save because the current snapshot predates restore/cleanup activity.

## Code Changes

Key recovery implementations in this round:
- R20 builder now validates private template metadata from each cell's declared input while accepting the intentionally stripped public manifest.
- L3 smoke audit partitions 12,800 training and 601 final-validation shadows.
- Run placement policy and atomic placement recorder added.
- MMMU TSV writer escapes lone carriage returns; V2 configs/data preserve v1 artifacts.
- VLMEval validator now accepts timestamp-nested workbooks; infer-only recovery preserves source mode.
- Guarded raw-checkpoint restore verifies source, partial copy, published copy, and conflicts.
- Anchor resume launcher preserves native reward/config, pins EasyR1 import path, uses short Ray paths, and refuses concurrent project evaluators.

Focused verification executed in this round includes:
- 34 L3 reward/audit tests;
- 16 R20/metric tests;
- 16 MMMU adapter/placement tests;
- 34 scorer/postprocess tests;
- 21 storage/restore/retention tests;
- 33 sharded-launcher/placement tests;
- anchor resume launcher and native-anchor binding tests.

## Problems

- L1 parser agreement remains below the requested 0.95 threshold and is explicitly a PI review item.
- The anchor continuation is active but has not completed a resumed optimizer step or step 100.
- L7 is incomplete; the no-image condition is substantially slower because many samples consume the full 2,048-token budget.
- R19 human contact-sheet findings are still unfilled in `reports/fliptrack_v02r19_human_audit.md`; this blocks L12.
- L9, ViRL39K, and L11 scoring have no safe GPU window while anchor peak memory is being characterized and an29 runs L7 plus normal foreign neighbors.

## Decisions

- Keep the anchor continuation isolated until its first optimizer-step host-memory peak is measured.
- Keep the L7 caption prefix paused and resumable; do not treat it as a completed cell.
- Preserve all failed runs and superseded v1 artifacts; do not rewrite their statuses as success.
- Keep R20 geometry/chart downgraded under the frozen criteria and do not generate a rescue split.
- Continue to report ledger task completion separately from PI gate decisions.

## Next Actions

1. Observe anchor validation completion, first resumed optimizer step, and host-memory peak.
2. Resume L7 caption only if measured host-memory headroom is safe; otherwise leave it queued until anchor completion.
3. Refresh the quota-aware shared-storage snapshot before the step-100 save window.
4. Complete L7, build v2 summaries and distinct audited artifacts, then fill preregistration quantities.
5. Launch ViRL39K, L11 scoring, and L9 TP2/TP4 stress in the next safe GPU windows.
6. Request PI/team contact-sheet audit only when the L12 package is otherwise ready.
