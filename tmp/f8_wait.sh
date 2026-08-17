#!/usr/bin/env bash
# Block on the compute-side driver reaching a terminal state, bounded.
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
S="$ROOT/logs/mini_a5_f8_driver_20260730T004031Z"
LIMIT="${1:-540}"
END=$(( $(date +%s) + LIMIT ))
while [ ! -f "$S/DRIVER_STATUS" ]; do
  [ "$(date +%s)" -ge "$END" ] && { echo "STILL_RUNNING"; tail -3 "$S/driver.log"; exit 0; }
  command sleep 20
done
echo "TERMINAL status=$(cat "$S/DRIVER_STATUS")"
cat "$S/driver.log"
