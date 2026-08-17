#!/bin/bash
export PATH=$HOME/.local/bin:$PATH
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain || exit 9
echo "launch_host=$(hostname) utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) git=$(git rev-parse HEAD)"
echo "--- invoking launcher: a3_caption seed1 an29 4,5,6,7"
./scripts/launch_m7_virl_arm.sh a3_caption 1 an29 4,5,6,7
RC=$?
echo "--- launcher exit code: $RC"
exit $RC
