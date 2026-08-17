#!/bin/bash
export PATH="$HOME/.local/bin:$PATH"
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain || exit 2
h=$(hostname)
echo "HOST=$h"
if [ "$h" != "ln207" ]; then
  echo "WRONG_NODE"
  exit 3
fi
ok=0
for i in 1 2 3 4 5 6; do
  if timeout 100 git -c http.proxy=http://127.0.0.1:7890 push -q origin agent/gate2-recovery \
     && timeout 100 git -c http.proxy=http://127.0.0.1:7890 push -q origin agent/gate2-recovery:master \
     && timeout 100 git -c http.proxy=http://127.0.0.1:7890 push -q origin agent/gate2-recovery:main; then
    ok=1
    break
  fi
  echo "ATTEMPT_${i}_FAILED"
  sleep 12
done
if [ "$ok" = "1" ]; then
  echo "PUSH_OK"
  exit 0
else
  echo "PUSH_FAIL"
  exit 4
fi
