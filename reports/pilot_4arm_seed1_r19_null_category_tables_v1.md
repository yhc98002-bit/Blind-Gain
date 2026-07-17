# Seed-1 R19 Category Tables with Registered Null V1

Status:
- This companion places the registered within-template key-shuffle null beside every existing seed-1 R19 category/checkpoint row.
- It uses cached predictions only and makes no scientific interpretation or gate decision.
- Null rejection alone does not establish perceptual learning.

Evidence:
- Null and chart diagnostics: `reports/pilot_4arm_seed1_r19_null_v1.json`.
- PI-verified core readout: `reports/pilot_4arm_seed1_results_v1.json`.
- Human-facing chart label: `cued chart point-value reading`.

| Arm | Checkpoint | R19 construct | n | Step-0 pair acc | Observed pair acc | Delta (95% CI) | Null mean | p(null >= observed) |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A1 real | 0 | cued chart point-value reading | 300 | 0.4367 | 0.4367 | 0.0000 [reference checkpoint] | 0.0131 | 0.0010 |
| A1 real | 0 | document header indexing (calibration) | 300 | 0.8667 | 0.8667 | 0.0000 [reference checkpoint] | 0.0029 | 0.0010 |
| A1 real | 0 | geometry coordinate indexing | 600 | 0.4717 | 0.4717 | 0.0000 [reference checkpoint] | 0.0133 | 0.0010 |
| A1 real | 60 | cued chart point-value reading | 300 | 0.4367 | 0.5100 | 0.0733 [0.0267, 0.1200] | 0.0150 | 0.0010 |
| A1 real | 60 | document header indexing (calibration) | 300 | 0.8667 | 0.8867 | 0.0200 [-0.0033, 0.0433] | 0.0029 | 0.0010 |
| A1 real | 60 | geometry coordinate indexing | 600 | 0.4717 | 0.4733 | 0.0017 [-0.0233, 0.0267] | 0.0124 | 0.0010 |
| A1 real | 100 | cued chart point-value reading | 300 | 0.4367 | 0.5233 | 0.0867 [0.0367, 0.1367] | 0.0152 | 0.0010 |
| A1 real | 100 | document header indexing (calibration) | 300 | 0.8667 | 0.8967 | 0.0300 [0.0067, 0.0567] | 0.0030 | 0.0010 |
| A1 real | 100 | geometry coordinate indexing | 600 | 0.4717 | 0.4700 | -0.0017 [-0.0283, 0.0250] | 0.0122 | 0.0010 |
| A2 gray | 0 | cued chart point-value reading | 300 | 0.4367 | 0.4367 | 0.0000 [reference checkpoint] | 0.0131 | 0.0010 |
| A2 gray | 0 | document header indexing (calibration) | 300 | 0.8667 | 0.8667 | 0.0000 [reference checkpoint] | 0.0029 | 0.0010 |
| A2 gray | 0 | geometry coordinate indexing | 600 | 0.4717 | 0.4717 | 0.0000 [reference checkpoint] | 0.0133 | 0.0010 |
| A2 gray | 60 | cued chart point-value reading | 300 | 0.4367 | 0.4800 | 0.0433 [0.0033, 0.0867] | 0.0144 | 0.0010 |
| A2 gray | 60 | document header indexing (calibration) | 300 | 0.8667 | 0.8833 | 0.0167 [-0.0067, 0.0433] | 0.0029 | 0.0010 |
| A2 gray | 60 | geometry coordinate indexing | 600 | 0.4717 | 0.4433 | -0.0283 [-0.0533, -0.0017] | 0.0117 | 0.0010 |
| A2 gray | 100 | cued chart point-value reading | 300 | 0.4367 | 0.5000 | 0.0633 [0.0167, 0.1133] | 0.0151 | 0.0010 |
| A2 gray | 100 | document header indexing (calibration) | 300 | 0.8667 | 0.8933 | 0.0267 [0.0033, 0.0501] | 0.0030 | 0.0010 |
| A2 gray | 100 | geometry coordinate indexing | 600 | 0.4717 | 0.4267 | -0.0450 [-0.0733, -0.0183] | 0.0115 | 0.0010 |
| A2b no-image | 0 | cued chart point-value reading | 300 | 0.4367 | 0.4367 | 0.0000 [reference checkpoint] | 0.0131 | 0.0010 |
| A2b no-image | 0 | document header indexing (calibration) | 300 | 0.8667 | 0.8667 | 0.0000 [reference checkpoint] | 0.0029 | 0.0010 |
| A2b no-image | 0 | geometry coordinate indexing | 600 | 0.4717 | 0.4717 | 0.0000 [reference checkpoint] | 0.0133 | 0.0010 |
| A2b no-image | 60 | cued chart point-value reading | 300 | 0.4367 | 0.4433 | 0.0067 [-0.0367, 0.0500] | 0.0134 | 0.0010 |
| A2b no-image | 60 | document header indexing (calibration) | 300 | 0.8667 | 0.8833 | 0.0167 [-0.0067, 0.0400] | 0.0029 | 0.0010 |
| A2b no-image | 60 | geometry coordinate indexing | 600 | 0.4717 | 0.4533 | -0.0183 [-0.0433, 0.0067] | 0.0120 | 0.0010 |
| A2b no-image | 100 | cued chart point-value reading | 300 | 0.4367 | 0.4433 | 0.0067 [-0.0367, 0.0500] | 0.0138 | 0.0010 |
| A2b no-image | 100 | document header indexing (calibration) | 300 | 0.8667 | 0.8900 | 0.0233 [0.0000, 0.0500] | 0.0030 | 0.0010 |
| A2b no-image | 100 | geometry coordinate indexing | 600 | 0.4717 | 0.4483 | -0.0233 [-0.0483, 0.0017] | 0.0119 | 0.0010 |
| A3 caption | 0 | cued chart point-value reading | 300 | 0.4367 | 0.4367 | 0.0000 [reference checkpoint] | 0.0131 | 0.0010 |
| A3 caption | 0 | document header indexing (calibration) | 300 | 0.8667 | 0.8667 | 0.0000 [reference checkpoint] | 0.0029 | 0.0010 |
| A3 caption | 0 | geometry coordinate indexing | 600 | 0.4717 | 0.4717 | 0.0000 [reference checkpoint] | 0.0133 | 0.0010 |
| A3 caption | 60 | cued chart point-value reading | 300 | 0.4367 | 0.4700 | 0.0333 [-0.0133, 0.0800] | 0.0141 | 0.0010 |
| A3 caption | 60 | document header indexing (calibration) | 300 | 0.8667 | 0.8833 | 0.0167 [-0.0067, 0.0433] | 0.0029 | 0.0010 |
| A3 caption | 60 | geometry coordinate indexing | 600 | 0.4717 | 0.4567 | -0.0150 [-0.0400, 0.0100] | 0.0122 | 0.0010 |
| A3 caption | 100 | cued chart point-value reading | 300 | 0.4367 | 0.4900 | 0.0533 [0.0067, 0.1000] | 0.0145 | 0.0010 |
| A3 caption | 100 | document header indexing (calibration) | 300 | 0.8667 | 0.8900 | 0.0233 [0.0000, 0.0467] | 0.0030 | 0.0010 |
| A3 caption | 100 | geometry coordinate indexing | 600 | 0.4717 | 0.4633 | -0.0083 [-0.0350, 0.0167] | 0.0121 | 0.0010 |

Decision:
- None. The registered chart diagnostics remain in the companion null report and must accompany any later chart delta.
