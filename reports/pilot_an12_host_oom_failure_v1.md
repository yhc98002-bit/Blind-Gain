# an12 Pilot Host-Memory Failure

Status:
- The original A1 and A2-gray seed-1 runs are finalized `fail`. This report records an operational failure; it does not make or pass a scientific gate decision.

Evidence:
- A1 source run: `experiments/runs/mech_a1_real_an12_20260713T031454Z`, final status `fail`, exit code `1`, end `2026-07-14T05:36:20Z`.
- A2 source run: `experiments/runs/mech_a2_gray_an12_20260713T033946Z`, final status `fail`, exit code `1`, end `2026-07-14T05:36:20Z`.
- Both logs report `ray.exceptions.OutOfMemoryError: Task was killed due to the node running low on memory` at the same host state: `957.25GB / 1007.52GB (0.950107)`, above Ray's `0.95` threshold.
- The killed A1 worker reported `106.37GB`; the killed A2 worker reported `107.02GB`. This was host RAM pressure, not CUDA memory pressure or a shared-storage refusal.
- Each source has a complete durable `global_step_60` checkpoint. Uncheckpointed A1 steps 61-67 and A2 steps 61-66 are excluded from the recovered trajectories.

Problems:
- Running two synchronous pilot arms concurrently on one node synchronized their high host-RAM phases and crossed Ray's kill threshold.
- The earlier GPU-only health view did not make this host-memory hazard prominent.

Decision:
- Recover from step 60 under a one-pilot-trainer-per-node rule.
- Require at least 650 GiB `MemAvailable`, four target GPUs below 1,024 MiB, and at least 40 GiB free in `/dev/shm` immediately before launch.
- Do not alter registered optimizer, rollout, reward, data, seed, or checkpoint-budget settings. The only allowed config changes are the immutable experiment/checkpoint namespace and explicit load path.

Next actions:
- Run A1 alone on an12.
- Keep A2 queued until A1 releases an12 or both current an29 arms release an29.
- Monitor all 16 GPUs, host memory, process survival, logs, and step progress for one hour.
