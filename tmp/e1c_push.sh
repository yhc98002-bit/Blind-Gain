#!/usr/bin/env bash
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT"
export https_proxy=http://127.0.0.1:7890
export http_proxy=http://127.0.0.1:7890

push_with_retry() {
  local REFSPEC="$1"
  local OUT
  for attempt in $(seq 1 12); do
    OUT="$(git push origin "${REFSPEC}" 2>&1)"
    if [[ $? -eq 0 ]] && ! grep -qiE "503|rejected|fatal" <<<"${OUT}"; then
      echo "PUSH OK ${REFSPEC} (attempt ${attempt})"
      return 0
    fi
    echo "attempt ${attempt} failed for ${REFSPEC}: $(head -2 <<<"${OUT}" | tr '\n' ' ')"
    sleep 5
  done
  echo "PUSH FAILED ${REFSPEC} after 12 attempts"
  return 1
}

echo "### hostname: $(hostname)"
push_with_retry "agent/gate2-recovery:agent/gate2-recovery"; RC1=$?
push_with_retry "agent/gate2-recovery:master"; RC2=$?
echo "### remote heads"
git ls-remote origin agent/gate2-recovery master 2>&1
echo "### local head"
git rev-parse HEAD
exit $(( RC1 + RC2 ))
