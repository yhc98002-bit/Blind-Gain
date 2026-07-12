# Blind Gains Prelaunch Execution Update

Generated: 2026-07-12 06:38 UTC / 14:38 Asia/Shanghai

Status:
- L7 is complete as a measurement task with a passing independent audit; this is not a PI gate declaration.
- L3 is blocked after a self-audit found that the historical smoke actually used TP2 while claiming TP1. The launcher, auditor, stack provenance, and cleanup path are repaired; a replacement five-step TP1 run awaits four free GPUs.
- L9 72B strong-caption generation and L10 ViRL evaluation are active. The anchor step-100 fixed evaluation is also active.
- L12 remains a draft only. No pilot arm has taken an optimizer step, and L13 remains blocked.

Task ledger:
| Task | State | Current evidence |
| --- | --- | --- |
| L0 | pass | Shared-save to login-archive dry cycle passed all nine checks; storage guards and retention are active |
| L1 | pass | canonical-v2 audit complete; agreement 0.915625 is below 0.95 and explicitly retained for PI review |
| L2 | pass | `extractor_valid`/`contract_valid` split and strict-gain identity tested |
| L3 | blocked | Historical TP mismatch rejected by v6 audit; replacement TP1 smoke pending |
| L4 | pass | A3 caption path has 100% frozen-corpus coverage and no image payload |
| L5 | pass | 1,288 filtered training IDs frozen at SHA256 `8631d015ee8593669b46cc707b9fe1fb3690391520bccf416b64bbb2306ff7d1` |
| L6 | pass | Consistency auditor and non-gating GPU-hours reporting active |
| L7 | pass | Five conditions complete; all 13 independent audit checks true |
| L8 | pass | R20 one-shot 1,200-pair confirmatory run complete; document passes, chart/geometry downgraded to R19-selected |
| L9 | active | 72B combined R19/R20 question-blind caption store at 2,896/4,800 |
| L10 | active | Layer-1 rows complete; five ViRL conditions active |
| L11 | pass | One-shot harder-document calibration complete and still too easy at 7B real=1.00 |
| L12 | blocked | Draft generated; human R19 audit and both PI signatures remain |
| L13 | blocked | Depends on L3 and merged L12; no optimizer process launched |

Evidence:

## L7 Geometry3K blind solvability

- Report: `reports/blind_solvability_geo3k_v2.md`.
- Machine audit: `reports/blind_solvability_geo3k_v2_audited.json`, `status=pass`.
- Corpus: 1,288 frozen filtered-train items plus 601 untouched test items, exactly 1,889 per condition.
- Responses recomputed by the final audit: 160,565; score mismatches 0; invalid native shadows 0; MathRuler errors 0.
- Contract: greedy plus n=16 at temperature 1.0, 2,048 tokens, G=5, pilot-reward-v1, canonical-v2, POSIX 5-second symbolic guard.

Untouched Geometry3K test results:
| Condition | Pilot greedy accuracy | Canonical greedy accuracy | Mean q_i |
| --- | ---: | ---: | ---: |
| real | 0.1498 [0.1215, 0.1797] | 0.1747 [0.1464, 0.2030] | 0.3818 [0.3594, 0.4030] |
| gray | 0.0832 [0.0632, 0.1049] | 0.0899 [0.0682, 0.1131] | 0.2364 [0.2190, 0.2539] |
| noise | 0.0749 [0.0549, 0.0965] | 0.0815 [0.0599, 0.1048] | 0.2399 [0.2229, 0.2574] |
| none | 0.0682 [0.0483, 0.0882] | 0.0682 [0.0483, 0.0882] | 0.2326 [0.2159, 0.2506] |
| caption | 0.1963 [0.1664, 0.2280] | 0.2097 [0.1780, 0.2429] | 0.4064 [0.3834, 0.4288] |

- These are base-model corpus measurements, not pilot outcomes or causal estimates.
- Draft-only preregistration: `reports/preregistration_pilot_v1_DRAFT_20260712T0608Z.md`.

## L3 correction

- Historical run: `experiments/runs/pilot_reward_smoke_an29_20260711T165700Z`.
- Immutable log line 207 records `tensor_parallel_size: 2`; the old manifest claimed TP1 and one replica.
- Historical reward arithmetic remains valid for all 13,401 rows, but placement/provenance is invalid.
- Re-audit: `reports/pilot_reward_smoke_historical_reaudit_v6.json`, `status=fail`.
- Current launcher derives TP1 and four rollout replicas from a read-only run-local YAML snapshot.
- Each replacement run snapshots EasyR1 revision, full worktree diff, and patched logger; v6 verifies every hash and runtime TP.
- The unavoidable step-5 checkpoint uses an isolated `checkpoints/smoke/<run_id>` namespace. Cleanup requires a passing v6 audit, inventories and hashes every file before deletion, rechecks all hashes, and records the retention event in the run manifest.
- Focused L3 tests pass; the complete repository suite is 435 passed.

## Anchor

- Native-reward anchor reached step 100 and produced the verified final merged checkpoint documented in `reports/anchor_step100_oom_recovery_v2.md`.
- Final merged digest: `0653b7a428b19d99b1be9f1efece0cbcaf8156cacb49c44e6238f7c65b28d004`.
- A continuity audit found the step-80 resume reopened EasyR1's file logger with mode `w`. The surviving structured log contains validation step 80 and training steps 81–100 only.
- Machine continuity audit: `reports/anchor_metric_continuity_audit_v1.json`, `status=fail`.
- Consequence: checkpoint completion is valid, but a continuous machine-auditable 0–100 reward/KL curve is unavailable. The run remains an engineering anchor, not a claimed published reproduction.
- The resume-safe logger patch is now explicit, applied, tested with a sentinel log, and pinned in future run manifests.

## Active jobs

| Node/GPU | Job | Progress | Placement |
| --- | --- | ---: | --- |
| an12 GPU0 | ViRL real | 516/4,096 | TP1 replica |
| an12 GPU1 | ViRL gray | 534/4,096 | TP1 replica |
| an12 GPU2 | ViRL noise | 544/4,096 | TP1 replica |
| an12 GPU3 | ViRL no-image | 484/4,096 | TP1 replica |
| an12 GPU4 | ViRL caption | 472/4,096 | TP1 replica |
| an12 GPU5 | Anchor step-100 fixed real evaluation | 1,026/1,889 | TP1 replica |
| an12 GPUs6-7 | Free | available for post-caption QA | reserved only when launch preflight passes |
| an29 GPUs1,5,6,7 | Qwen2.5-VL-72B captioner | 2,896/4,800 | one TP4 replica, single node |
| an29 GPUs0,2,3,4 | Foreign process | normal neighbor | untouched |

- GPU utilization logging remains active under `logs/gpu_util_an12.jsonl` and `logs/gpu_util_an29.jsonl`.
- At the report snapshot, an12 GPUs0-5 held 61.5-64.2 GiB each; GPUs6-7 were empty. The L9 GPUs on an29 held about 80.9 GiB each at 99-100% utilization.

Problems:
- Human R19 contact-sheet audit is still pending. Contact sheets are:
  - `reports/contact_sheets/fliptrack_v02r19/header_cued_table_code_v02.png`
  - `reports/contact_sheets/fliptrack_v02r19/coordinate_register_twenty_point_x_v02.png`
  - `reports/contact_sheets/fliptrack_v02r19/starred_series_value_nine_v07.png`
- L1 agreement remains below the requested 0.95 threshold and is exposed for PI review, not waived.
- L9 must finish and release four an29 GPUs before the corrected L3 smoke can run.
- L10 is intentionally long: each item receives one greedy and 16 sampled 2,048-token responses.
- Latest completed quota-aware snapshot recorded 135,071,206,912 bytes free on Tier S. The 20 GiB shared floor remains enforced.

Decision:
- Keep L13 blocked and do not inspect nonexistent pilot metrics.
- Finish L9 captions, verify the committed 4,800-row store, delete the 146,833,336,607-byte ephemeral 72B checkout after hash validation, then launch the corrected L3 smoke on an29 GPUs1,5,6,7.
- Use an12 GPUs6 and 7 for concurrent one-replica R19 and R20 strong-caption QA after the combined caption store commits.
- Preserve all failed/superseded evidence and publish versioned replacements; do not rewrite historical numbers.

Next actions:
1. Complete and validate the L9 72B caption store.
2. Hash-delete the ephemeral 72B weights and launch the five-step TP1 L3 replacement.
3. Build R19/R20 caption-QA adapters from the same committed store; run one TP1 QA replica on an12 GPU6 and one on GPU7.
4. Audit the replacement smoke with v6, publish `pilot_reward_spec_v3.md`, and checksum-delete its retention-expired checkpoint.
5. Aggregate L9 per-template leakage and publish `reports/strong_caption_stress.md` after QA and deletion evidence exist.
6. Continue L10 and anchor evaluation without changing their contracts.
7. Keep final L12 absent until the human audit and both PI approvals are recorded.
