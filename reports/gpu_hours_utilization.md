# GPU-Hours Utilization Report

Status:
- Telemetry has been integrated as a utilization report only; it is not a compute gate.
- Foreign processes are treated as normal and are included because process ownership cannot be reconstructed from `nvidia-smi` samples.

Evidence:
- Inputs: `logs/gpu_util_an12.jsonl`, `logs/gpu_util_an29.jsonl`.
- Machine status JSON: `reports/gpu_hours_utilization.json`.
- Intervals longer than 15 minutes are omitted instead of imputed.
- Active GPU-hours use sampled GPU utilization >=5%; occupied GPU-hours use memory >=1,024 MiB.

| Node | Samples | Coverage | Observed GPU-h | Active GPU-h | Occupied GPU-h | Util.-equiv. GPU-h | Mean util. | Omitted gaps |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| an12 | 8,168 | 2026-07-08T04:09:41+08:00 to 2026-07-11T18:36:13+08:00 | 679.60 | 188.67 | 189.92 | 167.60 | 24.66% | 8 |
| an29 | 8,304 | 2026-07-08T04:09:41+08:00 to 2026-07-11T18:36:47+08:00 | 691.61 | 70.12 | 159.49 | 53.26 | 7.70% | 0 |

Problems:
- Utilization telemetry does not identify process owners, commands, or scientific value; it must not be used to infer project-only efficiency.
- A short high-utilization job between samples may be missed.

Decision:
- Remove per-GPU idle violations from `scripts/compute_gate2.py`; retain this descriptive accounting alongside run manifests.

Next actions:
- Continue collection and publish a new versioned report for the pilot window rather than rewriting this snapshot.
