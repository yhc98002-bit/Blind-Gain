#!/bin/bash
# Push agent/gate2-recovery + mirror to master and main, via ln207 proxy.
set -u
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain || exit 9
echo "push node: $(hostname)"
ok=1
for ref in "agent/gate2-recovery" "agent/gate2-recovery:master" "agent/gate2-recovery:main"; do
  pushed=0
  for try in 1 2 3 4 5; do
    if git -c http.proxy=http://127.0.0.1:7890 push origin "$ref" 2>&1; then
      echo "PUSHED $ref (try $try)"
      pushed=1
      break
    fi
    echo "retry $try failed for $ref"
    sleep 5
  done
  [ "$pushed" = 1 ] || { echo "FAILED $ref"; ok=0; }
done
[ "$ok" = 1 ] && echo ALL_PUSHED || echo PUSH_INCOMPLETE
