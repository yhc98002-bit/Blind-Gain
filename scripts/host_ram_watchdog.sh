#!/usr/bin/env bash
# Host-RAM backstop for the one-ramping-trainer-per-node rule. Every 10 min per
# node: log available GiB; if < 120 GiB with >1 live trainer, kill the YOUNGEST
# trainer (the older one has more sunk compute) and log loudly. Solo trainers
# never get near the threshold (measured solo floor ~478 GiB available).
set -u
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
export PATH="$HOME/.local/bin:$PATH"
LOG="$ROOT/logs/host_ram_watchdog.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
DEADLINE=$(( $(date -u +%s) + 6*24*3600 ))
log "watchdog start"
while :; do
  [ "$(date -u +%s)" -gt "$DEADLINE" ] && { log "deadline reached; exiting"; exit 0; }
  for node in an12 an29; do
    avail=$(ssh -o BatchMode=yes -o ConnectTimeout=15 "$node" "free -g | awk 'NR==2 {print \$7}'" 2>/dev/null)
    [ -n "${avail:-}" ] || { log "$node: unreachable"; continue; }
    ntr=$(ssh -o BatchMode=yes -o ConnectTimeout=15 "$node" "pgrep -fc 'verl.trainer.mai[n]' || true" 2>/dev/null | head -1)
    log "$node avail=${avail}GiB trainers=${ntr:-?}"
    if [ "${avail:-999}" -lt 120 ] && [ "${ntr:-0}" -gt 1 ]; then
      young=$(ssh -o BatchMode=yes -o ConnectTimeout=15 "$node" "pgrep -f 'verl.trainer.mai[n]' | xargs -r ps -o pid=,etimes= -p | sort -k2 -n | head -1 | awk '{print \$1}'" 2>/dev/null)
      if [ -n "${young:-}" ]; then
        log "$node: LOW RAM with ${ntr} trainers -> killing youngest trainer pid $young"
        ssh -o BatchMode=yes -o ConnectTimeout=15 "$node" "kill -- -$young 2>/dev/null || kill $young" 2>/dev/null
        log "$node: kill issued"
      fi
    fi
  done
  sleep 600
done
