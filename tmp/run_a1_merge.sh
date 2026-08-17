#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT"
mkdir -p tmp
exec bash scripts/launch_easyr1_checkpoint_merge.sh \
  an29 \
  checkpoints/m7/m7_virl_a1_real_seed1/global_step_100/actor \
  m7_a1_real_seed1_step100
