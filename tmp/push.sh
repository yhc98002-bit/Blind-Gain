#!/bin/bash
export https_proxy=http://127.0.0.1:7890
export http_proxy=http://127.0.0.1:7890
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain || exit 9
echo "push_host=$(hostname)"
BR=$(git branch --show-current)
SHA=$(git rev-parse HEAD)
echo "branch=$BR head=$SHA"
echo "NOTE: not committing anything; another session has in-flight edits to"
echo "      src/eval/layer1_blind.py and tests/test_layer1_blind.py. Pushing existing commits only."
git merge-base --is-ancestor origin/master HEAD && echo "origin/master is ancestor of HEAD -> fast-forward safe" || { echo "NOT a fast-forward; refusing"; exit 8; }
for TARGET in "$BR" master; do
  echo "=== pushing HEAD -> $TARGET"
  for i in $(seq 1 12); do
    if git push origin "HEAD:refs/heads/$TARGET" 2>&1 | tee /tmp/pushout.$$ | tail -3; then
      if grep -qE "Everything up-to-date|->" /tmp/pushout.$$; then echo "  OK on attempt $i"; break; fi
    fi
    echo "  attempt $i failed, retrying"; sleep 6
  done
  rm -f /tmp/pushout.$$
done
echo "=== final remote state ==="
git ls-remote origin refs/heads/master refs/heads/agent/gate2-recovery
