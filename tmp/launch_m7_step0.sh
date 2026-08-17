#!/usr/bin/env bash
# R3 / M7 step-0 base evaluation over the frozen held-out split, one condition per GPU.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"

export VIRL_MANIFEST=data/virl39k_m7_heldout_v3_eval.jsonl
export VIRL_SAMPLE_SPEC=reports/virl39k_m7_heldout_v3_sample.json
export VIRL_SPLITS=train
export VIRL_CAPTION_SHARDS=data/virl39k_caption_store_3b_main_v2.jsonl
export VIRL_MODEL_PATH=artifacts/models/Qwen/Qwen2.5-VL-3B-Instruct
export VIRL_RUN_PREFIX=m7_step0_heldout
export VIRL_JOB_TYPE=r3_m7_step0_heldout_base_eval

OUT=tmp/m7_step0_run_dirs.txt
: > "$OUT"
gpu=4
for cond in real gray none caption; do
  echo "=== launching ${cond} on an29 gpu${gpu} ==="
  d=$(bash scripts/launch_virl39k_blind_v1_condition.sh an29 "$gpu" "$cond" base)
  rc=$?
  echo "exit=${rc} run_dir=${d}"
  if [[ $rc -eq 0 && -n "$d" ]]; then echo "$d" >> "$OUT"; fi
  gpu=$((gpu+1))
done
echo "=== run dirs ==="
cat "$OUT"
