#!/usr/bin/env bash
# Push the F8 secondaries commit to both remote branches.
# The git proxy lives on ln207 only; exit 78 if we landed elsewhere so the caller retries.
export PATH=$HOME/.local/bin:$PATH
export https_proxy=http://127.0.0.1:7890
export http_proxy=http://127.0.0.1:7890
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1

HOST=$(hostname)
echo "host=$HOST"
if [ "$HOST" != "ln207" ]; then
  echo "not ln207; no proxy here"
  exit 78
fi

LOCAL=$(git rev-parse HEAD)
echo "HEAD=$LOCAL branch=$(git rev-parse --abbrev-ref HEAD)"

push_with_retry () {
  local refspec="$1"
  local ref="${refspec##*:}"
  for attempt in $(seq 1 8); do
    echo "--- push $ref attempt $attempt"
    git push origin "$refspec" 2>&1 | sed 's/^/    /'
    local remote_sha
    remote_sha=$(git ls-remote origin "$ref" 2>/dev/null | awk '{print $1}')
    if [ "$remote_sha" = "$LOCAL" ]; then
      echo "    OK: remote $ref == local HEAD"
      return 0
    fi
    echo "    remote $ref is '$remote_sha'; retrying"
    sleep 6
  done
  echo "    FAILED: $ref"
  return 1
}

RC=0
push_with_retry "HEAD:refs/heads/agent/gate2-recovery" || RC=1
push_with_retry "HEAD:refs/heads/master" || RC=1

echo
echo "===== final remote state ====="
git ls-remote origin refs/heads/agent/gate2-recovery refs/heads/master 2>&1 | sed 's/^/   /'
echo "local HEAD = $LOCAL"
exit $RC
