#!/usr/bin/env bash
# Login-node loop: every 60 s, run the on-node translator so the LH2 chain's
# plain-text claims (rewritten at each segment boundary) stay guard-legible.
# 5-day deadline covers the LH2 stage.
set -u
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
DEADLINE=$(( $(date -u +%s) + 5*24*3600 ))
while :; do
  [ "$(date -u +%s)" -gt "$DEADLINE" ] && exit 0
  ssh -o BatchMode=yes -o ConnectTimeout=15 an12 "bash $ROOT/scripts/lh2_claim_translate_local.sh" 2>/dev/null
  sleep 60
done
