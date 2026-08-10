#!/usr/bin/env bash
# an12 packing chain: when a2_gray (solo, attempt 2) completes -> launch its
# held-out eval on gpu 7 and relaunch the LH2 segment chain (gates itself on
# an12 0-3 idle + host RAM >= 650 GiB; the 1-GPU eval on gpu 7 does not ramp).
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
LOG="$ROOT/logs/seed2_an12_chain.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
ARM_RUN=experiments/runs/m7_virl_a2_gray_seed2_an12_20260810T143944Z
log "waiting on a2_gray attempt 2: $ARM_RUN"
DEADLINE=$(( $(date -u +%s) + 60*3600 ))
while :; do
  (( $(date -u +%s) > DEADLINE )) && { log "deadline; abort"; exit 4; }
  s=$(grep -oE '"status": *"[a-z]+"' "$ARM_RUN/run_manifest.json" 2>/dev/null | tail -1)
  [[ "$s" == *complete* ]] && break
  [[ "$s" == *fail* ]] && { log "a2_gray FAILED; stopping (no auto-retry)"; exit 1; }
  sleep 600
done
log "a2_gray complete; launching its eval (gpu 7) + LH2 chain relaunch"
setsid nohup bash scripts/launch_m7_seed2_eval.sh a2_gray gray an12 7 </dev/null >/dev/null 2>&1 &
sleep 30
setsid nohup bash "$ROOT/scripts/lh2_segment_chain.sh" </dev/null >/dev/null 2>&1 &
log "LH2 chain relaunched (it re-gates itself; seg1 restarts from step 0 — no boundary was banked)"
