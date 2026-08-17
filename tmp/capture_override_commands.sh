#!/usr/bin/env bash
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"

.venv/bin/python tmp/instrument.py scripts/launch_virl39k_blind_v1_condition.sh tmp/_instr_ovr.sh >&2
chmod +x tmp/_instr_ovr.sh

export VIRL_MANIFEST=data/virl39k_m7_heldout_v3_eval.jsonl
export VIRL_SAMPLE_SPEC=reports/virl39k_m7_heldout_v3_sample.json
export VIRL_SPLITS=train
export VIRL_CAPTION_SHARDS=data/virl39k_caption_store_3b_main_v2.jsonl
export VIRL_RUN_PREFIX=m7_step0_heldout
export VIRL_JOB_TYPE=r3_m7_step0_heldout_base_eval

gpu=4
for cond in real gray none caption; do
  printf '### condition=%s gpu=%s\n' "$cond" "$gpu"
  bash tmp/_instr_ovr.sh an29 "$gpu" "$cond" base
  printf 'exit=%s\n' "$?"
  gpu=$((gpu+1))
done
rm -f tmp/_instr_ovr.sh
