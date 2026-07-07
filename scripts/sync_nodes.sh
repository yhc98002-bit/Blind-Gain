#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain}"

for node in an12 an29; do
  echo "== $node =="
  ssh "$node" "cd '$ROOT' && pwd && git status --short --branch 2>/dev/null || true"
done

