#!/usr/bin/env bash
# Relaunch M7 arm 4 (a3_caption seed 1) on an29 GPUs 4-7 once they are genuinely free.
#
# Arm 4's first launch died with a CUDA OOM in vLLM KV-cache allocation because two
# concurrent M5c noise-floor evaluations (run_blind_solvability_v2.py) claimed an29
# GPUs 4-5 at ~63 GB each in the same window. The colocation guard did not stop it:
# it derives occupancy from live trainer manifests plus nvidia-smi, and at launch
# time those eval processes had not yet allocated. That is a race between two of our
# own workstreams, not a config fault.
#
# This watcher removes the race by being the single claimant: it waits until all four
# GPUs are actually idle before invoking the launcher, and it re-checks immediately
# before launching.
set -uo pipefail

ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"      # launcher needs jq

LOG="$ROOT/logs/m7_arm4_relaunch_watch.log"
mkdir -p "$(dirname "$LOG")"
FREE_MIB=1000
NEEDED=(4 5 6 7)
MAX_WAIT_S=$((8 * 3600))
START=$(date -u +%s)

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }

all_free() {
  local g used
  for g in "${NEEDED[@]}"; do
    used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$g" 2>/dev/null || echo 999999)
    [[ "${used:-999999}" -lt "$FREE_MIB" ]] || return 1
  done
  return 0
}

log "watcher start; waiting for an29 GPUs ${NEEDED[*]} to fall below ${FREE_MIB} MiB"

while :; do
  if (( $(date -u +%s) - START > MAX_WAIT_S )); then
    log "GAVE UP after ${MAX_WAIT_S}s; GPUs never freed. Arm 4 NOT launched."
    exit 4
  fi

  # If a checkpoint dir appeared, someone else launched it -- do not double-launch.
  if [[ -e "$ROOT/checkpoints/m7/m7_virl_a3_caption_seed1" ]]; then
    log "checkpoint dir exists; another launch won. Exiting without launching."
    exit 0
  fi

  if all_free; then
    sleep 20                      # settle, then re-check to avoid a fresh claimant
    if all_free; then
      log "GPUs free; launching arm 4"
      OUT=$(bash scripts/launch_m7_virl_arm.sh a3_caption 1 an29 4,5,6,7 2>&1)
      RC=$?
      log "launcher rc=$RC"
      printf '%s\n' "$OUT" >> "$LOG"
      if [[ $RC -eq 0 ]]; then
        sleep 180
        ALIVE=$(pgrep -fc 'verl.trainer.mai[n]' 2>/dev/null || echo 0)
        log "post-launch: verl trainers on this node = $ALIVE"
        nvidia-smi --query-gpu=index,memory.used --format=csv,noheader >> "$LOG"
      fi
      exit $RC
    fi
    log "a new claimant appeared during settle; continuing to wait"
  fi
  sleep 60
done
