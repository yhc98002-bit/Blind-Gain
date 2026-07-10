# Gate 2 Machine-Check Definition

Status:
- `scripts/compute_gate2.py` maps the proposal checklist to concrete ledger entries and artifact paths.
- It emits `machine_ready_for_pi_audit`, not a PI gate decision. `pi_gate_decision` remains `not_evaluated`.

Checks:
| Machine check | Required evidence |
| --- | --- |
| Measurement repair | P0.1-P0.5 all `pass` in `reports/gate2_progress.md` |
| Anchor | P1.1 `pass` plus `reports/anchor_recipe_report.md` |
| Layer-1 base table | P1.2 `pass` plus `reports/base_external_benchmarks.md` |
| V0.2 packaging | P1.4 `pass` plus truthy `reports/fliptrack_v02r19_lint.json.status` |
| V0.2 artifact gate | P1.5 `pass` plus truthy `reports/artifact_gate_v02_r19.json.gate.status` |
| V0.2 templates | P1.6 `pass` plus at least three R19 contact sheets |
| Positive controls | P1.7 `pass` plus `reports/positive_controls_v02.md` |
| Exact caption stores | P1.8 `pass` plus complete 3B/7B caption cells in `reports/fliptrack_v02r19_exact_package.json` |
| Mechanical pilot | P2.1 `pass` plus `reports/mech_pilot_3arm_geo3k.md` |
| Blind solvability | P2.2 `pass` plus integrity-audited `reports/blind_solvability_geo3k_v3_audited.md` |
| Data/licenses | P1.9 `pass` plus `reports/license_log_v2.csv` |
| Decontamination | P1.10 `pass` plus `reports/decon_geo3k_vs_layer1.md` |
| Repo/gate logic | P1.11 `pass` plus `tests/test_gate_logic.py` |
| Idle audit | `reports/gpu_idle_audit_gate2.json.violations` is empty |

Decision:
- Machine readiness is the logical AND of all checks above.
- Only the PI may convert machine readiness into a Gate 2 scientific decision.
