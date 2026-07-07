#!/usr/bin/env bash
set -euo pipefail

NODE="${1:-$(hostname)}"
OUT="${2:-logs/gpu_util_${NODE}.jsonl}"
INTERVAL="${INTERVAL:-300}"

mkdir -p "$(dirname "$OUT")"

while true; do
  TS="$(date -Is)"
  if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi --query-gpu=index,uuid,name,memory.total,memory.used,utilization.gpu,utilization.memory,temperature.gpu,power.draw --format=csv,noheader,nounits \
      | awk -v ts="$TS" -v node="$NODE" -F ', ' '{
          printf("{\"ts\":\"%s\",\"node\":\"%s\",\"gpu_index\":%s,\"uuid\":\"%s\",\"name\":\"%s\",\"memory_total_mib\":%s,\"memory_used_mib\":%s,\"util_gpu_pct\":%s,\"util_mem_pct\":%s,\"temp_c\":%s,\"power_w\":%s}\n", ts, node, $1, $2, $3, $4, $5, $6, $7, $8, $9)
        }' >> "$OUT"
  else
    printf '{"ts":"%s","node":"%s","error":"nvidia-smi not found"}\n' "$TS" "$NODE" >> "$OUT"
  fi
  sleep "$INTERVAL"
done

