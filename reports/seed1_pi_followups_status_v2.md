# Seed-1 PI Follow-Ups Status V2

Status:
- The PI-verified four-arm core readout remains unchanged; no retraining or
  reconstruction was performed.
- The cached R19 null, chart diagnostics, and the registered M10 64-draw
  follow-up are complete.
- The M7 informed-prediction amendment remains merged before any optimizer step.
- Pilot seed 2, M5, and M11 continue under immutable manifests with seed-two
  performance sealed.
- No scientific gate decision is made here.

Evidence:
- R19 null: `reports/pilot_4arm_seed1_r19_null_v1.json`, SHA256
  `5c8bb51bfca8a9175c8ad7f4efd9d8d8f80e56d3595f3f1c9f30645a7d9c4f78`.
- Null audit: `reports/pilot_4arm_seed1_r19_null_v1_audit.json`, status `pass`.
- M10 readout: `reports/support_sharpening_seed1_v2.{md,json}`.
- M10 total: 80 candidates and 5,120 new registered draws.
- High-confidence support-expansion candidate counts: A1 16/47, A2-gray 1/8,
  A2b-no-image 5/7, and A3-caption 2/18.
- Every 0/80 item has Jeffreys 95% posterior interval
  `[0.00000612, 0.03081626]`.
- M7 amendment: `docs/registered_m7_amendment_v1.md`.

Problems:
- Null rejection does not identify a perceptual mechanism.
- M10 item-level sampling uncertainty does not measure run-to-run RL variance.
- M7 readiness inputs and all three continuing GPU programs remain separate
  incomplete tasks.

Decision:
- Preserve `high-confidence support-expansion candidate` and
  `observed in support-sharpening samples` exactly as registered.
- Continue M3/M5/M11 without opening seed-two values; schedule M6 only after its
  frozen readiness dependencies release a full node.
