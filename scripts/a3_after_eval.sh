#!/usr/bin/env bash
# Launch M7 seed-2 a3_caption on an29 4-7 once the a1-seed2 held-out eval
# (an29 gpu 6) completes. Fail-closed; guard+claims handled by the arm launcher.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
LOG="$ROOT/logs/a3_after_eval.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
EVAL_DIR=experiments/runs/m7_step100_heldout_seed2_a1_real_seed2_real_an29_20260809T144439Z
DEADLINE=$(( $(date -u +%s) + 16*3600 ))
log "waiting on a1-seed2 eval: $EVAL_DIR"
while :; do
  (( $(date -u +%s) > DEADLINE )) && { log "deadline; abort"; exit 4; }
  s=$(grep -oE '"status": *"[a-z]+"' "$EVAL_DIR/run_manifest.json" 2>/dev/null | tail -1)
  [[ "$s" == *complete* ]] && break
  [[ "$s" == *fail* ]] && { log "a1-seed2 eval FAILED; not launching a3; abort"; exit 1; }
  sleep 600
done
log "a1-seed2 eval complete; releasing its claim and launching a3_caption on an29 4-7"
ssh -o ConnectTimeout=15 an29 "rm -f /dev/shm/blind-gains/gpu_claims/an29_gpu6.claim" 2>/dev/null || true
out=$(bash scripts/launch_m7_virl_arm.sh a3_caption 2 an29 4,5,6,7 2>&1 | tail -1)
log "a3_caption -> $out"
[[ "$out" == experiments/runs/* ]] && log "a3 launched OK" || { log "A3 LAUNCH REFUSED"; exit 1; }
