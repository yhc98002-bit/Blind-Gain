#!/usr/bin/env bash
# Mini-A5 secondary endpoint 1 (addendum section 6.1): candidate-evidence ranking
# for both Mini-A5 arms at global_step_120, condition 'real'.
# Invocation shape copied verbatim from the completed prior run
#   experiments/runs/d1_visual_evidence_a1_seed2_step100_real_an29_gpu4_x5_ranking_matrix_queue_login_20260725T021220Z
# (its worker.sh + run_manifest.json.command), with RANKING_CONFIG / RANKING_REGISTRATION
# pointed at the Mini-A5 config and the binding Mini-A5 endpoint readout registration.
set -euo pipefail
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
export PATH="$HOME/.local/bin:$PATH"   # jq is not on the non-interactive ssh PATH

export RANKING_CONFIG=configs/eval/mini_a5_visual_evidence_ranking_v1.json
export RANKING_REGISTRATION=docs/registered_mini_a5_endpoint_readout_v1.md

TS="$(date -u +%Y%m%dT%H%M%SZ)"
echo "RUN_TS=${TS}"
echo "GIT_HEAD=$(git rev-parse HEAD)"

# Record the working-tree state verbatim at launch (F8 plan recommended action).
git status --porcelain > "reports/mini_a5_s1_ranking_git_status_at_launch_${TS}.txt" || true

CP_DIR="experiments/runs/mini_a5_s1_ranking_cp_step120_real_an29_gpu4_${TS}"
MB_DIR="experiments/runs/mini_a5_s1_ranking_member_step120_real_an29_gpu5_${TS}"

bash scripts/launch_visual_evidence_ranking_cell.sh an29 4 mini_a5_cp_step120     real "${CP_DIR}"
bash scripts/launch_visual_evidence_ranking_cell.sh an29 5 mini_a5_member_step120 real "${MB_DIR}"

echo "CP_DIR=${CP_DIR}"
echo "MB_DIR=${MB_DIR}"
