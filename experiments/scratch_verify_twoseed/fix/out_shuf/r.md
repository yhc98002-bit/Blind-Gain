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

Machine artifact: `out_shuf/r.json`.

## Strata accounting

- Joint (source, category) strata recounted from `data/fixture_heldout.jsonl`: 4 total, 3 eligible (>= 30 held-out items), 1 descriptive-small-n.
- Eligibility depends only on sample count, never on a model outcome; descriptive-small-n strata are published, not merged or discarded, and enter no rank statistic.

## Corpus aggregate (two seeds (seeds 1, 2; registered two-seed mean))

| Arm | n | q_bar | Acc_final step 0 | Acc_final step 100 | Gain (95% CI) |
|---|---:|---:|---:|---:|---:|
| A1 real | 95 | 0.2105 | 0.2737 | 0.3789 | 0.1053 [0.0421, 0.1684] |
| A2 gray | 95 | 0.2105 | 0.2316 | 0.4000 | 0.1684 [0.1053, 0.2316] |
| A2b no-image | 95 | 0.2105 | 0.2316 | 0.3684 | 0.1368 [0.0789, 0.1947] |
| A3 caption | 95 | 0.2105 | 0.2632 | 0.3895 | 0.1263 [0.0684, 0.1895] |

Corpus A1 denominator: estimate 0.1053, paired SE 0.0325, stable `true` (rule: gain[A1] > 0 and gain[A1] >= 2 * paired_se).

| Blind arm | Aggregate recovery (95% CI) | Status | Undefined draws | Interval label |
|---|---:|---|---:|---|
| A2 gray | 1.6000 [NA] | stable | 533/5000 | unstable |
| A2b no-image | 1.3000 [NA] | stable | 532/5000 | unstable |
| A3 caption | 1.2000 [NA] | stable | 539/5000 | unstable |

## Registered joint strata: q_bar (3 eligible)

| Source | Category | n | q_bar A1 | q_bar A2 | q_bar A2b | q_bar A3 |
|---|---|---:|---:|---:|---:|---:|
| srcA | catX | 30 | 0.1000 | 0.1000 | 0.3000 | 0.2000 |
| srcA | catY | 30 | 0.2000 | 0.3000 | 0.2000 | 0.1000 |
| srcB | catX | 30 | 0.3000 | 0.2000 | 0.1000 | 0.3000 |

## Registered joint strata: gains (two seeds (seeds 1, 2; registered two-seed mean))

| Source | Category | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) | A1 stable |
|---|---|---:|---:|---:|---:|---:|---|
| srcA | catX | 30 | 0.0167 [-0.0833, 0.1000] | 0.1667 [0.0667, 0.2667] | 0.1833 [0.0833, 0.3000] | 0.1667 [0.0667, 0.2833] | false |
| srcA | catY | 30 | 0.1500 [0.0333, 0.2667] | 0.1667 [0.0500, 0.2833] | 0.1667 [0.0500, 0.2833] | 0.0333 [-0.0500, 0.1167] | true |
| srcB | catX | 30 | 0.1500 [0.0333, 0.2667] | 0.1833 [0.0667, 0.3000] | 0.0500 [-0.0333, 0.1333] | 0.1833 [0.0667, 0.3000] | true |

## Registered joint strata: recovery (two seeds (seeds 1, 2; registered two-seed mean))

Recovery is `gain[b,s] / gain[A1,s]` only when the A1 denominator is stable (gain[A1,s] > 0 and >= 2 paired SE); otherwise `undefined-unstable-denominator`. Unstable strata stay in the gain analysis and are omitted from the recovery rank statistic.

| Source | Category | A2 recovery (95% CI) | A2b recovery (95% CI) | A3 recovery (95% CI) |
|---|---|---:|---:|---:|
| srcA | catX | undefined-unstable-denominator | undefined-unstable-denominator | undefined-unstable-denominator |
| srcA | catY | 1.1111 [0.2308, 4.5875] | 1.1111 [0.4000, 3.0000] | 0.2222 [-0.5000, 1.2857] |
| srcB | catX | 1.2222 [0.3333, 5.3333] | 0.3333 [-0.2000, 2.0000] | 1.2222 [0.3333, 5.3333] |

## Descriptive small-n strata (1)

Published per registration; not merged, not discarded, not in any rank statistic.

| Source | Category | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) |
|---|---|---:|---:|---:|---:|---:|
| srcB | catY | 5 | 0.1000 [-0.2000, 0.4000] | 0.1000 [0.0000, 0.3000] | 0.2000 [0.0000, 0.4000] | 0.1000 [0.0000, 0.3000] |

## Rank statistics (two seeds (seeds 1, 2; registered two-seed mean))

Tie-corrected Spearman across eligible strata; undefined bootstrap draws are counted, never replaced with zero; an interval with more than 5% undefined draws is labeled unstable.

| Blind arm | rho_gain (95% CI) | Undefined | Label | Direction > 0 holds | rho_recovery (95% CI) | Recovery strata | Undefined | Label | Direction > 0 holds |
|---|---:|---:|---|---|---:|---:|---:|---|---|
| A2 gray | 0.0000 [-1.0000, 1.0000] | 38/5000 | stable | false | -1.0000 [-1.0000, 1.0000] | 2/3 | 2312/5000 | unstable | false |
| A2b no-image | 1.0000 [0.0000, 1.0000] | 3/5000 | stable | true | 1.0000 [-1.0000, 1.0000] | 2/3 | 2211/5000 | unstable | true |
| A3 caption | 1.0000 [0.0000, 1.0000] | 0/5000 | stable | true | 1.0000 [-1.0000, 1.0000] | 2/3 | 2148/5000 | unstable | true |

## Source-only descriptive table

Role: descriptive robustness view; does not replace the registered joint-stratum analysis.

| Group | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) |
|---|---:|---:|---:|---:|---:|
| srcA | 60 | 0.0833 [0.0083, 0.1583] | 0.1667 [0.0917, 0.2500] | 0.1750 [0.0998, 0.2583] | 0.1000 [0.0331, 0.1750] |
| srcB | 35 | 0.1429 [0.0429, 0.2571] | 0.1714 [0.0714, 0.2714] | 0.0714 [-0.0143, 0.1571] | 0.1714 [0.0571, 0.2714] |

## Category-only descriptive table

Role: descriptive robustness view; does not replace the registered joint-stratum analysis.

| Group | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) |
|---|---:|---:|---:|---:|---:|
| catX | 60 | 0.0833 [0.0083, 0.1583] | 0.1750 [0.1000, 0.2583] | 0.1167 [0.0500, 0.1917] | 0.1750 [0.1000, 0.2583] |
| catY | 35 | 0.1429 [0.0286, 0.2571] | 0.1571 [0.0571, 0.2571] | 0.1714 [0.0714, 0.2714] | 0.0429 [-0.0429, 0.1286] |

## Geometry3K anchor comparison (two seeds (seeds 1, 2; registered two-seed mean); informed comparison)

This comparison is informed, not fully prospective: the anchors are the completed Geometry3K seed-1 recovery readout (Informed-Prediction Disclosure, docs/registered_m7_amendment_v1.md).

| Blind arm | Geometry3K anchor | ViRL recovery (95% CI) | Difference (95% CI) | Direction (> anchor) holds | Interval label |
|---|---:|---:|---:|---|---|
| A2 gray | 0.0789 | 1.6000 | 1.5211 [0.6811, 2.8400] | true | unstable |
| A2b no-image | 0.1184 | 1.3000 | 1.1816 [0.4956, 2.1941] | true | unstable |
| A3 caption | no registered anchor | 1.2000 [NA] | NA | NA | unstable |

## M10 support-sharpening candidates

Rule: base 0/16 under the arm's own condition, step-0 greedy wrong, step-100 greedy correct; 64-sample frozen-base follow-up is reported separately under M10.

Seed rule: candidate lists are computed per seed and published separately; no union/intersection/two-seed candidate rule is registered (docs/registered_extensions_v1.md:142), so they are not merged.

| Arm | Seed | Candidates | Artifact |
|---|---|---:|---|
| A1 real | seed1 | 4 | `out_shuf/arts/support_candidates_a1_real_seed1.jsonl` |
| A1 real | seed2 | 2 | `out_shuf/arts/support_candidates_a1_real_seed2.jsonl` |
| A2 gray | seed1 | 1 | `out_shuf/arts/support_candidates_a2_gray_seed1.jsonl` |
| A2 gray | seed2 | 5 | `out_shuf/arts/support_candidates_a2_gray_seed2.jsonl` |
| A2b no-image | seed1 | 5 | `out_shuf/arts/support_candidates_a2b_noimage_seed1.jsonl` |
| A2b no-image | seed2 | 3 | `out_shuf/arts/support_candidates_a2b_noimage_seed2.jsonl` |
| A3 caption | seed1 | 0 | `out_shuf/arts/support_candidates_a3_caption_seed1.jsonl` |
| A3 caption | seed2 | 3 | `out_shuf/arts/support_candidates_a3_caption_seed2.jsonl` |

Candidate selection does not claim that RL created or taught a capability; M10 language remains non-causal.

## Seed dispersion (descriptive only)

Role: descriptive only. 'Seed-to-seed dispersion is also reported descriptively and is not replaced by item-bootstrap uncertainty' (docs/registered_m7_amendment_v1.md:81-82); 'Use item-paired intervals; seed dispersion is separately descriptive' (docs/registered_extensions_v1.md:143). Two seeds is n=2: no seed-level confidence interval, significance test, or 'the effect replicates' claim is registered. No registered branch keys on seed disagreement; the direction verdict is read off the two-seed mean statistic in payload['rank_statistics'] and fires unchanged whatever the per-seed values do.

- q_bar[b,s] is the item mean of the frozen Jeffreys-smoothed base q_i under arm b's own information condition (docs/registered_m7_amendment_v1.md:49-51); it comes from the shared step-0 cells and is identical for both seeds.
- Registered direction verdict source: payload['rank_statistics'], computed on the two-seed mean; the per-seed values below fire no registered branch.
- Every number in this section is a point estimate. No interval, test, or replication claim is attached to a two-point seed spread.

| Arm | Gain seed1 | Gain seed2 | Gain difference | Two-seed mean gain (95% CI) |
|---|---:|---:|---:|---:|
| A1 real | 0.0947 | 0.1158 | -0.0211 | 0.1053 [0.0421, 0.1684] |
| A2 gray | 0.1158 | 0.2211 | -0.1053 | 0.1684 [0.1053, 0.2316] |
| A2b no-image | 0.1263 | 0.1474 | -0.0211 | 0.1368 [0.0789, 0.1947] |
| A3 caption | 0.1053 | 0.1474 | -0.0421 | 0.1263 [0.0684, 0.1895] |

| Blind arm | Statistic | seed1 | seed2 | Difference | Two-seed mean (registered) |
|---|---|---:|---:|---:|---:|
| A2 gray | aggregate_recovery | 1.2222 | 1.9091 | -0.6869 | 1.6000 |
| A2 gray | rho_gain | 0.0000 | NA | NA | 0.0000 |
| A2 gray | rho_recovery | NA | NA | NA | -1.0000 |
| A2b no-image | aggregate_recovery | 1.3333 | 1.2727 | 0.0606 | 1.3000 |
| A2b no-image | rho_gain | -0.8660 | 1.0000 | -1.8660 | 1.0000 |
| A2b no-image | rho_recovery | NA | 1.0000 | NA | 1.0000 |
| A3 caption | aggregate_recovery | 1.1111 | 1.2727 | -0.1616 | 1.2000 |
| A3 caption | rho_gain | 0.8660 | 0.8660 | 0.0000 | 1.0000 |
| A3 caption | rho_recovery | NA | 1.0000 | NA | 1.0000 |

## Provenance

- Held-out manifest: `data/fixture_heldout.jsonl` (sha256 `00317d1babc4dde5165c844effc94f67a20607a26b314a5fea8d32920fbb9605`, 95 rows).
- Analysis git head: `d5848c37e10e04472961640e28c9e4eb4ad8af5e`.
- Bootstrap: 5000 draws, seed 20260716; deterministic statistic/arm labels hashed into independent streams via src.analysis.pilot_fourarm.deterministic_seed.
- data/virl39k_m7_split_manifest_v2.json n_strata_rank_eligible=21 counts component labels, not items, and was not used; eligibility was recounted directly from the held-out jsonl.
- Registered documents: `docs/registered_m7_amendment_v1.md`, `docs/registered_m7_seed_scope_v1.md`, `docs/registered_m7_single_image_v2.md`, `docs/registered_extensions_v1.md`.

| Arm | Step | Run dir | per_item sha256 |
|---|---|---|---|
| A1 real | step0 | `runs/step0_a1_real` | `847188da1c9a7cd83b42fa10cd3abdce81c39de337eafd94b8c3710fd329d8d9` |
| A1 real | step100_seed1 | `runs/step100_a1_real_seed1` | `241bfc561a9bea78329a28c242cb764fbee7b106e0baa4a2227fd0df1121a9d5` |
| A1 real | step100_seed2 | `runs/shuf_step100_a1_real_seed2` | `e0e64bda946303c7a3ca21d57d14958df3de82b4045f1d080426ac82141e56c8` |
| A2 gray | step0 | `runs/step0_a2_gray` | `4aafb26660aed79232ea357aae759377745d1e11577fb004d9cf2ba95bb78b47` |
| A2 gray | step100_seed1 | `runs/step100_a2_gray_seed1` | `515dcebe9c9d2bfbe90be55ac801be12d417c9d4399b065ac1eb5e7b9d283243` |
| A2 gray | step100_seed2 | `runs/shuf_step100_a2_gray_seed2` | `e9db137ca8a54b4deae0fb8e5797aae0232d0e9c2898e4ae3a7e23235e96990b` |
| A2b no-image | step0 | `runs/step0_a2b_noimage` | `92d284867827110958c9ae8fa8a99ddaae6720136a28b7b312994bbc464537c6` |
| A2b no-image | step100_seed1 | `runs/step100_a2b_noimage_seed1` | `5c819689148b0e549f03629c92b83f65cd7f6fd031b25a0c4063e5f3cc9fc649` |
| A2b no-image | step100_seed2 | `runs/shuf_step100_a2b_noimage_seed2` | `c34039b242673ba13fe3b8106b83fdad0181653efa5c52048d05bf86509c22c3` |
| A3 caption | step0 | `runs/step0_a3_caption` | `ba6a574fd97bce953f81de861d393a997239fad0a84002b2e3658e77f00bbec9` |
| A3 caption | step100_seed1 | `runs/step100_a3_caption_seed1` | `236a817458f5b957b33091d19e324ae4175480d1859e18104b7b9174bf160cf0` |
| A3 caption | step100_seed2 | `runs/shuf_step100_a3_caption_seed2` | `113a013cd07dfd4089a7256bb0b5595345eead7bde2dda253271586f2c7b39d9` |
