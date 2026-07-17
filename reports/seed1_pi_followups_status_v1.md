# Seed-1 PI Follow-Ups Status V1

Status:
- The PI-verified four-arm core readout is unchanged; no seed-1 retraining or
  reconstruction was performed.
- The registered R19 null and chart diagnostics are complete from cached
  predictions.
- The M10 64-draw rule and M7 informed-prediction amendment are merged.
- M10 execution, pilot seed 2, M5, and M11 continue under immutable manifests.
- No scientific gate decision is made here.

Evidence:
- Null machine artifact: `reports/pilot_4arm_seed1_r19_null_v1.json`, SHA256
  `5c8bb51bfca8a9175c8ad7f4efd9d8d8f80e56d3595f3f1c9f30645a7d9c4f78`.
- Null report: `reports/pilot_4arm_seed1_r19_null_v1.md`, SHA256
  `8f3b27adbd7d922747b0fc28d60db255bc8e1c444425f627a3b63deb656cb286`.
- Category companion: `reports/pilot_4arm_seed1_r19_null_category_tables_v1.md`,
  SHA256 `472f39bbac0fa43e16112eb489077a2e8db68c3e868e93b0f90d09c545e71add`.
- Null coverage: 4 arms x 3 checkpoints x 3 frozen templates = 36 cells;
  1,000 within-template key shuffles per unique cell, seed 0, canonical-v2
  scorer and the frozen answer-tag contract.
- Human-facing chart label is `cued chart point-value reading`; the legacy
  identifier appears only in machine compatibility fields.
- Chart diagnostics report prediction frequency and answer-conditioned
  accuracy at steps 0/60/100, plus every change from step 0.
- M10 registration: `reports/support_sharpening_registry_v3.md`.
- M10 active A1/A2-gray, completed A3, and remaining-arm queue:
  `reports/support_sharpening_execution_status_v1.md` and
  `experiments/runs/m10_support_seed1_remaining_queue_login_20260717T074237Z`.
- M7 amendment: `docs/registered_m7_amendment_v1.md`.
- M11 replacement/reconciliation: `reports/m11_reconciliation_v2.md`.

Problems:
- The null tests compatibility with marginal answer-key regularities; rejecting
  it does not identify a perceptual mechanism.
- M10 A2-gray is active and A2b is queued; the four-arm readout is not complete.
  M7 readiness inputs remain incomplete, and no M7 optimizer step is authorized
  yet.
- M11 has six structurally running cells; the 18-cell metric table remains
  unopened.

Decision:
- Chart deltas may enter a paper figure only through a hash-pinned spec that
  includes the completed null artifact.
- Preserve both requested seed-1 values as
  `registered seed-1 result; confirmation pending seeds 2–3`.
- Continue the standing M3/M5/M11/M10 schedule without opening seed-2 values.
