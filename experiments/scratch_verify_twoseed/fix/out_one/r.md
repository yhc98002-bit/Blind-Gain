# M7 R3 Readout V1

Status: `complete`.

Scope:
- Seed scope: seed 1 only for all four arms; every gain, recovery, and correlation below is a per-seed (one seed) number and no between-seed variance claim is made (docs/registered_m7_seed_scope_v1.md).
- Single-image restriction: M7 is restricted to single-image rows (worker.rollout.limit_images=1); retained 23,542/25,255 train rows (93.2%) and 4,239/4,501 held-out rows (94.2%) (docs/registered_m7_single_image_v2.md).
- Pooled-only readout is prohibited; corpus aggregate, every joint stratum, and source-only/category-only descriptive tables are all published; A2/A2b/A3 are never pooled into one generic blind arm (docs/registered_extensions_v1.md Extension 3, docs/registered_m7_amendment_v1.md).
- This report contains numbers and provenance only; interpretation is reserved to the PIs.

Machine artifact: `out_one/r.json`.

## Strata accounting

- Joint (source, category) strata recounted from `data/fixture_heldout.jsonl`: 4 total, 3 eligible (>= 30 held-out items), 1 descriptive-small-n.
- Eligibility depends only on sample count, never on a model outcome; descriptive-small-n strata are published, not merged or discarded, and enter no rank statistic.

## Corpus aggregate (one seed (seed 1))

| Arm | n | q_bar | Acc_final step 0 | Acc_final step 100 | Gain (95% CI) |
|---|---:|---:|---:|---:|---:|
| A1 real | 95 | 0.2105 | 0.2737 | 0.3684 | 0.0947 [0.0105, 0.1789] |
| A2 gray | 95 | 0.2105 | 0.2316 | 0.3474 | 0.1158 [0.0316, 0.2000] |
| A2b no-image | 95 | 0.2105 | 0.2316 | 0.3579 | 0.1263 [0.0421, 0.2105] |
| A3 caption | 95 | 0.2105 | 0.2632 | 0.3684 | 0.1053 [0.0211, 0.1895] |

Corpus A1 denominator: estimate 0.0947, paired SE 0.0425, stable `true` (rule: gain[A1] > 0 and gain[A1] >= 2 * paired_se).

| Blind arm | Aggregate recovery (95% CI) | Status | Undefined draws | Interval label |
|---|---:|---|---:|---|
| A2 gray | 1.2222 [NA] | stable | 2016/5000 | unstable |
| A2b no-image | 1.3333 [NA] | stable | 2016/5000 | unstable |
| A3 caption | 1.1111 [NA] | stable | 2037/5000 | unstable |

## Registered joint strata: q_bar (3 eligible)

| Source | Category | n | q_bar A1 | q_bar A2 | q_bar A2b | q_bar A3 |
|---|---|---:|---:|---:|---:|---:|
| srcA | catX | 30 | 0.1000 | 0.1000 | 0.3000 | 0.2000 |
| srcA | catY | 30 | 0.2000 | 0.3000 | 0.2000 | 0.1000 |
| srcB | catX | 30 | 0.3000 | 0.2000 | 0.1000 | 0.3000 |

## Registered joint strata: gains (one seed (seed 1))

| Source | Category | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) | A1 stable |
|---|---|---:|---:|---:|---:|---:|---|
| srcA | catX | 30 | 0.0667 [-0.1000, 0.2333] | 0.1000 [-0.0333, 0.2333] | 0.1000 [-0.0333, 0.2333] | 0.1000 [-0.0333, 0.2333] | false |
| srcA | catY | 30 | 0.1000 [-0.0333, 0.2667] | 0.1000 [-0.0333, 0.2333] | 0.1333 [0.0000, 0.3000] | 0.1000 [-0.0667, 0.2667] | false |
| srcB | catX | 30 | 0.1000 [-0.0333, 0.2333] | 0.1333 [0.0000, 0.3000] | 0.1333 [0.0000, 0.3000] | 0.1333 [0.0000, 0.3000] | false |

## Registered joint strata: recovery (one seed (seed 1))

Recovery is `gain[b,s] / gain[A1,s]` only when the A1 denominator is stable (gain[A1,s] > 0 and >= 2 paired SE); otherwise `undefined-unstable-denominator`. Unstable strata stay in the gain analysis and are omitted from the recovery rank statistic.

| Source | Category | A2 recovery (95% CI) | A2b recovery (95% CI) | A3 recovery (95% CI) |
|---|---|---:|---:|---:|
| srcA | catX | undefined-unstable-denominator | undefined-unstable-denominator | undefined-unstable-denominator |
| srcA | catY | undefined-unstable-denominator | undefined-unstable-denominator | undefined-unstable-denominator |
| srcB | catX | undefined-unstable-denominator | undefined-unstable-denominator | undefined-unstable-denominator |

## Descriptive small-n strata (1)

Published per registration; not merged, not discarded, not in any rank statistic.

| Source | Category | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) |
|---|---|---:|---:|---:|---:|---:|
| srcB | catY | 5 | 0.2000 [0.0000, 0.6000] | 0.2000 [0.0000, 0.6000] | 0.2000 [0.0000, 0.6000] | 0.0000 [0.0000, 0.0000] |

## Rank statistics (one seed (seed 1))

Tie-corrected Spearman across eligible strata; undefined bootstrap draws are counted, never replaced with zero; an interval with more than 5% undefined draws is labeled unstable.

| Blind arm | rho_gain (95% CI) | Undefined | Label | Direction > 0 holds | rho_recovery (95% CI) | Recovery strata | Undefined | Label | Direction > 0 holds |
|---|---:|---:|---|---|---:|---:|---:|---|---|
| A2 gray | 0.0000 [-1.0000, 1.0000] | 94/5000 | stable | false | undefined-insufficient-recovery-strata | 0/3 | 4466/5000 | unstable | NA |
| A2b no-image | -0.8660 [-1.0000, 1.0000] | 76/5000 | stable | false | undefined-insufficient-recovery-strata | 0/3 | 4462/5000 | unstable | NA |
| A3 caption | 0.8660 [-1.0000, 1.0000] | 80/5000 | stable | true | undefined-insufficient-recovery-strata | 0/3 | 4468/5000 | unstable | NA |

## Source-only descriptive table

Role: descriptive robustness view; does not replace the registered joint-stratum analysis.

| Group | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) |
|---|---:|---:|---:|---:|---:|
| srcA | 60 | 0.0833 [-0.0333, 0.1833] | 0.1000 [0.0000, 0.2000] | 0.1167 [0.0167, 0.2167] | 0.1000 [0.0000, 0.2167] |
| srcB | 35 | 0.1143 [0.0000, 0.2571] | 0.1429 [0.0000, 0.2857] | 0.1429 [0.0000, 0.2857] | 0.1143 [0.0000, 0.2571] |

## Category-only descriptive table

Role: descriptive robustness view; does not replace the registered joint-stratum analysis.

| Group | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) |
|---|---:|---:|---:|---:|---:|
| catX | 60 | 0.0833 [-0.0167, 0.1833] | 0.1167 [0.0167, 0.2167] | 0.1167 [0.0167, 0.2167] | 0.1167 [0.0167, 0.2167] |
| catY | 35 | 0.1143 [0.0000, 0.2571] | 0.1143 [0.0000, 0.2571] | 0.1429 [0.0000, 0.2857] | 0.0857 [-0.0571, 0.2286] |

## Geometry3K anchor comparison (one seed (seed 1); informed comparison)

This comparison is informed, not fully prospective: the anchors are the completed Geometry3K seed-1 recovery readout (Informed-Prediction Disclosure, docs/registered_m7_amendment_v1.md).

| Blind arm | Geometry3K anchor | ViRL recovery (95% CI) | Difference (95% CI) | Direction (> anchor) holds | Interval label |
|---|---:|---:|---:|---|---|
| A2 gray | 0.0789 | 1.2222 | 1.1433 [0.1711, 1.9211] | true | unstable |
| A2b no-image | 0.1184 | 1.3333 | 1.2149 [0.1893, 2.0245] | true | unstable |
| A3 caption | no registered anchor | 1.1111 [NA] | NA | NA | unstable |

## M10 support-sharpening candidates

Rule: base 0/16 under the arm's own condition, step-0 greedy wrong, step-100 greedy correct; 64-sample frozen-base follow-up is reported separately under M10.

| Arm | Candidates | Artifact |
|---|---:|---|
| A1 real | 4 | `out_one/arts/support_candidates_a1_real.jsonl` |
| A2 gray | 1 | `out_one/arts/support_candidates_a2_gray.jsonl` |
| A2b no-image | 5 | `out_one/arts/support_candidates_a2b_noimage.jsonl` |
| A3 caption | 0 | `out_one/arts/support_candidates_a3_caption.jsonl` |

Candidate selection does not claim that RL created or taught a capability; M10 language remains non-causal.

## Provenance

- Held-out manifest: `data/fixture_heldout.jsonl` (sha256 `00317d1babc4dde5165c844effc94f67a20607a26b314a5fea8d32920fbb9605`, 95 rows).
- Analysis git head: `d5848c37e10e04472961640e28c9e4eb4ad8af5e`.
- Bootstrap: 5000 draws, seed 20260716; deterministic statistic/arm labels hashed into independent streams via src.analysis.pilot_fourarm.deterministic_seed.
- data/virl39k_m7_split_manifest_v2.json n_strata_rank_eligible=21 counts component labels, not items, and was not used; eligibility was recounted directly from the held-out jsonl.
- Registered documents: `docs/registered_m7_amendment_v1.md`, `docs/registered_m7_seed_scope_v1.md`, `docs/registered_m7_single_image_v2.md`, `docs/registered_extensions_v1.md`.

| Arm | Step | Run dir | per_item sha256 |
|---|---|---|---|
| A1 real | step0 | `runs/step0_a1_real` | `847188da1c9a7cd83b42fa10cd3abdce81c39de337eafd94b8c3710fd329d8d9` |
| A1 real | step100 | `runs/step100_a1_real_seed1` | `241bfc561a9bea78329a28c242cb764fbee7b106e0baa4a2227fd0df1121a9d5` |
| A2 gray | step0 | `runs/step0_a2_gray` | `4aafb26660aed79232ea357aae759377745d1e11577fb004d9cf2ba95bb78b47` |
| A2 gray | step100 | `runs/step100_a2_gray_seed1` | `515dcebe9c9d2bfbe90be55ac801be12d417c9d4399b065ac1eb5e7b9d283243` |
| A2b no-image | step0 | `runs/step0_a2b_noimage` | `92d284867827110958c9ae8fa8a99ddaae6720136a28b7b312994bbc464537c6` |
| A2b no-image | step100 | `runs/step100_a2b_noimage_seed1` | `5c819689148b0e549f03629c92b83f65cd7f6fd031b25a0c4063e5f3cc9fc649` |
| A3 caption | step0 | `runs/step0_a3_caption` | `ba6a574fd97bce953f81de861d393a997239fad0a84002b2e3658e77f00bbec9` |
| A3 caption | step100 | `runs/step100_a3_caption_seed1` | `236a817458f5b957b33091d19e324ae4175480d1859e18104b7b9174bf160cf0` |
