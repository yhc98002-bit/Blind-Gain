#!/bin/bash
export PATH=$HOME/.local/bin:$PATH
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
echo "=== cp_grpo_reward.py (full) ==="
cat src/rewards/cp_grpo_reward.py
echo "=== cp_grouping.py (head 120) ==="
head -120 src/train/cp_grouping.py
echo "=== launch_manifest_blind_solvability.sh ==="
cat scripts/launch_manifest_blind_solvability.sh
