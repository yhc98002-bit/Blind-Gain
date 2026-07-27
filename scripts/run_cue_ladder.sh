#!/usr/bin/env bash
# Cue-ladder scoring. Usage: run_cue_ladder.sh <cell_name> <model_path> <gpu_csv>
# Scores all four rungs for one model cell, one rung per GPU.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT"

CELL="$1"; MODEL="$2"; GPUS="$3"   # GPUS e.g. "4,5,6,7"
[ -d "$MODEL" ] || { echo "FAIL missing model: $MODEL"; exit 1; }

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="experiments/runs/cue_ladder_${CELL}_${STAMP}"
IFS=',' read -r -a GPUARR <<< "$GPUS"

i=0
for rung in exact region none decoy; do
  GPU="${GPUARR[$((i % ${#GPUARR[@]}))]}"
  D="$OUT/$rung"
  mkdir -p "$D/logs"
  ssh an12 "cd '$ROOT' && source .venv/bin/activate && (nohup env \
PYTHONUNBUFFERED=1 PYTHONHASHSEED=0 TRANSFORMERS_OFFLINE=1 \
HF_HOME='$ROOT/artifacts/hf_home' CUDA_VISIBLE_DEVICES=$GPU \
python scripts/eval_qwen_vl_fliptrack.py \
--model-path '$MODEL' \
--manifest data/cue_ladder_v1/${rung}_manifest.jsonl \
--output '$ROOT/$D/predictions.jsonl' \
--metrics-output '$ROOT/$D/metrics.json' \
--num-shards 1 --shard-index 0 --image-mode real \
--image-cache-dir '$ROOT/$D/img_cache' \
--seed 0 --noise-seed 0 --max-new-tokens 32 \
> '$ROOT/$D/logs/cell.log' 2>&1 < /dev/null & echo \$! > '$ROOT/$D/logs/pid')"
  echo "launched $CELL/$rung on an12:gpu$GPU"
  i=$((i+1))
done
echo "$OUT"
