# Main Objective Audit V1

Status:
- Machine audit status: `pass`.
- Machine status JSON: `reports/main_objective_audit_v3.json`.
- This audit checks registry and dependency integrity; scientific task gates remain PI decisions.

Checks:
| Check | Result |
| --- | --- |
| `registry_defines_exact_M0_through_M14` | `true` |
| `progress_has_exactly_one_valid_line_per_registry_task` | `true` |
| `every_pass_has_all_nonempty_named_reports` | `true` |
| `M2_or_M3_pass_requires_preregistration` | `true` |
| `M5_M6_M7_or_M9_pass_requires_registered_extensions` | `true` |
| `audited_files_are_not_byte_identical_to_counterparts` | `true` |

Evidence:
- Registry task IDs: `['M0', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9', 'M10', 'M11', 'M12', 'M13', 'M14']`.
- Ledger rows: `15`.
- Tasks currently marked pass: `['M0', 'M1']`.
- Audited files examined: `6`.
- Errors: `[]`.

Decision:
- A machine `pass` proves only the enumerated repository invariants at this revision.
- The separate full `python -m pytest tests/` invocation remains required evidence.
