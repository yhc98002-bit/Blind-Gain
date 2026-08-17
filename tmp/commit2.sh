#!/usr/bin/env bash
set -euo pipefail
export PATH=$HOME/.local/bin:$PATH
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
echo "=== branch tracking ==="
git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>&1 || echo "no upstream"
git log --oneline -1 origin/main 2>&1 || echo "no origin/main ref"
git log --oneline -1 origin/agent/gate2-recovery 2>&1 || echo "no origin branch ref"
echo "=== is HEAD an ancestor-descendant of origin/main? ==="
git merge-base --is-ancestor origin/main HEAD 2>/dev/null && echo "origin/main is ancestor of HEAD (fast-forwardable)" || echo "NOT fast-forwardable"
