#!/usr/bin/env bash
export PATH=$HOME/.local/bin:$PATH
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
echo "=== jq available: $(command -v jq) ==="
echo "=== free bytes on repo fs ==="
df --output=avail -B1 . | tail -1
echo "=== invoking launcher: a2_gray seed 1 an12 4,5,6,7 ==="
set +e
bash scripts/launch_m7_virl_arm.sh a2_gray 1 an12 4,5,6,7
RC=$?
set -e
echo "=== launcher exit code: ${RC} ==="
