# M0 Preregistration Finalization

Status:
- Both PI approvals were received on 2026-07-12.
- The final registration path was introduced by commit
  `2782815cc057d85a302af8bac232cac2b0e1ec75`.
- The provenance follow-up records that commit in the final document and adds
  the launcher's exact `merged-at-HEAD` marker.
- No pilot optimizer step ran before either registration commit.

Evidence:
- Final document: `reports/preregistration_pilot_v1.md`.
- Approved source:
  `reports/preregistration_pilot_v1_DRAFT_v3_20260712.md`.
- Human audit: `reports/fliptrack_v02r19_human_audit.md`, accepted 60/60.
- Reward weighting evidence: `reports/pilot_reward_spec_v3.md`; native r1v
  resolves to 0.5 accuracy plus 0.5 format.
- The final document contains all ten M0 requirements enumerated in
  `docs/MAIN_PHASE_BRIEF.md`.

Checks:
| Check | Result |
| --- | --- |
| Both PI approvals recorded | true |
| Final path tracked in Git | true |
| Introduction commit hash pinned | true |
| `PENDING_RICHARD_MERGE` absent | true |
| Exact merged-at-HEAD marker present | true |
| No-step statement present | true |
| R19 human-audit marker present | true |
| Prior-observation disclosure present | true |
| R20 caveat present | true |
| Chart construct disclosure present | true |

Decision:
- M0 implementation is complete and recorded as `pass` in the task ledger
  under the PI-approved merge rule. This is not an independent scientific gate
  declaration by the implementing agent.

Next actions:
- Run all four fail-closed authorization probes at this commit.
- Launch M2 only through `scripts/launch_mech_pilot_arm.sh`.
