# Registered Extensions Audit V3

Status:
- M4 repository-deliverable status: `pass`.
- Scope: extension transcription, audited M1 dependency resolution, explicit
  computed-field placeholders, and a fail-closed downstream handoff.
- Scientific launch authorization is not asserted by this status.
- Machine status JSON: `reports/registered_extensions_audit_v3.json`.

Evidence:
- PI source: `docs/MAIN_PHASE_BRIEF.md`, SHA256
  `2a426299dfef487b67d708982222bf4a110225840c876f97ad27a1ae235c109f`.
- Transcription: `docs/registered_extensions_v1.md`, SHA256
  `5d9e629add21468ff114bcd57aa04d1f19d8b01568bb9ec93cef19596f27f07d`.
- Audited M1 ruling: `reports/virl_fork_ruling.md`, SHA256
  `28c7cac92a276385dbeda5d1b7c499e12d822f652260456347cefd65dba584a1`.
- V2 remains immutable historical evidence of the two unresolved authorization
  inputs.

Completion checks:
| Repository requirement | Result |
| --- | --- |
| PI extension designs transcribed | pass |
| M1 heterogeneity fork resolved from audited evidence | pass |
| M3/M7/M8-dependent fields explicit | pass |
| missing flat/rising rule disclosed | pass |
| absent canonical authorization marker disclosed | pass |
| M5-M7/M9 launchers remain fail-closed | pass |
| V2 audit retained | pass |

Problems:
- The PI source does not operationalize the long-horizon flat/rising verdict.
- The exact line `- Registration state: merged-at-HEAD; merge is sign-off.` is
  absent from the transcription.

Decision:
- M4 is complete as a repository transcription and dependency-accounting task.
- This does not authorize M5, M6, M7, or M9. Those tasks remain `blocked` until
  the missing PI rule lands and Richard merges the exact authorization marker.
- No training launcher or scientific gate is weakened by this bookkeeping
  status distinction.

Next actions:
- Fill computed fields only from frozen M3/M7/M8 artifacts.
- Obtain the PI-defined rule and merge marker before any affected optimizer
  step.
