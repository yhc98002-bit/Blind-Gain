# M2 Pilot Completion Watchdog

Status:
- A login-node watchdog is active for the four seed-1 M2 pilot training runs.
- It polls the four pinned run manifests every 120 seconds.
- Initial heartbeat at `2026-07-13T13:03:22Z`: `0/4` complete; all four parent outcomes were `running`.
- This is mechanical completion monitoring only. It does not declare or interpret a scientific gate.

Evidence:
- Watchdog run: `experiments/runs/m2_pilot_completion_watchdog_login_20260713T130322Z`
- Run manifest: `experiments/runs/m2_pilot_completion_watchdog_login_20260713T130322Z/run_manifest.json`
- Live state: `experiments/runs/m2_pilot_completion_watchdog_login_20260713T130322Z/watchdog_state.json`
- Runtime log: `experiments/runs/m2_pilot_completion_watchdog_login_20260713T130322Z/logs/login.log`
- Runtime Git revision: `441ad568629fb44835deaded94860e79367cd913`
- Config SHA256: `471a47007873b6f976340b821d7ee44f71f54b408f9c94cb19e18cbb51477ea7`
- Runtime: `scripts/watch_m2_pilot_completion.py`
- Launcher: `scripts/launch_m2_completion_watchdog.sh`
- Tests: `18 passed` across the new watchdog tests, M11 release-queue tests, and manifest-runner tests.

Pinned parents:

| Arm | Node | Run ID |
|---|---|---|
| A1 real | `an12` | `mech_a1_real_an12_20260713T031454Z` |
| A2 gray | `an12` | `mech_a2_gray_an12_20260713T033946Z` |
| A2b no-image | `an29` | `mech_a2b_noimage_retry4_an29_20260713T113556Z` |
| A3 caption | `an29` | `mech_a3_caption_an29_20260713T033039Z` |

Completion contract:
- An arm is complete only when its pinned manifest has the expected job type, arm, node, and run ID; `status=complete`; `exit_code=0`; `artifacts_exist=true`; and a nonempty end time.
- A failed parent, identity mismatch, inconsistent terminal state, or falsely labeled completion makes the watchdog fail closed.
- Temporary manifest read errors remain nonterminal and are retried on the next poll.
- The runtime contains no SSH, `nvidia-smi`, subprocess launch, process signal, or GPU-control path.
- The launcher checks only its own prior watchdog PID to prevent duplicate monitors. It never checks, signals, stops, or restarts a trainer.

Terminal artifacts:
- Success or failure writes immutable machine output to `terminal_notification.json` in the watchdog run directory.
- The same terminal state is rendered to `terminal_notification.md` in that directory.
- On success, the watchdog run manifest finalizes as `complete`; on any parent failure it finalizes as `fail` with the per-arm reason retained.
- The already-running M11 queue independently observes successful blind-arm completion and remains responsible for its registered release behavior.

Problems:
- A local watchdog cannot wake the Codex chat or initiate a new assistant turn. It provides a durable terminal notification that Codex will inspect on the next `continue` or status request.

Decision:
- Pin exact run IDs rather than use broad globs, preventing an older successful attempt from masking failure of the active retry.
- Keep notification separate from checkpoint retention and M11 scheduling. This avoids changing either running trainers or registered downstream behavior.

Next actions:
- Continue polling until all four parents complete or one fails.
- On the next interactive turn after termination, inspect both terminal notification files, parent logs, checkpoint-watcher states, and registered evaluation readiness before updating M2 accounting.
