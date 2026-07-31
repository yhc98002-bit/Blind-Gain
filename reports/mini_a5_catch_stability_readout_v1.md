# Mini-A5 catch-trial stability — registered readout v1

Numbers, checks, and provenance only; no interpretation. Registration (binding): `docs/registered_mini_a5_catch_stability_v1.md`; instrument committed at `fc57cb8`; scorer schema `blind-gains.mini-a5-catch-stability.v1`.

**Scope.** This readout fills the registered-but-instrument-absent F8 secondary 2 (catch-trial stability, `reports/f8_secondaries_v1.md` section 2). The F8 primary readout (`reports/f8_mini_a5_endpoint_readout_v1.md`) is already published and its branch decision has fired; **nothing in this file can alter the published F8 primary or that branch decision**. No decision branch is attached to this secondary (`automatic_branch_assignment: false`).

## 1. What ran

| item | value |
|---|---|
| eval manifest | `data/derived/mini_a5_catch_eval_manifest_v1.jsonl` (300 pairs, 3 templates x 100; sha256 `c4bb508f930ec47c...`, verified pre-launch and post-run) |
| CP checkpoint | `checkpoints/mini_a5/mini_a5_cp_seed1/global_step_120/actor/huggingface` (index sha256 `4bb3b752a9895596...`, recomputed post-run, matches registration) |
| member checkpoint | `checkpoints/mini_a5/mini_a5_same_data_seed1/global_step_120/actor/huggingface` (index sha256 `b4270b12dda440fd...`, recomputed post-run, matches registration) |
| harness | `scripts/eval_qwen_vl_fliptrack.py` via `scripts/launch_fliptrack_eval_shards.sh` (same path as the F8 cells); greedy, seed 0, max-new-tokens 32, image-mode real, prompt contract `answer-tags-v1` |
| CP run | `experiments/runs/mini_a5_catch_cp_step120_real_an29_20260731T162926Z` — an29 GPU 5, 2026-07-31T16:29:43Z to 2026-07-31T16:33:16Z, status complete |
| member run | `experiments/runs/mini_a5_catch_member_step120_real_an29_20260731T162926Z` — an29 GPU 7, 2026-07-31T16:29:47Z to 2026-07-31T16:33:20Z, status complete |
| git HEAD at launch | `b1ace8662291481f803747536bcfdd3f71d11194` |
| scorer | `src/eval/catch_stability.py` (sha256 `d15eaa5d878cb757...`), exit code 0 |
| out-of-band provenance | `reports/mini_a5_catch_run_provenance_v1.json` (launcher records null checkpoint provenance for this job type; see that file) |

## 2. Checks

- Every pinned hash of registration section 2 re-verified on disk at launch AND recomputed post-run: source pairs, decontamination, audit, adapter, derived manifest + provenance sidecar + tracked record, scorer, both checkpoint index files. All pass (`hash_checks` block of the provenance record).
- Row counts: 300 pairs per arm in each shard output; `prediction_a` and `prediction_b` present on every row = 600 generations per arm, 1,200 total.
- Scorer join checks (from the readout JSON): identical uid sets across arms, 300 pairs joined, template ids agree across arms, 100 pairs per template.
- Both run manifests: status `complete`, pinned manifest hash, pinned prompt contract sha256, seed 0, max_new_tokens 32, image_mode real.
- The readout JSON consumed exactly the two shard files produced by these runs (paths and sha256s match; asserted when this file was generated).
- Instrument test suite `tests/test_catch_stability.py`: 27 passed at the launch HEAD.
- Placement: one GPU per arm on an29 (GPUs 5 and 7), guard-checked and claim-file protected; GPUs 0-3 (M7 training) and 6 (A1-real eval) untouched; claims removed after completion.

## 3. Per-template rates (100 pairs per template per arm; never pooled — I13)

### CP-GRPO arm

| template | stable_lenient | stable_strict | pair_correct | strict_pair_correct | stable_and_correct_lenient | stable_and_correct_strict |
|---|---|---|---|---|---|---|
| mini_a5_catch_distractor_matrix_v1 | 100/100 (1.00) | 95/100 (0.95) | 100/100 (1.00) | 95/100 (0.95) | 100/100 (1.00) | 95/100 (0.95) |
| mini_a5_catch_distractor_scatter_v1 | 100/100 (1.00) | 100/100 (1.00) | 100/100 (1.00) | 100/100 (1.00) | 100/100 (1.00) | 100/100 (1.00) |
| mini_a5_catch_distractor_trajectory_v1 | 98/100 (0.98) | 64/100 (0.64) | 96/100 (0.96) | 64/100 (0.64) | 96/100 (0.96) | 64/100 (0.64) |

### same-data GRPO (member) arm

| template | stable_lenient | stable_strict | pair_correct | strict_pair_correct | stable_and_correct_lenient | stable_and_correct_strict |
|---|---|---|---|---|---|---|
| mini_a5_catch_distractor_matrix_v1 | 100/100 (1.00) | 89/100 (0.89) | 100/100 (1.00) | 89/100 (0.89) | 100/100 (1.00) | 89/100 (0.89) |
| mini_a5_catch_distractor_scatter_v1 | 100/100 (1.00) | 100/100 (1.00) | 100/100 (1.00) | 100/100 (1.00) | 100/100 (1.00) | 100/100 (1.00) |
| mini_a5_catch_distractor_trajectory_v1 | 96/100 (0.96) | 28/100 (0.28) | 95/100 (0.95) | 28/100 (0.28) | 95/100 (0.95) | 28/100 (0.28) |

## 4. CP minus member, per template (paired bootstrap 10,000 draws, percentile 2.5/97.5, identical indices; exact two-sided McNemar)

| template | indicator | idx | seed | delta | 95% CI | excl. 0 | b01/b10 | McNemar p |
|---|---|---:|---:|---:|---|---|---|---:|
| mini_a5_catch_distractor_matrix_v1 | stable_lenient | 0 | 20260729 | +0.0000 | [+0.0000, +0.0000] | False | 0/0 | 1 |
| mini_a5_catch_distractor_matrix_v1 | stable_strict | 1 | 20261729 | +0.0600 | [+0.0200, +0.1100] | True | 0/6 | 0.0312 |
| mini_a5_catch_distractor_matrix_v1 | pair_correct | 2 | 20262729 | +0.0000 | [+0.0000, +0.0000] | False | 0/0 | 1 |
| mini_a5_catch_distractor_matrix_v1 | strict_pair_correct | 3 | 20263729 | +0.0600 | [+0.0200, +0.1100] | True | 0/6 | 0.0312 |
| mini_a5_catch_distractor_matrix_v1 | stable_and_correct_lenient | 4 | 20264729 | +0.0000 | [+0.0000, +0.0000] | False | 0/0 | 1 |
| mini_a5_catch_distractor_matrix_v1 | stable_and_correct_strict | 5 | 20265729 | +0.0600 | [+0.0200, +0.1100] | True | 0/6 | 0.0312 |
| mini_a5_catch_distractor_scatter_v1 | stable_lenient | 0 | 20260739 | +0.0000 | [+0.0000, +0.0000] | False | 0/0 | 1 |
| mini_a5_catch_distractor_scatter_v1 | stable_strict | 1 | 20261739 | +0.0000 | [+0.0000, +0.0000] | False | 0/0 | 1 |
| mini_a5_catch_distractor_scatter_v1 | pair_correct | 2 | 20262739 | +0.0000 | [+0.0000, +0.0000] | False | 0/0 | 1 |
| mini_a5_catch_distractor_scatter_v1 | strict_pair_correct | 3 | 20263739 | +0.0000 | [+0.0000, +0.0000] | False | 0/0 | 1 |
| mini_a5_catch_distractor_scatter_v1 | stable_and_correct_lenient | 4 | 20264739 | +0.0000 | [+0.0000, +0.0000] | False | 0/0 | 1 |
| mini_a5_catch_distractor_scatter_v1 | stable_and_correct_strict | 5 | 20265739 | +0.0000 | [+0.0000, +0.0000] | False | 0/0 | 1 |
| mini_a5_catch_distractor_trajectory_v1 | stable_lenient | 0 | 20260749 | +0.0200 | [+0.0000, +0.0500] | False | 0/2 | 0.5 |
| mini_a5_catch_distractor_trajectory_v1 | stable_strict | 1 | 20261749 | +0.3600 | [+0.2700, +0.4600] | True | 0/36 | 2.91e-11 |
| mini_a5_catch_distractor_trajectory_v1 | pair_correct | 2 | 20262749 | +0.0100 | [+0.0000, +0.0300] | False | 0/1 | 1 |
| mini_a5_catch_distractor_trajectory_v1 | strict_pair_correct | 3 | 20263749 | +0.3600 | [+0.2700, +0.4500] | True | 0/36 | 2.91e-11 |
| mini_a5_catch_distractor_trajectory_v1 | stable_and_correct_lenient | 4 | 20264749 | +0.0100 | [+0.0000, +0.0300] | False | 0/1 | 1 |
| mini_a5_catch_distractor_trajectory_v1 | stable_and_correct_strict | 5 | 20265749 | +0.3600 | [+0.2700, +0.4500] | True | 0/36 | 2.91e-11 |

Seeds follow the frozen derivation `seed = 20260729 + 1000*indicator_index + 10*template_index` (template order sorted: matrix 0, scatter 1, trajectory 2); every resolved seed above is also recorded per cell in the readout JSON. Alpha 0.05, two-sided, no multiplicity correction; 18 contrasts, none feeds a decision rule. Intervals quantify evaluation uncertainty on a fixed pair set only; each arm is one training run.

## 5. Artifacts

| artifact | sha256 |
|---|---|
| `reports/mini_a5_catch_stability_readout_v1.json` | `f723aa9d08066d92a0f5f7cf265c997500d5217fd314a92827151548e13620c5` |
| `experiments/runs/mini_a5_catch_cp_step120_real_an29_20260731T162926Z/shards/shard_0.jsonl` | `90708819d06dddbb1492582e9032948cd020a5f95c5090b1ce6108dc15886c2f` |
| `experiments/runs/mini_a5_catch_cp_step120_real_an29_20260731T162926Z/catch_stability_rows_cp.jsonl` | `b7ec214dac530696d939f4c6941eb347474ba43afe59232694979976284bc7e8` |
| `experiments/runs/mini_a5_catch_member_step120_real_an29_20260731T162926Z/shards/shard_0.jsonl` | `8a93fcf7604953faf370844ed65a91a0869d23805915d2d44dacc58376c745af` |
| `experiments/runs/mini_a5_catch_member_step120_real_an29_20260731T162926Z/catch_stability_rows_member.jsonl` | `858882ffa274cca2be57436884f48fbe8d129b8e8ec6aa26a3a40de506064526` |
| `reports/mini_a5_catch_run_provenance_v1.json` | (this commit) |

`experiments/runs/` is gitignored; shard predictions, per-row scored files, logs, and the driver state dir live on cluster storage. This file, the readout JSON, and the provenance record are the committed record.
