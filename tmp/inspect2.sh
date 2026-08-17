#!/usr/bin/env bash
export PATH=$HOME/.local/bin:$PATH
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
echo "=== arm1 config (a1_real_seed1) ==="
cat configs/train/m7_virl_a1_real_seed1_3b.yaml
echo
echo "=== template trainer block a1 ==="
grep -n -A30 '^trainer:' configs/train/mech_a1_real_seed3_3b_geo3k.yaml
echo
echo "=== save_model_only anywhere in configs/train ==="
grep -rn 'save_model_only' configs/train/ | head -20
echo "=== save_model_only in EasyR1 source ==="
grep -rn 'save_model_only' artifacts/repos/EasyR1/verl/ | head -20
