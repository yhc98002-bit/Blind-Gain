# Blind Gains Research Progress Review

- **Snapshot time:** 2026-07-16 14:30 UTC
- **Repository:** `/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain`
- **Branch / HEAD:** `agent/gate2-recovery` / `9f1f7c18f7d927586f792136e65f65d15196c8f2`
- **Purpose:** engineering and research-status snapshot for PI review. This document does not declare a scientific gate passed.

## Executive Answer

The four **registered seed-1 pilot training runs** all reached global step 100 and exited successfully:

1. A1 real images: training complete.
2. A2 gray images: training complete.
3. A2b no image: training complete.
4. A3 fixed question-blind captions: training complete.

The four-arm experiment is **not yet complete end to end**. A2-gray finished training, but its post-training retention watcher failed when the login-node `/tmp` storage guard rejected relocation of the step-80 raw state. Consequently, A2-gray still lacks a merged step-100 Hugging Face checkpoint, the registered FlipTrack R19 evaluation, and the 601-item Geometry3K evaluation/audit. The step-100 raw state remains intact, so A2 should be recoverable without retraining.

There is also an arm-naming discrepancy that matters for review:

- The current preregistered pilot uses **A1, A2, A2b, and A3**.
- The original proposal's **A4 optional text-only/math-transfer arm has not been launched**.
- If “A1, A2, A3, and A4” means the four currently executed pilot conditions, the fourth condition is A2b no-image, not proposal A4.

No registered four-arm result has been computed. Performance values from the three completed evaluation lifecycles remain deliberately unopened until A2 lands, avoiding a partial-arm peeking deviation. The required result file `reports/pilot_4arm_seed1_results_v1.md` does not exist yet.

## Registered Pilot Design

The pilot was preregistered before its first optimizer step in [`reports/preregistration_pilot_v1.md`](preregistration_pilot_v1.md).

| Field | Registered value |
| --- | --- |
| Base model | Qwen2.5-VL-3B-Instruct |
| Exact revision | `66285546d2b821cf421d4f5eb2576359d3770cd3` |
| Training corpus | Filtered Geometry3K train subset |
| Frozen subset | 1,288 of 2,101 training items |
| Shared data hash | `f3d88dd1e52ccef833f266880e487eef252193f774c1076f7dfbccd180b450e6` |
| Vision tower | Frozen for pilot arms |
| Reward | Canonical-v2 extraction, mathruler precedence, 0.5 accuracy + 0.5 format |
| Rollout group size | `G=5` |
| Budget | 100 optimizer/global steps per arm |
| Seed | 1 for the first pilot |
| Checkpoints | 0, 20, 40, 60, 80, 100 |
| Main benchmark readout | Greedy, locked-contract, full 601-item Geometry3K test |
| Visual-dependence readout | FlipTrack R19 at registered checkpoints, geometry primary |
| Main arm difference | `image_condition` only: real, gray, none, or fixed caption |

Primary RQ1 is the matched cross-arm change in final benchmark accuracy. Primary RQ2 is the change in R19 geometry pair accuracy. The q-opportunity hurdle contrast, R19 overall, caption contrasts, strict-format accounting, and per-category endpoints are registered secondary analyses.

## Seed-1 Pilot Lifecycle

| Arm | Training | Step-100 model state | R19 step-100 | Geometry3K step-100 | End-to-end status |
| --- | --- | --- | --- | --- | --- |
| A1 real | 100/100, exit 0 | Merged and exact-checkpoint validated | Complete; all 15 marker checks true | 601 rows; independent audit pass; 0 static, score, or strict mismatches | Evaluation lifecycle complete; joint analysis withheld |
| A2 gray | 100/100, exit 0 | Raw FSDP/optimizer state intact; merged weights absent | Not run | Not run | Blocked in post-training storage/merge lifecycle |
| A2b no-image | 100/100, exit 0 | Merged and exact-checkpoint validated | Complete; all 15 marker checks true | 601 rows; independent audit pass; 0 static, score, or strict mismatches | Evaluation lifecycle complete; joint analysis withheld |
| A3 caption | 100/100, exit 0 | Merged and exact-checkpoint validated | Complete; all 15 marker checks true | 601 rows; independent audit pass; 0 static, score, or strict mismatches | Evaluation lifecycle complete; joint analysis withheld |
| Proposal A4 text/math | Not launched | None | None | None | Outside the current four-arm pilot |

### Exact Training Runs

| Arm | Immutable run | Placement | Final segment | Config hash | Deviations |
| --- | --- | --- | --- | --- | --- |
| A1 | `experiments/runs/mech_a1_real_resume60_an12_20260714T080855Z` | an12 GPUs 0-3, TP1 x4 | 2026-07-14 08:10 to 2026-07-15 00:36 UTC | `511e6c3276e37b893aeb50be643036635dbd9be165188e8f7e8ccf7d4247e1ab` | Resumed verified step 60 after Ray host-memory pressure; uncheckpointed steps 61-67 excluded; no scientific config change |
| A2 | `experiments/runs/mech_a2_gray_resume60_retry2_an12_20260715T165701Z` | an12 GPUs 0-3, TP1 x4 | 2026-07-15 17:00 to 2026-07-16 08:57 UTC | `2f41f7155e2a84c7da6e6d62bf3697843c35604f2b0c973c4f8466778b9532e7` | Resumed verified step 60 after Ray pressure; retried after an21 release; discarded only uncheckpointed work; no scientific config change |
| A2b | `experiments/runs/mech_a2b_noimage_retry4_an29_20260713T113556Z` | an29 GPUs 0-3, TP1 x4 | 2026-07-13 11:36 to 2026-07-14 16:43 UTC | `5d629d2f5bd8dd8b0af7b83e51213d57e21b93d4030eae82dc621c42c4026bfb` | Fresh restart after a pre-process temporary-filesystem failure; no scientific config change |
| A3 | `experiments/runs/mech_a3_caption_resume20_an29_20260713T144233Z` | an29 GPUs 4-7, TP1 x4 | 2026-07-13 14:42 to 2026-07-14 15:23 UTC | `45ae4c0b5573c2c6cfbab75704c88a4a357c1da7f4ac2de2330d1cf3f20c0945` | Resumed verified step 20 after compute-node temporary-space exhaustion; no scientific config change |

The displayed times cover the immutable final/recovery run segments, not necessarily all earlier superseded attempts. Each final manifest records the node, GPUs, model revision, seed, command, hashes, checkpoint path, and deviations.

### Completed Evaluation Evidence

Exact R19 completion markers exist for A1, A2b, and A3:

- `experiments/runs/mech_a1_real_resume60_an12_20260714T080855Z/step100_fliptrack_complete.json`
- `experiments/runs/mech_a2b_noimage_retry4_an29_20260713T113556Z/step100_fliptrack_complete.json`
- `experiments/runs/mech_a3_caption_resume20_an29_20260713T144233Z/step100_fliptrack_complete.json`

Each marker confirms 1,200-pair coverage, exact checkpoint identity, locked decoding and prompt contract, the registered R19 manifest, and complete aggregate artifacts.

Independent Geometry3K audits exist for the same three arms:

- `experiments/runs/pilot_geo3k_step100_audit_m2_geo3k_a1_real_seed1_step100_an12_gpu4_20260715T210056Z_20260715T211733Z/audit.json`
- `experiments/runs/pilot_geo3k_step100_audit_m2_geo3k_a2b_noimage_seed1_step100_an12_gpu5_20260715T210056Z_20260715T211906Z/audit.json`
- `experiments/runs/pilot_geo3k_step100_audit_m2_geo3k_a3_caption_seed1_step100_an12_gpu6_20260715T210056Z_20260715T212255Z/audit.json`

All three audits completed with exit 0, exactly 601 rows, and zero row-identity, score-recomputation, or strict-accounting mismatches.

## A2-Gray Failure Analysis

This is a storage-policy failure after successful training, not an optimization failure.

1. A2 training reached step 100 and its run manifest closed `complete`, exit 0.
2. The retention watcher attempted to relocate step-80 raw state to the login-node archive.
3. The storage guard refused the copy because it would leave less than the required 40 GiB scratch floor.
4. The watcher then failed closed. The dependent R19 and Geometry3K queues terminated without launching evaluations.

Exact failure evidence:

- Retention watcher: `experiments/runs/pilot_resume60_checkpoint_watch_mech_a2_gray_resume60_retry2_login_20260715T170029Z`
- Failed relocation: `experiments/runs/easyr1_raw_relocation_mech_a2_gray_resume60_retry2_step80_login_20260716T012028Z`
- Exception: `StorageGuardRefusal: scratch write would leave less than the configured free-space floor`
- R19 queue: `experiments/runs/pilot_step100_eval_queue_a2_gray_login_20260715T211716Z`, failed without artifacts
- Geometry3K queue: `experiments/runs/pilot_geo3k_step100_queue_a2_gray_login_20260715T213231Z`, failed because the R19 dependency failed

Current storage facts:

| Item | Size/state |
| --- | ---: |
| Login `/tmp` available | 49,037,582,336 bytes, about 45.7 GiB |
| Configured scratch floor | 40 GiB |
| A2 step-100 raw files | 40,954,356,556 bytes, about 38.1 GiB |
| A2 step-80 directory | about 46 GiB |
| A2 step-100 directory | about 39 GiB |
| Login checkpoint archive | about 401 GiB |
| Shared persistent allocation | PI reports about 1.0 TB available |

The step-100 `actor/huggingface` directory contains configuration/tokenizer files but no merged model shards or `model.safetensors.index.json`. Both the step-80 and step-100 raw states remain on shared storage because the guard correctly prevented an unsafe partial relocation.

### Required A2 Recovery

1. Inventory the 401 GiB login archive and list/hash retention-expired or superseded contents before moving or deleting anything.
2. Move eligible archive material to approved shared persistent storage, or otherwise create enough login scratch headroom for the raw copy plus the 40 GiB floor and margin.
3. Merge the intact A2 step-100 FSDP state into a Hugging Face checkpoint.
4. Verify the merged index and model-shard SHA256 manifest.
5. Apply latest-raw-only retention and record every relocation/deletion in immutable manifests.
6. Launch new immutable R19 and Geometry3K evaluation queues; do not reuse or overwrite the failed queues.
7. Run the independent 601-row audit, then compute all registered four-arm estimands in one readout.

No A2 retraining is currently indicated.

## Why Pilot Results Are Not Reported Yet

The project explicitly registered a four-arm comparison. Opening A1/A2b/A3 values before A2 is available would permit adaptation to partial results and weaken the preregistration. Therefore:

- available per-arm output files are preserved but not interpreted;
- no three-arm interim result is reported;
- `reports/pilot_4arm_seed1_results_v1.md` remains absent;
- StrictGain, hurdle/rank analyses, paired intervals, recovery fractions, and cross-arm contrasts remain uncomputed;
- M3 seeds 2-3 have not launched.

## Established Findings Before This Pilot

These are completed prior observations and instrument/corpus audits. They are context, not the missing seed-1 four-arm result.

| Work item | Established evidence | Interpretation boundary |
| --- | --- | --- |
| 3B Geometry3K engineering anchor, 100 steps | Test accuracy 0.1498 to 0.4359, gain +0.2862 with CI [+0.2446, +0.3278]; R19 overall +0.0017 [-0.0183, +0.0209]; R19 geometry +0.0083 [-0.0183, +0.0367] | Prior observation; unfiltered corpus, native reward, and unfrozen vision tower differ from pilot A1 |
| FlipTrack R19 | 1,200 pairs: document 300, geometry 600, chart 300; category pair accuracy for 3B real was 0.87 / 0.47 / 0.44; gray/noise floor; attacker and degradation checks pass | R19 chart is “cued chart point-value reading,” not a full legend-to-series localization task |
| R19 human audit | Richard accepted 60/60 sampled pairs on all six checks | Chart notes preserved: answer-pointing circle, inaccurate star sentence, marginal nine-series color separation |
| R20 one-shot split | All validity criteria pass; geometry 0.397 and chart 0.390 narrowly miss the frozen 3B-real >=0.40 floor | Geometry/chart reported as R19-selected robustness evidence, not confirmatory pass |
| 72B caption stress on R19/R20 | Caption-only pair accuracy 0.0533 / 0.0617 | Strong anti-caption-shortcut evidence for the frozen instrument; old 72B weights were hash-deleted |
| Filtered Geometry3K blind-solvability v2 | Greedy real 0.1535, caption 0.1747, gray 0.0651, noise 0.0588, none 0.0503; mean q real 0.363, caption 0.374, gray 0.220, none 0.218 | Caption-mediated accessibility is substantial on this corpus; this is a base-model audit, not training gain |
| Parser/reward audit | Canonical-v2/native agreement 0.9156; all 27 residuals canonical-favorable; 5-step reward smoke logged 13,401 valid shadow rows with no NaNs | Disagreements are retained row by row; mathruler precedence and parser version are frozen |
| 3B ViRL39K 4,096-item audit | Mean q real 0.5115, caption 0.4355, gray 0.4188, noise 0.4251, none 0.4151; all 15 audit checks pass | Registered fork selected strong source/category heterogeneity; H-mixed is the headline |

## Newly Completed 7B ViRL39K Base Audit (M8)

The five-condition 7B audit completed after the last ledger update. It is an inference-only corpus/readiness audit, not a trained-arm experiment.

- Model: Qwen2.5-VL-7B-Instruct revision `cc594898137f460bfe9f0759e9844b3ce807cfb5`.
- Sample: frozen 4,096 ViRL39K items.
- Protocol: greedy plus 16 samples at temperature 1.0, max 2,048 tokens, G=5.
- Conditions: real, gray, noise, no image, and fixed question-blind caption.
- Machine audit: `pass`; all 15 registered checks true; zero recomputed-score mismatches; image hashes and row identities exact.

| Condition | Greedy pilot accuracy | Mean p_i | Mean q_i | Format rate |
| --- | ---: | ---: | ---: | ---: |
| Real | 0.3579 [0.3435, 0.3726] | 0.3058 | 0.5356 | 0.5464 |
| Gray | 0.2456 [0.2327, 0.2595] | 0.2267 | 0.4424 | 0.5280 |
| Noise | 0.2483 [0.2351, 0.2617] | 0.2259 | 0.4439 | 0.5441 |
| None | 0.1824 [0.1702, 0.1939] | 0.2109 | 0.4144 | 0.4558 |
| Caption | 0.1624 [0.1504, 0.1733] | 0.2016 | 0.4458 | 0.6567 |

Evidence:

- [`reports/blind_solvability_virl39k_7b_sample_v1.md`](blind_solvability_virl39k_7b_sample_v1.md)
- `reports/blind_solvability_virl39k_7b_sample_v1.json`
- [`reports/blind_solvability_virl39k_7b_sample_v1_audited.md`](blind_solvability_virl39k_7b_sample_v1_audited.md)
- `reports/blind_solvability_virl39k_7b_sample_v1_audited.json`

These four report files are currently untracked and need a normal consistency/ledger commit before M8 is represented as complete in project bookkeeping.

## Main-Phase Progress M0-M14

| Task | Current evidence-based state | What remains |
| --- | --- | --- |
| M0 preregistration | Complete; both PI approvals recorded and merged before training | No action for seed 1 |
| M1 3B ViRL audit/fork | Complete; 4,096 rows, five conditions, audit pass; H-mixed fork selected | Carry stratification into later readouts |
| M2 pilot seed 1 | All four training runs complete; 3/4 evaluation lifecycles complete | Recover/merge/evaluate A2, then build registered report |
| M3 pilot seeds 2-3 | Not launched | Requires validated seed-1 lifecycle and scheduling |
| M4 registered extensions | Repository transcription/audit complete | Scientific launch remains fail-closed pending PI flat/rising rule and exact merged-at-HEAD authorization marker |
| M5 long horizon | Not launched | M4 authorization and resume-integrity check |
| M6 mini-A5 | Not launched | M4 authorization, pair corpus, reward/grouping audits |
| M7 ViRL 3B decomposition | Not launched | M4 authorization and frozen/decontaminated data readiness |
| M8 7B preparation | Five-condition 4,096-item run and machine audit complete | Reconcile reports, ledger, registry, and M4 computed fields |
| M9 7B flagship | Not launched | M4 authorization and completed/committed M8 readiness |
| M10 support sharpening | Selector, 64-sample protocol, Jeffreys summary, and language lock implemented | Execute within complete post-training readouts |
| M11 non-Qwen audits | Six one-row smoke cells validated; 18 full cells pending | Queue is fail-closed on all four M2 markers; full matrix and audit not run |
| M12 chart v08 | Declared 100-pair calibration and local model/attacker lifecycles structurally complete; values unopened | Human no-zoom audit, 72B caption scoring, gate audit, interpretation, possible freeze and one-shot split |
| M13 paper pipeline | Reusable skeleton, figure/table pipeline, and consistency-safe wording implemented | Populate only after registered results exist |
| M14 merge-back | Not launched | Requires M6, M9 seed 1, and registered M4 addendum |

## M11 and M12 Operational Detail

### M11 Non-Qwen Generalization

The login scheduler process is still alive:

`experiments/runs/m11_generalization_full_recovery_login_20260715T182317Z`

It is GPU-inert in `waiting_m2_priority`, with 18/18 full cells pending. It has validated smoke paths for InternVL3-9B and Gemma-3-12B-IT under real/no-image/caption conditions, but no smoke metric is being treated as a result. Its state file has not advanced since initialization and should be audited/restarted after the exact fourth M2 marker exists rather than assumed to transition correctly.

### M12 Chart V08

Completed structural lifecycles include 3B/7B real, caption, gray, and noise; 7B no-star/random-star necessity; and grouped DINOv2/frequency/metadata attacker runs. Their performance values remain unopened pending the human gate.

The new 72B ModelScope checkout completed on an12:

- Run: `experiments/runs/modelscope_ephemeral_qwen25vl72b_m12_chartv08_an12_20260715T211129Z`
- End: 2026-07-15 22:58 UTC, exit 0
- Inventory: 51 files, 146,833,336,607 bytes
- Tree SHA256: `2a9b2f96fa1a20764ad675dc6fb35afe869f631a0d1bdfe69ace35052e0333e3`
- Volatile path: `an12:/dev/shm/blind-gains/models/Qwen2.5-VL-72B-Instruct`

TP4 strong-caption generation/scoring has not started. The no-zoom human audit has not completed. Freeze and confirmatory generation remain unauthorized. The existing M12 status V5 predates the download completion and is stale.

## Current Compute and Storage State

At 2026-07-16 14:30 UTC:

- an12: all eight GPUs at 0% utilization, 2 MiB used each; no active compute process listed.
- an29: all eight GPUs at 0% utilization, 2 MiB used each; no active compute process listed.
- M11 has a login-node watcher process only; it is not allocating GPUs.
- Shared persistent storage has about 1.0 TB available according to the PI-provided quota update.
- Login `/tmp` is 95% used with about 45.7 GiB available; the Blind Gains checkpoint archive accounts for about 401 GiB.
- `/HOME` has about 31 GiB available and is unsuitable for model/checkpoint weights under the project policy.

Idle GPUs are expected at this exact snapshot only because M2's next operation is checkpoint recovery/merge and the queued M11/M12 jobs are fail-closed on dependencies or human gates. They should not remain idle after A2 recovery or after explicitly scheduling unblocked work.

## Bookkeeping Discrepancies

The live artifacts are ahead of the committed status documents:

1. [`reports/main_progress.md`](main_progress.md) still says A2 is at step 70. A2 actually finished step 100, while its post-training watcher and queues failed.
2. `docs/RESEARCH_DOC.md` has the same stale A2 step-70 description.
3. The ledger says M8 is still running. The five conditions, summary, and independent machine audit are complete, but the four M8 reports are untracked.
4. M12 status V5 says the 72B download is running. The checkout has completed and been hash-verified, but scoring remains pending.
5. M11's process is alive, but its queue state is stale and still reflects the missing four-arm marker.
6. The working tree contains unrelated/user-owned modifications and generated status snapshots. They were not reverted or folded into this review.

Until the ledger and research document are reconciled in one controlled commit, reviewers should use immutable run manifests and this dated snapshot for current operational state, while treating the committed ledger as historical.

## Scientific Limitations at This Snapshot

- There is no complete four-arm seed-1 comparison yet.
- There are no seeds 2-3, so no run-to-run RL variance estimate exists.
- The original optional A4 text/math arm has not been tested.
- No 7B training decomposition has started; M8 is inference-only readiness evidence.
- M11 full non-Qwen generalization is absent.
- Chart v08 is not frozen or confirmed and cannot yet support a headline claim.
- The anchor's large Geometry3K gain and near-zero R19 change are prior observations under a non-matched configuration, not a substitute for M2.

## Recommended Execution Order

1. Recover A2-gray step 100 from the intact raw state and complete its two registered evaluations plus independent audit.
2. Build `reports/pilot_4arm_seed1_results_v1.md` from all four arms in one locked analysis; run the StrictGain identity and registered hurdle/rank checks.
3. Reconcile M2 and M8 machine state into `reports/main_progress.md` and `docs/RESEARCH_DOC.md` without overwriting prior reports.
4. Launch M3 seeds 2-3 only after seed-1 lifecycle validation.
5. Obtain the remaining M4 authorization inputs before M5-M7/M9 training.
6. Use free capacity for M11 full inference and M12 72B caption stress when their exact fail-closed conditions are satisfied.
7. Delete the volatile M12 72B weights only after caption stores/results are committed and the deletion/hash record is written.

## Bottom Line

- **Training completion:** yes for all four registered seed-1 pilot conditions.
- **Scientific experiment completion:** no; A2-gray post-training merge/evaluation is missing.
- **Original proposal A4 completion:** no; it was not part of this pilot and was never launched.
- **Current recovery risk:** operational and storage-related, with intact A2 raw state; no retraining is presently required.
- **Current headline result:** intentionally unavailable until the fourth audited arm completes.
