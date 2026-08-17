#!/usr/bin/env bash
set -uo pipefail
if [[ "$(hostname)" != "ln207" ]]; then echo "WRONG_NODE $(hostname)"; exit 9; fi
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
echo "host=$(hostname)"
git -c http.proxy=http://127.0.0.1:7890 push origin agent/gate2-recovery
echo "push_branch_rc=$?"
git -c http.proxy=http://127.0.0.1:7890 push origin agent/gate2-recovery:master
echo "push_master_rc=$?"
git -c http.proxy=http://127.0.0.1:7890 ls-remote origin agent/gate2-recovery master
