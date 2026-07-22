# Mini-A5 Plumbing Smoke Audit V1

Status:
- Independent engineering audit: `pass`.
- This audit authorizes zero main-arm optimizer steps and makes no PI gate decision.

Evidence:
- Machine artifact: `/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/reports/mini_a5_plumbing_smoke_audit_v1.json`.
- CP run: `experiments/runs/mini_a5_cp_plumbing_smoke_an29_20260722T041049Z/run_manifest.json`; checks passed `15/15`.
- Member run: `/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/experiments/runs/mini_a5_member_plumbing_smoke_an29_20260722T045328Z/run_manifest.json`; checks passed `15/15`.
- CP runtime marker: `[{'advantages_finite': True, 'pair_count': 8, 'rollout_counts': [5], 'row_count': 80}]`.
- CP checkpoint inventory: `20` files / `16282047374` bytes.
- Member checkpoint inventory: `20` files / `16282047374` bytes.

Checks:
| Check | Result |
| --- | --- |
| `cp_run_passed` | `pass` |
| `member_run_passed` | `pass` |
| `same_single_node_and_gpu_set` | `pass` |
| `sequential_nonoverlapping_runs` | `pass` |
| `configs_differ_only_in_registered_fields` | `pass` |

Problems:
- CP errors: `[]`.
- Member errors: `[]`.

Decision:
- A pass establishes only the registered one-step plumbing path.
- Main M6 arms remain blocked until a separate post-smoke marker binds this audit and the exact main configs.
