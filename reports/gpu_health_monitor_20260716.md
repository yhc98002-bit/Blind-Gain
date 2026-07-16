# GPU Health Monitor 2026-07-16

Status:
- Two one-hour, read-only monitors completed with exit code 0 and all expected
  artifacts present.
- M5 restore/continuation and seed-2 A1 both showed structural forward progress.
- This is an operations report. It opens no scientific performance values and
  makes no scientific gate decision.

Evidence:

| Window | Run | Samples | Tracked structural progress | Raw-sample SHA256 |
| --- | --- | ---: | --- | --- |
| 16:55:36-17:55:25 UTC | `experiments/runs/gpu_health_16x60m_login_20260716T165512Z` | 115 | integrity child 100→101; seed-2 A1 startup→2 | `95c22e7e516162c5e8cc89d3ce8a132ef7c6385cacda4e9eae2834523ec29e9e` |
| 17:35:08-18:34:51 UTC | `experiments/runs/gpu_health_16x60m_login_20260716T173441Z` | 115 | M5 continuation startup→102; seed-2 A1 1→3 | `1c8cf780528428d4fcaf2dd49d8cb189221318449ad4e98993e1c7daa7af8dfd` |

Artifact hashes:
- First summary JSON:
  `77ab79859c718aafda9eb3c99ccb58a9a41a97e292907c9a52e4c1ae67b3d156`.
- First summary Markdown:
  `3d481b33a15a8d8f310069dc327297b3732bb562b4a4d17e2ee7744d8f2ed44e`.
- Second summary JSON:
  `88b1cfb5239b77a355560051f37c160d9f07a22f13c4d2f0be29d116f4f56bf2`.
- Second summary Markdown:
  `84cfa6e1fa9bab8577a593590f7315be80d61cfae1fe93fed3796b2bd4c4eef4`.

Tracked-run health:

| Window | Run | Health observations | Stdout advanced | Step advanced | Terminal state at window end |
| --- | --- | --- | --- | --- | --- |
| 1 | M5 integrity child, an12:0-3 | 61 healthy, 53 warning, 1 observing | yes | yes | complete |
| 1 | seed-2 A1, an29:2/5/6/7 | 113 healthy, 1 warning, 1 observing | yes | yes | running |
| 2 | M5 step-400 continuation, an12:0-3 | 113 healthy, 1 warning, 1 observing | yes | yes | running |
| 2 | seed-2 A1, an29:2/5/6/7 | 114 healthy, 1 observing | yes | yes | running |

Resource envelope:
- In the second window M5 GPUs averaged 79.3%-81.7% utilization, reached at
  most 64,292 MiB, and stayed at or below 51 C.
- Seed-2 A1 GPUs averaged 90.7%-93.5% utilization, reached at most 62,232 MiB,
  and stayed at or below 73 C.
- an12 GPU7 remained unassigned for all 115 samples. It was subsequently
  allocated to the inference-only mini-A5 step-0 diagnostic after this monitor
  ended; it was not counted as a health failure while idle.
- Minimum available host memory was 461.8 GiB on an12 and 532.5 GiB on an29
  across the two windows. Maximum swap use was zero on both nodes.

Problems:
- The first window intentionally straddled the one-step integrity child and
  fixed continuation startup. Phase transitions produced 53 warning samples;
  wrapper survival, stdout movement, later step movement, and the completed
  child manifest show these were transient observations rather than fatal
  failures.
- GPU idleness is a reported metric, not a gate.

Decision:
- Continue M5 and seed-2 A1 unchanged.
- Keep checkpoint/evaluation watchers active and continue to classify health
  from process survival, logs, steps, and fatal signatures rather than
  utilization alone.

Next actions:
- Reconcile M5 step-150 and seed-2 step-20 checkpoint lifecycles when their
  immutable watchers observe them.
- Keep M11 and the mini-A5 step-0 diagnostic on disjoint GPUs.
