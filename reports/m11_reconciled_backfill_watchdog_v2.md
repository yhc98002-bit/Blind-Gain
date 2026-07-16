# M11 Reconciled Backfill Watchdog V2

Status:
- Active. This supersedes V1's implementation-status note; no prior run or number is overwritten.
- The watchdog has reconciled the 18-cell registry and launched the first automatic backfill. M11 remains blocked pending cell completion and final audit.

Evidence:
- Watchdog: `experiments/runs/m11_reconciled_backfill_login_20260716T172041Z`; config SHA256 `21687cdf5de6b36ef637e223253baaca442f565193430148d26acad86ab57c65`.
- At capacity poll 2: 4 cells complete, 7 running, 7 pending, and `performance_values_opened=false`.
- Automatic launch: `flip_gemma3_r19_none` on an29 GPU 3 at `2026-07-16T17:21:46Z`, after two stable-free polls.
- Manual pre-watchdog Gemma cell: R19 real on an29 GPU 0. The remaining an29 M11 jobs occupy GPUs 1/4; seed-2 remains isolated on GPUs 2/5/6/7.
- Commit `aff1c7f` replaces the final builder's exact-two-stage assumption with coverage of every `(backend, node)` used by the evaluation manifests.
- The mixed-node adversarial fixture fails when InternVL an12 stage evidence is absent and passes only after a verified an12 stage is supplied. Seven focused builder/watchdog tests pass.

Problems:
- Scientific outputs remain incomplete. No interpretation or aggregate M11 report is authorized from partial cells.

Decision:
- Continue capacity-driven backfill on an29 GPUs 0/1/3/4, stopping fail-closed on any cell failure.
- Build the final report with three stage manifests: InternVL an29, InternVL an12, and Gemma an29.

Next actions:
- Monitor structural progress and errors only.
- Once all cells complete, run the placement-aware builder and publish `reports/generalization_audits_v1.md` plus machine JSON.
