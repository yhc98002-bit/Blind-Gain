#!/usr/bin/env bash
# Detached push driver: retries hard against the intermittently-503 proxy.
export PATH=$HOME/.local/bin:$PATH
export https_proxy=http://127.0.0.1:7890
export http_proxy=http://127.0.0.1:7890
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
LOG="$ROOT/logs/m7_fix_push.log"
mkdir -p "$ROOT/logs"

{
  echo "=== push driver start $(date -u +%Y-%m-%dT%H:%M:%SZ) host=$(hostname)"
  HEAD_SHA=$(git rev-parse HEAD)
  echo "LOCAL_HEAD=$HEAD_SHA"
  for br in agent/gate2-recovery master; do
    ok=0
    for attempt in $(seq 1 12); do
      echo "--- $br attempt $attempt $(date -u +%H:%M:%SZ)"
      timeout 120 git push origin "HEAD:refs/heads/$br" 2>&1 | sed 's/^/    /'
      remote_sha=$(timeout 90 git ls-remote origin "refs/heads/$br" 2>/dev/null | awk '{print $1}')
      echo "    remote=$remote_sha"
      if [ "$remote_sha" = "$HEAD_SHA" ]; then echo "    OK $br up to date"; ok=1; break; fi
      sleep 8
    done
    [ "$ok" = 1 ] || echo "    FAILED $br after 12 attempts"
  done
  echo "=== final:"
  timeout 90 git ls-remote origin refs/heads/agent/gate2-recovery refs/heads/master 2>&1 | sed 's/^/    /'
  echo "=== push driver done $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} >> "$LOG" 2>&1
