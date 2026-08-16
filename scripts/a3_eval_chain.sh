#!/usr/bin/env bash
# Launch a3_caption seed-2's held-out eval (an29 gpu 1) when its solo training
# run completes. Mirrors seed2_an29_chain.sh's eval step.
#
# Wait-loop discipline (dispatch 2026-08-16, infra 1b): active deadline via
# scripts/chain_wait_helper.py — WEDGED (alive, saves storage-stalled) pauses
# the clock and is visible here; only genuinely-running time counts; a dead
# trainer stops the waiter loudly. See seed2_an12_chain.sh for the incident
# this encodes.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
PY="$ROOT/.venv/bin/python"
LOG="$ROOT/logs/a3_eval_chain.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
ARM_RUN=experiments/runs/m7_virl_a3_caption_seed2_an29_20260811T040410Z
log "waiting on a3 attempt 2: $ARM_RUN"
DEADLINE_ACTIVE_SECONDS=$(( 60*3600 ))
WAIT_STATE="$ROOT/logs/a3_eval_chain.waitstate.json"
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
    failed) log "a3 FAILED; stopping (no auto-retry)"; exit 1 ;;
    dead) log "a3 DEAD (manifest running, pids gone); stopping loudly"; exit 2 ;;
  esac
  [[ "$verdict" == *deadline_exhausted=1* ]] && { log "active deadline exhausted; abort"; exit 4; }
  sleep 600
done
log "a3 complete; launching its eval on an29 gpu 1"
out=$(bash scripts/launch_m7_seed2_eval.sh a3_caption caption an29 1 2>&1 | tail -1)
log "a3 eval -> $out"
