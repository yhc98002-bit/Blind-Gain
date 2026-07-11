# Blind Gains Prelaunch Execution Update

Snapshot: 2026-07-11 17:00 UTC

Status:
- This is an execution snapshot, not a PI gate declaration.
- L0, L1, L2, L4, L5, L6, L8, and L11 are recorded `pass` in `reports/prelaunch_progress.md` because their named deliverables exist and the objective auditor accepts them.
- L3, L7, L9, L10, L12, and L13 remain `blocked`. No pilot optimizer step has been taken and L12 is not merged.
- Current git HEAD is `476c97ae7c3f9136e362c76c7186b0bb27fa9e2b` on `agent/gate2-recovery`; this commit is pushed to `origin/agent/gate2-recovery`.

## Task Matrix

| Task | Ledger | Current evidence |
|---|---|---|
| L0 | pass | Shared-save to login-archive dry cycle and guard/retention tests remain valid. |
| L1 | pass | canonical-v2 fixtures pass; agreement is 0.915625 and remains explicitly below the 0.95 PI-review threshold. |
| L2 | pass | extractor/contract validity split and exact StrictGain identity are implemented. |
| L3 | blocked | New 5-second symbolic-grader guard is unit-tested; replacement five-step smoke is active on `an29`. |
| L4 | pass | Caption arm has exact fixed-store coverage and no image tensor path. |
| L5 | pass | Frozen 1,288-row Geometry3K train subset hash remains `8631d015...6ff7d1`. |
| L6 | pass | Consistency checks and non-gating utilization reporting remain in force. |
| L7 | blocked | Real/gray/noise complete; no-image paused at a validated 1,104-row prefix; caption is 1,120/1,889 and active. |
| L8 | pass | R20 has all 1,200 pairs and 11 cells; document passes, geometry/chart are downgraded to R19-selected. |
| L9 | blocked | 72B ModelScope download is active in `an29` `/dev/shm`; TP4 caption generation and QA remain. |
| L10 | blocked | MathVerse/MMMU rows complete; ViRL39K five-condition sample remains. |
| L11 | pass | One-shot report complete; 3B real 0.69, 7B real 1.00, 7B caption 0.04; verdict too-easy. |
| L12 | blocked | Requires L7, PI sign-off, and the human R19 contact-sheet audit. |
| L13 | blocked | Hard ordering remains enforced; no pilot arm has launched. |

## Active Jobs

| Node | GPUs | TP / replicas | Run | State and expected artifact |
|---|---:|---:|---|---|
| an12 | 0,1,2,3 | TP1 / one synchronous RL job | `experiments/runs/anchor_a0_recipe_3b_geo3k_resume80_20260711T150633Z` | Restored native-reward anchor has completed step 84/100 and continues untouched toward the final checkpoint. |
| an12 | 6 | TP1 / 1 | `experiments/runs/blind_solvability_v2_geo3k_filtered_v2_timeoutguard_caption_an12_20260711T154213Z` | Guarded caption L7 condition, 1,120/1,889 rows at snapshot. |
| an29 | 1,5,6,7 | TP1 / one synchronous RL job | `experiments/runs/pilot_reward_smoke_an29_20260711T165700Z` | Guarded L3 five-step smoke starting from config hash `66e75b45...6725058`; exact four-GPU colocated placement. |
| an29 | none | TP0 / 0 | `experiments/runs/modelscope_ephemeral_qwen25vl72b_l9_session_an29_20260711T160604Z` | ModelScope download through supervised reverse proxy; about 74.8 GB of 146.8 GB present at snapshot. |

Foreign jobs occupy `an29` GPUs 0,2,3,4. They are normal neighbors and are untouched.

## L3 Guard Recovery

Evidence:
- The first no-image L7 process stalled after row 100 in a CPU-only state consistent with an unbounded MathRuler/SymPy call.
- `src/rewards/pilot_reward.py` now bounds both the optimized MathRuler verdict and the native-r1v shadow at 5 seconds and logs guard/error validity fields.
- Adversarial hanging-grader fixtures pass. The smoke auditor now rejects missing guard metadata or invalid native shadows.
- Pilot configs pin `symbolic_grader_timeout_seconds: 5.0`.
- The replacement no-image evaluator advanced past the old frontier before its planned L3 pause, so the old exact mechanism remains inferential rather than overclaimed.
- Paused prefix report: `reports/l7_none_pause_for_l3_guard_smoke.md`.

Decision:
- L3 remains blocked until the active smoke completes five optimizer steps and the v4 audit passes all 12,800 training plus exact validation-shadow checks.
- After smoke, resume no-image from the immutable 1,104-row prefix on a free TP1 GPU.

## Anchor Recovery

Evidence:
- Raw step-80 model/optimizer state was restored only after all eight shards passed SHA256.
- The continuation loaded ranks 0-3, completed validation, and has passed resumed steps 81-84.
- First resumed-step watcher minimum available memory was 795,235,916 KiB and maximum monitored RSS was 213,021,556 KiB.
- Caption coexistence has remained far below the previous Ray 95% host-memory kill condition.
- Detailed report: `reports/anchor_step100_oom_recovery.md`.

Decision:
- Keep the anchor untouched through step 100.
- Before step-100 save, refresh quota-aware shared usage; then hash, merge, and apply latest-raw-only retention exactly as registered.

## L7 State

| Condition | Rows | Manifest | State |
|---|---:|---|---|
| real | 1,889 | `blind_solvability_v2_geo3k_filtered_v2_real_an29_20260711T141452Z` | complete |
| gray | 1,889 | `blind_solvability_v2_geo3k_filtered_v2_gray_an29_20260711T141458Z` | complete |
| noise | 1,889 | `blind_solvability_v2_geo3k_filtered_v2_noise_an29_20260711T141503Z` | complete |
| none | 1,104 | `blind_solvability_v2_geo3k_filtered_v2_timeoutguard_none_an29_20260711T153747Z` | planned pause; prefix SHA256 `01a630b7...a1b2f` |
| caption | 1,120 | `blind_solvability_v2_geo3k_filtered_v2_timeoutguard_caption_an12_20260711T154213Z` | active |

Problems:
- Final L7 report cannot be generated until none and caption reach 1,889 rows.
- The final audit must recompute every score under the guarded implementation and report any mismatch; old finite-call scores are not assumed valid merely because generation completed.

## L8 and L11

Evidence:
- R20 automated outcomes remain: document passes; geometry and chart are downgraded to R19-selected under frozen criteria; no R21 is minted.
- A full-suite audit exposed that R20's historical metric hash referenced a mutable live path. The repair preserved the original hash, recovered the exact blob from commit `40589245`, and stores it at `src/fliptrack/frozen_r20/fliptrack_metrics.py`.
- Targeted R20 tests pass 3/3 and the full repository suite passes 400/400 in 76.54 seconds.
- L11 report: `reports/document_v_next_calibration.md`; machine artifact: `reports/document_v_next_calibration.json`.

Decision:
- Do not reinterpret the L11 7B saturation as success. The family is recorded too easy and receives no second batch this round.
- Do not alter R20 outputs or frozen hashes in response to later scorer maintenance.

## L9 Download

Evidence:
- Public ModelScope artifact: `Qwen/Qwen2.5-VL-72B-Instruct`, 51 files, 146,833,336,607 bytes.
- License: Qwen License Agreement; research use is allowed and redistribution requires notices and attribution.
- Direct ModelScope failed; the documented proxy fallback succeeds through a supervised SSH reverse tunnel.
- Tier-T guard passed with 375,222,919,168 bytes free before the 160 GB reservation and a 42,949,672,960-byte floor.
- Route and license report: `reports/modelscope_72b_route_probe.md`.

Decision:
- Weights stay only in `/dev/shm/blind-gains/models/Qwen2.5-VL-72B-Instruct`.
- Serving is one single-node TP4 replica; both R19 and R20 are captioned in the same model load.
- Delete weights after caption stores commit and record the deletion in `reports/strong_caption_stress.md`.

## Tests and Audits

- Full suite: 400 passed in 76.54 seconds.
- Latest prelaunch objective audit: `reports/prelaunch_objective_audit_20260711T1646Z.json`, status pass.
- The objective audit confirms exact L0-L13 ledger shape and named reports for every recorded pass.
- No current pass is used to assert PI approval of L12 or launch authority for L13.

Problems:
- L3 guarded smoke has not completed.
- L7 no-image and caption are incomplete.
- ViRL39K five-condition scoring has not started because the exact guarded reward smoke is not yet revalidated.
- Human R19 audit and PI preregistration sign-off remain external gates.
- GitHub proxy transport is intermittent, but current HEAD is pushed as of this snapshot.

Next actions:
1. Monitor L3 smoke through five steps; run the v4 shadow audit and publish a versioned L3 report.
2. Resume no-image from 1,104 rows; finish caption; run L7 summary and true audit artifacts.
3. Finish 72B download, run one TP4 combined R19/R20 caption store, build 7B caption-only QA, report per-template leakage, then delete weights.
4. Use the first released four-GPU window for ViRL39K conditions after L3 returns to pass.
5. Continue anchor to step 100, refresh quota before save, merge/hash, and enforce raw-state retention.
6. Present completed L7 outputs and the existing R19 contact sheets for PI/team review before L12 can merge.
