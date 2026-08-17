#!/bin/bash
set -uo pipefail
R=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$R"
echo "HOST: $(hostname)"
PROXY="http://127.0.0.1:7890"
echo "=== push agent/gate2-recovery ==="
git -c http.proxy=$PROXY push origin agent/gate2-recovery 2>&1 | tail -5
echo "=== fast-forward master to agent/gate2-recovery and push ==="
git -c http.proxy=$PROXY push origin agent/gate2-recovery:master 2>&1 | tail -5
echo "=== remote state ==="
git -c http.proxy=$PROXY ls-remote origin agent/gate2-recovery master 2>&1 | tail -5
git rev-parse HEAD
