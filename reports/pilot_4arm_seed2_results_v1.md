# Pilot Four-Arm Seed-2 Results V1

Status:
- Registered seed-2 readout: `complete`.
- This report computes registered analyses only and makes no PI gate decision.
- Proposal-A4 text-only transfer was not launched and is outside Paper-1 scope.

Evidence:
- Machine artifact: `reports/pilot_4arm_seed2_results_v1.json`.
- Geometry3K: `601` audited rows per arm.
- FlipTrack R19: `1200` paired items at steps 0, 60, and 100.
- Bootstrap: `5000` paired item draws, seed `20260716`.
- All four inputs passed independent audit before any per-item result was loaded.
- Training is reported as a matched optimizer budget; no FLOP-equality claim is made.

## Training Resource Accounting

| Arm | Steps | Retained trajectory tokens | Active step time (h) | Final process segment (h) | Node / GPUs |
|---|---:|---:|---:|---:|---|
| A1 real | 100 | 200895890 | 46.52 | 46.76 | an29 / 2,5,6,7 |
| A2 gray | 100 | 192515324 | 45.05 | 31.53 | an12 / 0,1,2,3 |
| A2b no-image | 100 | 102422320 | 37.68 | 23.04 | an29 / 0,1,2,3 |
| A3 caption | 100 | 150507584 | 30.44 | 30.75 | an29 / 0,1,2,3 |

Matched budget signature: `b6ce73b87585819bea0b8dd09930aa27c74e0690898c836648aa0fdb0ae71e7d`. Active step time is the sum of EasyR1's per-step `perf.time_per_step` on the retained 1-100 trajectory; final process time covers only the immutable terminal run segment and is not used as a compute-equivalence claim.

## Primary RQ1: Geometry3K

| Arm | Acc step 0 | Acc step 100 | Delta Acc_final (95% CI) | Strict step 0 | Strict step 100 |
|---|---:|---:|---:|---:|---:|
| A1 real | 0.1747 | 0.4210 | 0.2463 [0.2030, 0.2895] | 0.0599 | 0.4210 |
| A2 gray | 0.0899 | 0.0998 | 0.0100 [-0.0116, 0.0316] | 0.0050 | 0.0998 |
| A2b no-image | 0.0682 | 0.1231 | 0.0549 [0.0316, 0.0782] | 0.0017 | 0.1231 |
| A3 caption | 0.2097 | 0.2928 | 0.0832 [0.0483, 0.1181] | 0.0250 | 0.2928 |

| Registered contrast | Estimate (paired 95% CI) |
|---|---:|
| D_gray | 0.2363 [0.1896, 0.2829] |
| D_none | 0.1913 [0.1448, 0.2396] |
| D_caption | 0.1631 [0.1115, 0.2146] |

Recovery denominator stable: `true`.

| Arm | Recovery fraction (95% CI) | Interpretation permitted |
|---|---:|---:|
| A2 gray | 0.0405 [-0.0490, 0.1298] | true |
| A2b no-image | 0.2230 [0.1307, 0.3333] | true |
| A3 caption | 0.3378 [0.1908, 0.5000] | true |

## Registered Secondary Contrasts

| Estimand | Estimate (paired 95% CI) |
|---|---:|
| D_caption^final = Acc_A3,100 - Acc_A1,100 | -0.1281 [-0.1681, -0.0882] |
| D_caption^gain = Delta_A3 - Delta_A1 | -0.1631 [-0.2163, -0.1115] |
| Delta_A2gray - Delta_A2b | -0.0449 [-0.0765, -0.0166] |

Gray/no-image equivalence within +/-0.05 supported: `false`.

## Strict Accounting

| Arm | StrictGain | AnswerGain | G_format | Exact identity |
|---|---:|---:|---:|---:|
| A1 real | 0.3611 | 0.2463 | 0.1148 | true |
| A2 gray | 0.0948 | 0.0100 | 0.0849 | true |
| A2b no-image | 0.1215 | 0.0549 | 0.0666 | true |
| A3 caption | 0.2679 | 0.0832 | 0.1847 | true |

## Mechanism: Baseline Reward-Opportunity

`q_i` is a Jeffreys-smoothed estimate of baseline reward-opportunity, not a directly observed latent.

| Arm | Hurdle contrast (95% CI) | Floor n | Above n | Spearman all | Spearman above floor |
|---|---:|---:|---:|---:|---:|
| A1 real | 0.2106 [0.1282, 0.2920] | 278 | 323 | 0.2034 | 0.0352 |
| A2 gray | 0.0185 [-0.0765, 0.1156] | 480 | 121 | 0.0116 | -0.1602 |
| A2b no-image | 0.1426 [0.0514, 0.2356] | 483 | 118 | 0.1927 | -0.1067 |
| A3 caption | 0.0643 [-0.0044, 0.1320] | 284 | 317 | 0.0816 | 0.0165 |

The machine artifact contains the registered floor group and ten equal-count above-floor deciles for every arm.

## Primary RQ2: FlipTrack R19 Geometry

| Arm | Step | Pair acc step 0 | Pair acc checkpoint | Delta (paired 95% CI) | No material change supported |
|---|---:|---:|---:|---:|---:|
| A1 real | 60 | 0.4717 | 0.4767 | 0.0050 [-0.0200, 0.0283] | true |
| A1 real | 100 | 0.4717 | 0.4800 | 0.0083 [-0.0167, 0.0333] | true |
| A2 gray | 60 | 0.4717 | 0.4517 | -0.0200 [-0.0450, 0.0050] | true |
| A2 gray | 100 | 0.4717 | 0.4267 | -0.0450 [-0.0733, -0.0183] | false |
| A2b no-image | 60 | 0.4717 | 0.4550 | -0.0167 [-0.0433, 0.0083] | true |
| A2b no-image | 100 | 0.4717 | 0.4467 | -0.0250 [-0.0517, 0.0017] | false |
| A3 caption | 60 | 0.4717 | 0.4633 | -0.0083 [-0.0333, 0.0167] | true |
| A3 caption | 100 | 0.4717 | 0.4600 | -0.0117 [-0.0383, 0.0150] | true |

## R19 Overall and Categories

Overall R19 is shown with every per-category result; no R19-minus-chart composite is computed.
The chart label is **cued chart point-value reading**. Document is calibration only.

| Arm | Step | Scope | Pair acc step 0 | Pair acc checkpoint | Delta (95% CI) |
|---|---:|---|---:|---:|---:|
| A1 real | 60 | overall | 0.5617 | 0.5750 | 0.0133 [-0.0033, 0.0308] |
| A1 real | 60 | category:chart_two_hop_read | 0.4367 | 0.4767 | 0.0400 [-0.0067, 0.0834] |
| A1 real | 60 | category:document_header_indexing | 0.8667 | 0.8700 | 0.0033 [-0.0233, 0.0300] |
| A1 real | 60 | category:geometry_coordinate_indexing | 0.4717 | 0.4767 | 0.0050 [-0.0200, 0.0283] |
| A1 real | 100 | overall | 0.5617 | 0.5825 | 0.0208 [0.0033, 0.0392] |
| A1 real | 100 | category:chart_two_hop_read | 0.4367 | 0.4900 | 0.0533 [0.0099, 0.1000] |
| A1 real | 100 | category:document_header_indexing | 0.8667 | 0.8800 | 0.0133 [-0.0100, 0.0367] |
| A1 real | 100 | category:geometry_coordinate_indexing | 0.4717 | 0.4800 | 0.0083 [-0.0167, 0.0333] |
| A2 gray | 60 | overall | 0.5617 | 0.5667 | 0.0050 [-0.0133, 0.0225] |
| A2 gray | 60 | category:chart_two_hop_read | 0.4367 | 0.4767 | 0.0400 [-0.0033, 0.0833] |
| A2 gray | 60 | category:document_header_indexing | 0.8667 | 0.8867 | 0.0200 [-0.0033, 0.0467] |
| A2 gray | 60 | category:geometry_coordinate_indexing | 0.4717 | 0.4517 | -0.0200 [-0.0450, 0.0050] |
| A2 gray | 100 | overall | 0.5617 | 0.5567 | -0.0050 [-0.0233, 0.0142] |
| A2 gray | 100 | category:chart_two_hop_read | 0.4367 | 0.4900 | 0.0533 [0.0067, 0.1000] |
| A2 gray | 100 | category:document_header_indexing | 0.8667 | 0.8833 | 0.0167 [-0.0033, 0.0400] |
| A2 gray | 100 | category:geometry_coordinate_indexing | 0.4717 | 0.4267 | -0.0450 [-0.0733, -0.0183] |
| A2b no-image | 60 | overall | 0.5617 | 0.5650 | 0.0033 [-0.0150, 0.0208] |
| A2b no-image | 60 | category:chart_two_hop_read | 0.4367 | 0.4600 | 0.0233 [-0.0200, 0.0667] |
| A2b no-image | 60 | category:document_header_indexing | 0.8667 | 0.8900 | 0.0233 [-0.0033, 0.0500] |
| A2b no-image | 60 | category:geometry_coordinate_indexing | 0.4717 | 0.4550 | -0.0167 [-0.0433, 0.0083] |
| A2b no-image | 100 | overall | 0.5617 | 0.5575 | -0.0042 [-0.0225, 0.0142] |
| A2b no-image | 100 | category:chart_two_hop_read | 0.4367 | 0.4500 | 0.0133 [-0.0333, 0.0600] |
| A2b no-image | 100 | category:document_header_indexing | 0.8667 | 0.8867 | 0.0200 [-0.0067, 0.0467] |
| A2b no-image | 100 | category:geometry_coordinate_indexing | 0.4717 | 0.4467 | -0.0250 [-0.0517, 0.0017] |
| A3 caption | 60 | overall | 0.5617 | 0.5667 | 0.0050 [-0.0133, 0.0233] |
| A3 caption | 60 | category:chart_two_hop_read | 0.4367 | 0.4533 | 0.0167 [-0.0300, 0.0633] |
| A3 caption | 60 | category:document_header_indexing | 0.8667 | 0.8867 | 0.0200 [-0.0033, 0.0433] |
| A3 caption | 60 | category:geometry_coordinate_indexing | 0.4717 | 0.4633 | -0.0083 [-0.0333, 0.0167] |
| A3 caption | 100 | overall | 0.5617 | 0.5708 | 0.0092 [-0.0100, 0.0283] |
| A3 caption | 100 | category:chart_two_hop_read | 0.4367 | 0.4700 | 0.0333 [-0.0133, 0.0800] |
| A3 caption | 100 | category:document_header_indexing | 0.8667 | 0.8933 | 0.0267 [0.0033, 0.0500] |
| A3 caption | 100 | category:geometry_coordinate_indexing | 0.4717 | 0.4600 | -0.0117 [-0.0383, 0.0150] |

## Support-Sharpening

- No new M10 candidate set is minted from a follow-up seed; the registered frozen seed-1 candidate sets remain authoritative.

Problems:
- This single-seed report does not by itself quantify run-to-run RL variance; the registered multi-seed summary remains pending.

Decision:
- None. PIs interpret the registered estimands and decide subsequent gates.

Next actions:
- Complete the remaining registered pilot seeds and build the pooled descriptive summary.
- Keep R19/R20 unpooled and preserve all raw per-item artifacts.
