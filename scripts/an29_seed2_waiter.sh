#!/usr/bin/env bash
# Launch M7 seed-2 arms a2_gray (an29 0-3) and a2b_noimage (an29 4-7) once an29
# is free of the last 7B arm — with a coordination window so Gate-1's brief
# 8-GPU plumbing smokes (T7) can use the node first if their prework finishes
# in time.
#
# Order of gates:
#   1. an29 idle: zero trainers, all GPUs < 1 GiB, and the A1-real 7B merge is
#      verified on shared storage (its index parses at the 7B size).
#   2. Grace window for Gate-1 T7: if the T6 marker
#      reports/mini_a5_gate1_completion_registration_marker_v1.json appears
#      within 12 h of an29 freeing, hold a further 3 h (smokes take ~1 h);
#      otherwise proceed at the 12 h mark. Every decision logged.
#   3. Launch both seed-2 arms via the registered launcher (its own gates and
#      claim files apply). 3B arms colocate safely; no 7B offload arm remains.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
LOG="$ROOT/logs/an29_seed2_waiter.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
log "waiter start"

DEADLINE=$(( $(date -u +%s) + 36*3600 ))
FREED_AT=""
while :; do
  (( $(date -u +%s) > DEADLINE )) && { log "DEADLINE 36h; stopping"; exit 4; }
  trainers=$(ssh -o ConnectTimeout=15 an29 "pgrep -fc 'verl.trainer.mai[n]' || true" 2>/dev/null | head -1)
  maxmem=$(ssh -o ConnectTimeout=15 an29 "nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | sort -n | tail -1" 2>/dev/null || echo 999999)
  merged=no
  if .venv/bin/python - checkpoints/c5/c5_a1_real_seed1_7b/global_step_100/actor/huggingface/model.safetensors.index.json <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1]))
assert d["metadata"]["total_size"] == 16584333312
PYEOF
  then merged=yes; fi
  log "an29 trainers=$trainers maxmem=${maxmem}MiB a1_7b_merged=$merged"
  if [[ "$trainers" == "0" && "${maxmem:-999999}" -lt 1024 && "$merged" == yes ]]; then
    [[ -z "$FREED_AT" ]] && { FREED_AT=$(date -u +%s); log "an29 free at $(date -u +%H:%M:%SZ); opening 12h T7 grace window"; }
    elapsed=$(( $(date -u +%s) - FREED_AT ))
    if [[ -f reports/mini_a5_gate1_completion_registration_marker_v1.json ]]; then
      log "T6 marker present; holding 3h more for T7 smokes (elapsed ${elapsed}s)"
      if (( elapsed >= 3*3600 )); then log "3h post-marker hold done"; break; fi
    elif (( elapsed >= 12*3600 )); then
      log "12h grace expired without T6 marker; proceeding"
      break
    fi
  else
    FREED_AT=""
  fi
  sleep 600
done

log "launching seed-2 a2_gray on an29 0-3"
out1=$(bash scripts/launch_m7_virl_arm.sh a2_gray 2 an29 0,1,2,3 2>&1 | tail -1); log "a2_gray: $out1"
sleep 120
log "launching seed-2 a2b_noimage on an29 4-7"
out2=$(bash scripts/launch_m7_virl_arm.sh a2b_noimage 2 an29 4,5,6,7 2>&1 | tail -1); log "a2b: $out2"
sleep 240
alive=$(ssh -o ConnectTimeout=15 an29 "pgrep -fc 'verl.trainer.mai[n]'" 2>/dev/null)
log "post-launch trainers on an29: $alive (expect 2)"
[[ "$alive" == "2" ]] && log "BOTH SEED-2 ARMS RUNNING" || log "ATTENTION: expected 2 trainers, found $alive"
