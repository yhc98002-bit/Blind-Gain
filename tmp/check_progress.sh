#!/usr/bin/env bash
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"

echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
echo "--- an29 GPUs ---"
ssh -o ConnectTimeout=20 an29 "nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader"
echo "--- M7 TRAINING ARMS (must be 2 on an12, 1 on an29) ---"
ssh -o ConnectTimeout=20 an12 "ps -eo pid,etime,cmd | grep verl.trainer.main | grep -v grep | sed 's#.*runs/##'"
ssh -o ConnectTimeout=20 an29 "ps -eo pid,etime,cmd | grep verl.trainer.main | grep -v grep | sed 's#.*runs/##'"
echo "--- step-0 eval runs ---"
while read -r d; do
  [[ -z "$d" ]] && continue
  n=$(wc -l < "$d/per_item.jsonl" 2>/dev/null || echo 0)
  st=$(jq -r '.status' "$d/run_manifest.json" 2>/dev/null)
  ec=$(jq -r '.exit_code // "-"' "$d/run_manifest.json" 2>/dev/null)
  log=$(ls "$d"/logs/*.log 2>/dev/null | head -1)
  last=$(tail -c 2000 "$log" 2>/dev/null | tr -d '\r' | grep -E '"processed"' | tail -1)
  err=$(grep -aE 'Traceback|Error|FileNotFound|ValueError|KeyError|TypeError|CUDA out of memory|Killed' "$log" 2>/dev/null | tail -2)
  printf '%s\n  status=%s exit=%s rows=%s\n  progress=%s\n' "$(basename "$d")" "$st" "$ec" "$n" "${last:-<none>}"
  [[ -n "$err" ]] && printf '  ERR: %s\n' "$err"
done < tmp/m7_step0_run_dirs.txt
