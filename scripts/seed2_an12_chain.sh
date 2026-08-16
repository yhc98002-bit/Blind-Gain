#!/usr/bin/env bash
# an12 packing chain: when a2_gray (solo, attempt 2) completes -> launch its
# held-out eval on gpu 7 and relaunch the LH2 segment chain (gates itself on
# an12 0-3 idle + host RAM >= 650 GiB; the 1-GPU eval on gpu 7 does not ramp).
#
# Wait-loop discipline (dispatch 2026-08-16, infra 1b): the deadline is an
# ACTIVE deadline scored by scripts/chain_wait_helper.py. A live trainer whose
# saves are stalled by storage reads WEDGED — visible here, deadline clock
# paused — because on 2026-08-13 a pure wall-clock deadline abandoned two
# live, storage-wedged trainers ("deadline; abort"). A dead trainer (manifest
# "running", pids gone) stops this waiter loudly instead of idling to a
# deadline.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
PY="$ROOT/.venv/bin/python"
LOG="$ROOT/logs/seed2_an12_chain.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
ARM_RUN=experiments/runs/m7_virl_a2_gray_seed2_an12_20260810T143944Z
log "waiting on a2_gray attempt 2: $ARM_RUN"
DEADLINE_ACTIVE_SECONDS=$(( 60*3600 ))
WAIT_STATE="$ROOT/logs/seed2_an12_chain.waitstate.json"
last_class=""
while :; do
  verdict=$(PYTHONPATH=. "$PY" scripts/chain_wait_helper.py "$ARM_RUN" \
      --deadline-active-seconds "$DEADLINE_ACTIVE_SECONDS" \
      --state-file "$WAIT_STATE" 2>>"$LOG") \
    || verdict="helper-error active_seconds=? deadline_exhausted=0"
  cls=${verdict%% *}
  if [[ "$cls" != "$last_class" ]]; then log "watch: $verdict"; last_class="$cls"; fi
  case "$cls" in
    complete) break ;;
    failed) log "a2_gray FAILED; stopping (no auto-retry)"; exit 1 ;;
    dead) log "a2_gray DEAD (manifest running, pids gone); stopping loudly"; exit 2 ;;
  esac
  [[ "$verdict" == *deadline_exhausted=1* ]] && { log "active deadline exhausted; abort"; exit 4; }
  sleep 600
done
log "a2_gray complete; launching its eval (gpu 7) + LH2 chain relaunch"
setsid nohup bash scripts/launch_m7_seed2_eval.sh a2_gray gray an12 7 </dev/null >/dev/null 2>&1 &
sleep 30
setsid nohup bash "$ROOT/scripts/lh2_segment_chain.sh" </dev/null >/dev/null 2>&1 &
log "LH2 chain relaunched (it re-gates itself; seg1 restarts from step 0 — no boundary was banked)"
