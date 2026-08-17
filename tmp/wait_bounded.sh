#!/bin/bash
# Exit 0 as soon as an29 GPUs 4-7 are clear; exit 2 if still busy after ~9 min.
DEADLINE=$(( $(date +%s) + 540 ))
while [ $(date +%s) -lt $DEADLINE ]; do
  OUT=$(ssh -o ConnectTimeout=20 an29 'nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits' 2>/dev/null)
  if [ -n "$OUT" ]; then
    BUSY=$(printf '%s\n' "$OUT" | awk -F', *' '$1+0>=4 && $2+0>1000 {print $1"="$2"MiB"}' | tr '\n' ' ')
    if [ -z "$BUSY" ]; then echo "CLEAR $(date -u +%H:%M:%SZ)"; exit 0; fi
    echo "$(date -u +%H:%M:%SZ) busy: $BUSY"
  else
    echo "$(date -u +%H:%M:%SZ) probe failed"
  fi
  sleep 40
done
echo "STILL_BUSY_AT_DEADLINE $(date -u +%H:%M:%SZ)"; exit 2
