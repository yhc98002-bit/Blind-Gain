#!/usr/bin/env bash
# Push the M7 launcher fix commit. Must run on ln207 (proxy lives there).
export PATH=$HOME/.local/bin:$PATH
export https_proxy=http://127.0.0.1:7890
export http_proxy=http://127.0.0.1:7890
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1

echo "host=$(hostname)"
echo "HEAD=$(git rev-parse HEAD)  branch=$(git rev-parse --abbrev-ref HEAD)"

push_with_retry () {
  local refspec="$1"
  for attempt in $(seq 1 12); do
    echo "--- push $refspec attempt $attempt"
    if git push origin "$refspec" 2>&1 | sed 's/^/    /'; then
      # verify by comparing remote ref to local HEAD
      local remote_sha
      remote_sha=$(git ls-remote origin "${refspec##*:}" 2>/dev/null | awk '{print $1}')
      if [ "$remote_sha" = "$(git rev-parse HEAD)" ]; then
        echo "    OK: remote ${refspec##*:} == local HEAD ($remote_sha)"
        return 0
      fi
      echo "    push reported success but remote ref is '$remote_sha'; retrying"
    fi
    sleep 6
  done
  echo "    FAILED after 12 attempts: $refspec"
  return 1
}

RC=0
push_with_retry "HEAD:refs/heads/agent/gate2-recovery" || RC=1
push_with_retry "HEAD:refs/heads/master" || RC=1

echo
echo "===== final remote state ====="
git ls-remote origin refs/heads/agent/gate2-recovery refs/heads/master 2>&1 | sed 's/^/   /'
echo "local HEAD = $(git rev-parse HEAD)"
exit $RC
