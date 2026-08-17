#!/usr/bin/env bash
set -euo pipefail
export PATH=$HOME/.local/bin:$PATH
R=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$R"
BK="$R/tmp/m7_config_backup_pre_seedscope"
rm -rf "$BK"; mkdir -p "$BK"
cp -p configs/train/m7_virl_*_3b.yaml "$BK"/
cp -p reports/m7_arm_configs_v1.json "$BK"/
echo "backed up: $(ls -1 "$BK" | wc -l) files"
rm -f configs/train/m7_virl_*_3b.yaml
echo "=== running builder ==="
"$R/.venv/bin/python" scripts/build_m7_configs.py
