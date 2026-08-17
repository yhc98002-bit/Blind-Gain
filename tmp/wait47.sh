#!/bin/bash
# Waits until an29 GPUs 4,5,6,7 are all free of compute contexts.
for i in $(seq 1 70); do
  OUT=$(ssh -o ConnectTimeout=20 an29 'nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits' 2>/dev/null)
  if [ -z "$OUT" ]; then echo "iter $i: ssh/nvidia-smi FAILED (fail-closed, keep waiting)"; sleep 45; continue; fi
  BUSY=$(printf '%s\n' "$OUT" | awk -F', *' '$1+0>=4 && $2+0>1000 {print $1"="$2"MiB"}' | tr '\n' ' ')
  if [ -z "$BUSY" ]; then echo "GPUS_4_7_CLEAR at $(date -u +%Y-%m-%dT%H:%M:%SZ) iter=$i"; exit 0; fi
  echo "iter $i $(date -u +%H:%M:%SZ) still busy: $BUSY"
  sleep 45
done
echo "WAIT_TIMEOUT after 70 iters"; exit 1
