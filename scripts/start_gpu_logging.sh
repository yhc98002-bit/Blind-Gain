#!/usr/bin/env bash
set -euo pipefail

NODE="${1:-$(hostname)}"
OUT="${2:-logs/gpu_util_${NODE}.jsonl}"
INTERVAL="${INTERVAL:-300}"

mkdir -p "$(dirname "$OUT")" logs

if pgrep -f "bash scripts/collect_gpu_util.sh ${NODE} ${OUT}" >/dev/null 2>&1; then
  pgrep -f "bash scripts/collect_gpu_util.sh ${NODE} ${OUT}" | head -1 > "logs/gpu_util_${NODE}.pid"
  echo "already running: $(cat "logs/gpu_util_${NODE}.pid")"
  exit 0
fi

nohup env INTERVAL="$INTERVAL" bash scripts/collect_gpu_util.sh "$NODE" "$OUT" \
  >> "logs/gpu_util_${NODE}.nohup.log" 2>&1 &
echo "$!" > "logs/gpu_util_${NODE}.pid"
echo "started: $(cat "logs/gpu_util_${NODE}.pid")"

