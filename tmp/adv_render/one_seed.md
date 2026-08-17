# M7 R3 Readout V1

Status: `complete`.

Scope:
- Seed scope: seed 1 only for all four arms; every gain, recovery, and correlation below is a per-seed (one seed) number and no between-seed variance claim is made (docs/registered_m7_seed_scope_v1.md).
- Single-image restriction: M7 is restricted to single-image rows (worker.rollout.limit_images=1); retained 23,542/25,255 train rows (93.2%) and 4,239/4,501 held-out rows (94.2%) (docs/registered_m7_single_image_v2.md).
- Pooled-only readout is prohibited; corpus aggregate, every joint stratum, and source-only/category-only descriptive tables are all published; A2/A2b/A3 are never pooled into one generic blind arm (docs/registered_extensions_v1.md Extension 3, docs/registered_m7_amendment_v1.md).
- This report contains numbers and provenance only; interpretation is reserved to the PIs.

Machine artifact: `reports/one.json`.

## Strata accounting

- Joint (source, category) strata recounted from `data/heldout.jsonl`: 6 total, 5 eligible (>= 30 held-out items), 1 descriptive-small-n.
- Eligibility depends only on sample count, never on a model outcome; descriptive-small-n strata are published, not merged or discarded, and enter no rank statistic.

## Corpus aggregate (one seed (seed 1))

| Arm | n | q_bar | Acc_final step 0 | Acc_final step 100 | Gain (95% CI) |
|---|---:|---:|---:|---:|---:|
| A1 real | 179 | 0.2757 | 0.0726 | 0.9162 | 0.8436 [0.7598, 0.9274] |
| A2 gray | 179 | 0.2757 | 0.0000 | 0.1788 | 0.1788 [0.1228, 0.2346] |
| A2b no-image | 179 | 0.2757 | 0.0000 | 0.1788 | 0.1788 [0.1228, 0.2346] |
| A3 caption | 179 | 0.2757 | 0.0000 | 0.1732 | 0.1732 [0.1228, 0.2236] |

Corpus A1 denominator: estimate 0.8436, paired SE 0.0395, stable `true` (rule: gain[A1] > 0 and gain[A1] >= 2 * paired_se).

| Blind arm | Aggregate recovery (95% CI) | Status | Undefined draws | Interval label |
|---|---:|---|---:|---|
| A2 gray | 0.2119 [NA] | stable | 0/200 | stable |
| A2b no-image | 0.2119 [NA] | stable | 0/200 | stable |
| A3 caption | 0.2053 [NA] | stable | 0/200 | stable |

## Registered joint strata: q_bar (5 eligible)

| Source | Category | n | q_bar A1 | q_bar A2 | q_bar A2b | q_bar A3 |
|---|---|---:|---:|---:|---:|---:|
| s1 | cat | 30 | 0.1000 | 0.1000 | 0.1000 | 0.1000 |
| s2 | cat | 30 | 0.2000 | 0.2000 | 0.2000 | 0.2000 |
| s3 | cat | 30 | 0.3000 | 0.3000 | 0.3000 | 0.3000 |
| s4 | cat | 30 | 0.4000 | 0.4000 | 0.4000 | 0.4000 |
| s5 | cat | 30 | 0.5000 | 0.5000 | 0.5000 | 0.5000 |

## Registered joint strata: gains (one seed (seed 1))

| Source | Category | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) | A1 stable |
|---|---|---:|---:|---:|---:|---:|---|
| s1 | cat | 30 | 1.0000 [1.0000, 1.0000] | 0.4000 [0.2658, 0.6000] | 0.4000 [0.2333, 0.6000] | 0.0000 [0.0000, 0.0000] | true |
| s2 | cat | 30 | 1.0000 [1.0000, 1.0000] | 0.3000 [0.1325, 0.4667] | 0.3000 [0.1667, 0.4667] | 0.1000 [0.0000, 0.2333] | true |
| s3 | cat | 30 | 1.0000 [1.0000, 1.0000] | 0.2000 [0.0667, 0.3333] | 0.2000 [0.0667, 0.3667] | 0.2000 [0.0992, 0.3333] | true |
| s4 | cat | 30 | 1.0000 [1.0000, 1.0000] | 0.1000 [0.0000, 0.2008] | 0.1000 [0.0000, 0.2000] | 0.3000 [0.1667, 0.4667] | true |
| s5 | cat | 30 | 0.0667 [-0.2667, 0.3675] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.4000 [0.2333, 0.6000] | false |

## Registered joint strata: recovery (one seed (seed 1))

Recovery is `gain[b,s] / gain[A1,s]` only when the A1 denominator is stable (gain[A1,s] > 0 and >= 2 paired SE); otherwise `undefined-unstable-denominator`. Unstable strata stay in the gain analysis and are omitted from the recovery rank statistic.

| Source | Category | A2 recovery (95% CI) | A2b recovery (95% CI) | A3 recovery (95% CI) |
|---|---|---:|---:|---:|
| s1 | cat | 0.4000 [0.2333, 0.5675] | 0.4000 [0.2667, 0.5667] | 0.0000 [0.0000, 0.0000] |
| s2 | cat | 0.3000 [0.1333, 0.4667] | 0.3000 [0.1333, 0.4667] | 0.1000 [0.0000, 0.2008] |
| s3 | cat | 0.2000 [0.0667, 0.3333] | 0.2000 [0.0667, 0.3333] | 0.2000 [0.0667, 0.3675] |
| s4 | cat | 0.1000 [0.0000, 0.2000] | 0.1000 [0.0325, 0.2000] | 0.3000 [0.1667, 0.4342] |
| s5 | cat | undefined-unstable-denominator | undefined-unstable-denominator | undefined-unstable-denominator |

## Descriptive small-n strata (1)

Published per registration; not merged, not discarded, not in any rank statistic.

| Source | Category | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) |
|---|---|---:|---:|---:|---:|---:|
| s6 | cat | 29 | 1.0000 [1.0000, 1.0000] | 0.0690 [0.0000, 0.1724] | 0.0690 [0.0000, 0.1724] | 0.0345 [0.0000, 0.1034] |

## Rank statistics (one seed (seed 1))

Tie-corrected Spearman across eligible strata; undefined bootstrap draws are counted, never replaced with zero; an interval with more than 5% undefined draws is labeled unstable.

| Blind arm | rho_gain (95% CI) | Undefined | Label | Direction > 0 holds | rho_recovery (95% CI) | Recovery strata | Undefined | Label | Direction > 0 holds |
|---|---:|---:|---|---|---:|---:|---:|---|---|
| A2 gray | -1.0000 [-1.0000, -0.7000] | 0/200 | stable | false | -1.0000 [-1.0000, -0.3162] | 4/5 | 0/200 | stable | false |
| A2b no-image | -1.0000 [-1.0000, -0.7000] | 0/200 | stable | false | -1.0000 [-1.0000, -0.3162] | 4/5 | 0/200 | stable | false |
| A3 caption | 1.0000 [0.6992, 1.0000] | 0/200 | stable | true | 1.0000 [0.6325, 1.0000] | 4/5 | 0/200 | stable | true |

## Source-only descriptive table

Role: descriptive robustness view; does not replace the registered joint-stratum analysis.

| Group | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) |
|---|---:|---:|---:|---:|---:|
| s1 | 30 | 1.0000 [1.0000, 1.0000] | 0.4000 [0.2333, 0.5675] | 0.4000 [0.2667, 0.5667] | 0.0000 [0.0000, 0.0000] |
| s2 | 30 | 1.0000 [1.0000, 1.0000] | 0.3000 [0.1333, 0.4675] | 0.3000 [0.1667, 0.4667] | 0.1000 [0.0000, 0.2000] |
| s3 | 30 | 1.0000 [1.0000, 1.0000] | 0.2000 [0.0667, 0.3333] | 0.2000 [0.0667, 0.3333] | 0.2000 [0.1000, 0.3675] |
| s4 | 30 | 1.0000 [1.0000, 1.0000] | 0.1000 [0.0333, 0.2000] | 0.1000 [0.0000, 0.2000] | 0.3000 [0.1667, 0.4667] |
| s5 | 30 | 0.0667 [-0.3000, 0.3675] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.4000 [0.2000, 0.6000] |
| s6 | 29 | 1.0000 [1.0000, 1.0000] | 0.0690 [0.0000, 0.1724] | 0.0690 [0.0000, 0.1733] | 0.0345 [0.0000, 0.1034] |

## Category-only descriptive table

Role: descriptive robustness view; does not replace the registered joint-stratum analysis.

| Group | n | A1 gain (95% CI) | A2 gain (95% CI) | A2b gain (95% CI) | A3 gain (95% CI) |
|---|---:|---:|---:|---:|---:|
| cat | 179 | 0.8436 [0.7817, 0.9218] | 0.1788 [0.1284, 0.2291] | 0.1788 [0.1228, 0.2293] | 0.1732 [0.1173, 0.2292] |

## Geometry3K anchor comparison (one seed (seed 1); informed comparison)

This comparison is informed, not fully prospective: the anchors are the completed Geometry3K seed-1 recovery readout (Informed-Prediction Disclosure, docs/registered_m7_amendment_v1.md).

| Blind arm | Geometry3K anchor | ViRL recovery (95% CI) | Difference (95% CI) | Direction (> anchor) holds | Interval label |
|---|---:|---:|---:|---|---|
| A2 gray | 0.0789 | 0.2119 | 0.1330 [0.0734, 0.1969] | true | stable |
| A2b no-image | 0.1184 | 0.2119 | 0.0935 [0.0307, 0.1720] | true | stable |
| A3 caption | no registered anchor | 0.2053 [NA] | NA | NA | stable |

## M10 support-sharpening candidates

Rule: base 0/16 under the arm's own condition, step-0 greedy wrong, step-100 greedy correct; 64-sample frozen-base follow-up is reported separately under M10.

| Arm | Candidates | Artifact |
|---|---:|---|
| A1 real | 0 | `reports/artifacts_one/support_candidates_a1_real.jsonl` |
| A2 gray | 5 | `reports/artifacts_one/support_candidates_a2_gray.jsonl` |
| A2b no-image | 0 | `reports/artifacts_one/support_candidates_a2b_noimage.jsonl` |
| A3 caption | 0 | `reports/artifacts_one/support_candidates_a3_caption.jsonl` |

Candidate selection does not claim that RL created or taught a capability; M10 language remains non-causal.

## Provenance

- Held-out manifest: `data/heldout.jsonl` (sha256 `9ae6a2435e53313cf284178cd2f9fcb38cbf83312abc67c1402512a7273b7177`, 179 rows).
- Analysis git head: `None`.
- Bootstrap: 200 draws, seed 20260716; deterministic statistic/arm labels hashed into independent streams via src.analysis.pilot_fourarm.deterministic_seed.
- data/virl39k_m7_split_manifest_v2.json n_strata_rank_eligible=21 counts component labels, not items, and was not used; eligibility was recounted directly from the held-out jsonl.
- Registered documents: `docs/registered_m7_amendment_v1.md`, `docs/registered_m7_seed_scope_v1.md`, `docs/registered_m7_single_image_v2.md`, `docs/registered_extensions_v1.md`.

| Arm | Step | Run dir | per_item sha256 |
|---|---|---|---|
| A1 real | step0 | `runs/a1_real_step0` | `e8f2913e000b8777a9883572e57ae1e4be3302f4db45db1cf2e66ac6e0117ad3` |
| A1 real | step100 | `runs/a1_real_step100_seed1` | `4d7b6e95fc05ee39992572df6510dd414749fa02df119bf9655951f00ac791f9` |
| A2 gray | step0 | `runs/a2_gray_step0` | `c4ecc7097a39c7402971c03471f4aa3ead722b9e3bd716ad86aebebff80d9148` |
| A2 gray | step100 | `runs/a2_gray_step100_seed1` | `4b5156adf1ac3f641533fcbaa677fbb153ffd2b546ff7ff88cb6708418263c4b` |
| A2b no-image | step0 | `runs/a2b_noimage_step0` | `4c6e827364cb3139086d6446e99ae54c9669e3cbc3ef6168defb0523bf68a9f0` |
| A2b no-image | step100 | `runs/a2b_noimage_step100_seed1` | `33c9cc698e4d106df1f7ad539bdb332f6c33381629e2df5eb6a1b82bc924ac9a` |
| A3 caption | step0 | `runs/a3_caption_step0` | `43ca41d3b6dc83756cefc8c412ef938c5d255353c10bba04dea7a13ad5e10da0` |
| A3 caption | step100 | `runs/a3_caption_step100_seed1` | `3219fb71e2ad5b249a6155fe01705bc607af0176d4516293727e090ae82483d9` |
