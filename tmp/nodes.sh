#!/usr/bin/env bash
for N in an12 an29; do
  echo "===== $N ====="
  ssh -o ConnectTimeout=20 "$N" 'echo "-- pgrep verl.trainer.main --"; pgrep -af "verl.trainer.mai[n]" | head -5; echo "-- nvidia-smi --"; nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader; echo "-- compute apps --"; nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader | head -20'
done
