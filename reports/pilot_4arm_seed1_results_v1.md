# Pilot Four-Arm Seed-1 Results V1

Status:
- Registered seed-1 readout: `complete`.
- This report computes registered analyses only and makes no PI gate decision.
- Proposal-A4 text-only transfer was not launched and is outside Paper-1 scope.

Evidence:
- Machine artifact: `reports/pilot_4arm_seed1_results_v1.json`.
- Geometry3K: `601` audited rows per arm.
- FlipTrack R19: `1200` paired items at steps 0, 60, and 100.
- Bootstrap: `5000` paired item draws, seed `20260716`.
- All four inputs passed independent audit before any per-item result was loaded.
- Training is reported as a matched optimizer budget; no FLOP-equality claim is made.

## Training Resource Accounting

| Arm | Steps | Retained trajectory tokens | Active step time (h) | Final process segment (h) | Node / GPUs |
|---|---:|---:|---:|---:|---|
| A1 real | 100 | 203927728 | 39.70 | 16.42 | an12 / 0,1,2,3 |
| A2 gray | 100 | 194590491 | 38.92 | 15.96 | an12 / 0,1,2,3 |
| A2b no-image | 100 | 107931491 | 28.97 | 29.11 | an29 / 0,1,2,3 |
| A3 caption | 100 | 151707698 | 30.41 | 24.68 | an29 / 4,5,6,7 |

Matched budget signature: `685fbbc6ff0d76cfd1cccd27bf17bc2632b3746dd4e978a75e3735751a5cf3c6`. Active step time is the sum of EasyR1's per-step `perf.time_per_step` on the retained 1-100 trajectory; final process time covers only the immutable terminal run segment and is not used as a compute-equivalence claim.

## Primary RQ1: Geometry3K

| Arm | Acc step 0 | Acc step 100 | Delta Acc_final (95% CI) | Strict step 0 | Strict step 100 |
|---|---:|---:|---:|---:|---:|
| A1 real | 0.1747 | 0.4276 | 0.2529 [0.2097, 0.2945] | 0.0599 | 0.4276 |
| A2 gray | 0.0899 | 0.1098 | 0.0200 [-0.0017, 0.0416] | 0.0050 | 0.1098 |
| A2b no-image | 0.0682 | 0.0982 | 0.0300 [0.0083, 0.0516] | 0.0017 | 0.0982 |
| A3 caption | 0.2097 | 0.3195 | 0.1098 [0.0732, 0.1448] | 0.0250 | 0.3195 |

| Registered contrast | Estimate (paired 95% CI) |
|---|---:|
| D_gray | 0.2329 [0.1880, 0.2779] |
| D_none | 0.2230 [0.1764, 0.2696] |
| D_caption | 0.1431 [0.0915, 0.1963] |

Recovery denominator stable: `true`.

| Arm | Recovery fraction (95% CI) | Interpretation permitted |
|---|---:|---:|
| A2 gray | 0.0789 [-0.0065, 0.1677] | true |
| A2b no-image | 0.1184 [0.0339, 0.2042] | true |
| A3 caption | 0.4342 [0.2831, 0.6053] | true |

## Registered Secondary Contrasts

| Estimand | Estimate (paired 95% CI) |
|---|---:|
| D_caption^final = Acc_A3,100 - Acc_A1,100 | -0.1082 [-0.1481, -0.0682] |
| D_caption^gain = Delta_A3 - Delta_A1 | -0.1431 [-0.1947, -0.0899] |
| Delta_A2gray - Delta_A2b | -0.0100 [-0.0383, 0.0200] |

Gray/no-image equivalence within +/-0.05 supported: `true`.

## Strict Accounting

| Arm | StrictGain | AnswerGain | G_format | Exact identity |
|---|---:|---:|---:|---:|
| A1 real | 0.3677 | 0.2529 | 0.1148 | true |
| A2 gray | 0.1048 | 0.0200 | 0.0849 | true |
| A2b no-image | 0.0965 | 0.0300 | 0.0666 | true |
| A3 caption | 0.2945 | 0.1098 | 0.1847 | true |

## Mechanism: Baseline Reward-Opportunity

`q_i` is a Jeffreys-smoothed estimate of baseline reward-opportunity, not a directly observed latent.

| Arm | Hurdle contrast (95% CI) | Floor n | Above n | Spearman all | Spearman above floor |
|---|---:|---:|---:|---:|---:|
| A1 real | 0.2296 [0.1488, 0.3110] | 278 | 323 | 0.2326 | 0.0648 |
| A2 gray | 0.0785 [-0.0084, 0.1694] | 480 | 121 | 0.1017 | -0.1633 |
| A2b no-image | 0.0998 [0.0066, 0.1930] | 483 | 118 | 0.1514 | -0.0296 |
| A3 caption | 0.1081 [0.0400, 0.1762] | 284 | 317 | 0.1371 | 0.0403 |

The machine artifact contains the registered floor group and ten equal-count above-floor deciles for every arm.

## Primary RQ2: FlipTrack R19 Geometry

| Arm | Step | Pair acc step 0 | Pair acc checkpoint | Delta (paired 95% CI) | No material change supported |
|---|---:|---:|---:|---:|---:|
| A1 real | 60 | 0.4717 | 0.4733 | 0.0017 [-0.0233, 0.0267] | true |
| A1 real | 100 | 0.4717 | 0.4700 | -0.0017 [-0.0283, 0.0250] | true |
| A2 gray | 60 | 0.4717 | 0.4433 | -0.0283 [-0.0533, -0.0017] | false |
| A2 gray | 100 | 0.4717 | 0.4267 | -0.0450 [-0.0733, -0.0183] | false |
| A2b no-image | 60 | 0.4717 | 0.4533 | -0.0183 [-0.0433, 0.0067] | true |
| A2b no-image | 100 | 0.4717 | 0.4483 | -0.0233 [-0.0483, 0.0017] | true |
| A3 caption | 60 | 0.4717 | 0.4567 | -0.0150 [-0.0400, 0.0100] | true |
| A3 caption | 100 | 0.4717 | 0.4633 | -0.0083 [-0.0350, 0.0167] | true |

## R19 Overall and Categories

Overall R19 is shown with every per-category result; no R19-minus-chart composite is computed.
The chart label is **cued chart point-value reading**. Document is calibration only.

| Arm | Step | Scope | Pair acc step 0 | Pair acc checkpoint | Delta (95% CI) |
|---|---:|---|---:|---:|---:|
| A1 real | 60 | overall | 0.5617 | 0.5858 | 0.0242 [0.0067, 0.0425] |
| A1 real | 60 | category:chart_two_hop_read | 0.4367 | 0.5100 | 0.0733 [0.0267, 0.1200] |
| A1 real | 60 | category:document_header_indexing | 0.8667 | 0.8867 | 0.0200 [-0.0033, 0.0433] |
| A1 real | 60 | category:geometry_coordinate_indexing | 0.4717 | 0.4733 | 0.0017 [-0.0233, 0.0267] |
| A1 real | 100 | overall | 0.5617 | 0.5900 | 0.0283 [0.0100, 0.0475] |
| A1 real | 100 | category:chart_two_hop_read | 0.4367 | 0.5233 | 0.0867 [0.0367, 0.1367] |
| A1 real | 100 | category:document_header_indexing | 0.8667 | 0.8967 | 0.0300 [0.0067, 0.0567] |
| A1 real | 100 | category:geometry_coordinate_indexing | 0.4717 | 0.4700 | -0.0017 [-0.0283, 0.0250] |
| A2 gray | 60 | overall | 0.5617 | 0.5625 | 0.0008 [-0.0167, 0.0183] |
| A2 gray | 60 | category:chart_two_hop_read | 0.4367 | 0.4800 | 0.0433 [0.0033, 0.0867] |
| A2 gray | 60 | category:document_header_indexing | 0.8667 | 0.8833 | 0.0167 [-0.0067, 0.0433] |
| A2 gray | 60 | category:geometry_coordinate_indexing | 0.4717 | 0.4433 | -0.0283 [-0.0533, -0.0017] |
| A2 gray | 100 | overall | 0.5617 | 0.5617 | 0.0000 [-0.0200, 0.0200] |
| A2 gray | 100 | category:chart_two_hop_read | 0.4367 | 0.5000 | 0.0633 [0.0167, 0.1133] |
| A2 gray | 100 | category:document_header_indexing | 0.8667 | 0.8933 | 0.0267 [0.0033, 0.0501] |
| A2 gray | 100 | category:geometry_coordinate_indexing | 0.4717 | 0.4267 | -0.0450 [-0.0733, -0.0183] |
| A2b no-image | 60 | overall | 0.5617 | 0.5583 | -0.0033 [-0.0208, 0.0142] |
| A2b no-image | 60 | category:chart_two_hop_read | 0.4367 | 0.4433 | 0.0067 [-0.0367, 0.0500] |
| A2b no-image | 60 | category:document_header_indexing | 0.8667 | 0.8833 | 0.0167 [-0.0067, 0.0400] |
| A2b no-image | 60 | category:geometry_coordinate_indexing | 0.4717 | 0.4533 | -0.0183 [-0.0433, 0.0067] |
| A2b no-image | 100 | overall | 0.5617 | 0.5575 | -0.0042 [-0.0217, 0.0142] |
| A2b no-image | 100 | category:chart_two_hop_read | 0.4367 | 0.4433 | 0.0067 [-0.0367, 0.0500] |
| A2b no-image | 100 | category:document_header_indexing | 0.8667 | 0.8900 | 0.0233 [0.0000, 0.0500] |
| A2b no-image | 100 | category:geometry_coordinate_indexing | 0.4717 | 0.4483 | -0.0233 [-0.0483, 0.0017] |
| A3 caption | 60 | overall | 0.5617 | 0.5667 | 0.0050 [-0.0133, 0.0233] |
| A3 caption | 60 | category:chart_two_hop_read | 0.4367 | 0.4700 | 0.0333 [-0.0133, 0.0800] |
| A3 caption | 60 | category:document_header_indexing | 0.8667 | 0.8833 | 0.0167 [-0.0067, 0.0433] |
| A3 caption | 60 | category:geometry_coordinate_indexing | 0.4717 | 0.4567 | -0.0150 [-0.0400, 0.0100] |
| A3 caption | 100 | overall | 0.5617 | 0.5767 | 0.0150 [-0.0042, 0.0333] |
| A3 caption | 100 | category:chart_two_hop_read | 0.4367 | 0.4900 | 0.0533 [0.0067, 0.1000] |
| A3 caption | 100 | category:document_header_indexing | 0.8667 | 0.8900 | 0.0233 [0.0000, 0.0467] |
| A3 caption | 100 | category:geometry_coordinate_indexing | 0.4717 | 0.4633 | -0.0083 [-0.0350, 0.0167] |

## Support-Sharpening Candidates

| Arm | Base 0/16, greedy wrong -> step-100 correct | Candidate artifact |
|---|---:|---|
| A1 real | 47 | `experiments/runs/pilot_4arm_seed1_readout_retry_login_20260716T161914Z/artifacts/support_candidates_a1_real.jsonl` |
| A2 gray | 8 | `experiments/runs/pilot_4arm_seed1_readout_retry_login_20260716T161914Z/artifacts/support_candidates_a2_gray.jsonl` |
| A2b no-image | 7 | `experiments/runs/pilot_4arm_seed1_readout_retry_login_20260716T161914Z/artifacts/support_candidates_a2b_noimage.jsonl` |
| A3 caption | 18 | `experiments/runs/pilot_4arm_seed1_readout_retry_login_20260716T161914Z/artifacts/support_candidates_a3_caption.jsonl` |

The registered 64-sample frozen-base follow-up is reported separately under M10; candidate selection here does not claim that RL created or taught a capability.

Problems:
- Seed dispersion is unavailable in this one-seed pilot and item-level intervals do not quantify run-to-run RL variance.
- M10 64-sample support-sharpening follow-up remains pending for the listed candidates.

Decision:
- None. PIs interpret the registered estimands and decide subsequent gates.

Next actions:
- Run the registered M10 follow-up and launch seed-2 plus M5 according to PI priority.
- Keep R19/R20 unpooled and preserve all raw per-item artifacts.
