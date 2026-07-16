# Main-Phase PI Ruling, 2026-07-16

The review's recovery sequence is approved as written.

## R1 — M4 Long-Horizon Authorization

Primary contrast: `Delta = R19 geometry pair-acc(step 400) - pair-acc(step 100)`,
with an item-paired bootstrap 95% confidence interval.

- `FLAT` iff the confidence interval is contained in `[-0.05, +0.05]`.
- `RISING` iff `Delta >= +0.05` and the confidence-interval lower bound is greater than zero.
- `FALLING` iff `Delta <= -0.05` and the confidence-interval upper bound is less than zero.
- `INDETERMINATE` otherwise. Report that outcome as such.
- Step 400 is terminal. Do not extend or rerun under any outcome.
- Steps 150, 200, and 300 are descriptive.

Context condition for “delayed-learning objection answered”: the Geometry3K benchmark
step-300-to-step-400 paired delta has a confidence interval containing zero or an
absolute delta below two percentage points. If the benchmark is still rising at step
400, report the objection as partially addressed and stop.

Secondaries are overall R19 under the same rule, a per-category table, and blind-floor
persistence at step 400: gray/noise pair accuracy at most 0.05 and Collapse Rate at
least 0.95. There is one primary and no multiplicity correction.

Merge this rule as the M4 authorization marker, run the restore-and-resume integrity
check, and launch M5.

## R2 — A2 Recovery

Execute the approved seven-step P0 sequence: list and hash eligible login-archive
content before sweeping it to shared storage; merge A2 step 100; verify shards; use
fresh immutable evaluation queues; complete the 601-row audit; then compute every
registered four-arm estimand in one readout at
`reports/pilot_4arm_seed1_results_v1.md`. Three-arm values remain unopened.

If A2 recovery exceeds 24 hours, a three-arm partial read is pre-authorized only after
an additional explicit PI instruction and with a deviations-log line. Do not exercise
that fallback automatically.

## R3 — Evaluation/Relocation Decoupling

Merge and evaluation depend on the checkpoint, not the archive move. A
`StorageGuardRefusal` during relocation must never again block evaluation. Patch the
watcher/queue dependency and add an adversarial fixture.

## R4 — 7B Gray Arm

The precommitted rule fired: the 7B base audit has gray accuracy 0.2456 and no-image
accuracy 0.1824 with non-overlapping intervals. Retain A2-gray in the 7B flagship.
The 7B template has A1, A2, A2b, and A3, with three seeds each. Record this as a
rule-citation, not a judgment call.

## R5 — Post-A2 GPU Priority

1. Seed-2 arms and M5 concurrently.
2. M11 full matrix after all M2 markers complete.
3. M6 when the pair corpus and reward/grouping audits are ready.
4. Seed 3.
5. M7, with the stratification amendment present, and M9 according to readiness.

Scheduling within this order is delegated to the implementing researcher.

## R6 — M8

Commit the four 7B audit reports with normal consistency and ledger reconciliation.
Fill the M4 7B computed fields supported by those artifacts.

## R7 — Chart V08 Audit Viewer

Extend the v08 viewer with mechanically disabled zoom and fixed-size rendering, the
six standard checks, two v08 ratings (`no-zoom-correct` and `series-unambiguous`), and
exportable JSON. Report ready for human review. Richard schedules the audit after the
seed-1 readout. This is not critical path.

## R8 — Naming

The registered four arms are A1, A2, A2b, and A3. Proposal A4 text-only transfer is
unlaunched and outside Paper 1 scope.

Stale ledgers, M8 reconciliation, the M11 scheduler, and GPU scheduling require no
further PI input.
