# M11 Reconciliation V2

Status:
- The failed V1 queue and failed InternVL real-image cell remain immutable.
- The fresh real-image replacement is active from row 0 on an29 GPU 1.
- A V2 login-node watcher reconciles all 18 registered M11 cells without
  opening metric values.
- M11 remains in progress; no generalization readout or gate decision is made.

Evidence:
- OOM diagnosis and preprocessing repair:
  `reports/m11_internvl_multiimage_oom_repair_v1.md`.
- Replacement run:
  `experiments/runs/m11_virl4096_patchbudgetv2_internvl3_real_s0of1_an29_20260717T072527Z`.
- V2 reconciliation config:
  `configs/eval/m11_generalization_reconciled_backfill_v2.json`.
- V2 watcher:
  `experiments/runs/m11_reconciled_backfill_v2_login_20260717T075457Z`.
- Preflight reconciled exactly 18 cells with zero pending identities and
  `performance_values_opened=false`. At watcher initialization, 12 manifests
  were structurally complete and 6 were running.

Problems:
- The replacement run changes InternVL real-image preprocessing from a
  per-image patch allowance to a strict 12-patch request budget. It therefore
  cannot reuse the preserved 2,219-row partial output.

Decision:
- Run the replacement from row 0 and preserve the failed partial as evidence.
- Publish the 18-cell table only after the V2 watcher reaches structural
  completion and the fail-closed finalizer verifies every runtime placement.
