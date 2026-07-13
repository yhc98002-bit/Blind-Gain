# Paper 1 Pipeline Status V2

Status:
- Supersedes `reports/paper1_pipeline_status.md`.
- M13 remains continuous and incomplete.
- The figure pipeline now fails closed on pending slots, missing inputs, hash
  mismatches, unsupported plot specs, and existing output paths.

Evidence:
- Figure builder: `scripts/paper1/build_figures.py`.
- Registered pending specs: `docs/paper1/figure_specs.json`.
- Tests: pending refusal, input-hash mismatch, and successful ready grouped-bar
  rendering.

Current slots:
| Figure | State | Blocking artifact |
| --- | --- | --- |
| decomposition bars | pending | M3/M7/M9 |
| hurdle mechanism | pending | M2/M3 |
| benchmark-FlipTrack dissociation | pending | M3/M7/M9 |
| audit table | pending | final selected audit inputs |

Decision:
- A figure spec changes to `ready` only in the same commit that pins every
  input path and SHA256.
- Generated figures are immutable; the builder refuses overwrite.
