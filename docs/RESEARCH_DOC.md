# Blind Gains — Living Research Document
Maintained in-repo (suggested path: `docs/RESEARCH_DOC.md`). Codex appends to the experiment logs after every closed task; PIs own §1–§3. Nothing here overrides the merged preregistration.

## 1. Thesis and claims

Multimodal RLVR (GRPO-family) is implicitly assumed to improve visual perception. Mechanistically, within a rollout group the image is encoded once and all reward variance comes from text sampling, so credit flows to text-side decisions; if training items are solvable from priors, captions, or format compliance, reward routes around the pixels. **Claim under test:** benchmark gains from standard multimodal RLVR are substantially text-side, and certified visual dependence does not improve.

**RQ1 (decomposition):** what fraction of RLVR gains survives removing visual information at training time (real / gray / no-image / caption arms)?
**RQ2 (certification):** does training move paired counterfactual flip accuracy (FlipTrack) above nulls?
**Positive control (mini-A5):** can RL move the instrument at all? A small CP-GRPO run (joint pair reward) serves as the RL-trainability existence proof — reframed from "repair" to control.

## 2. Paper 1 / Paper 2 charter (scope amendment, 2026-07-12; PI-2 ratification pending)

**Paper 1 — the measurement paper** ("what RLVR actually optimizes when you hand it images"): blind-solvability audit as a dataset property (multi-family, inference-only); decomposition on two corpora (geo3k, ViRL39K) at two scales (3B seeded, 7B flagship); FlipTrack certification with full validity dossier (attackers+CIs, one-shot R20, 72B caption stress, degradation/scale/SFT controls, mini-A5 RL control); G_format accounting identity; q_i reward-opportunity mechanism; robustness arms (unfrozen tower, long horizon). Renderable-only instrument, framed as artifact-immunity by construction; released as instrument+generator protocol (R19+R20+generator).

**Paper 2 — the method paper** (CP-GRPO as repair, at scale): transfer to external benchmarks, 7B, natural-scene counterfactual pairs, reward shapes/annealing, corpus mixtures, caption-grounded reward variants. Depends on Paper 1's instrument. Scoop mitigation: Paper 1 states the repair direction explicitly as open, timestamping the framing.

**Resist-list (bloat guard):** no extra benchmarks beyond the seven; no new eval templates beyond certified set + doc-vNext; no 32B/72B training (72B = inference stress tool only); no multi-recipe/framework sweeps; no Paper-2 transfer questions inside Paper 1's A5 section.

## 3. Standing design decisions (consolidated; chat-ratified)

Measurement: canonical-v2 parser (agreement-vs-native threshold retired — all residuals must be canonical-favorable with taxonomy); extractor_valid vs contract_valid split; Acc_strict = contract_valid ∧ Acc_final; StrictGain = AnswerGain + G_format (exact identity, fixture-enforced); final-answer-span scoring with tiered matching + ambiguity guard; within-template key-shuffle null; SESOI ±0.05 with paired-CI equivalence language.
Training: decomposition arms freeze the vision tower; anchor = recipe-reproduction arm (native reward, recipe settings, untouched); pilot reward = canonical-v2 extraction → mathruler precedence, 0.5/0.5 weights (evidence vs native pending), itimer 5s guard, native shadow logging; filtered corpus only (frozen ID hash); matched steps, report tokens/wall-clock, no FLOP claims.
Instrument: R20 no-iteration rule (failures downgrade, never regenerate); caption gates at main scale + 72B stress; per-category endpoints (geometry primary, overall secondary, document calibration-only due to 7B saturation); contamination language = "conservative candidates."
Process: preregistration merges before first optimizer step, no peeking; gates computed as AND, PI-declared only; every fix ships an adversarial fixture; honest `blocked` is always acceptable; ledger + goal mechanism per round.
Ops: single-node placement always at our scale; TP no wider than the model needs (TP1 replicas for ≤7B); GPUs grabbed opportunistically, researcher's jobs are normal neighbors; utilization is a report, not a gate; storage = shared-save → login-archive sweep, latest-raw retention, 20 GiB quota floor / guards as backstops; CP-GRPO implementation (Paper-1 mini-A5 and Paper 2) = shared group uid + broadcast pair reward (≡ pair-level normalization), advantage-tensor equivalence test required.

## 4. Completed experiments (headline numbers)

| # | Experiment | Result | Status/caveat |
|---|---|---|---|
| E1 | Recipe anchor, 3B geo3k GRPO, 100 steps | geo3k test 0.1498→0.4359 (+0.2862, CI [+0.2446,+0.3278]); FlipTrack R19 overall +0.0017 [−0.0183,+0.0209], geometry +0.0083 [−0.0183,+0.0367]; gray/noise 0.0000, collapse 1.0 | Prior observation disclosed in revised prereg. Unfiltered corpus (contains test-near conservative candidates); native reward; vision tower unfrozen vs frozen pilot A1 |
| E2 | FlipTrack R19 (1,200 pairs: doc 300/geo 600/chart 300) | 3B real 0.87/0.47/0.44; 7B caption ≤0.06; gray/noise 0; degradation monotone; scale control and attacker gates pass; Richard accepted 60/60 human-audit pairs | Frozen; no R19 edits. v07 chart construct relabeled “cued point-value reading”; circle bypasses legend→series hop, caption is inaccurate, nine-series color separation marginal |
| E3 | R20 one-shot confirmatory (fresh seeds, no iteration) | document: generator-pass; geometry 0.397 / chart 0.390 3B-real → miss the ≥0.40 band only; ALL validity criteria pass (caption ≤0.012@7B, floor 0, monotone) | geometry/chart certification = "R19-selected"; disclosed in prereg |
| E4 | 72B caption stress | R19 pair acc 0.0533; R20 0.0617 | Strongest validity evidence; weights hash-deleted (146.8 GB) |
| E5 | Blind-solvability audit v2 (pilot contract: 2048 tok, pilot reward, filtered 1,288 train + 601 test, 5 conditions × 16 samples) | greedy: real 0.1535, **caption 0.1747 (> real)**, gray 0.0651, noise 0.0588, none 0.0503; mean q_i: real 0.363, caption 0.374, gray 0.220, none 0.218; ≥75% of gray/none items at 0/16 floor | Prereg anchor numbers. v1 (512-tok) superseded, retained |
| E6 | Layer-1 base tables, 3B+7B, 7 suites + blind variants | e.g. 3B MMStar 0.554→0.261 blind; MathVista 0.624→0.329 blind | Harness pinned; local judge; G_format fields |
| E7 | Decontamination | geo3k↔Layer-1: 463 candidates; + train-vs-test → filtered subset 1,288/2,101, SHA 8631d015… | "Conservative candidates" language mandatory |
| E8 | Parser/reward infrastructure | agreement audit v2 = 0.9156, all 27 residuals canonical-favorable (native defects); pilot-reward 5-step smoke: 13,401 rows, shadows valid, no NaN; disagreements ~2% under mathruler precedence | Native r1v lines 45/49 establish 0.5 accuracy + 0.5 format; launched anchor has no kwargs override; pilot matches native |
| E9 | Doc v-next calibration (one-shot 100 pairs) | 3B real 0.69; 7B real 1.00 → too easy | No iteration; harder family = Paper-2/later |
| E10 | Ops/governance | storage guards+retention+quota tooling; goal-loop caught 3 Goodhart patterns (gate-status conjunction, duplicate audited file, registry authorship) — all structurally patched | Methodology section material |
| E11 | ViRL39K blind-solvability, 4,096 items, five conditions | mean q_i: real 0.5115, caption 0.4355, gray 0.4188, noise 0.4251, no-image 0.4151; all 15 independent audit checks pass | Registered fork selects strong source/category heterogeneity; H-mixed headline and stratified readouts |
| E12 | Paper-1 artifact pipeline | section/result/data-card/nonoverlap registries plus immutable builders for decomposition bars, hurdle intervals, dissociation scatter, and audit tables | Pipeline-delivery audit passes; scientific result slots remain explicit and fail closed |

## 5. In flight

- M0: both PIs approved; `reports/preregistration_pilot_v1.md` is final, pins introduction commit `2782815cc057...`, and records merge-as-sign-off before any optimizer step.
- M2: all four arms are active under merged-at-HEAD authorization as single-node four-GPU jobs: A1/A2-gray on disjoint an12 GPUs and A2b/A3 on disjoint an29 GPUs. The first A3 attempt failed before model allocation on in-memory validation image hashing; commit `8c904154...` fixed all 601 validation rows with zero caption misses.
- M8: real/gray/no-image/own-caption 7B runs were gracefully preempted to prioritize M2 A2-gray; 118/126/118/126 batch-aligned rows are preserved and resume-required. The exact-coverage own-caption store and node-local model remain ready; noise is unstarted.
- M11: ModelScope-first downloads and per-file SHA256-verified staging are complete for InternVL3-9B and Gemma-3-12B-IT at an29 `/dev/shm`; deterministic TP1 R19/R20 adapters and launch manifests are ready, while GPU smoke, blind-sample wiring, and registered inference remain.
- M12: the declared 100-pair v08 calibration batch is generated as separate legend-target and point-value families with no answer-pointing cues and explicit no-star/random-star diagnostics; scoring is pending.
- M13: pipeline delivery is complete and machine-audited; registered values remain explicit pending slots and are populated continuously only from hash-pinned readouts.
- Storage: the PI updated HDD_POOL capacity to 1.5 TiB (about 1.0 TiB available). The guard now uses a conservative 1,500-GiB capacity with the 20-GiB floor; storage is not an M2 blocker.

## 6. Upcoming experiments (order; ~60–70 node-days vs ~120 available)

1. **M2/M3** — launch the four-arm 3B pilot at three seeds, with registered hurdle mechanism analysis and checkpointed FlipTrack readouts.
2. **M4** — transcribe and merge the long-horizon, mini-A5, ViRL 3B, and 7B flagship extension registry before those training units launch.
3. **M8** — build the 7B own-caption store and run the 4,096-item pilot-contract blind-solvability preparation.
4. **M5/M6** — fixed step-400 anchor extension and matched CP-versus-member-reward mini-A5 control.
5. **M7/M8/M9** — ViRL 3B decomposition, 7B own-caption readiness, and three-seed 7B flagship.
6. **M10** — fold 64-sample support-sharpening checks into every applicable readout.
7. **M11/M12** — non-Qwen audits and two-subfamily chart v08 fill safe idle capacity; M13 maintenance consumes only landed, hash-pinned readouts.
8. **M14** — 7B CP merge-back readouts only after mini-A5 and flagship seed 1.

## 7. Open decisions and pre-committed forks

- PI-2 (GPT) ratification pending: prereg changes; Paper 1/2 charter; mini-A5 promotion; robustness arms; 7B arm set (A2-gray dropped at 7B); second-family list.
- **ViRL39K fork (pre-committed, decide by rule when L10 lands):** substantial blind reward-opportunity → thesis generalizes, run flagship as planned; genuinely visual corpus → reframe as "shortcut availability is a measurable corpus property," geo3k as demonstration, audit as the headline tool. Two-sided interpretation table goes into the prereg (optional change #5).
- Venue: ICLR 2027 preferred, not binding; scope is claim-driven, not deadline-driven.
- Human dependencies: R19 audit (now), R20 audit sample (this week).

## 8. Document maintenance protocol

Codex: after each ledger `pass`, append one row to §4 or update §5/§6 in the same commit; never edit §1–§3 or §7. PIs: decisions land as one line in §3 or §7 with date. This file never substitutes for the preregistration or the ledgers; on conflict, the merged prereg wins.
