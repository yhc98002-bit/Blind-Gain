#!/bin/bash
# Push agent/gate2-recovery (and its :master mapping) via the ln207-local proxy.
set -u
if [ "$(hostname)" != "ln207" ]; then
  echo "NOT_LN207: $(hostname)"
  exit 42
fi
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
git -c http.proxy=http://127.0.0.1:7890 push origin agent/gate2-recovery agent/gate2-recovery:master 2>&1
echo "push_exit=$?"
