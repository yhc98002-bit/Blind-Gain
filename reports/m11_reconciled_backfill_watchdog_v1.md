# M11 Reconciled Backfill Watchdog V1

Status:
- Active. A login-only watchdog reconciles the exact ten existing M11 cells and backfills the remaining eight Gemma-3 cells as `an29` GPUs 0/1/3/4 become stably free.
- M11 remains blocked until all 18 cells and the final audited report are complete.

Evidence:
- Config: `configs/eval/m11_generalization_reconciled_backfill_v1.json`, SHA256 `21687cdf5de6b36ef637e223253baaca442f565193430148d26acad86ab57c65`.
- Watchdog: `experiments/runs/m11_reconciled_backfill_login_20260716T172041Z`, source commit `f382f3e52d05a04df9d3c2fbded87ff711c79306`.
- Initial reconciliation: 10 exact immutable runs, comprising all nine InternVL cells and the active Gemma-3 R19-real cell; eight Gemma cells remain pending.
- Initial structural state: 4 complete, 6 running, 8 pending. Only status, identity, registered artifact existence, and GPU placement are read; `performance_values_opened=false`.
- The queue reserves only jobs on its target node. An adversarial fixture proves that an12 GPU 4 does not reserve an29 GPU 4.
- Capacity is restricted to an29 GPUs 0/1/3/4, leaving the seed-2 trainer's current placement on GPUs 2/5/6/7 untouched.
- All launched evaluations are independent TP1 replicas under the frozen M11 runtime and locked greedy protocol.
- Verification: 17 focused reconciliation, prior recovery, and non-Qwen tests passed before launch.

Problems:
- The final M11 report builder currently expects two model-stage manifests, while InternVL now has verified copies on both an29 and an12. Final reconciliation must preserve both placement records without weakening the existing stage checks.

Decision:
- Automate only launch/status reconciliation. The watchdog stops at `cells_complete_pending_report` and does not open scientific metrics or build the final report.
- Fail closed on any failed cell, identity drift, missing registered metrics artifact, or duplicate active watchdog.

Next actions:
- Let the watchdog backfill the eight pending Gemma cells as the remaining InternVL jobs release GPUs.
- Extend the final M11 builder to represent both verified InternVL placements, then publish `reports/generalization_audits_v1.md` only after the complete 18-cell matrix is structurally audited.
