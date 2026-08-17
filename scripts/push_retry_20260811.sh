#!/usr/bin/env bash
# Retry the three-ref push until the GitHub proxy window opens.
# The mihomo proxy at 127.0.0.1:7890 intermittently returns 503/TLS errors;
# this loop just waits it out. Exits as soon as all three refs match HEAD.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
LOG="$ROOT/logs/push_retry_20260811.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
export https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890

TARGET=$(git rev-parse HEAD)
log "=== push retry armed on $(hostname) for $TARGET ==="

for attempt in $(seq 1 240); do
  ok=1
  for ref in agent/gate2-recovery master main; do
    remote=$(timeout 60 git ls-remote origin "refs/heads/$ref" 2>/dev/null | awk '{print $1}')
    if [[ "$remote" == "$TARGET" ]]; then
      continue
    fi
    out=$(timeout 120 git push origin "HEAD:$ref" 2>&1 | tail -1)
    if [[ "$out" == *"fatal"* || "$out" == *"error"* ]]; then
      ok=0
      [[ $((attempt % 10)) -eq 1 ]] && log "attempt $attempt $ref: $out"
    else
      log "attempt $attempt $ref: PUSHED ($out)"
    fi
  done
  if [[ "$ok" == "1" ]]; then
    all=1
    for ref in agent/gate2-recovery master main; do
      remote=$(timeout 60 git ls-remote origin "refs/heads/$ref" 2>/dev/null | awk '{print $1}')
      [[ "$remote" == "$TARGET" ]] || all=0
    done
    if [[ "$all" == "1" ]]; then
      log "*** ALL THREE REFS AT $TARGET — retry loop done (attempt $attempt) ***"
      exit 0
    fi
  fi
  sleep 60
done
log "*** push retry gave up after 240 attempts; HEAD $TARGET still unpushed on some ref ***"
