# M5B long-horizon trajectory on two axes — v1

Machine artifact: `reports/m5b_trajectory_v1.json`
(schema `blind-gains.m5b-trajectory.v1`).

Scope: assembly and recomputation of existing artifacts. No new inference was
run. Both axes were rescored from stored responses through the canonical
scorers under prompt contract `answer-tags-v1`
(`7ac39f53a2a824490fc5ee22671a888d2d79d55e1d8351919006d7d71c7a8f3f`).

- Benchmark axis scorer: `src.eval.blind_solvability.score_greedy_item_pilot`
  (`pilot-reward-v1 + canonical-v2`, `posix-itimer-v1` guard, 5.0 s).
- Grounding axis scorer: `src.eval.fliptrack_metrics.pair_score`, rows
  restricted to `category == geometry_coordinate_indexing`.
- Intervals: 2,000-draw paired item bootstrap, 95%, seed `20260728`, via
  `src.eval.fliptrack_metrics.bootstrap_ci`. Unit is the item (`split`,
  `row_index`) on the benchmark axis and the `pair_id` on the grounding axis.
  These intervals do not estimate run-to-run RL variance.
- `p` is the exact McNemar two-sided p-value on the same paired indicators.
- Repo git hash at analysis: `e3b4cf69f060400f28126b2d6592bbcb74e1deb4`.

## 1. Metric-identity correction (read before using any earlier number)

The planning-level series supplied for the benchmark axis
(`0.4309 / 0.4692 / 0.4892 / 0.4742 / 0.4443` at steps 100/150/200/300/400)
**mixes two different metrics**. Recomputation shows:

| step | planning value | recomputed `acc_final` | recomputed `canonical_correct` |
| ---: | ---: | ---: | ---: |
| 100 | 0.4309 | 0.4359 | 0.4309 |
| 150 | 0.4692 | 0.4692 | 0.4626 |
| 200 | 0.4892 | 0.4892 | 0.4825 |
| 300 | 0.4742 | 0.4742 | 0.4642 |
| 400 | 0.4443 | 0.4443 | 0.4359 |

The step-100 entry is `canonical_correct`; steps 150–400 are `acc_final`. On
either metric held constant the step-100 anchor differs from the planning
series by +0.0050 (`acc_final`) or the later steps differ by −0.0066 to −0.0100
(`canonical_correct`). Every step-vs-step-100 delta computed from the mixed
series is inflated by +0.0050. **The recomputed single-metric series below
supersede the planning values.**

The grounding planning series (`0.4800 / 0.4733 / 0.4633 / 0.4467 / 0.4133`)
reproduces exactly; all five residuals are 0.0000.

## 2. Benchmark axis — Geometry3K test, greedy, n = 601

| step | `acc_final` (lenient) | 95% CI | `acc_strict` | 95% CI | `canonical_correct` | 95% CI | `contract_valid` |
| :--- | ---: | :---: | ---: | :---: | ---: | :---: | ---: |
| frozen base | 0.1498 (90) | [0.1231, 0.1780] | 0.0599 (36) | [0.0416, 0.0815] | 0.1747 (105) | [0.1448, 0.2063] | 0.4393 (264) |
| 100 | 0.4359 (262) | [0.3960, 0.4759] | 0.4359 (262) | [0.3960, 0.4759] | 0.4309 (259) | [0.3927, 0.4709] | 0.9684 (582) |
| 150 | 0.4692 (282) | [0.4293, 0.5108] | 0.4692 (282) | [0.4293, 0.5108] | 0.4626 (278) | [0.4243, 0.5042] | 0.9667 (581) |
| 200 | 0.4892 (294) | [0.4509, 0.5324] | 0.4892 (294) | [0.4509, 0.5324] | 0.4825 (290) | [0.4443, 0.5241] | 0.9784 (588) |
| 300 | 0.4742 (285) | [0.4326, 0.5141] | 0.4742 (285) | [0.4326, 0.5141] | 0.4642 (279) | [0.4243, 0.5058] | 0.9734 (585) |
| 400 | 0.4443 (267) | [0.4060, 0.4842] | 0.4443 (267) | [0.4060, 0.4842] | 0.4359 (262) | [0.3977, 0.4742] | 0.9867 (593) |

`acc_final == acc_strict` at every trained step (100–400); they differ only at
the frozen base (0.1498 vs 0.0599).

### 2.1 Paired delta vs step 100

| step | `acc_final` Δ | 95% CI | b01 / b10 | p | `canonical` Δ | 95% CI | p |
| :--- | ---: | :---: | :---: | ---: | ---: | :---: | ---: |
| frozen base | −0.2862 | [−0.3261, −0.2463] | 16 / 188 | 2.00e−38 | −0.2562 | [−0.2962, −0.2146] | 5.06e−31 |
| 150 | +0.0333 | [−0.0033, +0.0699] | 71 / 51 | 0.0850 | +0.0316 | [−0.0050, +0.0682] | 0.1042 |
| 200 | +0.0532 | [+0.0166, +0.0899] | 86 / 54 | 0.0086 | +0.0516 | [+0.0150, +0.0882] | 0.0107 |
| 300 | +0.0383 | [+0.0000, +0.0749] | 83 / 60 | 0.0654 | +0.0333 | [−0.0050, +0.0699] | 0.1130 |
| 400 | +0.0083 | [−0.0283, +0.0449] | 71 / 66 | 0.7327 | +0.0050 | [−0.0333, +0.0433] | 0.8644 |

`acc_strict` deltas vs step 100 are numerically identical to the `acc_final`
deltas at all trained steps; vs step 100 the frozen base is
−0.3760 [−0.4176, −0.3344], b01 = 8, b10 = 234, p = 7.60e−59.

### 2.2 Paired delta vs frozen base

| step | `acc_final` Δ | 95% CI | `acc_strict` Δ | 95% CI | `canonical` Δ | 95% CI |
| :--- | ---: | :---: | ---: | :---: | ---: | :---: |
| 100 | +0.2862 | [+0.2463, +0.3261] | +0.3760 | [+0.3344, +0.4176] | +0.2562 | [+0.2146, +0.2978] |
| 150 | +0.3195 | [+0.2779, +0.3627] | +0.4093 | [+0.3677, +0.4526] | +0.2879 | [+0.2463, +0.3295] |
| 200 | +0.3394 | [+0.2978, +0.3844] | +0.4293 | [+0.3877, +0.4742] | +0.3078 | [+0.2662, +0.3511] |
| 300 | +0.3245 | [+0.2812, +0.3677] | +0.4143 | [+0.3710, +0.4576] | +0.2895 | [+0.2479, +0.3328] |
| 400 | +0.2945 | [+0.2512, +0.3378] | +0.3844 | [+0.3428, +0.4260] | +0.2612 | [+0.2180, +0.3028] |

All fifteen intervals exclude zero; the largest McNemar p across all fifteen is
2.92e−30 (canonical, step 400).

## 3. Grounding axis — FlipTrack R19 geometry_coordinate_indexing, real images, n = 600 pairs

| step | `pair_correct` (lenient) | 95% CI | `strict_pair_correct` | 95% CI | collapse rate | `contract_valid` |
| :--- | ---: | :---: | ---: | :---: | ---: | ---: |
| frozen base | 0.4717 (283) | [0.4317, 0.5100] | 0.4433 (266) | [0.4033, 0.4817] | 0.1283 (77) | 0.9500 (570) |
| 100 | 0.4800 (288) | [0.4400, 0.5183] | 0.4800 (288) | [0.4400, 0.5183] | 0.0883 (53) | 1.0000 (600) |
| 150 | 0.4733 (284) | [0.4350, 0.5133] | 0.4733 (284) | [0.4350, 0.5133] | 0.0767 (46) | 1.0000 (600) |
| 200 | 0.4633 (278) | [0.4233, 0.5017] | 0.4633 (278) | [0.4233, 0.5017] | 0.0750 (45) | 1.0000 (600) |
| 300 | 0.4467 (268) | [0.4083, 0.4850] | 0.4467 (268) | [0.4083, 0.4850] | 0.0800 (48) | 1.0000 (600) |
| 400 | 0.4133 (248) | [0.3750, 0.4533] | 0.4133 (248) | [0.3750, 0.4533] | 0.0783 (47) | 1.0000 (600) |

`pair_correct == strict_pair_correct` at every trained step (100–400);
they differ only at the frozen base (0.4717 vs 0.4433). `contract_valid` is
1.0000 at every trained step.

### 3.1 Paired delta vs step 100 (lenient and strict are identical at every trained step)

| step | Δ lenient = Δ strict | 95% CI | b01 / b10 | p |
| :--- | ---: | :---: | :---: | ---: |
| frozen base (lenient) | −0.0083 | [−0.0367, +0.0217] | 35 / 40 | 0.6445 |
| frozen base (strict) | −0.0367 | [−0.0650, −0.0050] | 34 / 56 | 0.0263 |
| 150 | −0.0067 | [−0.0300, +0.0167] | 23 / 27 | 0.6718 |
| 200 | −0.0167 | [−0.0400, +0.0067] | 20 / 30 | 0.2026 |
| 300 | −0.0333 | [−0.0600, −0.0067] | 23 / 43 | 0.0187 |
| 400 | −0.0667 | [−0.0933, −0.0400] | 16 / 56 | 2.40e−06 |

### 3.2 Paired delta vs frozen base

| step | Δ lenient | 95% CI | p | Δ strict | 95% CI | p |
| :--- | ---: | :---: | ---: | ---: | :---: | ---: |
| 100 | +0.0083 | [−0.0217, +0.0367] | 0.6445 | +0.0367 | [+0.0050, +0.0650] | 0.0263 |
| 150 | +0.0017 | [−0.0283, +0.0317] | 1.0000 | +0.0300 | [−0.0017, +0.0617] | 0.0854 |
| 200 | −0.0083 | [−0.0367, +0.0217] | 0.6570 | +0.0200 | [−0.0117, +0.0517] | 0.2615 |
| 300 | −0.0250 | [−0.0550, +0.0067] | 0.1462 | +0.0033 | [−0.0283, +0.0383] | 0.9241 |
| 400 | −0.0583 | [−0.0900, −0.0267] | 4.25e−04 | −0.0300 | [−0.0633, +0.0033] | 0.1078 |

## 4. Shape of the two series (computed, not smoothed)

| property | value |
| :--- | :--- |
| benchmark `acc_final` series (100/150/200/300/400) | 0.4359 / 0.4692 / 0.4892 / 0.4742 / 0.4443 |
| benchmark `canonical_correct` series | 0.4309 / 0.4626 / 0.4825 / 0.4642 / 0.4359 |
| benchmark argmax step (`acc_final`) | 200 |
| benchmark argmax step (`canonical_correct`) | 200 |
| benchmark monotone non-decreasing over 100→400 | false |
| grounding `pair_correct` series | 0.4800 / 0.4733 / 0.4633 / 0.4467 / 0.4133 |
| grounding argmax step | 100 |
| grounding monotone non-increasing over 100→400 | true |
| first step at which grounding falls below frozen base | 200 |
| first step at which benchmark falls below frozen base | none in 100–400 |

Terminal-step positions relative to the frozen base: benchmark
+0.2945 [+0.2512, +0.3378] (`acc_final`); grounding
−0.0583 [−0.0900, −0.0267] (lenient) and −0.0300 [−0.0633, +0.0033] (strict).

## 5. Blind floors at step 400 — geometry slice, n = 600 pairs

| condition | `pair_correct` | 95% CI | `strict_pair_correct` | collapse rate | `contract_valid` |
| :--- | ---: | :---: | ---: | ---: | ---: |
| real | 0.4133 (248) | [0.3750, 0.4533] | 0.4133 (248) | 0.0783 | 1.0000 |
| gray | 0.0000 (0) | [0.0000, 0.0000] | 0.0000 (0) | 1.0000 (600) | 1.0000 |
| noise | 0.0000 (0) | [0.0000, 0.0000] | 0.0000 (0) | 1.0000 (600) | 1.0000 |

Paired delta vs step-400 real, both conditions and both metrics:
−0.4133 [−0.4533, −0.3750], p = 4.42e−75. Both blind conditions match the
expected floor (0.0000 accuracy, 1.0000 collapse) exactly.

## 6. Checks

Benchmark axis:

| check | result |
| :--- | :--- |
| test rows = 601 in every run | true |
| item-id (`split`, `row_index`) sets identical across all six runs | true |
| `ground_truth`, `problem`, `qid`, `image_sha256` identical on every joined item | true (0 mismatches, 601/601) |
| `format_prompt_sha256`, `source_manifest_sha256`, `prompt_contract_sha256`, `parser_version`, `scoring_mode`, `symbolic_grader_guard_version`, `symbolic_grader_timeout_seconds`, `format_weight` identical across runs | true |
| greedy decoding sub-contract identical (`n=1`, `temperature=0.0`, `top_p=1.0`, `max_tokens=2048`, `seed=20260710`) | true |
| raw `decoding` field byte-identical across runs | **false** — the base/step-100 guarded-rescore rows carry a combined `{greedy, sampled}` record, the M5 rows carry the greedy record only; the greedy sub-contract is identical |
| recomputed `acc_final`/`acc_strict`/`canonical_correct`/`contract_valid` equal stored fields | true, 601/601 in all six runs |

Grounding axis:

| check | result |
| :--- | :--- |
| geometry pairs = 600 in every run (of 1,200 total rows) | true |
| `pair_id` sets identical across all eight runs; no duplicates | true (600 common, 0 duplicates) |
| `answer_a`, `answer_b`, `question` identical on every joined pair | true (0 mismatches) |
| `data_manifest_hash` identical across all eight runs (`e1dde98451e1c747…`) | true |
| `max_new_tokens = 32`, greedy decoding, single template | true |
| equal-gold (invariance) pairs inside the geometry slice | 0 — the P0.2 equal-gold branch of `pair_score` is inert on this slice |
| recomputed `pair_correct`/`strict_pair_correct`/`collapsed` equal stored fields | true, 600/600 in all eight runs |
| training lineage continuous from step 100 | true (see §7) |

Cited reference values reproduced from artifacts:

| citation | source document | recomputed |
| :--- | :--- | ---: |
| geo3k frozen-base greedy canonical accuracy 0.1747 | `reports/anchor_recipe_report_v2.md` line 23; also `reports/grpo_anchor_step100_prepost_v1.md` | 0.1747 |
| geo3k step-100 greedy canonical accuracy 0.4309 | `reports/anchor_recipe_report_v2.md` line 23; also `reports/grpo_anchor_step100_prepost_v1.md` | 0.4309 |
| R19 geometry frozen base lenient 0.4717 | `reports/anchor_step100_fliptrack_r19_v2.md` | 0.4717 |
| R19 geometry frozen base strict 0.4433 | `reports/anchor_step100_fliptrack_r19_v2.md` | 0.4433 |
| R19 geometry step-100 lenient 0.4800 | `reports/anchor_step100_fliptrack_r19_v2.md`, `reports/m5_terminal_readout_v1.md` | 0.4800 |

## 7. Provenance

Training lineage (from each eval run's `source_training_manifest_snapshot.json`):

| step | source checkpoint | resumed from | training run |
| ---: | :--- | ---: | :--- |
| 100 | `checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z/global_step_100` | — | `anchor_a0_recipe_3b_geo3k_20260709T224852Z` (+ `…resume80_20260711T150633Z`) |
| 150 | anchor step 100 | 100 | `m5_anchor_longhorizon_400_an12_20260716T173030Z` |
| 200 | `m5_anchor_longhorizon_400/global_step_150` | 150 | `m5_anchor_longhorizon_400_resume150_an12_20260721T160431Z` |
| 300 | `m5_anchor_longhorizon_400_resume150/global_step_250` | 250 | `m5_anchor_longhorizon_segment250_300_an12_20260725T100517Z` |
| 400 | `m5_anchor_longhorizon_400_resume150/global_step_350` | 350 | `m5_anchor_longhorizon_segment350_400_an12_20260727T073429Z` |

Benchmark axis evaluation runs (`per_item.jsonl` SHA256 prefix, node):

| step | run | sha256 |
| :--- | :--- | :--- |
| frozen base | `experiments/runs/blind_solvability_v2_guarded_rescore_geo3k_filtered_v2_retry_real_login_20260712T050905Z` | `021da42f00eab94b…` |
| 100 | `experiments/runs/blind_solvability_v2_guarded_rescore_anchor_step100_geo3k_real_login_20260712T082107Z` | `22d93ad3f5510c49…` |
| 150 | `experiments/runs/m5_geo3k_step150_an12_gpu4_20260718T051839Z` (an12) | `90c97b6df7c4c78d…` |
| 200 | `experiments/runs/m5_geo3k_step200_an29_gpu4_20260722T141052Z` (an29) | `0371dfe7b3dada60…` |
| 300 | `experiments/runs/m5_geo3k_step300_an12_gpu0_20260726T083303Z` (an12) | `81dd02a133eea021…` |
| 400 | `experiments/runs/m5_geo3k_step400_an12_gpu0_20260728T053115Z` (an12) | `60eac65a8b5bb9b3…` |

The base and step-100 `output_sha256` values match those recorded in
`reports/grpo_anchor_step100_prepost_v1.json`.

Grounding axis evaluation runs (all `shards/*.jsonl`, per-file SHA256 in the
JSON artifact):

| step / condition | run | shards × rows |
| :--- | :--- | :--- |
| frozen base | `experiments/runs/fliptrack_v02r19_packaged_qwen25vl3b_real_an29_20260710T142716Z` | 1 × 1200 |
| 100 | `experiments/runs/fliptrack_v02r19_anchor_step100_real_an12_20260712T085144Z` | 1 × 1200 |
| 150 | `experiments/runs/m5_r19_step150_real_an12_20260718T051758Z` | 3 × 400 |
| 200 | `experiments/runs/m5_r19_step200_real_an29_20260722T141033Z` | 3 × 400 |
| 300 | `experiments/runs/m5_r19_step300_real_an12_20260726T083248Z` | 3 × 400 |
| 400 real | `experiments/runs/m5_r19_step400_real_an12_20260728T052218Z` | 4 × 300 |
| 400 gray | `experiments/runs/m5_r19_step400_gray_an12_20260728T054005Z` | 2 × 600 |
| 400 noise | `experiments/runs/m5_r19_step400_noise_an12_20260728T054005Z` | 2 × 600 |

The frozen-base R19 run predates contract stamping (`prompt_contract_sha256`
and `parser_version` are null in its rows); it was rescored here under
`answer-tags-v1` / `canonical-v2`, and its recomputed values match the
canonical-v2 reaggregate reported in `reports/anchor_step100_fliptrack_r19_v2.md`.

Analysis scripts (written for this readout, not committed):
`tmp/m5b_probe.py`, `tmp/m5b_traj.py`, `tmp/m5b_summ.py`.

## 8. Limitations of these numbers

- One long-horizon training run, one seed, one corpus, one model scale. The
  paired item bootstrap covers evaluation-item uncertainty only; it does not
  estimate run-to-run RL variance, so no interval here supports a claim about
  the trajectory being reproducible.
- The two axes are different datasets with different item counts (601 items vs
  600 pairs) and different scorers. Differences between the two axes' deltas
  are not tested here and no such difference statistic is reported.
- No multiplicity correction is applied across the 5 steps × 2 axes × 2
  strictness levels reported above.
- The frozen-base R19 rows lack an in-row contract stamp; contract identity for
  that run rests on the shared `data_manifest_hash`, identical `max_new_tokens`,
  identical question/answer fields, and the rescoring performed here.
- Geometry3K is the anchor's training family; the held-out test split avoids row
  reuse but is not an external-transfer measurement.
- The R19 human contact-sheet audit is recorded as unresolved in
  `reports/anchor_step100_fliptrack_r19_v2.md`; the word "certified" is not
  applied to this instrument here.
