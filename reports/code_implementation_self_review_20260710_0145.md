# Blind Gains Code Implementation Self-Review

Generated: 2026-07-10 01:45 Asia/Shanghai
Workspace: `/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain`

## Status

- This document is a source-code self-review for the current recovery implementation.
- The implementation is a recovery scaffold plus an initial renderable FlipTrack V0.1 instrument.
- It is not the full proposal implementation.
- The main discrepancy is that the proposal describes a full RLVR decomposition pipeline with ViRL39K/MMK12 acquisition, matched A1/A2/A3/A5 training arms, natural-scene counterfactuals, artifact gates, and external benchmark evaluation. The current code implements only the early infrastructure and recovery subset.

## Most Critical Files for Audit

| Priority | File | Why it matters |
| ---: | --- | --- |
| 1 | `src/fliptrack/build_v01.py` | Generates the 300-pair FlipTrack V0.1 dataset and determines whether the evaluation instrument is valid. |
| 2 | `src/fliptrack/schema.py` | Defines pair schema, image hashes, masks, provenance, and manifest serialization. |
| 3 | `scripts/eval_qwen_vl_fliptrack.py` | Runs real/gray/noise Qwen2.5-VL evaluation and creates scored JSONL shards. |
| 4 | `scripts/caption_fliptrack.py` | Generates question-blind captions used by the caption-only baseline. |
| 5 | `scripts/eval_caption_qa_fliptrack.py` | Evaluates model answers from captions only. |
| 6 | `src/eval/fliptrack_metrics.py` | Implements pair accuracy, member accuracy, collapse rate, bootstrap CI, permutation null, and McNemar test. |
| 7 | `src/fliptrack/artifact_attackers.py` | Implements DINOv2, frequency/statistical, and metadata artifact probes. |
| 8 | `configs/train/easyr1_qwen25vl3b_geo3k_recovery30.yaml` | Defines the actual 30-step GRPO recovery training run. |
| 9 | `scripts/launch_easyr1_geo3k_recovery30.sh` | Launches the recovery run and writes run metadata. |
| 10 | `src/rewards/answer_reward.py` | Implements binary answer reward/parser used by tests and intended RL reward plumbing. |
| 11 | `src/rewards/cp_grpo_reward.py` | Implements minimal joint pair reward for CP-GRPO, but not the full rollout integration. |
| 12 | `tests/test_fliptrack_metrics.py` | Covers only toy metric cases; important because headline metrics depend on this code. |
| 13 | `tests/test_reward_parser.py` | Covers answer parser and CP pair reward basics. |
| 14 | `tests/test_easyr1_sdpa_patch.py` | Checks that the SDPA patch is documented, not that EasyR1 runtime is fully hardened. |
| 15 | `configs/train/a1_real_3b_pilot.yaml`, `configs/train/a2_gray_3b_pilot.yaml` | Prepared Stage 2 configs; currently not launched and not complete training recipes. |

## Implementation Logic

### 1. FlipTrack Manifest and Schema

`src/fliptrack/schema.py` provides shared helpers:

- `stable_id(...)` creates deterministic pair IDs from JSON-serialized generation inputs.
- `sha256_file(...)` records image file hashes in the manifest.
- `pair_record(...)` creates each pair row with:
  - `pair_id`
  - `image_a_path`, `image_b_path`
  - image SHA256 hashes
  - changed region masks
  - question and paired answers
  - category/template metadata
  - provenance
  - verifier results
  - artifact score placeholder
  - catch twin placeholder
- `write_jsonl(...)` serializes manifests deterministically with sorted keys.

Audit concern:
- `SCHEMA_VERSION` is still `fliptrack.v0` even for V0.1 rows. This should be updated or versioned more explicitly before release.
- File paths currently encode `_a` and `_b`; this caused the artifact metadata attacker failure.

### 2. FlipTrack V0.1 Generation

`src/fliptrack/build_v01.py` generates 100 pairs per family:

- Chart/legend template: `starred_legend_label_v01`
  - Renders a dashboard-style plot with a legend.
  - A black star marks one legend entry.
  - Pair B changes the label next to the same starred color.
  - Question asks for the label next to the starred legend entry.

- Document/OCR template: `dense_table_code_v01`
  - Renders a warehouse exception table.
  - Pair B changes one cell at a row/column coordinate.
  - Question asks for the 3-character code at the queried row/column.

- Geometry/spatial template: `symbol_grid_v01`
  - Renders a 6x6 labeled grid with symbols.
  - Pair B changes the symbol in one highlighted indexed cell.
  - Question asks which symbol appears at row/column.

Important implementation decisions:
- Images are generated with PIL.
- Answers are exact by construction.
- Masks are generated as rectangular regions around the changed visual cell/legend row.
- The generator writes `data/fliptrack_v01_manifest.jsonl`.

Proposal discrepancy:
- The proposal asks for chart, document/OCR, geometry, and natural-scene categories. The current V0.1 only implements renderable chart/doc/geometry.
- The proposal asks for catch twins. The schema has `catch_twin_id`, but the V0.1 generator does not create answer-preserving catch twins.
- The proposal asks for more artifact-gate robustness before trusting the eval split. The current manifest fails the path metadata gate.

### 3. Qwen-VL Image Evaluation

`scripts/eval_qwen_vl_fliptrack.py` evaluates a Qwen2.5-VL checkpoint on a manifest shard.

Logic:
- Reads manifest rows.
- Shards by `idx % num_shards == shard_index`.
- Loads `Qwen2_5_VLForConditionalGeneration` and `AutoProcessor`.
- For each pair:
  - Materializes image A and B according to `--image-mode`.
  - `real`: use original image.
  - `gray`: create a same-size gray image.
  - `noise`: create deterministic random noise keyed by image path and seed.
  - Applies the Qwen chat template.
  - Generates deterministic outputs with `do_sample=False`.
  - Writes predictions and eval image paths to JSONL.
- Computes shard-level metrics using `aggregate_pair_metrics`.

Audit concerns:
- The script loads a full model per shard/GPU, which is simple but inefficient.
- It assumes Qwen2.5-VL class names and is not model-family generic.
- It does not explicitly set all possible determinism flags, although decoding is greedy.
- Gray/noise training-time transforms are not integrated into the EasyR1 training data path; this is eval only.

### 4. Caption-Only Evaluation

`scripts/caption_fliptrack.py`:
- Generates captions from each image using Qwen2.5-VL.
- Uses a fixed question-blind caption prompt.
- Stores `caption_a` and `caption_b` in JSONL.

`scripts/eval_caption_qa_fliptrack.py`:
- Reads caption rows.
- Asks the model to answer the original question using only the caption.
- Writes `prediction_a` and `prediction_b`.
- Computes pair metrics.

Important result:
- Qwen2.5-VL-3B caption-only pair accuracy is 0.1000.
- Qwen2.5-VL-7B caption-only pair accuracy is 0.5167.

Audit concerns:
- The caption prompt asks for visible text, labels, numbers, colors, shapes, counts, and spatial relations. It is question-blind but intentionally information-rich.
- The 7B caption result shows that some templates, especially `starred_legend_label_v01`, are compressible into captions.

### 5. Metrics

`src/eval/fliptrack_metrics.py` implements:

- `normalize_text(...)`: lowercase/strip/terminal punctuation normalization.
- `is_correct(...)`: exact match or substring-style match.
- `pair_score(...)`: scores A and B and detects prediction collapse.
- `aggregate_pair_metrics(...)`: member accuracy, pair accuracy, collapse rate.
- `bootstrap_ci(...)`, `pair_accuracy_ci(...)`: bootstrap confidence interval.
- `permutation_null_pair_accuracy(...)`: null generated by randomly swapping pair predictions.
- `mcnemar_exact(...)`: paired test between two eval result sets.

Audit concerns:
- `is_correct(...)` allows substring matching, which may be too permissive for short answers.
- Collapse detection only checks equality of normalized predictions, not semantically equivalent wrong answers.
- Bootstrap/permutation are adequate for recovery but not a full publication analysis audit.
- There is no per-template aggregation function in the core module; I computed per-template metrics externally.

### 6. Artifact Attackers

`src/fliptrack/artifact_attackers.py` implements the first attacker gate:

- Reads scored JSONL.
- Builds a member table with labels 0 for image A and 1 for image B.
- Extracts:
  - simple frequency/statistical features from resized images,
  - metadata/path features including file size, path length, stem hash, `_a.png`, `_b.png`,
  - optional DINOv2 CLS features.
- Splits by pair/template group.
- Fits deterministic ridge least-squares probes and reports AUC.

Observed results:
- Packaged manifest:
  - metadata AUC 1.0000
  - DINOv2 AUC about 0.4717
  - best attacker AUC 1.0000
- Sanitized-path ablation:
  - metadata AUC about 0.4217
  - DINOv2 AUC about 0.4719
  - best attacker AUC about 0.4719

Interpretation:
- The image content is not obviously artifact-detectable by these simple probes.
- The packaged paths leak A/B side and must be fixed.

Proposal discrepancy:
- The proposal calls for an attacker ensemble before natural-scene mass production. This is only a minimal first gate.
- It does not yet include a mature train/test split by parent image for natural scenes because natural scenes are not implemented.

### 7. GRPO Recovery Training

`configs/train/easyr1_qwen25vl3b_geo3k_recovery30.yaml` defines the recovery run:

- Dataset: `hiyouga/geometry3k@train`, validation `hiyouga/geometry3k@test[:32]`.
- Model: Qwen2.5-VL-3B-Instruct.
- Algorithm: GRPO with KL loss enabled.
- Max steps: 30.
- GPUs: 2.
- Logger: file.
- Checkpoint path: `checkpoints/stage0_repro/easyr1_geo3k_recovery30`.

`scripts/launch_easyr1_geo3k_recovery30.sh`:
- Creates immutable run directory.
- Computes git/config/data hashes.
- Writes `run_manifest.json`.
- Launches EasyR1 remotely through SSH.
- Sets `EASYR1_ATTN_IMPLEMENTATION=sdpa`.
- Enables offline HF cache behavior.

Observed checkpoint:
- `global_step_30/actor`
- tracker best/last global step 30
- best validation reward score 0.1562

Proposal discrepancy:
- This is Geometry3K fallback, not ViRL39K/PAPO lineage.
- It is a 30-step engineering anchor, not a published reproduction.
- Base-vs-trained checkpoint evaluation is not complete.
- A1/A2/A3 matched decomposition training is not launched.

### 8. Rewards

`src/rewards/answer_reward.py`:
- Extracts final answers from `<answer>...</answer>`, `\boxed{...}`, or `Answer:` lines.
- Normalizes strings.
- Supports numeric equivalence for simple floats/fractions/percentages.
- Returns binary reward.

`src/rewards/cp_grpo_reward.py`:
- Implements `cp_pair_reward(...)`: returns 1 only if both pair members are correct.
- Implements batch helper for rows with `prediction_a`, `answer_a`, `prediction_b`, `answer_b`.

Proposal discrepancy:
- CP-GRPO reward exists only as standalone logic.
- Pair-grouped rollouts and training integration are not implemented.

### 9. Stage 2 Pilot Configs

`configs/train/a1_real_3b_pilot.yaml` and `configs/train/a2_gray_3b_pilot.yaml` are placeholders:

- They declare A1/A2 arm metadata.
- They reference the recovery config and FlipTrack manifest.
- They are marked `status: prepared_not_launched`.

Proposal discrepancy:
- These are not complete training configs that EasyR1 can launch as-is.
- The image condition for A2 is not wired into training-time preprocessing.

## Selected Code Archive Contents

The archive includes:

- Source code under `src/`.
- Launch/eval/setup scripts under `scripts/`.
- Training/env configs under `configs/`.
- Tests under `tests/`.
- Patch docs under `docs/`.
- V0.1 JSONL manifests, but not generated PNG image assets.
- Key review reports and machine summaries.

It excludes:

- `.git/`
- `.venv/`
- downloaded model artifacts
- checkpoints
- generated PNG image assets
- heavy run logs/shards
- Python cache files

The exact selected file list is in:

```text
reports/review_selected_files_manifest_20260710_0145.txt
```

## Self-Review Findings

### Critical

1. Packaged FlipTrack V0.1 leaks A/B side through file paths.
   - Evidence: metadata attacker AUC 1.0.
   - Cause: filenames include `_a.png` and `_b.png`.
   - Fix: repackage with randomized/equalized path names and update manifests.

2. Stage 0 is not a full proposal reproduction.
   - Current run is Geometry3K fallback, 30 steps.
   - Missing ViRL39K/PAPO alignment and published tolerance.

3. A2 gray/noise blind training is not implemented.
   - Gray/noise exists in eval script only.
   - The training stack still uses Geometry3K images/data as provided.

4. CP-GRPO is not integrated into training.
   - Reward function exists.
   - Pair-grouped rollout and joint reward plumbing are missing.

### Major

1. FlipTrack V0.1 is renderable-only.
   - No natural-scene editing, GroundingDINO, SAM/SAM2, or local editor integration.

2. Caption-only leakage remains at template level.
   - 7B caption-only pair accuracy is 0.88 for `starred_legend_label_v01`.
   - This template needs redesign before release.

3. Metrics are recovery-grade, not publication-grade.
   - Core metrics exist.
   - Analysis notebook, seed aggregation, multiple-comparison handling, and final statistical audit are missing.

4. Dataset and license triage remains partial.
   - ViRL39K acquisition failed on `images.zip`.
   - MMK12/COCO/VisMin/VQAv2 licenses are unresolved.

### Moderate

1. `SCHEMA_VERSION` still says `fliptrack.v0`.
2. `artifact_gate.py` is a simple metadata scorer and mostly superseded by `artifact_attackers.py`.
3. Evaluation scripts duplicate model-loading logic.
4. The run launch scripts write manifests but do not record end time automatically.
5. `.gitignore` should be updated before committing generated V0.1 image assets.

## Recommended Audit Order

1. Read `src/fliptrack/build_v01.py`.
2. Read `src/fliptrack/schema.py`.
3. Read `src/eval/fliptrack_metrics.py`.
4. Read `scripts/eval_qwen_vl_fliptrack.py`, `scripts/caption_fliptrack.py`, and `scripts/eval_caption_qa_fliptrack.py`.
5. Read `src/fliptrack/artifact_attackers.py`.
6. Read `configs/train/easyr1_qwen25vl3b_geo3k_recovery30.yaml` and `scripts/launch_easyr1_geo3k_recovery30.sh`.
7. Read `src/rewards/answer_reward.py` and `src/rewards/cp_grpo_reward.py`.
8. Read tests.
9. Compare against `reports/stage0_proposal_gate_audit.md` and `reports/work_done_detailed_20260710_0133.md`.

## Bottom Line

The code is sufficient to audit the recovery claim:
- A 30-step GRPO recovery anchor was launched.
- A 300-pair renderable FlipTrack V0.1 was generated and evaluated.
- A minimal artifact attacker gate was implemented and found a real metadata leakage issue.
- The metric and reward parser basics have tests.

The code is not sufficient to claim the full proposal has been implemented:
- Main decomposition arms are not run.
- A2/A3 training transformations are not fully wired.
- CP-GRPO training is not wired.
- Natural-scene FlipTrack is not implemented.
- Dataset/license acquisition is partial.
- Artifact packaging must be repaired before dataset release.
