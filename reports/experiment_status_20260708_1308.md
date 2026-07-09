# Blind Gains Experiment Status - 2026-07-08 13:08 Asia/Shanghai

Status:
- Recovery status: machine-checkable Recovery Gate 1 predicates pass, with a remaining artifact-packaging caveat.
- `reports/recovery_gate1.json` is set to `pass`.
- Main caveat: FlipTrack V0.1 passes the aggregate 3B hardness target, but the artifact gate finds packaged path metadata leakage with AUC 1.0.
- Stage 0 proposal gate is `conditional`, not `pass`.
- Current git hash: `d07e8c3fc38192424a6ff5d8b6266d0aaf64fc2a`.
- Working tree has uncommitted recovery files and generated data; no new commit has been made.

Evidence:

| Area | Current result | Artifact |
| --- | --- | --- |
| Stage 0 proposal gate | Conditional | `reports/stage0_proposal_gate_audit.json` |
| GRPO recovery anchor | Completed 30 global steps | `experiments/runs/easyr1_geo3k_recovery30_20260708T043244Z` |
| GRPO checkpoint | Saved `global_step_30` actor | `checkpoints/stage0_repro/easyr1_geo3k_recovery30/global_step_30/actor` |
| Dataset/license triage | Partial | `reports/dataset_license_triage.md` |
| FlipTrack V0.1 generation | 300 pairs generated/scored | `data/fliptrack_v01_manifest.jsonl`, `data/fliptrack_v01_scored.jsonl` |
| Artifact gate | Fails packaged manifest, passes sanitized-path ablation | `experiments/runs/artifact_gate_v01_dinov2_20260708T045605Z/metrics.json` |
| Literature overlap | First-pass audit complete | `reports/literature_overlap_20260708.md` |
| Stage 2 | Configs prepared, not launched | `configs/train/a1_real_3b_pilot.yaml`, `configs/train/a2_gray_3b_pilot.yaml` |

Node and GPU picture:

| Node | Scientific jobs completed in this recovery window | Latest snapshot |
| --- | --- | --- |
| `an12` | GRPO 30-step anchor; 3B gray/noise V0.1 eval; 7B real/gray/noise V0.1 eval; DINO artifact gate rerun | 2026-07-08 13:04:58 CST: all GPUs 0 percent util, 2 MiB each |
| `an29` | 3B real/caption/caption-QA V0.1 eval; 7B caption/caption-QA V0.1 eval; sanitized-path artifact gate ablation | 2026-07-08 13:04:59 CST: all GPUs 0 percent util, GPU0 5 MiB, others 2 MiB |

The nodes are idle at the report snapshot. This is not ideal, but the next safe action is a CPU/code/data packaging fix for V0.1 metadata leakage before launching Stage 2 or more benchmark claims.

GRPO recovery anchor:

| Field | Value |
| --- | --- |
| Node/GPU | `an12`, GPUs `0,1` |
| Run dir | `experiments/runs/easyr1_geo3k_recovery30_20260708T043244Z` |
| Config | `configs/train/easyr1_qwen25vl3b_geo3k_recovery30.yaml` |
| Model | `artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct` |
| Data | `hiyouga/geometry3k@train`, validation `hiyouga/geometry3k@test[:32]` |
| Steps | 30 global steps |
| Tracker | best/last global step 30, best val reward score 0.1562 |
| Log | `experiments/runs/easyr1_geo3k_recovery30_20260708T043244Z/logs/an12.log` |

Interpretation:
- This is a meaningful engineering anchor, not a published GRPO reproduction.
- Missing before calling it a reproduction: published target/tolerance, base-vs-trained checkpoint evaluation, clean reward/KL curves, and exact paper recipe alignment.
- EasyR1 remains primary for recovery; verl remains fallback. The current stack still uses explicit SDPA fallback because FlashAttention2 is absent.

FlipTrack V0.1 dataset:

| Item | Value |
| --- | --- |
| Total pairs | 300 |
| Chart pairs | 100, `starred_legend_label_v01` |
| Document/OCR pairs | 100, `dense_table_code_v01` |
| Geometry/spatial pairs | 100, `symbol_grid_v01` |
| Manifest SHA256 | `c4eb035f2a60b6f2952a0142c440686bc32127f19147faad0e2c2d79faf7e7df` |
| Scored SHA256 | `add145002429fc8527e2fd8ea875225939e03d276f393c2741c477acbf02bce2` |

FlipTrack V0.1 aggregate scoring:

| Model/mode | Pair acc | Member acc | Collapse | Notes |
| --- | ---: | ---: | ---: | --- |
| Qwen2.5-VL-3B real | 0.8933 | 0.9300 | 0.0300 | Passes real-image target |
| Qwen2.5-VL-3B gray | 0.0000 | 0.0800 | 1.0000 | Near floor |
| Qwen2.5-VL-3B noise | 0.0000 | 0.0800 | 0.8000 | Near floor |
| Qwen2.5-VL-3B caption-only | 0.1000 | 0.2667 | 0.4300 | Passes caption ceiling |
| Qwen2.5-VL-7B real | 0.9333 | 0.9650 | 0.0133 | Strong |
| Qwen2.5-VL-7B gray | 0.0000 | 0.0800 | 1.0000 | Near floor |
| Qwen2.5-VL-7B noise | 0.0000 | 0.0800 | 0.8267 | Near floor |
| Qwen2.5-VL-7B caption-only | 0.5167 | 0.6367 | 0.1733 | Below 0.60 aggregate target, but too high for comfort |

Per-template warning:

| Template | 3B real pair | 3B caption pair | 7B real pair | 7B caption pair |
| --- | ---: | ---: | ---: | ---: |
| `dense_table_code_v01` | 0.91 | 0.05 | 0.99 | 0.09 |
| `starred_legend_label_v01` | 0.95 | 0.15 | 1.00 | 0.88 |
| `symbol_grid_v01` | 0.82 | 0.10 | 0.81 | 0.58 |

Interpretation:
- V0.1 is much better than V0 for 3B decomposition testing.
- It is not finished: the 7B caption model compresses the starred legend template heavily and nearly reaches the aggregate caption threshold.
- The next V0.1 repair should harden legend and grid templates, then re-score.

Artifact gate:

| Run | Metadata AUC | Frequency/stat AUC | DINOv2 AUC | Best AUC | Interpretation |
| --- | ---: | ---: | ---: | ---: | --- |
| Packaged manifest | 1.0000 | 0.4208 | 0.4717 | 1.0000 | Fails due path/member leakage |
| GPU packaged rerun | 1.0000 | 0.4208 | 0.4719 | 1.0000 | Confirms failure |
| Sanitized-path ablation | 0.4217 | 0.4208 | 0.4719 | 0.4719 | Visual/stat probes near chance after path cleanup |

Decision:
- Do not claim artifact robustness for the current packaged V0.1 manifest.
- The likely fix is straightforward: randomized/equalized released filenames and no `_a`/`_b` or side-identifying path components.
- After repackaging, rerun the same attacker gate and require best AUC near chance.

Dataset and license triage:

| Item | State |
| --- | --- |
| Geometry3K | In use as engineering fallback; license still marked `VERIFY` |
| ViRL39K | Attempted; `load_dataset("TIGER-Lab/ViRL39K")` produced 38,870 rows then failed on `images.zip` as parquet |
| MMK12 | Candidate repos identified, authoritative source/license unresolved |
| COCO | Not downloaded; image redistribution/license review still required |
| VisMin | Candidate identified; initial load triggered large multi-file download and was stopped |
| VQAv2 | Candidate source identified; not downloaded/license-reviewed |

Training stack:
- EasyR1 is the active recovery stack.
- Requirements now documented in `reports/training_stack_decision.md` and `configs/env/easyr1_or_verl_recovery.yaml`.
- SDPA fallback is explicit via `scripts/apply_easyr1_sdpa_patch.sh`; verifier test is `tests/test_easyr1_sdpa_patch.py`.
- Qwen3-VL should not be mixed into this environment; it needs a separate Transformers stack.

Verification run:
- `PYTHONPATH=. python -m pytest tests/test_reward_parser.py tests/test_fliptrack_metrics.py tests/test_easyr1_sdpa_patch.py`
- Result: 11 passed in 0.21s.
- Syntax checks passed for V0.1 builder, artifact attackers, eval/aggregate scripts, and launch scripts.

Problems:
- Current V0.1 release package leaks A/B side through paths.
- Stage 0 is still conditional because the GRPO anchor is not a published reproduction and lacks pre/post checkpoint evaluation.
- Dataset/license triage is partial; ViRL39K is not yet usable.
- Both A800 nodes are idle at the final snapshot; the immediate blocking work is metadata packaging and audit work rather than another safe long GPU job.
- There is unrelated activity on `an29` from `paper_prep/scripts/inspect_t5gemma_runtime.py`; I did not touch it.

Decision:
- Treat Recovery Gate 1 as passed for the requested summary predicates, but not as an artifact-robust dataset release.
- Do not launch full Stage 2 yet.
- Fix FlipTrack packaging and harden template-level caption leakage first.
- Then run base-vs-trained checkpoint evaluation for the 30-step GRPO anchor.

Next actions:
- Repackage V0.1 paths and filenames, regenerate `data/fliptrack_v01_scored.jsonl`, and rerun artifact gate.
- Add harder variants for `starred_legend_label_v01` and `symbol_grid_v01`, then rerun 3B/7B caption gates.
- Convert or evaluate the EasyR1 `global_step_30` actor against the same validation slice as the base checkpoint.
- Continue ViRL39K acquisition by manually handling the downloaded snapshot and `images.zip` layout, with license text captured before use.
- Commit the recovery code/reports after deciding whether generated image assets should be tracked or ignored.
