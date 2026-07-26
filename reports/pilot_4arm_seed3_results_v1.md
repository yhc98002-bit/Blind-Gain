# Pilot Four-Arm Seed-3 Results V1

Status:
- Registered seed-3 readout: `complete`.
- This report computes registered analyses only and makes no PI gate decision.
- Proposal-A4 text-only transfer was not launched and is outside Paper-1 scope.

Evidence:
- Machine artifact: `reports/pilot_4arm_seed3_results_v1.json`.
- Geometry3K: `601` audited rows per arm.
- FlipTrack R19: `1200` paired items at steps 0, 60, and 100.
- Bootstrap: `5000` paired item draws, seed `20260716`.
- All four inputs passed independent audit before any per-item result was loaded.
- Training is reported as a matched optimizer budget; no FLOP-equality claim is made.

## Training Resource Accounting

| Arm | Steps | Retained trajectory tokens | Active step time (h) | Final process segment (h) | Node / GPUs |
|---|---:|---:|---:|---:|---|
| A1 real | 100 | 201276341 | 40.48 | 40.62 | an29 / 0,1,2,3 |
| A2 gray | 100 | 196870226 | 39.52 | 39.76 | an12 / 0,1,2,3 |
| A2b no-image | 100 | 108383838 | 29.23 | 29.55 | an29 / 0,1,2,3 |
| A3 caption | 100 | 154171919 | 30.41 | 30.61 | an29 / 0,1,2,3 |

Matched budget signature: `fc55674f3eb2abfec5a082a431eb4b4f344cf8d53d05410f73b68c6ab73ebe4b`. Active step time is the sum of EasyR1's per-step `perf.time_per_step` on the retained 1-100 trajectory; final process time covers only the immutable terminal run segment and is not used as a compute-equivalence claim.

## Primary RQ1: Geometry3K

| Arm | Acc step 0 | Acc step 100 | Delta Acc_final (95% CI) | Strict step 0 | Strict step 100 |
|---|---:|---:|---:|---:|---:|
| A1 real | 0.1747 | 0.4060 | 0.2313 [0.1913, 0.2729] | 0.0599 | 0.4060 |
| A2 gray | 0.0899 | 0.1082 | 0.0183 [-0.0033, 0.0399] | 0.0050 | 0.1082 |
| A2b no-image | 0.0682 | 0.1215 | 0.0532 [0.0333, 0.0749] | 0.0017 | 0.1215 |
| A3 caption | 0.2097 | 0.3311 | 0.1215 [0.0865, 0.1547] | 0.0250 | 0.3311 |

| Registered contrast | Estimate (paired 95% CI) |
|---|---:|
| D_gray | 0.2130 [0.1681, 0.2596] |
| D_none | 0.1780 [0.1331, 0.2263] |
| D_caption | 0.1098 [0.0616, 0.1581] |

Recovery denominator stable: `true`.

| Arm | Recovery fraction (95% CI) | Interpretation permitted |
|---|---:|---:|
| A2 gray | 0.0791 [-0.0142, 0.1774] | true |
| A2b no-image | 0.2302 [0.1407, 0.3333] | true |
| A3 caption | 0.5252 [0.3701, 0.7117] | true |

## Registered Secondary Contrasts

| Estimand | Estimate (paired 95% CI) |
|---|---:|
| D_caption^final = Acc_A3,100 - Acc_A1,100 | -0.0749 [-0.1165, -0.0333] |
| D_caption^gain = Delta_A3 - Delta_A1 | -0.1098 [-0.1614, -0.0616] |
| Delta_A2gray - Delta_A2b | -0.0349 [-0.0616, -0.0083] |

Gray/no-image equivalence within +/-0.05 supported: `false`.

## Strict Accounting

| Arm | StrictGain | AnswerGain | G_format | Exact identity |
|---|---:|---:|---:|---:|
| A1 real | 0.3461 | 0.2313 | 0.1148 | true |
| A2 gray | 0.1032 | 0.0183 | 0.0849 | true |
| A2b no-image | 0.1198 | 0.0532 | 0.0666 | true |
| A3 caption | 0.3062 | 0.1215 | 0.1847 | true |

## Mechanism: Baseline Reward-Opportunity

`q_i` is a Jeffreys-smoothed estimate of baseline reward-opportunity, not a directly observed latent.

| Arm | Hurdle contrast (95% CI) | Floor n | Above n | Spearman all | Spearman above floor |
|---|---:|---:|---:|---:|---:|
| A1 real | 0.2496 [0.1719, 0.3258] | 278 | 323 | 0.2560 | 0.0650 |
| A2 gray | 0.0495 [-0.0394, 0.1384] | 480 | 121 | 0.0618 | -0.1430 |
| A2b no-image | 0.1657 [0.0870, 0.2480] | 483 | 118 | 0.2602 | 0.0468 |
| A3 caption | 0.0767 [0.0066, 0.1476] | 284 | 317 | 0.1200 | 0.0780 |

The machine artifact contains the registered floor group and ten equal-count above-floor deciles for every arm.

## Primary RQ2: FlipTrack R19 Geometry

| Arm | Step | Pair acc step 0 | Pair acc checkpoint | Delta (paired 95% CI) | No material change supported |
|---|---:|---:|---:|---:|---:|
| A1 real | 60 | 0.4717 | 0.4883 | 0.0167 [-0.0067, 0.0400] | true |
| A1 real | 100 | 0.4717 | 0.4817 | 0.0100 [-0.0150, 0.0350] | true |
| A2 gray | 60 | 0.4717 | 0.4517 | -0.0200 [-0.0467, 0.0050] | true |
| A2 gray | 100 | 0.4717 | 0.4350 | -0.0367 [-0.0650, -0.0100] | false |
| A2b no-image | 60 | 0.4717 | 0.4567 | -0.0150 [-0.0400, 0.0083] | true |
| A2b no-image | 100 | 0.4717 | 0.4383 | -0.0333 [-0.0600, -0.0067] | false |
| A3 caption | 60 | 0.4717 | 0.4600 | -0.0117 [-0.0367, 0.0117] | true |
| A3 caption | 100 | 0.4717 | 0.4767 | 0.0050 [-0.0183, 0.0283] | true |

## R19 Overall and Categories

Overall R19 is shown with every per-category result; no R19-minus-chart composite is computed.
The chart label is **cued chart point-value reading**. Document is calibration only.

| Arm | Step | Scope | Pair acc step 0 | Pair acc checkpoint | Delta (95% CI) |
|---|---:|---|---:|---:|---:|
| A1 real | 60 | overall | 0.5617 | 0.5917 | 0.0300 [0.0125, 0.0483] |
| A1 real | 60 | category:chart_two_hop_read | 0.4367 | 0.5067 | 0.0700 [0.0233, 0.1167] |
| A1 real | 60 | category:document_header_indexing | 0.8667 | 0.8833 | 0.0167 [-0.0067, 0.0433] |
| A1 real | 60 | category:geometry_coordinate_indexing | 0.4717 | 0.4883 | 0.0167 [-0.0067, 0.0400] |
| A1 real | 100 | overall | 0.5617 | 0.5883 | 0.0267 [0.0083, 0.0450] |
| A1 real | 100 | category:chart_two_hop_read | 0.4367 | 0.5100 | 0.0733 [0.0233, 0.1200] |
| A1 real | 100 | category:document_header_indexing | 0.8667 | 0.8800 | 0.0133 [-0.0133, 0.0400] |
| A1 real | 100 | category:geometry_coordinate_indexing | 0.4717 | 0.4817 | 0.0100 [-0.0150, 0.0350] |
| A2 gray | 60 | overall | 0.5617 | 0.5650 | 0.0033 [-0.0150, 0.0208] |
| A2 gray | 60 | category:chart_two_hop_read | 0.4367 | 0.4667 | 0.0300 [-0.0133, 0.0733] |
| A2 gray | 60 | category:document_header_indexing | 0.8667 | 0.8900 | 0.0233 [-0.0033, 0.0500] |
| A2 gray | 60 | category:geometry_coordinate_indexing | 0.4717 | 0.4517 | -0.0200 [-0.0467, 0.0050] |
| A2 gray | 100 | overall | 0.5617 | 0.5625 | 0.0008 [-0.0183, 0.0200] |
| A2 gray | 100 | category:chart_two_hop_read | 0.4367 | 0.4867 | 0.0500 [0.0000, 0.0967] |
| A2 gray | 100 | category:document_header_indexing | 0.8667 | 0.8933 | 0.0267 [0.0033, 0.0533] |
| A2 gray | 100 | category:geometry_coordinate_indexing | 0.4717 | 0.4350 | -0.0367 [-0.0650, -0.0100] |
| A2b no-image | 60 | overall | 0.5617 | 0.5700 | 0.0083 [-0.0092, 0.0258] |
| A2b no-image | 60 | category:chart_two_hop_read | 0.4367 | 0.4767 | 0.0400 [-0.0033, 0.0833] |
| A2b no-image | 60 | category:document_header_indexing | 0.8667 | 0.8900 | 0.0233 [-0.0033, 0.0500] |
| A2b no-image | 60 | category:geometry_coordinate_indexing | 0.4717 | 0.4567 | -0.0150 [-0.0400, 0.0083] |
| A2b no-image | 100 | overall | 0.5617 | 0.5642 | 0.0025 [-0.0167, 0.0217] |
| A2b no-image | 100 | category:chart_two_hop_read | 0.4367 | 0.4867 | 0.0500 [0.0033, 0.0933] |
| A2b no-image | 100 | category:document_header_indexing | 0.8667 | 0.8933 | 0.0267 [0.0000, 0.0533] |
| A2b no-image | 100 | category:geometry_coordinate_indexing | 0.4717 | 0.4383 | -0.0333 [-0.0600, -0.0067] |
| A3 caption | 60 | overall | 0.5617 | 0.5683 | 0.0067 [-0.0108, 0.0242] |
| A3 caption | 60 | category:chart_two_hop_read | 0.4367 | 0.4667 | 0.0300 [-0.0167, 0.0767] |
| A3 caption | 60 | category:document_header_indexing | 0.8667 | 0.8867 | 0.0200 [-0.0033, 0.0433] |
| A3 caption | 60 | category:geometry_coordinate_indexing | 0.4717 | 0.4600 | -0.0117 [-0.0367, 0.0117] |
| A3 caption | 100 | overall | 0.5617 | 0.5650 | 0.0033 [-0.0150, 0.0225] |
| A3 caption | 100 | category:chart_two_hop_read | 0.4367 | 0.4267 | -0.0100 [-0.0600, 0.0400] |
| A3 caption | 100 | category:document_header_indexing | 0.8667 | 0.8800 | 0.0133 [-0.0133, 0.0400] |
| A3 caption | 100 | category:geometry_coordinate_indexing | 0.4717 | 0.4767 | 0.0050 [-0.0183, 0.0283] |

## Support-Sharpening

- No new M10 candidate set is minted from a follow-up seed; the registered frozen seed-1 candidate sets remain authoritative.

Problems:
- This single-seed report does not by itself quantify run-to-run RL variance; the registered multi-seed summary remains pending.

Decision:
- None. PIs interpret the registered estimands and decide subsequent gates.

Next actions:
- Complete the remaining registered pilot seeds and build the pooled descriptive summary.
- Keep R19/R20 unpooled and preserve all raw per-item artifacts.
