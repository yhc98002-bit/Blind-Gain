#!/usr/bin/env bash
# Launch a3_caption seed-2's held-out eval (an29 gpu 1) when its solo training
# run completes. Mirrors seed2_an29_chain.sh's eval step.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
LOG="$ROOT/logs/a3_eval_chain.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
ARM_RUN=experiments/runs/m7_virl_a3_caption_seed2_an29_20260811T040410Z
log "waiting on a3 attempt 2: $ARM_RUN"
DEADLINE=$(( $(date -u +%s) + 60*3600 ))
while :; do
  (( $(date -u +%s) > DEADLINE )) && { log "deadline; abort"; exit 4; }
  s=$(grep -oE '"status": *"[a-z]+"' "$ARM_RUN/run_manifest.json" 2>/dev/null | tail -1)
  [[ "$s" == *complete* ]] && break
  [[ "$s" == *fail* ]] && { log "a3 FAILED; stopping (no auto-retry)"; exit 1; }
  sleep 600
done
log "a3 complete; launching its eval on an29 gpu 1"
out=$(bash scripts/launch_m7_seed2_eval.sh a3_caption caption an29 1 2>&1 | tail -1)
log "a3 eval -> $out"
