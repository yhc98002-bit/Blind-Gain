# M7 R3 Readout V2 (registered two-seed estimator)

Status: `complete`.

Scope:
- Seed scope: the registered two-seed estimator over both fixed M7 seeds (1 and 2) for all four arms. gain[b,s] is the mean across the two seeds of Acc_final(step_final) - Acc_final(step_0) on paired held-out items, taken per item before any stratum mean, ratio, rank statistic or bootstrap draw (docs/registered_m7_amendment_v1.md:52-53). step_0 is the shared base model and is never checkpointed, so one step-0 cell per arm serves both seeds (docs/registered_m7_seed_scope_v1.md:62-64, docs/registered_pilot_seed23_v1.md:19).
- Between-seed dispersion: measured and reported descriptively in payload['seed_dispersion']; n_seeds = 2, so no seed-level interval, test, or replication claim is registered or made. Item-paired bootstrap uncertainty does not replace seed dispersion and seed dispersion does not replace it (docs/registered_m7_amendment_v1.md:81-82, docs/registered_extensions_v1.md:143).
- Seed mean is taken per item, before any stratum mean, ratio, rank statistic or bootstrap draw.
- Step-0 reuse: the four step-0 cells are seed-independent and one set serves both seeds (under a shared step_0, mean_over_seeds(Acc_100,seed - Acc_0) = mean_over_seeds(Acc_100,seed) - Acc_0 exactly; the step-0 term is shared, not averaged).
- PI sign-off flag: docs/registered_m7_seed_scope_v1.md:39-40 reads 'Every M7 readout must carry the scope tag "one seed" wherever a gain, recovery or correlation is reported.' That sentence was written for the seed-1-only regime it introduces at lines 23-26. This readout keeps a scope tag on every gain, recovery and correlation but sets its value to the true scope; it does not print the literal string 'one seed' on a two-seed number. That literal wording is the one line a two-seed readout contradicts and is flagged here rather than silently reinterpreted.
- Single-image restriction: M7 is restricted to single-image rows (worker.rollout.limit_images=1); retained 23,542/25,255 train rows (93.2%) and 4,239/4,501 held-out rows (94.2%) (docs/registered_m7_single_image_v2.md).
- Pooled-only readout is prohibited; corpus aggregate, every joint stratum, and source-only/category-only descriptive tables are all published; A2/A2b/A3 are never pooled into one generic blind arm (docs/registered_extensions_v1.md Extension 3, docs/registered_m7_amendment_v1.md).
- This report contains numbers and provenance only; interpretation is reserved to the PIs.

Machine artifact: `reports/out.json`.

## Strata accounting

- Joint (source, category) strata recounted from `data/heldout.jsonl`: 6 total, 5 eligible (>= 30 held-out items), 1 descriptive-small-n.
- Eligibility depends only on sample count, never on a model outcome; descriptive-small-n strata are published, not merged or discarded, and enter no rank statistic.

## Corpus aggregate (two seeds (seeds 1, 2; registered two-seed mean))

| Arm | n | q_bar | Acc_final step 0 | Acc_final step 100 | Gain (95% CI) |
|---|---:|---:|---:|---:|---:|
| A1 real | 179 | 0.2757 | 0.0726 | 0.9162 | 0.8436 [0.7598, 0.9274] |
| A2 gray | 179 | 0.2757 | 0.0000 | 0.2877 | 0.2877 [0.2429, 0.3353] |
| A2b no-image | 179 | 0.2757 | 0.0000 | 0.2039 | 0.2039 [0.1451, 0.2572] |
| A3 caption | 179 | 0.2757 | 0.0000 | 0.1732 | 0.1732 [0.1228, 0.2236] |

Corpus A1 denominator: estimate 0.8436, paired SE 0.0395, stable `true` (rule: gain[A1] > 0 and gain[A1] >= 2 * paired_se).

| Blind arm | Aggregate recovery (95% CI) | Status | Undefined draws | Interval label |
|---|---:|---|---:|---|
| A2 gray | 0.3411 [NA] | stable | 0/200 | stable |
| A2b no-image | 0.2417 [NA] | stable | 0/200 | stable |
| A3 caption | 0.2053 [NA] | stable | 0/200 | stable |

## Registered joint strata: q_bar (5 eligible)

| Source | Category | n | q_bar A1 | q_bar A2 | q_bar A2b | q_bar A3 |
|---|---|---:|---:|---:|---:|---:|
| s1 | cat | 30 | 0.1000 | 0.1000 | 0.1000 | 0.1000 |
| s2 | cat | 30 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| s3 | cat | 30 | 0.3000 | 0.3000 | 0.3000 | 0.3000 |
| s4 | cat | 30 | 0.4000 | 0.4000 | 0.4000 | 0.4000 |
| s5 | cat | 30 | 0.5000 | 0.5000 | 0.5000 | 0.5000 |

## Registered joint strata: gains (two seeds (seeds 1, 2; registered two-seed mean))

| Source | Category | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) | A1 stable |
|---|---|---:|---:|---:|---:|---:|---|
| s1 | cat | 30 | 1.0000 [1.0000, 1.0000] | 0.2000 [0.1329, 0.3000] | 0.4667 [0.3167, 0.6500] | 0.0000 [0.0000, 0.0000] | true |
| s2 | cat | 30 | 1.0000 [1.0000, 1.0000] | 0.2667 [0.0996, 0.4338] | 0.3500 [0.2167, 0.5000] | 0.1000 [0.0000, 0.2333] | true |
| s3 | cat | 30 | 1.0000 [1.0000, 1.0000] | 0.3333 [0.2000, 0.4667] | 0.2333 [0.1000, 0.3838] | 0.2000 [0.0992, 0.3333] | true |
| s4 | cat | 30 | 1.0000 [1.0000, 1.0000] | 0.4000 [0.2996, 0.5000] | 0.1167 [0.0167, 0.2167] | 0.3000 [0.1667, 0.4667] | true |
| s5 | cat | 30 | 0.0667 [-0.2667, 0.3675] | 0.4667 [0.4333, 0.5000] | 0.0000 [0.0000, 0.0000] | 0.4000 [0.2333, 0.6000] | false |

## Registered joint strata: recovery (two seeds (seeds 1, 2; registered two-seed mean))

Recovery is `gain[b,s] / gain[A1,s]` only when the A1 denominator is stable (gain[A1,s] > 0 and >= 2 paired SE); otherwise `undefined-unstable-denominator`. Unstable strata stay in the gain analysis and are omitted from the recovery rank statistic.

| Source | Category | A2 recovery (95% CI) | A2b recovery (95% CI) | A3 recovery (95% CI) |
|---|---|---:|---:|---:|
| s1 | cat | 0.2000 [0.1167, 0.2838] | 0.4667 [0.3167, 0.6333] | 0.0000 [0.0000, 0.0000] |
| s2 | cat | 0.2667 [0.1329, 0.4171] | 0.3500 [0.2000, 0.5333] | 0.1000 [0.0000, 0.2008] |
| s3 | cat | 0.3333 [0.1833, 0.4500] | 0.2333 [0.0833, 0.3833] | 0.2000 [0.0667, 0.3675] |
| s4 | cat | 0.4000 [0.3000, 0.5000] | 0.1167 [0.0333, 0.2171] | 0.3000 [0.1667, 0.4342] |
| s5 | cat | undefined-unstable-denominator | undefined-unstable-denominator | undefined-unstable-denominator |

## Descriptive small-n strata (1)

Published per registration; not merged, not discarded, not in any rank statistic.

| Source | Category | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) |
|---|---|---:|---:|---:|---:|---:|
| s6 | cat | 29 | 1.0000 [1.0000, 1.0000] | 0.0517 [0.0000, 0.1384] | 0.0517 [0.0000, 0.1379] | 0.0345 [0.0000, 0.1034] |

## Rank statistics (two seeds (seeds 1, 2; registered two-seed mean))

Tie-corrected Spearman across eligible strata; undefined bootstrap draws are counted, never replaced with zero; an interval with more than 5% undefined draws is labeled unstable.

| Blind arm | rho_gain (95% CI) | Undefined | Label | Direction > 0 holds | rho_recovery (95% CI) | Recovery strata | Undefined | Label | Direction > 0 holds |
|---|---:|---:|---|---|---:|---:|---:|---|---|
| A2 gray | 1.0000 [0.6000, 1.0000] | 0/200 | stable | true | 1.0000 [0.3979, 1.0000] | 4/5 | 0/200 | stable | true |
| A2b no-image | -1.0000 [-1.0000, -0.8000] | 0/200 | stable | false | -1.0000 [-1.0000, -0.3162] | 4/5 | 0/200 | stable | false |
| A3 caption | 1.0000 [0.6992, 1.0000] | 0/200 | stable | true | 1.0000 [0.6325, 1.0000] | 4/5 | 0/200 | stable | true |

## Source-only descriptive table

Role: descriptive robustness view; does not replace the registered joint-stratum analysis.

| Group | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) |
|---|---:|---:|---:|---:|---:|
| s1 | 30 | 1.0000 [1.0000, 1.0000] | 0.2000 [0.1167, 0.2838] | 0.4667 [0.3329, 0.6500] | 0.0000 [0.0000, 0.0000] |
| s2 | 30 | 1.0000 [1.0000, 1.0000] | 0.2667 [0.1329, 0.4333] | 0.3500 [0.2000, 0.5004] | 0.1000 [0.0000, 0.2000] |
| s3 | 30 | 1.0000 [1.0000, 1.0000] | 0.3333 [0.2167, 0.4667] | 0.2333 [0.1163, 0.3504] | 0.2000 [0.1000, 0.3675] |
| s4 | 30 | 1.0000 [1.0000, 1.0000] | 0.4000 [0.2833, 0.5000] | 0.1167 [0.0329, 0.2167] | 0.3000 [0.1667, 0.4667] |
| s5 | 30 | 0.0667 [-0.3000, 0.3675] | 0.4667 [0.4167, 0.5000] | 0.0000 [0.0000, 0.0000] | 0.4000 [0.2000, 0.6000] |
| s6 | 29 | 1.0000 [1.0000, 1.0000] | 0.0517 [0.0000, 0.1207] | 0.0517 [0.0000, 0.1552] | 0.0345 [0.0000, 0.1034] |

## Category-only descriptive table

Role: descriptive robustness view; does not replace the registered joint-stratum analysis.

| Group | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) |
|---|---:|---:|---:|---:|---:|
| cat | 179 | 0.8436 [0.7817, 0.9218] | 0.2877 [0.2429, 0.3325] | 0.2039 [0.1453, 0.2654] | 0.1732 [0.1173, 0.2292] |

## Geometry3K anchor comparison (two seeds (seeds 1, 2; registered two-seed mean); informed comparison)

This comparison is informed, not fully prospective: the anchors are the completed Geometry3K seed-1 recovery readout (Informed-Prediction Disclosure, docs/registered_m7_amendment_v1.md).

| Blind arm | Geometry3K anchor | ViRL recovery (95% CI) | Difference (95% CI) | Direction (> anchor) holds | Interval label |
|---|---:|---:|---:|---|---|
| A2 gray | 0.0789 | 0.3411 | 0.2622 [0.2073, 0.3442] | true | stable |
| A2b no-image | 0.1184 | 0.2417 | 0.1233 [0.0645, 0.1964] | true | stable |
| A3 caption | no registered anchor | 0.2053 [NA] | NA | NA | stable |

## M10 support-sharpening candidates

Rule: base 0/16 under the arm's own condition, step-0 greedy wrong, step-100 greedy correct; 64-sample frozen-base follow-up is reported separately under M10.

Seed rule: candidate lists are computed per seed and published separately; no union/intersection/two-seed candidate rule is registered (docs/registered_extensions_v1.md:142), so they are not merged.

| Arm | Seed | Candidates | Artifact |
|---|---|---:|---|
| A1 real | seed1 | 0 | `reports/artifacts/support_candidates_a1_real_seed1.jsonl` |
| A1 real | seed2 | 0 | `reports/artifacts/support_candidates_a1_real_seed2.jsonl` |
| A2 gray | seed1 | 5 | `reports/artifacts/support_candidates_a2_gray_seed1.jsonl` |
| A2 gray | seed2 | 3 | `reports/artifacts/support_candidates_a2_gray_seed2.jsonl` |
| A2b no-image | seed1 | 0 | `reports/artifacts/support_candidates_a2b_noimage_seed1.jsonl` |
| A2b no-image | seed2 | 0 | `reports/artifacts/support_candidates_a2b_noimage_seed2.jsonl` |
| A3 caption | seed1 | 0 | `reports/artifacts/support_candidates_a3_caption_seed1.jsonl` |
| A3 caption | seed2 | 0 | `reports/artifacts/support_candidates_a3_caption_seed2.jsonl` |

Candidate selection does not claim that RL created or taught a capability; M10 language remains non-causal.

## Seed dispersion (descriptive only)

Role: descriptive only. 'Seed-to-seed dispersion is also reported descriptively and is not replaced by item-bootstrap uncertainty' (docs/registered_m7_amendment_v1.md:81-82); 'Use item-paired intervals; seed dispersion is separately descriptive' (docs/registered_extensions_v1.md:143). Two seeds is n=2: no seed-level confidence interval, significance test, or 'the effect replicates' claim is registered. No registered branch keys on seed disagreement; the direction verdict is read off the two-seed mean statistic in payload['rank_statistics'] and fires unchanged whatever the per-seed values do.

- q_bar[b,s] is the item mean of the frozen Jeffreys-smoothed base q_i under arm b's own information condition (docs/registered_m7_amendment_v1.md:49-51); it comes from the shared step-0 cells and is identical for both seeds.
- Registered direction verdict source: payload['rank_statistics'], computed on the two-seed mean; the per-seed values below fire no registered branch.
- Every number in this section is a point estimate. No interval, test, or replication claim is attached to a two-point seed spread.

| Arm | Gain seed1 | Gain seed2 | Gain difference | Two-seed mean gain (95% CI) |
|---|---:|---:|---:|---:|
| A1 real | 0.8436 | 0.8436 | 0.0000 | 0.8436 [0.7598, 0.9274] |
| A2 gray | 0.1788 | 0.3966 | -0.2179 | 0.2877 [0.2429, 0.3353] |
| A2b no-image | 0.1788 | 0.2291 | -0.0503 | 0.2039 [0.1451, 0.2572] |
| A3 caption | 0.1732 | 0.1732 | 0.0000 | 0.1732 [0.1228, 0.2236] |

| Blind arm | Statistic | seed1 | seed2 | Difference | Two-seed mean (registered) |
|---|---|---:|---:|---:|---:|
| A2 gray | aggregate_recovery | 0.2119 | 0.4702 | -0.2583 | 0.3411 |
| A2 gray | rho_gain | -1.0000 | 1.0000 | -2.0000 | 1.0000 |
| A2 gray | rho_recovery | -1.0000 | 1.0000 | -2.0000 | 1.0000 |
| A2b no-image | aggregate_recovery | 0.2119 | 0.2715 | -0.0596 | 0.2417 |
| A2b no-image | rho_gain | -1.0000 | -1.0000 | 0.0000 | -1.0000 |
| A2b no-image | rho_recovery | -1.0000 | -1.0000 | 0.0000 | -1.0000 |
| A3 caption | aggregate_recovery | 0.2053 | 0.2053 | 0.0000 | 0.2053 |
| A3 caption | rho_gain | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| A3 caption | rho_recovery | 1.0000 | 1.0000 | 0.0000 | 1.0000 |

## Provenance

- Held-out manifest: `data/heldout.jsonl` (sha256 `9ae6a2435e53313cf284178cd2f9fcb38cbf83312abc67c1402512a7273b7177`, 179 rows).
- Analysis git head: `None`.
- Bootstrap: 200 draws, seed 20260716; deterministic statistic/arm labels hashed into independent streams via src.analysis.pilot_fourarm.deterministic_seed.
- data/virl39k_m7_split_manifest_v2.json n_strata_rank_eligible=21 counts component labels, not items, and was not used; eligibility was recounted directly from the held-out jsonl.
- Registered documents: `docs/registered_m7_amendment_v1.md`, `docs/registered_m7_seed_scope_v1.md`, `docs/registered_m7_single_image_v2.md`, `docs/registered_extensions_v1.md`.

| Arm | Step | Run dir | per_item sha256 |
|---|---|---|---|
| A1 real | step0 | `runs/a1_real_step0` | `e8f2913e000b8777a9883572e57ae1e4be3302f4db45db1cf2e66ac6e0117ad3` |
| A1 real | step100_seed1 | `runs/a1_real_step100_seed1` | `4d7b6e95fc05ee39992572df6510dd414749fa02df119bf9655951f00ac791f9` |
| A1 real | step100_seed2 | `runs/a1_real_step100_seed2` | `4d7b6e95fc05ee39992572df6510dd414749fa02df119bf9655951f00ac791f9` |
| A2 gray | step0 | `runs/a2_gray_step0` | `c4ecc7097a39c7402971c03471f4aa3ead722b9e3bd716ad86aebebff80d9148` |
| A2 gray | step100_seed1 | `runs/a2_gray_step100_seed1` | `4b5156adf1ac3f641533fcbaa677fbb153ffd2b546ff7ff88cb6708418263c4b` |
| A2 gray | step100_seed2 | `runs/a2_gray_step100_seed2` | `fe2dfcdfc247cce78788e02a9320279423d2da357f11627fe15d76b8a256853a` |
| A2b no-image | step0 | `runs/a2b_noimage_step0` | `4c6e827364cb3139086d6446e99ae54c9669e3cbc3ef6168defb0523bf68a9f0` |
| A2b no-image | step100_seed1 | `runs/a2b_noimage_step100_seed1` | `33c9cc698e4d106df1f7ad539bdb332f6c33381629e2df5eb6a1b82bc924ac9a` |
| A2b no-image | step100_seed2 | `runs/a2b_noimage_step100_seed2` | `d28b489bcec8deae02bb668a0d852405ac7b6a074bf1025a851c173da6b2f515` |
| A3 caption | step0 | `runs/a3_caption_step0` | `43ca41d3b6dc83756cefc8c412ef938c5d255353c10bba04dea7a13ad5e10da0` |
| A3 caption | step100_seed1 | `runs/a3_caption_step100_seed1` | `3219fb71e2ad5b249a6155fe01705bc607af0176d4516293727e090ae82483d9` |
| A3 caption | step100_seed2 | `runs/a3_caption_step100_seed2` | `3219fb71e2ad5b249a6155fe01705bc607af0176d4516293727e090ae82483d9` |
