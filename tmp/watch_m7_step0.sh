#!/usr/bin/env bash
# Waits for the four R3 step-0 evals to leave "running", then verifies them.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
LOGDIR="$ROOT/logs/m7_step0_heldout_watch_20260730T154447Z"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/watch.log"
say() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
say "watcher started on $(hostname) pid=$$"
while true; do
  running=0
  while read -r d; do
    [ -z "$d" ] && continue
    st=$(jq -r '.status' "$d/run_manifest.json" 2>/dev/null)
    [ "$st" = "running" ] && running=$((running+1))
  done < tmp/m7_step0_run_dirs.txt
  if [ "$running" -eq 0 ]; then break; fi
  say "still running: ${running}/4 | $(while read -r d; do [ -z "$d" ] && continue; printf '%s=%s ' "$(jq -r .condition "$d/run_manifest.json" 2>/dev/null)" "$(wc -l < "$d/per_item.jsonl" 2>/dev/null || echo 0)"; done < tmp/m7_step0_run_dirs.txt)"
  sleep 600
done
say "all four left running state; verifying"
PYTHONPATH=. .venv/bin/python tmp/verify_m7_step0.py >> "$LOGDIR/verification.txt" 2>&1
say "verification rc=$? -> $LOGDIR/verification.txt"
