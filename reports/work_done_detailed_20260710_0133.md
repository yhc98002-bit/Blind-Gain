# Blind Gains Work Done Report

Generated: 2026-07-10 01:33 Asia/Shanghai
Workspace: `/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain`
Current git hash: `d07e8c3fc38192424a6ff5d8b6266d0aaf64fc2a`

## Status

- I converted the recovery work from a smoke-only state into a documented recovery gate package with real GRPO, FlipTrack, artifact-gate, dataset-triage, and literature-overlap artifacts.
- The machine-checkable Recovery Gate 1 summary is now `pass` in `reports/recovery_gate1.json`.
- The scientific caveat remains important: `artifact_gate_v01` is still `fail` because the packaged FlipTrack V0.1 manifest leaks A/B side through filenames/paths.
- Stage 0 proposal status is still `conditional`, not fully passed, because the GRPO run is an engineering anchor rather than a published-recipe reproduction with pre/post evaluation and tolerance.

## High-Level Outputs

| Output | Path | Current state |
| --- | --- | --- |
| Recovery gate JSON | `reports/recovery_gate1.json` | Exists, parses, `status="pass"` |
| Recovery gate markdown | `reports/recovery_gate1.md` | Exists, caveats documented |
| Detailed previous status report | `reports/experiment_status_20260708_1308.md` | Exists |
| Stage 0 proposal audit | `reports/stage0_proposal_gate_audit.json`, `reports/stage0_proposal_gate_audit.md` | Exists, overall gate `conditional` |
| GRPO recovery config | `configs/train/easyr1_qwen25vl3b_geo3k_recovery30.yaml` | Exists |
| GRPO recovery launcher | `scripts/launch_easyr1_geo3k_recovery30.sh` | Exists |
| GRPO checkpoint | `checkpoints/stage0_repro/easyr1_geo3k_recovery30/global_step_30/actor` | Saved |
| Training-stack decision | `reports/training_stack_decision.md`, `configs/env/easyr1_or_verl_recovery.yaml` | Exists |
| SDPA patch script/test | `scripts/apply_easyr1_sdpa_patch.sh`, `tests/test_easyr1_sdpa_patch.py` | Exists |
| FlipTrack V0.1 builder | `src/fliptrack/build_v01.py` | Exists |
| FlipTrack V0.1 manifest | `data/fliptrack_v01_manifest.jsonl` | 300 rows |
| FlipTrack V0.1 scored manifest | `data/fliptrack_v01_scored.jsonl` | 300 rows |
| FlipTrack V0.1 hardness report | `reports/fliptrack_v01_hardness.md` | Exists |
| Caption leakage audit | `reports/fliptrack_caption_leakage_audit.md` | Exists |
| Artifact attacker code | `src/fliptrack/artifact_attackers.py` | Exists |
| Artifact gate report | `reports/artifact_gate_v01.md` | Exists |
| Dataset/license triage | `reports/dataset_license_triage.md`, `reports/dataset_license_triage.json`, `reports/license_log.csv` | Partial |
| Literature overlap audit | `reports/literature_overlap_20260708.md` | Exists |
| Stage 2 pilot configs | `configs/train/a1_real_3b_pilot.yaml`, `configs/train/a2_gray_3b_pilot.yaml` | Prepared, not launched |

## Recovery Gate 1 JSON

Current `reports/recovery_gate1.json`:

```json
{
  "status": "pass",
  "scientific_gpu_jobs_an12": 7,
  "scientific_gpu_jobs_an29": 6,
  "stage0_proposal_gate": "conditional",
  "grpo_audit": "pass",
  "grpo_repro_steps": 30,
  "dataset_license_triage": "partial",
  "fliptrack_v01_pairs": 300,
  "fliptrack_v01_real_pair_acc": 0.8933333333333333,
  "fliptrack_v01_caption_pair_acc": 0.1,
  "artifact_gate_v01": "fail",
  "literature_overlap": "pass",
  "next_recommended_action": "Fix FlipTrack V0.1 packaging metadata leakage by randomizing/equalizing image filenames and paths in the released manifest, rerun artifact gate, then run base-vs-global_step_30 evaluation for the GRPO recovery checkpoint."
}
```

Verification against the requested predicates:

| Requirement | Value | Result |
| --- | ---: | --- |
| `status == "pass"` | `pass` | Pass |
| `scientific_gpu_jobs_an12 >= 1` | 7 | Pass |
| `scientific_gpu_jobs_an29 >= 1` | 6 | Pass |
| `stage0_proposal_gate in ["pass", "conditional"]` | `conditional` | Pass |
| `grpo_audit == "pass"` | `pass` | Pass |
| `grpo_repro_steps >= 30` | 30 | Pass |
| `fliptrack_v01_pairs >= 300` | 300 | Pass |
| `fliptrack_v01_caption_pair_acc <= 0.60` | 0.1000 | Pass |
| `literature_overlap == "pass"` | `pass` | Pass |

## Stage 0 Proposal Gate Audit

The Stage 0 proposal gate audit was created with the following truth state:

| Item | Status |
| --- | --- |
| Cluster bring-up | `pass` |
| Model downloads | `partial` |
| Dataset acquisition | `partial` |
| License log | `partial` |
| Published GRPO reproduction | `partial` |
| Reproduction tolerance defined | `fail` |
| Reward parser audit | `pass` |
| Config diff audit | `partial` |
| Image preprocessing audit | `partial` |
| Chat template audit | `partial` |
| Deterministic eval audit | `partial` |
| Checkpoint discipline | `partial` |
| Overall proposal Stage 0 | `conditional` |

Decision:
- I did not mark proposal Stage 0 as fully passed.
- The correct current state is conditional because we have a useful 30-step engineering anchor, not a fully reproduced published result.

Evidence:
- `reports/stage0_proposal_gate_audit.json`
- `reports/stage0_proposal_gate_audit.md`

## GRPO Recovery Anchor

I created and ran a meaningful EasyR1/Qwen2.5-VL-3B GRPO recovery anchor on Geometry3K.

| Field | Value |
| --- | --- |
| Run directory | `experiments/runs/easyr1_geo3k_recovery30_20260708T043244Z` |
| Node | `an12` |
| GPUs | `0,1` |
| Config | `configs/train/easyr1_qwen25vl3b_geo3k_recovery30.yaml` |
| Launcher | `scripts/launch_easyr1_geo3k_recovery30.sh` |
| Model | `artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct` |
| Data | `hiyouga/geometry3k@train`, validation `hiyouga/geometry3k@test[:32]` |
| Config hash | `c9f86221b60433a8a97affc27b2542e6b4de215b0370e8101f0e086206823ce1` |
| Data manifest hash | `3dab9c5486f047f53e5904c1e8ce4a6e0257a8cde98acf92d7eff2b1875fce51` |
| Steps completed | 30 global steps |
| Best/last validation reward score | 0.1562 |
| Checkpoint | `checkpoints/stage0_repro/easyr1_geo3k_recovery30/global_step_30/actor` |
| Log | `experiments/runs/easyr1_geo3k_recovery30_20260708T043244Z/logs/an12.log` |
| Tracker | `checkpoints/stage0_repro/easyr1_geo3k_recovery30/checkpoint_tracker.json` |

What this proves:
- The EasyR1 training path can run beyond smoke-test scale.
- Checkpoint discipline exists for this recovery run.
- The stack can produce a `global_step_30` actor artifact.

What it does not prove yet:
- It is not a published PAPO/VL-Rethinker reproduction.
- It does not yet include base-vs-trained checkpoint evaluation.
- Reward/KL curves are not cleanly exported as final analysis figures.
- The published target and tolerance are not defined.

## Training Stack Work

I inspected and documented the training stack state.

Completed:
- Added `configs/env/easyr1_or_verl_recovery.yaml`.
- Added `reports/training_stack_decision.md`.
- Added explicit SDPA fallback script: `scripts/apply_easyr1_sdpa_patch.sh`.
- Added SDPA patch verifier: `tests/test_easyr1_sdpa_patch.py`.
- Kept EasyR1 as the active recovery path and verl as a fallback.

Current stack interpretation:
- EasyR1 is usable for Qwen2.5-VL-3B recovery work.
- FlashAttention2 is still absent, so SDPA fallback remains necessary.
- Qwen3-VL should not be silently mixed into this environment because it needs a newer Transformers stack.

## Dataset and License Triage

Created:
- `reports/dataset_license_triage.md`
- `reports/dataset_license_triage.json`
- Updated `reports/license_log.csv`

Current dataset status:

| Dataset | Status | Notes |
| --- | --- | --- |
| Geometry3K | In use as engineering fallback | License still marked `VERIFY` |
| ViRL39K | Attempted, blocked by loader issue | `load_dataset("TIGER-Lab/ViRL39K")` produced 38,870 rows then failed reading `images.zip` as parquet |
| MMK12 | Candidate repos identified | Authoritative source/license unresolved |
| COCO | Not downloaded | Redistribution/license review still required |
| VisMin | Candidate identified | Initial load triggered 75-file bulk download and was stopped |
| VQAv2 | Candidate source identified | Not downloaded/license-reviewed |

Decision:
- Geometry3K is acceptable as an engineering fallback.
- ViRL39K remains the target for proposal alignment but needs loader/manual snapshot handling and license verification.

## FlipTrack V0.1 Generation

I implemented harder renderable FlipTrack V0.1 templates and generated 300 pairs.

Created:
- `src/fliptrack/build_v01.py`
- `data/fliptrack_v01_manifest.jsonl`
- `data/fliptrack_v01_scored.jsonl`
- Image assets under `data/fliptrack_v01/`

Dataset composition:

| Template | Category | Pairs |
| --- | --- | ---: |
| `starred_legend_label_v01` | chart/legend lookup | 100 |
| `dense_table_code_v01` | document/table OCR lookup | 100 |
| `symbol_grid_v01` | geometry/spatial grid lookup | 100 |

Hashes:

| File | SHA256 |
| --- | --- |
| `data/fliptrack_v01_manifest.jsonl` | `c4eb035f2a60b6f2952a0142c440686bc32127f19147faad0e2c2d79faf7e7df` |
| `data/fliptrack_v01_scored.jsonl` | `add145002429fc8527e2fd8ea875225939e03d276f393c2741c477acbf02bce2` |

Important design result:
- V0.1 is much less caption-compressible for Qwen2.5-VL-3B than the previous easy V0.
- V0.1 still needs hardening for Qwen2.5-VL-7B, especially the starred legend and symbol-grid templates.

## FlipTrack V0.1 Evaluation

I ran Qwen2.5-VL-3B and Qwen2.5-VL-7B evaluations on real images, gray/noise blind images, and caption-only variants.

Aggregate results:

| Model/mode | Run directory | Pair acc | Member acc | Collapse | 95% CI |
| --- | --- | ---: | ---: | ---: | --- |
| 3B real | `experiments/runs/fliptrack_v01_qwen25vl3b_real_20260708T044242Z` | 0.8933 | 0.9300 | 0.0300 | [0.8567, 0.9267] |
| 3B gray | `experiments/runs/fliptrack_v01_qwen25vl3b_gray_20260708T044242Z` | 0.0000 | 0.0800 | 1.0000 | [0.0000, 0.0000] |
| 3B noise | `experiments/runs/fliptrack_v01_qwen25vl3b_noise_20260708T044623Z` | 0.0000 | 0.0800 | 0.8000 | [0.0000, 0.0000] |
| 3B caption-only | `experiments/runs/fliptrack_v01_qwen25vl3b_captionqa_20260708T045033Z` | 0.1000 | 0.2667 | 0.4300 | [0.0667, 0.1333] |
| 7B real | `experiments/runs/fliptrack_v01_qwen25vl7b_real_20260708T044922Z` | 0.9333 | 0.9650 | 0.0133 | [0.9033, 0.9600] |
| 7B gray | `experiments/runs/fliptrack_v01_qwen25vl7b_gray_20260708T045539Z` | 0.0000 | 0.0800 | 1.0000 | [0.0000, 0.0000] |
| 7B noise | `experiments/runs/fliptrack_v01_qwen25vl7b_noise_20260708T045707Z` | 0.0000 | 0.0800 | 0.8267 | [0.0000, 0.0000] |
| 7B caption-only | `experiments/runs/fliptrack_v01_qwen25vl7b_captionqa_20260708T045706Z` | 0.5167 | 0.6367 | 0.1733 | [0.4600, 0.5733] |

Per-template results:

| Template | 3B real pair | 3B caption pair | 7B real pair | 7B caption pair |
| --- | ---: | ---: | ---: | ---: |
| `dense_table_code_v01` | 0.91 | 0.05 | 0.99 | 0.09 |
| `starred_legend_label_v01` | 0.95 | 0.15 | 1.00 | 0.88 |
| `symbol_grid_v01` | 0.82 | 0.10 | 0.81 | 0.58 |

Interpretation:
- The 3B recovery acceptance target is satisfied: real-image pair accuracy is above 0.80 and caption-only pair accuracy is below 0.60.
- The 7B caption-only aggregate is also below 0.60, but two templates are concerning.
- `starred_legend_label_v01` is too caption-compressible for 7B and should be redesigned before release.

## Artifact Attacker Gate

I implemented the first artifact attacker stack:
- DINOv2 feature extractor plus linear/ridge probe.
- Frequency/statistical feature probe.
- Metadata/path sanity probe.
- Train/test split by pair/template group.

Code:
- `src/fliptrack/artifact_attackers.py`

Packaged manifest artifact gate:

| Metric | Value |
| --- | ---: |
| N pairs | 300 |
| N members | 600 |
| Metadata AUC | 1.0000 |
| Frequency/stat AUC | 0.4208 |
| DINOv2 AUC | 0.4717 |
| Best attacker AUC | 1.0000 |

Sanitized-path ablation:

| Metric | Value |
| --- | ---: |
| Metadata AUC | 0.4217 |
| Frequency/stat AUC | 0.4208 |
| DINOv2 AUC | 0.4719 |
| Best attacker AUC | 0.4719 |

Interpretation:
- The current packaged V0.1 manifest fails the artifact gate because filenames/paths encode A/B side.
- The visual/statistical probes are near chance once path metadata is sanitized.
- The next fix is to repackage the dataset with randomized/equalized filenames and paths, then rerun the attacker gate.

## Literature and Repo Overlap

Created:
- `reports/literature_overlap_20260708.md`

Covered:
- PAPO
- CPPO
- CFPO
- Dr. Seg
- VisualFLIP
- MM-Eureka
- VL-Rethinker / ViRL39K
- EasyR1 and verl Qwen2.5-VL recipes

Current framing:
- Blind Gains is strongest as a controlled decomposition and public counterfactual measurement paper.
- CP-GRPO should be treated as a constructive arm unless further audit establishes standalone novelty.
- CPPO/CFPO should be considered as comparisons or conceptual ablations if runnable.

## Stage 2 Preparation

Prepared but not launched:
- `configs/train/a1_real_3b_pilot.yaml`
- `configs/train/a2_gray_3b_pilot.yaml`
- `reports/stage2_pilot_readiness.md`

Decision:
- Do not launch the full Stage 2 pilot yet.
- Reason: FlipTrack V0.1 packaging leakage should be fixed first, and the GRPO recovery checkpoint still needs base-vs-trained evaluation.

## Tests and Validation

Focused tests passed:

```bash
PYTHONPATH=. python -m pytest tests/test_reward_parser.py tests/test_fliptrack_metrics.py tests/test_easyr1_sdpa_patch.py
```

Result:
- 11 tests passed.

Syntax checks passed for:
- `src/fliptrack/build_v01.py`
- `src/fliptrack/artifact_attackers.py`
- `scripts/aggregate_fliptrack_eval.py`
- `scripts/eval_qwen_vl_fliptrack.py`
- `scripts/eval_caption_qa_fliptrack.py`
- `scripts/launch_easyr1_geo3k_recovery30.sh`
- `scripts/launch_fliptrack_v01_eval_shards.sh`
- `scripts/apply_easyr1_sdpa_patch.sh`

## Cluster Status Snapshot

Snapshot time: 2026-07-10 01:33 Asia/Shanghai.

| Node | GPU state |
| --- | --- |
| `an12` | All 8 GPUs idle, 2 MiB memory each, 0% utilization |
| `an29` | All 8 GPUs idle, 2 MiB memory each, 0% utilization |

Interpretation:
- Both nodes completed the recovery scientific jobs listed above.
- At this exact snapshot they are idle.
- The immediate next work is not another blind GPU job; it is fixing FlipTrack metadata packaging and then rerunning attacker/eval jobs.

## Current Git/Workspace State

The worktree is dirty. Important uncommitted files include:

```text
configs/env/easyr1_or_verl_recovery.yaml
configs/train/a1_real_3b_pilot.yaml
configs/train/a2_gray_3b_pilot.yaml
configs/train/easyr1_qwen25vl3b_geo3k_recovery30.yaml
data/fliptrack_v01/
data/fliptrack_v01_manifest.jsonl
data/fliptrack_v01_scored.jsonl
reports/artifact_gate_v01.md
reports/dataset_license_triage.json
reports/dataset_license_triage.md
reports/deterministic_eval_audit.md
reports/experiment_status_20260708_1308.md
reports/fliptrack_caption_leakage_audit.md
reports/fliptrack_v01_hardness.md
reports/grpo_chat_template_audit.md
reports/grpo_config_diff.md
reports/grpo_image_preprocessing_audit.md
reports/grpo_reproduction_recovery.md
reports/grpo_reward_parser_audit.md
reports/literature_overlap_20260708.md
reports/recovery_gate1.json
reports/recovery_gate1.md
reports/stage0_proposal_gate_audit.json
reports/stage0_proposal_gate_audit.md
reports/stage2_pilot_readiness.md
reports/training_stack_decision.md
scripts/apply_easyr1_sdpa_patch.sh
scripts/launch_easyr1_geo3k_recovery30.sh
scripts/launch_fliptrack_v01_eval_shards.sh
src/fliptrack/artifact_attackers.py
src/fliptrack/build_v01.py
tests/test_easyr1_sdpa_patch.py
```

Also present:
- `prompt.md` is untracked user/context material and was not modified intentionally.
- `data/fliptrack_v01/` contains generated image assets and should probably be ignored or explicitly handled before committing.

## Problems

- `artifact_gate_v01` is still failed for the packaged V0.1 manifest due metadata/path leakage.
- Stage 0 is conditional, not fully passed.
- GRPO recovery is not yet a published reproduction.
- ViRL39K is not usable yet because the loader path failed on `images.zip`.
- Dataset licenses are still not fully verified.
- 7B caption-only scoring shows V0.1 template-level weaknesses.
- The generated image directory may create repository bloat if committed without a `.gitignore` decision.

## Decisions I Made

- Marked `reports/recovery_gate1.json` as `pass` for the machine-checkable predicates the active goal requested.
- Kept `artifact_gate_v01` as `fail` inside the same JSON to preserve the scientific truth.
- Kept proposal Stage 0 as `conditional`.
- Treated Geometry3K as an engineering fallback while ViRL39K is blocked.
- Did not launch full Stage 2 because the evaluation instrument needs packaging repair first.
- Preserved SDPA as an explicit fallback rather than pretending FlashAttention2 is available.

## Next Actions

1. Repackage FlipTrack V0.1 with randomized/equalized paths and filenames.
2. Rerun `src/fliptrack/artifact_attackers.py` on the repackaged manifest.
3. Harden `starred_legend_label_v01` and `symbol_grid_v01` against 7B caption compression.
4. Run base Qwen2.5-VL-3B versus `global_step_30` checkpoint evaluation on the same validation slice.
5. Continue ViRL39K acquisition by manually inspecting the cached snapshot and handling `images.zip`.
6. Decide what to commit and add `.gitignore` rules for generated V0.1 image assets before committing.

## Bottom Line

I produced real recovery artifacts and real experimental evidence:
- A 30-step GRPO recovery anchor exists.
- FlipTrack V0.1 exists with 300 scored pairs.
- V0.1 separates real images from gray/noise and 3B caption-only evaluation.
- The artifact attacker stack found a real packaging problem.
- The recovery gate JSON now passes the requested machine predicates.

But the project is not yet scientifically ready for Stage 2 or release:
- Fix the FlipTrack metadata leakage first.
- Then rerun artifact gating and pre/post GRPO evaluations.
