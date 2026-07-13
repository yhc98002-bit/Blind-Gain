# M11 Pilot-Release Gate V1

Status:
- M11 remains `blocked` and queued behind the pilot by design.
- The accidentally opened queue
  `m11_generalization_queue_login_20260713T110714Z` was stopped before launch;
  all six smoke and 18 full cells remain pending.

Evidence:
- Its only capacity poll observed an29 GPUs 0-3 free, but no GPU reached the
  existing two-poll stability threshold.
- Final queue-state SHA256:
  `493bdcbea234ed4c0d0cb81de43ea609d88b764972862c66f7d62fc5bb5ed8ea`.
- The retained state records `launched_cells=0` and reason
  `pilot_failure_vacancy_is_not_a_blind_arm_release`.
- The replacement gate requires status `complete` and exit code `0` from both
  `a2b_noimage` and `a3_caption` manifests on an29 before capacity polling can
  advance.
- The adversarial fixture supplies a failed A2b manifest, a completed A3
  manifest, and otherwise free capacity; the release gate remains closed.

Problems:
- GPU vacancy alone cannot distinguish normal pilot completion from an
  operational crash.

Decision:
- Pilot completion and stable free capacity are conjunctive conditions.
- A failed blind arm leaves M11 dormant rather than failing or launching it.
- M11 remains TP1 per model and uses the isolated audited inference runtime once
  both conditions are met.

Next actions:
- Commit the gate before relaunching the login-node queue.
- Verify the live queue reports `waiting_pilot_release` with 24 pending cells.
