#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 8 || $# -gt 9 ]]; then
  echo "usage: $0 NODE GLOBAL_STEP SOURCE_RUN CHECKPOINT R19_MANIFEST RUN_DIR NUM_SHARDS 'GPU_LIST' [real|gray|noise]" >&2
  exit 2
fi

NODE="$1"
GLOBAL_STEP="$2"
SOURCE_RUN="$3"
CHECKPOINT="$4"
R19_MANIFEST="$5"
RUN_DIR="$6"
NUM_SHARDS="$7"
GPU_LIST="$8"
IMAGE_MODE="${9:-real}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT}"
for path in docs/registered_extensions_v1.md reports/registered_extensions_authorization_v4.json \
  scripts/launch_fliptrack_eval_shards.sh scripts/launch_m5_fliptrack_checkpoint_eval.sh; do
  git ls-files --error-unmatch "${path}" >/dev/null 2>&1 || {
    echo "M5 FlipTrack contract file is untracked: ${path}" >&2; exit 3;
  }
done
git diff --quiet HEAD -- docs/registered_extensions_v1.md \
  reports/registered_extensions_authorization_v4.json scripts/launch_fliptrack_eval_shards.sh \
  scripts/launch_m5_fliptrack_checkpoint_eval.sh || {
  echo "M5 FlipTrack contract differs from HEAD" >&2; exit 3;
}
jq -e '(.status=="authorized") and (.authorization.m5=="authorized_after_restore_integrity_pass") and
  ([.checks[]] | all)' reports/registered_extensions_authorization_v4.json >/dev/null || {
  echo "M5 authorization artifact is invalid" >&2; exit 3;
}

BLIND_GAINS_M5_SOURCE_RUN="${SOURCE_RUN}" \
BLIND_GAINS_M5_GLOBAL_STEP="${GLOBAL_STEP}" \
BLIND_GAINS_EVAL_SEED=0 \
  bash scripts/launch_fliptrack_eval_shards.sh "${NODE}" 0 "${NUM_SHARDS}" \
    "${CHECKPOINT}" "${R19_MANIFEST}" "${RUN_DIR}" 32 "${GPU_LIST}" "${IMAGE_MODE}"
