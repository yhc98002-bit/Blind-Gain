# Prelaunch Progress

The ledger-accounting objective from the last prompt is complete. This does **not** mean the scientific prelaunch gate has passed.

## Completed

- Added the authoritative L0-L13 registry: `PRELAUNCH_TASKS.md`
- Added the objective auditor: `scripts/audit_prelaunch_objective.py`
- Added 11 adversarial fixtures: `tests/test_prelaunch_objective.py`
- Repaired the byte-identical audited-report violation.
- Verified exactly one valid ledger entry for every task L0-L13.
- Ran the full test suite: **248 passed in 182.81 seconds**.
- Published the machine audit: `reports/prelaunch_objective_audit.json`
- Committed and pushed as `edf90bc8619c7cc983183589c8ce327eebe5e62f` on `agent/gate2-recovery`.

The machine audit reports `status: pass` for ledger integrity, with no errors. It reports `pass_task_count: 0`, because no scientific task is currently declared passed.

## Scientific Status

The authoritative ledger is `reports/prelaunch_progress.md`.

| Tasks | Status | Reason |
|---|---|---|
| L0 | Blocked | Storage guards and tests pass, but persistent node-local pilot checkpoint paths are not approved. |
| L1-L5 | Blocked | Hard ordering requires L0 first. |
| L6 | Blocked, partial work complete | Consistency auditor implemented; stale-report repairs and GPU-hours report remain. |
| L7-L11 | Blocked | Depend on L0 and Wave-1 contracts. |
| L12 | Blocked | Requires L7, human R19 audit, and PI approval. |
| L13 | Blocked | Requires merged L12 plus L3-L5. No pilot optimizer step has been launched. |

No PI gate has been declared passed.

## Active Anchor Job

The existing anchor remains untouched as required:

- Run: `anchor_a0_recipe_3b_geo3k`
- Node: `an12`, GPUs 0-3
- Latest observed checkpoint: step 60
- Training process remains active.
- GPUs were approximately 73-76% utilized at the latest inspection.
- The retention watcher is running and waiting for stable step 80.
- Watcher run: `experiments/runs/anchor_checkpoint_retention_watch_login_20260711T052335Z`

## Blocking Decision

L0 needs approved writable persistent node-local paths on both `an12` and `an29` for pilot checkpoints while preserving the 40 GiB scratch floor. The detailed storage findings are in `reports/storage_preflight.md`.

Unrelated worktree changes to `CLAUDE.md` and `AGENTS.md` were left untouched.
