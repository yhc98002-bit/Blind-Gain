#!/usr/bin/env bash
# an29 packing chain: when a2b (solo) completes -> launch its held-out eval on
# gpu 0 and relaunch a3_caption solo on gpus 4-7. One ramping ViRL trainer per
# node (2026-08-10 placement rule: two colocated ViRL trainers exhausted an12
# host RAM at 17 h; a small eval does not ramp and may colocate).
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
LOG="$ROOT/logs/seed2_an29_chain.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
ARM_RUN=experiments/runs/m7_virl_a2b_noimage_seed2_an29_20260809T150728Z
log "waiting on a2b: $ARM_RUN"
DEADLINE=$(( $(date -u +%s) + 40*3600 ))
while :; do
  (( $(date -u +%s) > DEADLINE )) && { log "deadline; abort"; exit 4; }
  s=$(grep -oE '"status": *"[a-z]+"' "$ARM_RUN/run_manifest.json" 2>/dev/null | tail -1)
  [[ "$s" == *complete* ]] && break
  [[ "$s" == *fail* ]] && { log "a2b FAILED; stopping (no auto-retry)"; exit 1; }
  sleep 600
done
log "a2b complete; launching its eval (gpu 0) + a3 relaunch (4-7)"
setsid nohup bash scripts/launch_m7_seed2_eval.sh a2b_noimage none an29 0 </dev/null >/dev/null 2>&1 &
sleep 120   # let the eval's merge start before the trainer launch claims GPUs
out=$(bash scripts/launch_m7_virl_arm.sh a3_caption 2 an29 4,5,6,7 2>&1 | tail -1)
log "a3 relaunch -> $out"
[[ "$out" == experiments/runs/* ]] && log "a3 relaunched OK" || { log "A3 RELAUNCH REFUSED"; exit 1; }
