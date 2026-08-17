#!/usr/bin/env bash
set -euo pipefail
export PATH=$HOME/.local/bin:$PATH
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
echo "=== branch / remote ==="
git rev-parse --abbrev-ref HEAD
git remote -v | head -4
echo "=== staging ==="
git add scripts/build_m7_configs.py reports/m7_arm_configs_v1.json configs/train/m7_virl_a2_gray_seed1_3b.yaml configs/train/m7_virl_a2_gray_seed2_3b.yaml configs/train/m7_virl_a2b_noimage_seed1_3b.yaml configs/train/m7_virl_a2b_noimage_seed2_3b.yaml configs/train/m7_virl_a3_caption_seed1_3b.yaml configs/train/m7_virl_a3_caption_seed2_3b.yaml configs/train/m7_virl_a1_real_seed1_3b.yaml configs/train/m7_virl_a1_real_seed2_3b.yaml
git status --short -- scripts/build_m7_configs.py reports/m7_arm_configs_v1.json configs/train/
echo "=== diffstat (staged) ==="
git diff --cached --stat
