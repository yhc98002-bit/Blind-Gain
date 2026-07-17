# M11 InternVL Multi-Image OOM Repair V1

Status:
- Engineering root cause identified and a bounded preprocessing repair is
  implemented with adversarial fixtures.
- The failed run and its 2,219-row partial output are preserved unchanged.
- A fresh full 4,096-row real-image cell is required; the partial output will
  not be resumed because its preprocessing policy differs.
- No M11 performance value was opened.

Evidence:
- Failed run:
  `experiments/runs/m11_virl4096_retry1_internvl3_real_s0of1_an12_20260716T170736Z`.
- Run-manifest SHA256:
  `b880d85fe9ed49ddf023c45b29574c89cd081ba222c67439b62bae350cb5092d`.
- Preserved partial: 2,219 rows, SHA256
  `3f3b866442207b2ef5dfeb44cb2e184140dedca2a8a8b0b01d901fb3d2052f03`.
- Failure item: frozen row index 2,219, five source images.
- Failure: CUDA OOM during the first forward pass after the adapter assigned
  up to 12 dynamic patches independently to each of five images; the runtime
  attempted an additional 24.80 GiB allocation.
- The failed run directory occupies approximately 7.5 MiB and is retained as
  failed-run evidence.

Repair:
- `max_dynamic_patches=12` is now a strict total request budget rather than a
  per-image allowance.
- The budget is balanced deterministically across images. Five images receive
  `[3, 3, 2, 2, 2]`; every image receives at least one patch.
- A thumbnail remains inside, rather than in addition to, each image's assigned
  budget.
- Runtime rows stamp
  `dynamic_patch_allocation=balanced_across_images` and
  `max_total_dynamic_patches=12`.
- Legacy completed single-image M11 rows remain valid. The repaired multi-image
  run starts from row 0 and cannot combine old and new preprocessing policies.

Tests:
- `tests/test_nonqwen_adapters.py` proves the five-image allocation sums to 12,
  no image receives the old per-image allowance, and thumbnail insertion stays
  inside a three-patch budget.
- Existing runtime, resume, and scorer fixtures remain applicable.

Problems:
- The original reconciled queue failed closed when this cell failed. A new
  immutable reconciliation queue must point to the repaired cell and the
  surviving completed/running cells; the failed queue is never rewritten.

Decision:
- Relaunch only `blind_internvl3_virl4096_real` from row 0 on a free TP1 GPU.
- Keep all other active M11 cells untouched.
- Publish the 18-cell readout only through the existing fail-closed finalizer
  after a new exact reconciliation state is complete.
