#!/bin/bash
set -x
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
git -c http.proxy=http://127.0.0.1:7890 push origin agent/gate2-recovery
git -c http.proxy=http://127.0.0.1:7890 push origin agent/gate2-recovery:master
git -c http.proxy=http://127.0.0.1:7890 push origin agent/gate2-recovery:main
