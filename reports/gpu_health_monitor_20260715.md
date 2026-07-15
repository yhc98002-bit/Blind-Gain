# GPU Health Monitor 2026-07-15

Status:
- One-hour read-only monitor: `complete`.
- A2-gray retry2 showed forward progress and no fatal-error, host-memory, swap,
  or process-survival failure during the window.
- No scientific gate decision is made from this operational monitor.

Evidence:
- Run: `experiments/runs/gpu_health_16x60m_login_20260715T170319Z`.
- Window: `2026-07-15T17:03:31Z` to `2026-07-15T18:03:33Z`.
- Sampling: 121 samples, 30-second interval, 16 GPUs across `an12` and `an29`.
- Samples SHA256:
  `ae3af297cb76209880b0f56f0ff34a3965814b4293d1f0700a06ae67beec5cf5`.
- Summary SHA256:
  `f1f05192bb02676920222bcb3faf1629ed1eee9f9211c23fbf307722a4b25ae5`.

A2-gray observations:
| GPU | Mean utilization | Max memory MiB | Max temperature C |
| --- | ---: | ---: | ---: |
| `an12:0` | 71.3% | 62,300 | 48 |
| `an12:1` | 71.9% | 62,308 | 48 |
| `an12:2` | 71.6% | 63,492 | 51 |
| `an12:3` | 70.1% | 63,460 | 49 |

Health accounting:
- Wrapper remained alive, stdout advanced, and the observed maximum logged step
  advanced from the resumed baseline to step 61.
- Health classifications: 109 `healthy`, 11 transient `warning`, and one initial
  `observing` sample.
- Every warning was a short interval with utilization below 5% and no new log
  progress during a normal phase transition; later samples recovered without
  intervention.
- No fatal log pattern was observed.
- Minimum `an12` available host memory: 657.9 GiB; maximum swap use: 0.
- Minimum `an29` available host memory: 728.8 GiB; maximum swap use: 0.

Decision:
- Continue A2 retry2 unchanged on `an12:0-3`.
- Do not classify phase-local GPU idleness as a failure when wrapper, logs, and
  subsequent step progress remain healthy.

Next actions:
- Keep the existing completion and checkpoint-retention watchdogs active.
- Run a shorter follow-up monitor around the step-80 save/merge transition.
