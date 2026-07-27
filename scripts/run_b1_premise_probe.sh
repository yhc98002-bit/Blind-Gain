#!/usr/bin/env bash
# B1 premise probe: 5 registered cells on an12 GPUs 4-7 (never 0-3, M5 holds those).
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
BASE=artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct
MANIFEST=data/b1_premise_probe_v1.jsonl
OUTROOT=experiments/runs/b1_premise_probe_$STAMP
mkdir -p "$OUTROOT"

declare -a CELLS=(
  "base|$BASE"
  "a1_seed1_step100|checkpoints/pilot/mech_a1_real_resume60/global_step_100/actor/huggingface"
  "a1_seed2_step100|checkpoints/pilot/mech_a1_real_seed2/global_step_100/actor/huggingface"
  "a2b_seed1_step100|checkpoints/pilot/mech_a2b_noimage_retry4/global_step_100/actor/huggingface"
  "a3_seed1_step100|checkpoints/pilot/mech_a3_caption_resume20/global_step_100/actor/huggingface"
)

for c in "${CELLS[@]}"; do
  p="${c#*|}"
  [ -d "$p" ] || { echo "FAIL missing checkpoint: $p"; exit 1; }
done
echo "all 5 checkpoints present"

launch() {
  local name="$1" model="$2" gpu="$3"
  local d="$OUTROOT/$name"
  mkdir -p "$d/logs"
  ssh an12 "cd '$ROOT' && source .venv/bin/activate && (nohup env PYTHONUNBUFFERED=1 PYTHONHASHSEED=0 \
    TRANSFORMERS_OFFLINE=1 HF_HOME='$ROOT/artifacts/hf_home' CUDA_VISIBLE_DEVICES=$gpu \
    python scripts/eval_qwen_vl_fliptrack.py --model-path '$model' --manifest '$MANIFEST' \
    --output '$d/predictions.jsonl' --metrics-output '$d/metrics.json' \
    --num-shards 1 --shard-index 0 --image-mode real --image-cache-dir '$d/img_cache' \
    --seed 0 --noise-seed 0 --max-new-tokens 32 > '$d/logs/cell.log' 2>&1 < /dev/null & echo \$! > '$d/logs/pid')"
  echo "launched $name on an12:gpu$gpu"
}

i=0
for c in "${CELLS[@]}"; do
  name="${c%%|*}"; model="${c#*|}"
  gpu=$((4 + i % 4))
  if [ $i -ge 4 ]; then
    # wait for a slot: the first cell must finish before reusing gpu4
    while ssh an12 "kill -0 \$(cat '$OUTROOT/base/logs/pid') 2>/dev/null"; do sleep 20; done
  fi
  launch "$name" "$model" "$gpu"
  i=$((i+1))
  sleep 3
done

echo "OUTROOT=$OUTROOT"
echo "$OUTROOT" > tmp/b1_premise_probe.txt
