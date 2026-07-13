# Registered Extensions Audit V2

Status:
- M4 remains `blocked`; this is a completed transcription audit, not registration sign-off.
- The M1-dependent fork field is now resolved from the audited ViRL39K ruling.
- M3-, M7-data-, and M8-dependent values remain explicit `{computed-pending}` fields.
- V1 is retained as historical evidence and superseded by this V2 audit.

Evidence:
- PI source: `docs/MAIN_PHASE_BRIEF.md`.
- Candidate: `docs/registered_extensions_v1.md`, SHA256 `5d9e629add21468ff114bcd57aa04d1f19d8b01568bb9ec93cef19596f27f07d`.
- Machine audit: `reports/registered_extensions_audit_v2.json`.
- M1 ruling: `reports/virl_fork_ruling.md`, SHA256 `28c7cac92a276385dbeda5d1b7c499e12d822f652260456347cefd65dba584a1`.

Checks:
| Requirement | Result |
| --- | --- |
| fixed step-400 long horizon | pass |
| evaluations at 150/200/300/400 | pass |
| exact no-early-stop sentence | pass |
| restore/resume integrity and disclosed fresh-run fallback | pass |
| operational flat/rising rule | **blocked** |
| CP joint reward and same-data member-reward control | pass |
| held-out-template primary contrast and matched budget | pass |
| advantage equivalence, catch stability, and step-0 reward statistics | pass |
| no silent shaped-reward switch | pass |
| ViRL four-arm, two-seed design | pass |
| audited M1 fork field resolved | pass |
| M3/M7/M8 dependent fields remain explicit | pass |
| flagship conditional-gray rule | pass |
| own-caption primary and fixed-3B sensitivity | pass |
| one-node and TP1 placement | pass |
| canonical merged-at-HEAD line present | **blocked** |

Problems:
- The PI source requires a predeclared `flat/rising` long-horizon verdict but gives no operational threshold or interval rule. Inventing one would violate M4's transcription-only constraint.
- The exact authorization line `- Registration state: merged-at-HEAD; merge is sign-off.` is absent. Merely mentioning that phrase elsewhere cannot authorize downstream training.

Decision:
- Keep M5-M7 and M9 fail-closed.
- Richard must define or supply the flat/rising rule and merge the exact candidate. The merge commit replaces the draft state line with the canonical authorization line.

Next actions:
- Fill M3/M7/M8-dependent fields only when their frozen artifacts land.
- Rerun the main consistency auditor after the registration merge.
