#!/usr/bin/env bash
S=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/tmp/push_m7_fixes.sh
if [ "$(hostname)" = "ln207" ]; then
  bash "$S"
else
  echo "landed on $(hostname); hopping to ln207 for the proxy"
  ssh -o ConnectTimeout=25 ln207 "bash $S"
fi
