# Blind Gains Prelaunch Brief

This document records the PI-authored prelaunch brief received on 2026-07-11. The storage layout in L0 is resolved by the PI decision recorded in `reports/storage_preflight.md`; all other requirements remain in force.

You are the implementing engineer-researcher for the Blind Gains project, continuing from the completed Gate-2 round. This brief covers the prelaunch sequence and the four-arm mechanical pilot launch. PIs audit results and compute gates; you never declare a gate passed. When a spec is ambiguous, record the question in the ledger as `blocked` and move to the next unblocked task.

## Environment

- Repo: `/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain`
- Compute: `ssh an12` and `ssh an29`, 8xA800-80GB each, plus the login node. The nodes also host the researcher's own unrelated jobs: treat foreign processes as normal, never kill or wait on them, and opportunistically use whatever GPUs are free. GPU utilization is a reported metric, not a gate; there is no idle-time violation.
- Python env: `source .venv/bin/activate`; EasyR1 at `artifacts/repos/EasyR1` with `EASYR1_ATTN_IMPLEMENTATION=sdpa`; models under `artifacts/models/`; ModelScope-first downloads, HF snapshot fallback, `HF_ENDPOINT=https://hf-mirror.com` second fallback.
- The recipe anchor run (`anchor_a0_recipe_3b_geo3k`, an12 GPUs 0-3) continues untouched to step 100. Do not modify it, its config, or its native reward. After each remaining checkpoint (60/80/100) is saved and hash-verified: relocate raw FSDP/optimizer state to the scratch archive as already practiced (raw-retention rule applies: keep latest only), and additionally relocate the step-60/80 MERGED checkpoints to scratch (with SHA256 manifests); only the step-100 merged checkpoint stays on shared storage.
- Storage measured on the reference host; L0 confirms per node:
  - Tier S, shared persistent, `/XYFS02/HDD_POOL/paratera_xy/pxy1289`: 92.7 GiB free of a 500 GiB quota (510 GiB hard limit). Holds reports, manifests, per-item JSONLs, ledgers, the R20 package, and FINAL merged checkpoints only. Guard floor: refuse any shared write that would leave less than 20 GiB quota headroom using the quota-aware command identified in L0, not bare `df`.
  - Tier S2, persistent overflow, `/HOME/paratera_xy/pxy1289`: 31.5 GiB free. Small persistent artifacts only (compressed log archives, scratch-manifest mirrors), capped at 15 GiB total project use; never model weights or checkpoints.
  - Tier T, node-local scratch, `/tmp` (or `/var/tmp`, same disk): approximately 339 GiB free on the reference host. Volatile, re-derivable content only: raw FSDP/optimizer state, intermediate merged checkpoints, strong-captioner weights, vLLM/download caches. Every Tier-T artifact gets a SHA256 manifest committed to Tier S. Guard floor: refuse scratch writes below 40 GiB free on that node.
  - `/dev/shm` (approximately 126 GiB): ephemeral staging only; nothing that must survive a process may live there.
  - Raw-state retention: keep only the most recent raw FSDP/optimizer state per run for resume. After the next checkpoint's merge is hash-verified, delete the older raw state and record the deletion and hashes in the run manifest. Merged intermediates in scratch are kept for the round.
  - Budget accounting is per node. With retention, worst-case concurrent scratch load is approximately 210 GiB on an12 and 295 GiB on an29. The scratch guard is the backstop, and L9 should avoid overlapping pilot arms on the same node when possible.
  - Nothing bulky is deleted unless it is listed in a report, with size, as failed, superseded, or retention-expired first.

## Operating Rules

1. Any `status` field is the logical AND of enumerated sub-checks; never asserted.
2. Every run writes `run_manifest.json` with git/config/data hashes, seed where applicable, node, GPU IDs, TP width, replica count, placement justification, and times in an immutable run directory.
3. Decoding lock for evaluations: greedy, temperature 0, top_p 1.0, n 1, fixed max tokens, one fixed prompt contract for every checkpoint including base.
4. Every fix ships with an adversarial fixture the old code fails.
5. Version, never overwrite: new tables are published alongside their predecessors with version tags. Superseded numbers remain in the repo.
6. Contamination language: flagged records are "conservative contamination candidates," never "confirmed duplicates." Apply this wording in all new and edited reports.
7. Ledger: `reports/prelaunch_progress.md`, one line per task `<task_id> | <pass|fail|blocked> | <one-line note>`. Named report files are required for every `pass`.
8. Hard ordering: no pilot arm takes its first optimizer step until L12 preregistration is merged. No one, including the implementing agent, inspects pilot training or validation metrics before that merge.

### PI GPU Placement Addendum (2026-07-11)

- Place every job on one node unless it genuinely requires more than eight GPUs. Never split one training or serving job across `an12` and `an29`.
- Use TP1 for models at or below 7B. For throughput, run independent TP1 replicas and shard requests across them. Use TP2 or TP4 only when a 32B or 72B model cannot fit on one GPU.
- Keep synchronous EasyR1/GRPO rollout and training colocated on one node; do not disaggregate them across nodes at this scale.
- Record `node`, normalized `gpu_ids`, `tensor_parallel_width`, `replica_count`, and `placement_justification` in every run manifest under policy version `pi-2026-07-11`.
- Colocating unrelated jobs on disjoint GPUs is normal. Treat the researcher's processes as normal neighbors and never as anomalies.
- For host-RAM-heavy synchronous training, admit normal disjoint-GPU neighbors only after checking aggregate host-memory headroom; GPU disjointness does not imply host-memory isolation.

## Execution Order

L0 runs first without GPUs. Wave 1 (L1-L6) starts immediately after, mostly login/CPU with small GPU needs. Wave 2 (L7-L11) is GPU-heavy and starts as its dependencies land. Wave 3 (L12-L13) is registration and launch.

Dependencies: L0 -> everything. L1 -> L3 and L7. L2 -> L7 and L13 reporting. L3 -> L7 scoring and L13. L4 -> L13. L5 -> L7 and L13 corpus. L7 -> L12 -> L13. L8 is independent. Human R19 contact-sheet audit -> L12 sign-off.

## L0 - Storage Preflight

Objective: confirm the measured baseline per node and install the guards and retention the whole brief assumes.

Requirements:

- Confirm per-node `/tmp` or `/var/tmp` capacity and free space on an12 and an29; identify and record the quota-aware free-space command for HDD_POOL; run `du -sh` for `checkpoints/`, `experiments/runs/`, `artifacts/models/`, `data/`, and caption stores.
- Compress logs older than the current round; archives may go to Tier S2 within its 15 GiB cap. Relocate remaining raw checkpoint state off shared storage. Delete only run directories explicitly marked failed or superseded, each listed with size before removal.
- Implement a shared storage guard invoked before every checkpoint save, relocation, and model download: 20 GiB quota-headroom floor on Tier S and 40 GiB floor on Tier T per node. On refusal, log `storage_guard` in the ledger note and route or queue. Add unit tests with mocked low-space conditions for both floors.
- Implement latest-raw retention and wire it into relocation. Record deletions and hashes in run manifests. Add a unit test.
- Configure EasyR1 pilot checkpoint directories and verify write/read/merge with a one-step dry save.
- Record one captioner-size decision: 72B if the serving node has at least 200 GiB scratch free after concurrent archives, otherwise 32B. Pilot mid-checkpoints use scratch.

Deliverable: `reports/storage_preflight.md` with per-node capacity table, reclamation list, guard and retention tests, and captioner decision.

Done when both guards and retention tests pass, the per-node table is published, and the decision is recorded.

## Wave 1 - Measurement and Plumbing

### L1 - Canonical-v2 Parser and Repeated Agreement Audit

Objective: close the diagnosed disagreement classes without introducing false positives.

Requirements:

- Extend the canonical parser with safe unit-suffix stripping and LaTeX presentation-wrapper normalization (`\\text{}`, `$...$`, `\\left`/`\\right`, degree symbols) applied to the extracted span before matching.
- Every normalization has false-positive fixtures, including unit changes that alter the answer such as `5 cm` versus `5 m`.
- Version the matcher as `parser_version: canonical-v2` and stamp it into every scoring output.
- Re-run the exact 320-row agreement audit against EasyR1 r1v/mathruler. Publish `reports/parser_agreement_audit_v2.md` with old agreement 0.9219, new agreement, and residual taxonomy.
- If new agreement is below 0.95, taxonomize residuals and mark the ledger note for PI review.

Done when fixtures pass and the v2 report exists with both rates.

### L2 - Split `extractor_valid` from `contract_valid`

Objective: make `Acc_strict` mean exact compliance with the run's prompt contract.

Requirements:

- Add per-row `extractor_valid`, meaning any supported tag, boxed, or answer-line convention, and `contract_valid`, meaning exact satisfaction of the run's registered contract, normally `<answer>...</answer>` from `src/eval/prompt_contract.py`.
- Read the contract per run; do not hardcode it.
- Redefine `Acc_strict = contract_valid AND Acc_final`. Keep `Acc_final` unchanged.
- Update scorer, the v2 section of `reports/scorer_v2_spec.md`, aggregators, and every report generator emitting format columns.
- Preserve the exact identity `StrictGain = AnswerGain + G_format` and add a fixture verifying it.

Done when fixtures pass and one regenerated sample table shows both validity columns.

### L3 - Pilot Training Reward with Shadow Logging

Objective: the reward optimized by pilot arms is defensible.

Requirements:

- Implement a custom EasyR1 reward for pilot arms only: canonical-v2 extraction followed by mathruler grading of the extracted span.
- If mathruler and canonical numeric equivalence disagree, mathruler's verdict is the reward and the disagreement is logged with a reason code.
- Compute and record format separately as `contract_valid`, weighted using the recipe's original format/accuracy split.
- Log per rollout: `training_reward`, `native_r1v_shadow_reward`, `canonical_eval_reward`, and `reward_disagreement_reason`.
- Test the 14 known multiline `<answer>` cases. Prove the anchor config still binds native r1v.
- Run a five-optimizer-step reward-plumbing smoke at pilot config on free GPUs. Verify populated shadow fields and nondegenerate, finite rewards.

Deliverables: `src/rewards/pilot_reward.py`, `reports/pilot_reward_spec.md`, and smoke run manifest.

Done when tests pass and smoke completes with populated shadow fields.

### L4 - A3 Caption Arm Data Path

Objective: fixed question-blind base-model captions replace the image in the fourth arm.

Requirements:

- Extend the EasyR1 flag to `image_condition: {real|gray|noise|none|caption}`.
- Under `caption`, send no image tokens. Insert the fixed 3B question-blind caption, keyed by content hash, as a text block using one frozen template.
- Record caption model and store hash in the run manifest. Document and freeze the exact template string.
- Missing captions fail loudly. Report store coverage of the filtered corpus; coverage must be 100 percent or enumerate the gap.
- Use homogeneous no-image batching following the existing `none` solution.
- Unit-test a real sampled training batch: no image tensor reaches the model and caption text appears in the tokenized prompt.

Deliverables: patch, extension to `tests/test_easyr1_image_condition_patch.py`, and `reports/a3_caption_path.md`.

Done when unit tests pass on a real sampled batch.

### L5 - Decontamination Completion for the Pilot Corpus

Objective: the corpus trained on and registered numbers describe the same filtered dataset.

Requirements:

- Run Geometry3K train-versus-test decontamination with calibrated thresholds and publish its manifest.
- Freeze the filtered training subset as Geometry3K train minus the union of Layer-1 auto-remove candidates and train-versus-test auto-remove candidates.
- Store the ID list and hash at `data/geo3k_pilot_filtered_ids.json`.
- Report filtered-versus-original shifts in category, answer type, question length, and base-model difficulty using existing audit rows.

Deliverables: `reports/decon_geo3k_train_vs_test.md` and `reports/geo3k_filtered_subset.md`.

Done when the frozen ID list is committed with hash and the shift table is published.

### L6 - Auditor Consistency Layer and Report Repairs

Objective: add scientific-consistency checks missing from the accounting auditor.

Requirements:

- Extend `scripts/audit_gate2_objective.py`, or a sibling run by the same entry point, to reject:
  - a `pass` ledger entry whose named report contains incomplete, pending, or failed status lines;
  - any `*_audited.*` file byte-identical to its unaudited counterpart;
  - a report whose referenced machine JSON is absent or has non-pass status;
  - a full-suite or full-table claim omitting registered members.
- Add fixtures for each rejection.
- Repair `eval_harness_version.md` for P1.2 completion state, the mechanical-pilot placeholder for P0.2 state, and retitle the Layer-1 table "Gate-2 Layer-1 subset" with MathVerse and MMMU marked as owed.
- Replace the per-GPU idle gate with a GPU-hours utilization report. Foreign processes are normal.

Done when fixtures pass, all three stale documents are repaired, and utilization is removed from `compute_gate2.py` inputs and replaced by the report.

## Wave 2 - Regeneration and Expansion

### L7 - Blind-Solvability Audit v2 Under the Pilot Contract

Dependencies: L1, L2, L3, and L5.

Objective: produce preregistration numbers measured exactly as the pilot trains.

Requirements:

- Use the L5 filtered training subset and untouched Geometry3K test, reported separately.
- Conditions: real, gray, noise, no-image, and caption using the same fixed 3B store as L4.
- Decode with `max_tokens=2048`, sampled `n=16` at pilot rollout temperature, plus greedy. Use the identical training prompt contract and record every parameter.
- Score with the exact L3 pilot reward and canonical-v2 evaluation for comparison.
- For each item compute Jeffreys-smoothed `p_i` from 16 samples and `q_i = 1 - p_i^G - (1-p_i)^G` at `G=5`.
- Publish per-condition aggregates with bootstrap confidence intervals, p-band table, q distributions, and real-versus-blind quadrants as v2 alongside v1. State that v1 used 512 tokens and canonical-v1.
- Commit distinct audited Markdown and JSON artifacts with row counts, identity and duplicate checks, decoding parameters, prompt hash, parser and reward versions, recomputed-score mismatches, and output hashes. L6 must accept them.

Deliverables: `reports/blind_solvability_geo3k_v2.md`, `reports/blind_solvability_geo3k_v2_audited.md`, `reports/blind_solvability_geo3k_v2_audited.json`, and per-item JSONL.

Done when all five conditions are complete on the filtered corpus and the audit passes L6.

### L8 - R20 Confirmatory Instrument Split

Objective: verify the R19 generator, not the R19 selection.

Requirements:

- Freeze and hash the R19 generator code and criteria.
- Generate R20 from new seeds at the same per-template counts: document 300, geometry 600, chart 300.
- No batch rejection, regeneration, or threshold changes; one shot.
- Run the same pipeline as R19: packaging, linter, attacker gate with confidence intervals, hardness cells for 3B/7B real, gray, noise, and 3B/7B caption at 384 tokens, plus degradation and scale controls.
- Include verbatim: "R20 is confirmatory. A template failing here has its certification downgraded to R19-selected; we do not mint R21. Generator-level pass = R20 meets the pre-frozen criteria without selection."
- Prepare R20 contact sheets for a second human audit sample.

Deliverables: `reports/fliptrack_r20_confirmatory.md` and machine JSON.

Done when all R20 cells and gates are reported with a per-template pass or downgrade verdict.

### L9 - Stronger-Captioner Stress

Starts after L8 generation frees GPUs.

Requirements:

- Default to 72B if L0 confirms at least 200 GiB free on the serving node after concurrent archives; otherwise use 32B and record which.
- Download ModelScope-first to node-local scratch only, never HDD_POOL, and serve with vLLM from scratch.
- Avoid overlap with pilot arms on the same node where possible; storage guard is the backstop.
- Generate question-blind captions with fixed prompt and 384 tokens for R19 and R20 images.
- Report caption-only pair accuracy per template under the standard QA protocol.
- Store captions and results on shared storage. Delete captioner weights from scratch after stores are committed and record deletion.
- State that this measures leakage headroom only and does not repair the document template's 7B ceiling.

Deliverable: `reports/strong_caption_stress.md`.

Done when the per-template strong-caption table exists and weight deletion is recorded.

### L10 - Layer-1 Completion and ViRL39K Sample Audit

Requirements:

- Add MathVerse and MMMU base rows for 3B and 7B under the pinned harness, including L2 validity columns, to the retitled Layer-1 table.
- Execute the committed ViRL39K 4,096-item stratified blind-solvability sample in `reports/virl39k_blind_sample_4096.json` under the L7 contract: 2048 tokens, pilot reward, and five conditions where images exist.
- Document multi-image handling and publish v1 tables with confidence intervals.

Deliverables: updated Layer-1 report, `reports/blind_solvability_virl39k_sample_v1.md`, and audited JSON.

Done when both reports are complete and pass L6 consistency checks.

### L11 - Harder Document Family Calibration

Lowest priority; run only on genuinely free GPUs.

Requirements:

- Target 7B real pair accuracy in [0.5, 0.9] using denser layouts, smaller glyphs, and distractor codes.
- Generate one declared 100-pair batch.
- Evaluate 3B real, 7B real, and 7B caption.
- Do not iterate this round; report and stop.

Deliverable: `reports/document_v_next_calibration.md`.

## Wave 3 - Registration and Launch

### L12 - Preregistration

Dependencies: L7, PI sign-off, and human R19 contact-sheet audit.

Create `reports/preregistration_pilot_v1.md` using computed L7 v2 fields. Submit through the researcher for PI review and merge only after both PIs approve.

Required content:

- Design: four arms (A1 real, A2 gray, A2b no-image, A3 caption), 3B, filtered Geometry3K corpus with ID-list hash, frozen vision tower, configs identical except `image_condition`, pinned L3 reward, `G=5`, approximately 100 steps, same seed, checkpoints 0/20/40/60/80/100, and greedy full Geometry3K-test validation every 10 steps.
- Include verbatim: "These are pilot estimands and directional predictions, not definitive hypothesis tests of the training procedure; item-level paired intervals quantify evaluation uncertainty, not run-to-run RL variance."
- Primary estimands: `D_gray = DeltaA1 - DeltaA2gray`, `D_none = DeltaA1 - DeltaA2b`, and `D_caption = DeltaA1 - DeltaA3`, each with paired item-bootstrap confidence intervals. Delta is final minus step-0 greedy `Acc_final` on Geometry3K test.
- Primary mechanistic prediction: within each blind arm, item gains concentrate on high initial `q_i` under that condition. Register rank correlation of per-item gain versus initial q greater than zero and a q-quartile gain table. Fix q values from L7.
- Directional predictions: DeltaA3 is at least DeltaA2gray and DeltaA2b; A1 and A3 are closer than either is to zero-visual-bit arms.
- Secondary: recovery ratios only if DeltaA1 is at least twice its paired standard error, labeled conditional descriptive intervals; equivalence of gray and no-image within plus or minus 0.05 only when the paired interval lies within the margin; format prediction uses `contract_valid` and is conditional on nontrivial A1 format gain.
- RQ2 endpoints on FlipTrack R19 at checkpoints 0, 60, and 100. Score step 60 from the scratch-resident checkpoint on its node. Primary is geometry-category pair accuracy; secondary is overall R19; document is calibration only because 7B is saturated.
- SESOI plus or minus 0.05. Include: "no material change" supported only if the paired CI is entirely within [-0.05, +0.05].
- Include verbatim: "If A1 improves geo3k strongly and produces a material geometry-FlipTrack gain while blind arms do not, the shortcut-only account is disfavored."
- Include an initially empty deviations log.

Done when merged with PI sign-off recorded in the ledger before any pilot optimizer step.

### L13 - Four-Arm Pilot Launch

Dependencies: L3, L4, L5, and merged L12.

Requirements:

- Launch `mech_a1_real`, `mech_a2_gray`, `mech_a2b_noimage`, and `mech_a3_caption` according to registration.
- Prefer four GPUs per arm; stagger when foreign jobs occupy capacity and record placement.
- Use identical config modulo `image_condition`.
- All saves land in the L0-approved checkpoint layout with latest-raw retention.
- After hash-verified merge, copy only each arm's step-100 merged checkpoint to HDD_POOL. Keep intermediate merged checkpoints and raw state in the scratch archive with SHA256 manifests on shared storage.
- Score step-60 FlipTrack from the scratch-resident checkpoint before cleanup. Step 0 is the existing base model and must not be duplicated.
- Run both storage guards before every save and copy.
- Report matched optimizer budget plus actual tokens and wall-clock per arm; make no FLOP-equality claim.
- On completion, score checkpoints on Geometry3K test using greedy L2 fields and both pilot-reward and canonical-v2 scoring, and on FlipTrack R19 using registered endpoints.
- Verify `StrictGain = AnswerGain + G_format` exactly.
- Produce `reports/pilot_4arm_results_v1.md` with every registered estimand and no interpretation beyond registered analyses; interpretation belongs to PIs.

Done when all four runs complete, all registered numbers are computed, and the results report is committed.

## Ledger

`reports/prelaunch_progress.md` contains exactly one line per task L0-L13. `blocked` with a clear question is acceptable; `pass` without deliverables is not.

## PI Storage Resolution

The PI subsequently resolved L0 as follows:

- The login node is fully available for orchestration and archive operations.
- Pilot checkpoints save to shared `checkpoints/pilot/<arm>/`, the only persistent path writable by GPU nodes.
- The existing login watcher sweeps raw state and intermediate merged checkpoints to the login `/tmp` archive. Step-100 merged remains on shared. Latest-raw-only retention applies.
- No save semaphore is required. The quota guard refuses a save that would breach the 20 GiB floor; on refusal, wait and retry. Save steps may be staggered if useful.
- Compute-node `/tmp` is not used for checkpoints. `/dev/shm` may hold re-derivable data, including 72B captioner weights, which must be downloaded, served, and deleted.
- Reclaiming approximately 66 GiB of superseded Gate-2 checkpoints to the login archive is opportunistic, not a gate.
- L1, L2, L5, L8 generation, L6 repairs, and L4 unit-test work start immediately.
- Close L0 after one dry save, sweep, and read-back cycle on the approved layout, then proceed.
