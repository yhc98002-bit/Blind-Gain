# Parser Agreement Audit

Status:
- Blocked for the required recovery-run agreement rate.

Evidence:
- Searched `experiments/runs/easyr1_geo3k_recovery30_*`.
- The recovery run directory contains only `run_manifest.json`, PID file, and `logs/an12.log`.
- `configs/train/easyr1_qwen25vl3b_geo3k_recovery30.yaml` had `val_freq: -1` and `val_before_train: false`, so no validation generation table was emitted.
- `rg` found no cached generation JSONL or logged sample table containing ≥300 `(response, ground_truth)` records.
- EasyR1 reference scorer inspected at `artifacts/repos/EasyR1/examples/reward_function/r1v.py`; it uses `<answer>` extraction plus `mathruler.grader.grade_answer`.

Agreement table:

| Source | Candidate records | Usable `(response, ground_truth)` pairs | Our accuracy | EasyR1 accuracy | Agreement |
| --- | ---: | ---: | ---: | ---: | ---: |
| `experiments/runs/easyr1_geo3k_recovery30_20260708T043244Z` | 0 | 0 | n/a | n/a | n/a |

Problem:
- P0.2 requires sampling at least 300 generations from the recovery run logs. Those generations were not logged by the 30-step recovery config.

Decision:
- Parser implementation and nested-brace tests are complete.
- The agreement audit cannot honestly pass until a run with logged validation generations exists or the old checkpoint is re-evaluated with generation logging.

Next actions:
- P1.1 should use `val_before_train: true`, `val_freq: 10`, and logged validation outputs.
- After generation JSONL exists, re-run this audit against at least 300 records.
