# Seed-1 R19 Key-Shuffle Null and Chart Diagnostics V1

Status:
- Cached-prediction analysis complete; no inference or retraining was run.
- This report adds the registered null and chart diagnostics to the PI-verified seed-1 core readout. It makes no scientific gate decision.
- Rejecting this null does not by itself establish perceptual learning.

Evidence:
- Machine artifact: `reports/pilot_4arm_seed1_r19_null_v1.json`.
- Frozen parser: `canonical-v2`; scorer SHA256: `7812612c4b0fcbd24e2c20b1afc48cf33b7884efd3b9e2baaea368f42d28b446`.
- Within-template answer-key shuffles: `1000`; seed: `0`.
- Every checkpoint row was recomputed from the immutable cached predictions and checked against the existing seed-1 category value.

## Within-Template Key-Shuffle Null

| Arm | Checkpoint | R19 construct | n | Observed pair acc | Null mean | p(null >= observed) |
|---|---:|---|---:|---:|---:|---:|
| A1 real | 0 | cued chart point-value reading | 300 | 0.4367 | 0.0131 | 0.0010 |
| A1 real | 0 | document header indexing (calibration) | 300 | 0.8667 | 0.0029 | 0.0010 |
| A1 real | 0 | geometry coordinate indexing | 600 | 0.4717 | 0.0133 | 0.0010 |
| A1 real | 60 | cued chart point-value reading | 300 | 0.5100 | 0.0150 | 0.0010 |
| A1 real | 60 | document header indexing (calibration) | 300 | 0.8867 | 0.0029 | 0.0010 |
| A1 real | 60 | geometry coordinate indexing | 600 | 0.4733 | 0.0124 | 0.0010 |
| A1 real | 100 | cued chart point-value reading | 300 | 0.5233 | 0.0152 | 0.0010 |
| A1 real | 100 | document header indexing (calibration) | 300 | 0.8967 | 0.0030 | 0.0010 |
| A1 real | 100 | geometry coordinate indexing | 600 | 0.4700 | 0.0122 | 0.0010 |
| A2 gray | 0 | cued chart point-value reading | 300 | 0.4367 | 0.0131 | 0.0010 |
| A2 gray | 0 | document header indexing (calibration) | 300 | 0.8667 | 0.0029 | 0.0010 |
| A2 gray | 0 | geometry coordinate indexing | 600 | 0.4717 | 0.0133 | 0.0010 |
| A2 gray | 60 | cued chart point-value reading | 300 | 0.4800 | 0.0144 | 0.0010 |
| A2 gray | 60 | document header indexing (calibration) | 300 | 0.8833 | 0.0029 | 0.0010 |
| A2 gray | 60 | geometry coordinate indexing | 600 | 0.4433 | 0.0117 | 0.0010 |
| A2 gray | 100 | cued chart point-value reading | 300 | 0.5000 | 0.0151 | 0.0010 |
| A2 gray | 100 | document header indexing (calibration) | 300 | 0.8933 | 0.0030 | 0.0010 |
| A2 gray | 100 | geometry coordinate indexing | 600 | 0.4267 | 0.0115 | 0.0010 |
| A2b no-image | 0 | cued chart point-value reading | 300 | 0.4367 | 0.0131 | 0.0010 |
| A2b no-image | 0 | document header indexing (calibration) | 300 | 0.8667 | 0.0029 | 0.0010 |
| A2b no-image | 0 | geometry coordinate indexing | 600 | 0.4717 | 0.0133 | 0.0010 |
| A2b no-image | 60 | cued chart point-value reading | 300 | 0.4433 | 0.0134 | 0.0010 |
| A2b no-image | 60 | document header indexing (calibration) | 300 | 0.8833 | 0.0029 | 0.0010 |
| A2b no-image | 60 | geometry coordinate indexing | 600 | 0.4533 | 0.0120 | 0.0010 |
| A2b no-image | 100 | cued chart point-value reading | 300 | 0.4433 | 0.0138 | 0.0010 |
| A2b no-image | 100 | document header indexing (calibration) | 300 | 0.8900 | 0.0030 | 0.0010 |
| A2b no-image | 100 | geometry coordinate indexing | 600 | 0.4483 | 0.0119 | 0.0010 |
| A3 caption | 0 | cued chart point-value reading | 300 | 0.4367 | 0.0131 | 0.0010 |
| A3 caption | 0 | document header indexing (calibration) | 300 | 0.8667 | 0.0029 | 0.0010 |
| A3 caption | 0 | geometry coordinate indexing | 600 | 0.4717 | 0.0133 | 0.0010 |
| A3 caption | 60 | cued chart point-value reading | 300 | 0.4700 | 0.0141 | 0.0010 |
| A3 caption | 60 | document header indexing (calibration) | 300 | 0.8833 | 0.0029 | 0.0010 |
| A3 caption | 60 | geometry coordinate indexing | 600 | 0.4567 | 0.0122 | 0.0010 |
| A3 caption | 100 | cued chart point-value reading | 300 | 0.4900 | 0.0145 | 0.0010 |
| A3 caption | 100 | document header indexing (calibration) | 300 | 0.8900 | 0.0030 | 0.0010 |
| A3 caption | 100 | geometry coordinate indexing | 600 | 0.4633 | 0.0121 | 0.0010 |

The legacy chart category identifier is retained only in the machine artifact for compatibility. Human-facing text uses **cued chart point-value reading**.

## Cued Chart Point-Value Reading

Prediction frequency is computed over the 600 pair members. Predictions outside the frozen answer support are grouped as `other/invalid`. Accuracy is member accuracy conditioned on the ground-truth answer value.

### A1 real

| Predicted value | Step 0 share | Step 60 share (change) | Step 100 share (change) |
|---|---:|---:|---:|
| 10 | 0.0133 | 0.0317 (+0.0183) | 0.0350 (+0.0217) |
| 20 | 0.0883 | 0.1100 (+0.0217) | 0.1117 (+0.0233) |
| 30 | 0.0800 | 0.0850 (+0.0050) | 0.0833 (+0.0033) |
| 40 | 0.1017 | 0.1033 (+0.0017) | 0.1050 (+0.0033) |
| 50 | 0.0867 | 0.1083 (+0.0217) | 0.1050 (+0.0183) |
| 60 | 0.1417 | 0.1250 (-0.0167) | 0.1267 (-0.0150) |
| 70 | 0.0383 | 0.0433 (+0.0050) | 0.0433 (+0.0050) |
| 80 | 0.2117 | 0.1950 (-0.0167) | 0.1983 (-0.0133) |
| 90 | 0.0667 | 0.0900 (+0.0233) | 0.0950 (+0.0283) |
| other/invalid | 0.1717 | 0.1083 (-0.0633) | 0.0967 (-0.0750) |

| Ground-truth value | n | Step 0 acc | Step 60 acc (change) | Step 100 acc (change) |
|---|---:|---:|---:|---:|
| 10 | 58 | 0.9310 | 0.5517 (-0.3793) | 0.5862 (-0.3448) |
| 20 | 76 | 0.6316 | 0.8026 (+0.1711) | 0.8158 (+0.1842) |
| 30 | 66 | 0.6818 | 0.7424 (+0.0606) | 0.7424 (+0.0606) |
| 40 | 61 | 0.6557 | 0.7377 (+0.0820) | 0.7705 (+0.1148) |
| 50 | 64 | 0.5781 | 0.6875 (+0.1094) | 0.6875 (+0.1094) |
| 60 | 63 | 0.8095 | 0.7937 (-0.0159) | 0.8095 (+0.0000) |
| 70 | 70 | 0.3143 | 0.3571 (+0.0429) | 0.3714 (+0.0571) |
| 80 | 66 | 0.9242 | 0.9394 (+0.0152) | 0.9545 (+0.0303) |
| 90 | 76 | 0.5132 | 0.6974 (+0.1842) | 0.7237 (+0.2105) |

### A2 gray

| Predicted value | Step 0 share | Step 60 share (change) | Step 100 share (change) |
|---|---:|---:|---:|
| 10 | 0.0133 | 0.0317 (+0.0183) | 0.0317 (+0.0183) |
| 20 | 0.0883 | 0.1083 (+0.0200) | 0.1117 (+0.0233) |
| 30 | 0.0800 | 0.0850 (+0.0050) | 0.0850 (+0.0050) |
| 40 | 0.1017 | 0.1067 (+0.0050) | 0.1083 (+0.0067) |
| 50 | 0.0867 | 0.1067 (+0.0200) | 0.1083 (+0.0217) |
| 60 | 0.1417 | 0.1267 (-0.0150) | 0.1267 (-0.0150) |
| 70 | 0.0383 | 0.0400 (+0.0017) | 0.0417 (+0.0033) |
| 80 | 0.2117 | 0.2033 (-0.0083) | 0.2017 (-0.0100) |
| 90 | 0.0667 | 0.0783 (+0.0117) | 0.0883 (+0.0217) |
| other/invalid | 0.1717 | 0.1133 (-0.0583) | 0.0967 (-0.0750) |

| Ground-truth value | n | Step 0 acc | Step 60 acc (change) | Step 100 acc (change) |
|---|---:|---:|---:|---:|
| 10 | 58 | 0.9310 | 0.5517 (-0.3793) | 0.5345 (-0.3966) |
| 20 | 76 | 0.6316 | 0.7895 (+0.1579) | 0.8158 (+0.1842) |
| 30 | 66 | 0.6818 | 0.7424 (+0.0606) | 0.7424 (+0.0606) |
| 40 | 61 | 0.6557 | 0.7541 (+0.0984) | 0.7541 (+0.0984) |
| 50 | 64 | 0.5781 | 0.6562 (+0.0781) | 0.6406 (+0.0625) |
| 60 | 63 | 0.8095 | 0.7937 (-0.0159) | 0.8095 (+0.0000) |
| 70 | 70 | 0.3143 | 0.3143 (+0.0000) | 0.3429 (+0.0286) |
| 80 | 66 | 0.9242 | 0.9242 (+0.0000) | 0.9545 (+0.0303) |
| 90 | 76 | 0.5132 | 0.6053 (+0.0921) | 0.6842 (+0.1711) |

### A2b no-image

| Predicted value | Step 0 share | Step 60 share (change) | Step 100 share (change) |
|---|---:|---:|---:|
| 10 | 0.0133 | 0.0317 (+0.0183) | 0.0300 (+0.0167) |
| 20 | 0.0883 | 0.1050 (+0.0167) | 0.1067 (+0.0183) |
| 30 | 0.0800 | 0.0800 (+0.0000) | 0.0783 (-0.0017) |
| 40 | 0.1017 | 0.1083 (+0.0067) | 0.1083 (+0.0067) |
| 50 | 0.0867 | 0.1050 (+0.0183) | 0.1117 (+0.0250) |
| 60 | 0.1417 | 0.1300 (-0.0117) | 0.1350 (-0.0067) |
| 70 | 0.0383 | 0.0383 (+0.0000) | 0.0333 (-0.0050) |
| 80 | 0.2117 | 0.1950 (-0.0167) | 0.2100 (-0.0017) |
| 90 | 0.0667 | 0.0750 (+0.0083) | 0.0733 (+0.0067) |
| other/invalid | 0.1717 | 0.1317 (-0.0400) | 0.1133 (-0.0583) |

| Ground-truth value | n | Step 0 acc | Step 60 acc (change) | Step 100 acc (change) |
|---|---:|---:|---:|---:|
| 10 | 58 | 0.9310 | 0.5345 (-0.3966) | 0.4828 (-0.4483) |
| 20 | 76 | 0.6316 | 0.7632 (+0.1316) | 0.7763 (+0.1447) |
| 30 | 66 | 0.6818 | 0.6970 (+0.0152) | 0.6818 (+0.0000) |
| 40 | 61 | 0.6557 | 0.7049 (+0.0492) | 0.7213 (+0.0656) |
| 50 | 64 | 0.5781 | 0.6250 (+0.0469) | 0.6250 (+0.0469) |
| 60 | 63 | 0.8095 | 0.7937 (-0.0159) | 0.8095 (+0.0000) |
| 70 | 70 | 0.3143 | 0.3000 (-0.0143) | 0.2714 (-0.0429) |
| 80 | 66 | 0.9242 | 0.8939 (-0.0303) | 0.9394 (+0.0152) |
| 90 | 76 | 0.5132 | 0.5789 (+0.0658) | 0.5789 (+0.0658) |

### A3 caption

| Predicted value | Step 0 share | Step 60 share (change) | Step 100 share (change) |
|---|---:|---:|---:|
| 10 | 0.0133 | 0.0300 (+0.0167) | 0.0300 (+0.0167) |
| 20 | 0.0883 | 0.1050 (+0.0167) | 0.1050 (+0.0167) |
| 30 | 0.0800 | 0.0817 (+0.0017) | 0.0867 (+0.0067) |
| 40 | 0.1017 | 0.1017 (+0.0000) | 0.1050 (+0.0033) |
| 50 | 0.0867 | 0.1133 (+0.0267) | 0.1067 (+0.0200) |
| 60 | 0.1417 | 0.1267 (-0.0150) | 0.1217 (-0.0200) |
| 70 | 0.0383 | 0.0417 (+0.0033) | 0.0450 (+0.0067) |
| 80 | 0.2117 | 0.2050 (-0.0067) | 0.2050 (-0.0067) |
| 90 | 0.0667 | 0.0833 (+0.0167) | 0.0900 (+0.0233) |
| other/invalid | 0.1717 | 0.1117 (-0.0600) | 0.1050 (-0.0667) |

| Ground-truth value | n | Step 0 acc | Step 60 acc (change) | Step 100 acc (change) |
|---|---:|---:|---:|---:|
| 10 | 58 | 0.9310 | 0.5345 (-0.3966) | 0.5172 (-0.4138) |
| 20 | 76 | 0.6316 | 0.7632 (+0.1316) | 0.7632 (+0.1316) |
| 30 | 66 | 0.6818 | 0.7121 (+0.0303) | 0.7424 (+0.0606) |
| 40 | 61 | 0.6557 | 0.7049 (+0.0492) | 0.7377 (+0.0820) |
| 50 | 64 | 0.5781 | 0.6562 (+0.0781) | 0.6562 (+0.0781) |
| 60 | 63 | 0.8095 | 0.8095 (+0.0000) | 0.7937 (-0.0159) |
| 70 | 70 | 0.3143 | 0.3286 (+0.0143) | 0.3571 (+0.0429) |
| 80 | 66 | 0.9242 | 0.9242 (+0.0000) | 0.9394 (+0.0152) |
| 90 | 76 | 0.5132 | 0.6447 (+0.1316) | 0.6974 (+0.1842) |

Problems:
- These diagnostics test compatibility with marginal answer-key regularities; they do not identify a perceptual mechanism.
- Seed-1 chart deltas remain non-final until seeds 2-3 land.

Decision:
- None. Chart outputs are now eligible for PI interpretation and paper-figure gating, subject to the registered caveats.

Next actions:
- Carry this null alongside every seed-1 chart category table.
- Recompute the same frozen analysis for the multi-seed summary without changing permutation settings.
