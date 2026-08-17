#!/usr/bin/env bash
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
echo "host=$(hostname) branch=$(git rev-parse --abbrev-ref HEAD)"
git add scripts/launch_virl39k_blind_v1_condition.sh \
        scripts/build_m7_heldout_eval_manifest.py \
        reports/virl39k_m7_heldout_v3_sample.json || exit 1
git commit -F tmp/commit_msg_r3.txt
echo "commit rc=$?"
git log --oneline -1
git status --porcelain scripts/ reports/virl39k_m7_heldout_v3_sample.json
