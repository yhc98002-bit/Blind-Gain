# Seed-1 Visual-Evidence Ranking Smoke V1

Status:
- Complete after the prospective registration commit; this is a two-pair engineering
  smoke and contains no scientific readout.
- No candidate score, margin, accuracy, or ranking value was opened for reporting.

Evidence:
- Run: `experiments/runs/d1_visual_evidence_smoke_base_real_an12_gpu4_20260717T173022Z`.
- Registration/launch commit: `642e03367f4916a5e3fca160be6083006fceab1c`.
- Placement: an12 GPU 4, TP1, one replica; base model, real-image condition.
- Lifecycle: exit code 0; two exact output rows; required fields present; every
  candidate score finite; every completion token count positive.
- Log scan: no traceback, OOM, NaN, infinity, or CUDA failure signature.

Problems:
- The smoke does not estimate throughput precisely and cannot support a scientific
  interpretation.

Decision:
- The token-prefix, exact-completion, model-loading, output, and manifest paths are
  mechanically viable for the full nine-cell matrix.

Next actions:
- Launch the frozen base/step-60/step-100 by real/no-image/gray matrix on disjoint
  free GPUs; the lifecycle queue does not read performance values.
