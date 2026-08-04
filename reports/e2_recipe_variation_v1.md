# E2 — Anchor as recipe variation: the dissociation under two configurations — v1

Machine artifact: `reports/e2_recipe_variation_v1.json` (schema `blind-gains.e2-recipe-variation.v1`). Registered as row E2 of `docs/EXPERIMENT_TODO.md`: reporting-only assembly, **no new runs, no GPU, no new inference, no new scoring**. Every number below is read programmatically from the canonical artifact cited next to it (`scripts/build_e2_recipe_variation_v1.py`; the build fails on any mismatch with the values cited in `reports/RESULTS.md` §§3, 6, 12, 12b).

Registered framing: *the anchor (unfrozen tower, native r1v reward, unfiltered corpus) alongside the pilot as evidence the dissociation is not an artifact of the frozen-tower / canonical-reward configuration* (row E2). Repo git hash at assembly: `239c21358d7126378f25729f730e6877a78be6d8`.

## 1. The two configurations (exact fields from the checked-in configs)

Pilot A1: `configs/train/mech_a1_real_3b_geo3k.yaml` (sha256 `abf9e9d9a48e35dd5f29e86a51dd674d1a666a088f9ced9f7acc86338a53560e`), seed variants `mech_a1_real_seed2_3b_geo3k.yaml`, `mech_a1_real_seed3_3b_geo3k.yaml` (differ only in `data.seed`, `experiment_name`, `save_checkpoint_path`).  
Anchor: `configs/train/anchor_a0_recipe_3b_geo3k.yaml` (sha256 `fdd39cead00fa6932d03c3040d90e76b71599983623b7478d67a309ce4dc3862`); extension `configs/train/m5_anchor_longhorizon_400.yaml` (differs from the anchor config only in `max_steps: 400`, `save_freq: 50`, `experiment_name`, checkpoint paths, and `load_checkpoint_path` = anchor `global_step_100`).

| recipe field | pilot A1 | anchor |
| :--- | :--- | :--- |
| vision tower (`worker.actor.model.freeze_vision_tower`) | **frozen** (`true`) | **unfrozen** (`false`) |
| reward (`worker.reward.reward_function`) | `src/rewards/pilot_reward.py:compute_score` with `format_weight: 0.5`, `require_shadow_log: true`, `symbolic_grader_timeout_seconds: 5.0` | **native r1v**: `artifacts/repos/EasyR1/examples/reward_function/r1v.py:compute_score`, no kwargs |
| training corpus (`data.train_files`) | `data/geo3k_pilot_filtered.jsonl` — frozen **filtered** subset, 1,288 of 2,101 geometry3k train rows (813 conservative contamination candidates removed; `reports/geo3k_filtered_subset.md`; file sha256 `f3d88dd1e52ccef8…`) | `hiyouga/geometry3k@train` — **unfiltered** (2,101 rows) |
| image-condition machinery | `image_condition: real`, `image_condition_seed: 20260710`, 3 caption-store shards (arm infrastructure; A1 trains on real images) | absent (stock EasyR1 data path) |
| seeds (`data.seed`) | 1, 2, 3 (three runs) | 1 (one run) |
| steps (`trainer.max_steps`) | 100 | 100, then extended to **400** via `m5_anchor_longhorizon_400.yaml` |
| rollout `tensor_parallel_size` | 1 | 2 (inference-engine sharding only) |

Verified identical across both configs: model (`Qwen2.5-VL-3B-Instruct`), GRPO with `kl_coef 0.01` (`low_var_kl`), `lr 1e-06`, `rollout_batch_size 512`, `global_batch_size 128`, `rollout.n 5` at temperature 1.0, prompt/response caps 2048/2048, pixel budget, greedy validation (`temperature 0.0`, `top_p 1.0`, `n 1`) on `hiyouga/geometry3k@test`, 1 node x 4 GPUs, `val_freq 10`. The full field-by-field list is in the JSON (`configuration_table.shared_fields_verified_identical`).

## 2. The dissociation, per configuration

Both sides are read against the **same frozen base** on the same geometry3k test split (n = 601, greedy) and the same FlipTrack R19 geometry slice (n = 600 pairs; registered primary visual anchor). Both scoring contracts are shown where available (I7). Naming note: the pilot readouts call canonical-v2 final-answer accuracy `acc_final` and pilot-reward-v1 accuracy `pilot_accuracy`; `m5b_trajectory_v1` calls the same two quantities `canonical_correct` and `acc_final` respectively. They are matched below by contract, not by field name (base 0.1747 canonical / 0.1498 pilot-lenient / 0.0599 strict in both).

### 2.1 Benchmark axis — Geometry3K test, step 100 vs base

| config | contract | base | step 100 | Δ | 95% CI | source |
| :--- | :--- | ---: | ---: | ---: | :---: | :--- |
| pilot A1 seed 1 | canonical-final | 0.1747 | 0.4276 | +0.2529 | [+0.2097, +0.2945] | `pilot_4arm_seed1_results_v1.json` |
| pilot A1 seed 2 | canonical-final | 0.1747 | 0.4210 | +0.2463 | [+0.2030, +0.2895] | `pilot_4arm_seed2_results_v1.json` |
| pilot A1 seed 3 | canonical-final | 0.1747 | 0.4060 | +0.2313 | [+0.1913, +0.2729] | `pilot_4arm_seed3_results_v1.json` |
| pilot A1 **3-seed mean** | canonical-final | 0.1747 | 0.4182 | **+0.2435** | — | mean of the three rows above |
| pilot A1 seed 1 | pilot-lenient | 0.1498 | 0.4276 | +0.2779 | [+0.2363, +0.3195] | `pilot_4arm_seed1_results_v1.json` |
| pilot A1 seed 2 | pilot-lenient | 0.1498 | 0.4210 | +0.2712 | [+0.2296, +0.3128] | `pilot_4arm_seed2_results_v1.json` |
| pilot A1 seed 3 | pilot-lenient | 0.1498 | 0.4060 | +0.2562 | [+0.2163, +0.2978] | `pilot_4arm_seed3_results_v1.json` |
| pilot A1 **3-seed mean** | pilot-lenient | 0.1498 | 0.4182 | **+0.2684** | — | mean of the three rows above |
| anchor (1 seed) | canonical-final | 0.1747 | 0.4309 | +0.2562 | [+0.2146, +0.2978] | `m5b_trajectory_v1.json` (McNemar p = 5.06e-31) |
| anchor (1 seed) | pilot-lenient | 0.1498 | 0.4359 | **+0.2862** | [+0.2463, +0.3261] | `m5b_trajectory_v1.json` (McNemar p = 2.00e-38) |

Strict (contract-strict) gains: pilot per-seed +0.3677 / +0.3611 / +0.3461 (mean **+0.3583**, `strict_gain_accounting.StrictGain`); anchor +0.3760 [+0.3344, +0.4176] (`m5b_trajectory_v1.json`). Strict gains exceed lenient gains in both configurations, so the lenient figures above are the conservative ones.

### 2.2 Grounding axis — FlipTrack R19 `geometry_coordinate_indexing` (registered primary visual anchor), step 100 vs base

| config | base | step 100 | Δ (lenient) | 95% CI | within SESOI ±0.05 | source |
| :--- | ---: | ---: | ---: | :---: | :--- | :--- |
| pilot A1 seed 1 | 0.4717 | 0.4700 | -0.0017 | [-0.0283, +0.0250] | yes (equivalence supported: true) | `pilot_4arm_seed1_results_v1.json` |
| pilot A1 seed 2 | 0.4717 | 0.4800 | +0.0083 | [-0.0167, +0.0333] | yes (equivalence supported: true) | `pilot_4arm_seed2_results_v1.json` |
| pilot A1 seed 3 | 0.4717 | 0.4817 | +0.0100 | [-0.0150, +0.0350] | yes (equivalence supported: true) | `pilot_4arm_seed3_results_v1.json` |
| pilot A1 **3-seed mean** | 0.4717 | 0.4772 | **+0.0056** | [-0.0183, +0.0294] | yes | `f2d_template_decomposition_v1.json` |
| anchor (1 seed) | 0.4717 | 0.4800 | **+0.0083** | [-0.0217, +0.0367] | yes (McNemar p = 0.6445) | `m5b_trajectory_v1.json` |

Strict, reported without interpretation (I7): pilot per-seed step-100 strict pair accuracy 0.3167 / 0.4767 / 0.4167 vs base 0.4433; anchor step-100 strict 0.4800 vs base 0.4433, +0.0367 [+0.0050, +0.0650], p = 0.0263 — nominally positive because strict scoring charges the frozen base for its contract failures (base `contract_valid` 0.9500 vs 1.0000 at step 100; at every trained step strict ≡ lenient). The lenient pair metric is the like-for-like series.

### 2.3 Corrosion and blind-floor evidence in each configuration

- **Pilot configuration** (frozen tower): the A2-gray arm of the same pilot shows replicated, item-identifiable corrosion on the same primary anchor — Δ vs base **−0.0450** [−0.0733, −0.0167] (seed 1), **−0.0450** [−0.0717, −0.0183] (seed 2), **−0.0367** [−0.0633, −0.0100] (seed 3); seed1∩seed2 = 42 shared degraded pairs, Jaccard 0.724 vs permutation null 0.098 (p = 1e−4); three-way Jaccard 0.661 vs null 0.012 (p = 1e−4); identical extracted wrong answer on 39/40 three-way shared wrong slots (`x3_a2_degradation_forensics_v1.json`, `x3_seed3_corrosion_replication_v1.json`).
- **Anchor configuration** (unfrozen tower): at step 400 the R19 geometry blind floors hold exactly — gray **0.0000** and noise **0.0000** pair accuracy with answer-collapse 1.0000 (600/600 each); paired Δ vs step-400 real −0.4133 [−0.4533, −0.3750], p = 4.42e−75, both conditions, both strictness levels (`m5b_trajectory_v1.json` §5). The decline on real images is read against an intact blind floor.

## 3. The extension only the anchor has: 100 → 400

Series (`m5b_trajectory_v1.json`, recomputed single-metric canonical series — the earlier planning series mixed metrics and is superseded):

| axis | 100 | 150 | 200 | 300 | 400 | step-400 vs step-100 |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| benchmark `acc_final` | 0.4359 | 0.4692 | 0.4892 | 0.4742 | 0.4443 | **+0.0083** [−0.0283, +0.0449], p = 0.7327 (peak-and-return, argmax step 200) |
| grounding `pair_correct` | 0.4800 | 0.4733 | 0.4633 | 0.4467 | 0.4133 | **−0.0667** [−0.0933, −0.0400], p = 2.40e−06 (monotone decline; below base from step 200; terminal vs base −0.0583 [−0.0900, −0.0267] lenient) |

Terminal rule readout: `m5_terminal_readout_v1.json` — endpoint "R19 geometry pair accuracy, step 400 minus step 100", Δ = -0.0667 [-0.0933, -0.0400], SESOI 0.05, verdict **FALLING**. Under the flat terminal benchmark the M5c turnover analysis shows 71 items gained / 66 lost between steps 100 and 400 (net +5; 137 of 601 items change state) and the turnover is not organised by visual necessity (`m5c_turnover_v1.json`, `m5c_necessity_stratification_v1.*`).

Attribution clause (I19), verbatim from `docs/PAPER1_RESEARCH_DOC.md` F6 Tier 2:

> *Attribution, required in every mention:* this extends the **anchor** configuration — unfrozen vision tower, native r1v reward, unfiltered corpus — never pilot A1. The unfrozen tower is what makes it consequential: corrosion occurs with gradients reaching the visual encoder. The unfiltered corpus is named as part of the configuration because abundant cheap reward is mechanistically relevant, not incidental. *Scope:* one trajectory; intervals quantify evaluation uncertainty, not run-to-run RL variance.

## 4. Limitations

- The anchor is one seed and one trajectory. Its intervals are paired item bootstraps and quantify evaluation uncertainty only, not run-to-run RL variance (m5b_trajectory_v1 limitation, carried verbatim in spirit).
- The two configurations differ in three coupled factors at once (vision-tower freezing, reward function, corpus filtering) plus non-scientific plumbing (rollout tensor_parallel_size, checkpoint cadence, experiment naming). No single-factor attribution is possible from this comparison; it is robustness evidence, not a factorial experiment.
- The unfiltered anchor corpus is itself a named confound (I19): it includes the 813 conservative contamination-candidate rows the pilot removed, so anchor benchmark levels are not comparable to pilot levels as measurements of clean generalization; only the presence of the benchmark-up / grounding-flat pattern is compared, and both sides are read on the same held-out geometry3k test split and the same R19 pair set against the same frozen base.
- The 100->400 extension exists only for the anchor; nothing here shows what a prolonged pilot-A1 run would do.
- Pilot strict grounding per-seed values are volatile (0.3167-0.4767) because strict scoring charges contract failures; the strict pilot grounding series is reported but not interpreted.
- Benchmark and grounding are different datasets with different item counts and scorers; no cross-axis difference statistic is computed here (same limitation as m5b).

## 5. Verdict on the registered framing sentence

The numbers support the registered sentence. Under both configurations the benchmark rises by a large, CI-excluding-zero margin at step 100 (pilot A1: +0.2435 canonical / +0.2684 pilot-lenient three-seed mean, every per-seed CI excluding zero; anchor: +0.2862 pilot-lenient / +0.2562 canonical, McNemar p <= 5.1e-31) while the registered primary grounding anchor does not rise materially (pilot A1: three-seed mean +0.0056 [-0.0183, +0.0294], all seeds inside SESOI +/-0.05 with equivalence supported; anchor: +0.0083 lenient, p = 0.6445). The dissociation therefore appears under the frozen-tower / pilot-reward / filtered-corpus recipe and under the unfrozen-tower / native-r1v / unfiltered-corpus recipe alike, so it is not an artifact of the pilot's frozen-tower / canonical-reward configuration. One qualifier is stated plainly: at anchor step 100 the strict grounding delta vs base is nominally +0.0367 (p = 0.0263), an artifact of the frozen base's contract failures under strict scoring, not of the trained checkpoints; and only the anchor was extended, where grounding declines monotonically to below base (-0.0667 vs step 100, p = 2.40e-06) while the benchmark peak-and-returns (+0.0083, p = 0.7327).

## 6. Sources and hashes

| source | sha256 |
| :--- | :--- |
| `configs/train/anchor_a0_recipe_3b_geo3k.yaml` | `fdd39cead00fa6932d03c3040d90e76b71599983623b7478d67a309ce4dc3862` |
| `configs/train/m5_anchor_longhorizon_400.yaml` | `73ff58bd3b6a5a9a190f6f379a927bc6405c88001bd524f61846ffb22996f48c` |
| `configs/train/mech_a1_real_3b_geo3k.yaml` | `abf9e9d9a48e35dd5f29e86a51dd674d1a666a088f9ced9f7acc86338a53560e` |
| `configs/train/mech_a1_real_seed2_3b_geo3k.yaml` | `c357a636fd6596dbe2ca3eb1e9677f30396d6d256b806c27812f203da3d629a5` |
| `configs/train/mech_a1_real_seed3_3b_geo3k.yaml` | `f066d29bebb540fc63d1a4db6a62e6e6f5de59e9624c204d8917d741df7481b3` |
| `data/geo3k_pilot_filtered.jsonl` | `f3d88dd1e52ccef833f266880e487eef252193f774c1076f7dfbccd180b450e6` |
| `reports/anchor_step100_fliptrack_r19_v2.json` | `618b8ffaaa527860f611bdbcb6961631557ea1d183558f237421f831d4b533d1` |
| `reports/f2d_template_decomposition_v1.json` | `b0c9e3203f9c0fee0a190b7f79f10eb8374db9910520ed3a1598fa8d6dfdafca` |
| `reports/geo3k_filtered_subset.md` | `3d05624e909971437a96df2b0d7db9c4d7993b62cdd80e48aceb7648f41e3ebf` |
| `reports/m5_terminal_readout_v1.json` | `fbb500a0609688f2da5bbe85c0a705c06315ebe1add4c12c28a7ede2567e6994` |
| `reports/m5b_trajectory_v1.json` | `ec42a7ff613c19bfbe140729480fc539ef7851686b01c2287c37da53160cf36a` |
| `reports/m5c_turnover_v1.json` | `7584ee6b070dfe4f73a7b017913f40206fffb99973ea8809bc9024f7c9752a73` |
| `reports/pilot_4arm_seed1_results_v1.json` | `56ce2b6372fd90212bdabe2ce4f78b0b0d8bab7c2e64d72aa8b35d803051c7f4` |
| `reports/pilot_4arm_seed2_results_v1.json` | `2e6f3b58408bb803d0f985b95eb8c88864b44de32343f9127ee04b70b377028a` |
| `reports/pilot_4arm_seed3_results_v1.json` | `b519d85be0b3ab91d04732c7e84a9759e447cb5192e9630dc270e8d315d87df3` |
| `reports/x3_a2_degradation_forensics_v1.json` | `35746ccb5b16fb9bdf4cae96b755a52c32996451cc96e3f4cee3e9e1767aa800` |
| `reports/x3_seed3_corrosion_replication_v1.json` | `20fc6b3e8eaa78bdb520a9a77413781c3fbdbf41e985a6758328cc623ff34e55` |

In-artifact provenance chains (per-item output sha256, run directories, checkpoint lineage, data-manifest hashes) are recorded inside `m5b_trajectory_v1.json` §7 and the pilot readout JSONs (`joined_geo3k_sha256`, `provenance.config_sha256`, `provenance.preregistration_sha256`) and are not duplicated here.
