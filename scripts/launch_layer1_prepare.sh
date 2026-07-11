#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 6 ]]; then
  echo "Usage: $0 DATASET SOURCE OUTPUT IMAGE_DIR METADATA_OUTPUT RUN_TAG" >&2
  exit 2
fi

DATASET="$1"
SOURCE="$2"
OUTPUT="$3"
IMAGE_DIR="$4"
METADATA_OUTPUT="$5"
RUN_TAG="$6"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "${DATASET}" != "mathvista" && "${DATASET}" != "mathverse" && "${DATASET}" != "mmmu" && "${DATASET}" != "blink" && "${DATASET}" != "mmvp" && "${DATASET}" != "hallusion" ]]; then
  echo "DATASET must be mathvista, mathverse, mmmu, blink, mmvp, or hallusion" >&2
  exit 2
fi
if [[ ! "${RUN_TAG}" =~ ^[a-z0-9][a-z0-9_-]*$ ]]; then
  echo "RUN_TAG contains unsupported characters" >&2
  exit 2
fi
if [[ ! -e "${SOURCE}" ]]; then
  echo "SOURCE does not exist: ${SOURCE}" >&2
  exit 2
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="prepare_layer1_${RUN_TAG}_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
SESSION="${RUN_ID//-/_}"
EXTRA_ARGS=""
if [[ "${DATASET}" == "mathvista" ]]; then
  EXTRA_ARGS="--drop-ambiguous-mathvista-choices"
fi
COMMAND="artifacts/envs/vlmevalkit/bin/python scripts/prepare_layer1_vlmeval.py --dataset ${DATASET} --source '${SOURCE}' --output '${OUTPUT}' --image-dir '${IMAGE_DIR}' --metadata-output '${METADATA_OUTPUT}' ${EXTRA_ARGS}"

cd "${ROOT}"
if [[ -e "${OUTPUT}" || -e "${METADATA_OUTPUT}" ]]; then
  echo "refusing to overwrite output or metadata" >&2
  exit 2
fi
if [[ -f "${SOURCE}" ]]; then
  SOURCE_HASH="$(sha256sum "${SOURCE}" | awk '{print $1}')"
elif [[ "${DATASET}" == "mmmu" ]]; then
  SOURCE_HASH="$({
    find "${SOURCE}" -mindepth 2 -maxdepth 2 -type f \
      \( -name 'dev-*.parquet' -o -name 'validation-*.parquet' \) -print0 \
      | sort -z | xargs -0 sha256sum
    test ! -f experiments/manifests/mmmu_hf_lfs_repair_v1.json \
      || sha256sum experiments/manifests/mmmu_hf_lfs_repair_v1.json
  } | sha256sum | awk '{print $1}')"
else
  SOURCE_HASH="$(find "${SOURCE}" -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')"
fi
mkdir -p "${RUN_DIR}/logs"
jq -n \
  --arg run_id "${RUN_ID}" \
  --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')" \
  --arg data_manifest "${SOURCE}" \
  --arg data_manifest_hash "${SOURCE_HASH}" \
  --arg command "${COMMAND}" \
  --arg start_time_utc "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg output "${OUTPUT}" \
  --arg image_dir "${IMAGE_DIR}" \
  --arg metadata "${METADATA_OUTPUT}" \
  '{
    run_id: $run_id,
    job_type: "layer1_dataset_adapter",
    node: "login",
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only dataset adaptation on the login node.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_hash: $config_hash,
    data_manifest: $data_manifest,
    data_manifest_hash: $data_manifest_hash,
    command: $command,
    start_time_utc: $start_time_utc,
    end_time_utc: null,
    status: "running",
    expected_artifacts: [$output, $image_dir, $metadata]
  }' > "${MANIFEST}"

tmux new-session -d -s "${SESSION}" \
  "${ROOT}/.venv/bin/python '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST}' '${ROOT}/${LOG}'"
echo "${RUN_DIR}"
echo "tmux_session=${SESSION} log=${LOG}"
