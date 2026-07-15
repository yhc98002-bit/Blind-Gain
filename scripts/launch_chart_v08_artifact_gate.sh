#!/usr/bin/env bash
set -euo pipefail

if [[ $# -gt 2 ]]; then
  echo "usage: $0 [an12|an29] [gpu-id]" >&2
  exit 2
fi

NODE="${1:-an12}"
GPU="${2:-4}"
[[ "${NODE}" == "an12" || "${NODE}" == "an29" ]] || {
  echo "artifact gate may target only permanent nodes an12 or an29" >&2
  exit 2
}
[[ "${GPU}" =~ ^[0-7]$ ]] || { echo "gpu-id must be in [0, 7]" >&2; exit 2; }

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
RELEASE_DIR="data/fliptrack_chart_v08_calibration_v1_human_release"
KEY_FILE=".private/fliptrack_chart_v08_calibration_v1_human_key.jsonl"
DINO_MODEL="facebook/dinov2-small"
DINO_REVISION_FILE="artifacts/hf_home/hub/models--facebook--dinov2-small/refs/main"
SEED=20260710

[[ -f "${RELEASE_DIR}/manifest.jsonl" ]] || { echo "release manifest absent" >&2; exit 2; }
[[ -f "${KEY_FILE}" ]] || { echo "private answer key absent" >&2; exit 2; }
[[ -f "${DINO_REVISION_FILE}" ]] || { echo "local DINOv2 revision absent" >&2; exit 2; }

CRITICAL_FILES=(
  scripts/launch_chart_v08_artifact_gate.sh
  src/fliptrack/artifact_attackers.py
  scripts/finalize_run_manifest.py
)
git diff --quiet HEAD -- "${CRITICAL_FILES[@]}" || {
  echo "artifact-gate code differs from HEAD" >&2
  exit 2
}
for FILE in "${CRITICAL_FILES[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || {
    echo "untracked critical file: ${FILE}" >&2
    exit 2
  }
done

LOCK_PATH="/tmp/blind_gains_${NODE}_chart_v08_artifact_gate_launch.lock"
exec 9>"${LOCK_PATH}"
if ! flock -n 9; then
  echo "another chart-v08 artifact-gate preflight is active on ${NODE}" >&2
  exit 75
fi
# shellcheck disable=SC2029
if [[ -n "$(ssh "${NODE}" "nvidia-smi -i '${GPU}' --query-compute-apps=pid --format=csv,noheader,nounits")" ]]; then
  echo "artifact-gate GPU ${GPU} on ${NODE} is occupied" >&2
  exit 75
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="chart_v08_artifact_gate_${NODE}_gpu${GPU}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
LOG_PATH="${RUN_DIR}/logs/${NODE}_gpu${GPU}.log"
PID_PATH="${RUN_DIR}/pids/${NODE}_gpu${GPU}.pid"
MANIFEST_PATH="${RUN_DIR}/run_manifest.json"
OUTPUT="${RUN_DIR}/metrics.json"
[[ ! -e "${RUN_DIR}" ]] || { echo "refusing to overwrite run directory" >&2; exit 73; }
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"

COMMAND="python -m src.fliptrack.artifact_attackers --release-dir ${RELEASE_DIR} --key-file ${KEY_FILE} --output ${OUTPUT} --dinov2-model ${DINO_MODEL} --batch-size 32 --n-splits 5 --n-bootstrap 1000 --seed ${SEED}"
CONFIG_HASH="$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')"
DATA_HASH="$( { sha256sum "${RELEASE_DIR}/manifest.jsonl"; sha256sum "${KEY_FILE}"; } | sha256sum | awk '{print $1}')"
DINO_REVISION="$(tr -d '\n' < "${DINO_REVISION_FILE}")"

jq -n \
  --arg run_id "${RUN_ID}" --arg node "${NODE}" --argjson gpu "${GPU}" \
  --arg git_hash "$(git rev-parse HEAD)" --arg config_hash "${CONFIG_HASH}" \
  --arg data_manifest "${RELEASE_DIR}/manifest.jsonl + private key" \
  --arg data_hash "${DATA_HASH}" --arg model_revision "${DINO_MODEL}@${DINO_REVISION}" \
  --arg command "${COMMAND}" --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" --arg log "${LOG_PATH}" --argjson seed "${SEED}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m12_chart_v08_artifact_gate",
    node: $node,
    gpu_ids: [$gpu],
    gpu_allocation: [$gpu],
    tensor_parallel_width: 1,
    replica_count: 1,
    placement_justification: "One local DINOv2 feature extractor plus CPU probes fit on one GPU; wider TP or cross-node placement provides no scientific benefit.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $data_manifest,
    data_manifest_hash: $data_hash,
    model_revision: $model_revision,
    seed: $seed,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    expected_artifacts: [$output],
    scientific_gate_decision: null,
    deviations: []
  }' > "${MANIFEST_PATH}"

# shellcheck disable=SC2029
ssh "${NODE}" "cd '${ROOT}' && source .venv/bin/activate && (nohup bash -lc 'set +e; env PYTHONUNBUFFERED=1 TRANSFORMERS_OFFLINE=1 HF_HOME=${ROOT}/artifacts/hf_home CUDA_VISIBLE_DEVICES=${GPU} PYTHONPATH=. ${COMMAND}; code=\$?; PYTHONPATH=. python scripts/finalize_run_manifest.py ${MANIFEST_PATH} \${code}; exit \${code}' > '${LOG_PATH}' 2>&1 < /dev/null & echo \$! > '${PID_PATH}')"
printf '%s\n' "${RUN_DIR}"
