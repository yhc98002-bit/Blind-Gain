#!/usr/bin/env bash
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain || exit 1
git -c http.proxy=http://127.0.0.1:7890 push origin agent/gate2-recovery agent/gate2-recovery:master agent/gate2-recovery:main 2>&1
echo "push_exit=$?"
