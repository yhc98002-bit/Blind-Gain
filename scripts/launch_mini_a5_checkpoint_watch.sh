#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <mini-a5-training-run-dir>" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
TRAINING_RUN="${1%/}"
[[ -s "${TRAINING_RUN}/run_manifest.json" ]] || { echo "training manifest absent: ${TRAINING_RUN}" >&2; exit 2; }

RUN_ROOT="$(jq -er '.checkpoint_path' "${TRAINING_RUN}/run_manifest.json")"
NODE="$(jq -er '.node' "${TRAINING_RUN}/run_manifest.json")"
MODE="$(jq -er '.mini_a5_mode // .mode // empty' "${TRAINING_RUN}/run_manifest.json")"
[[ -n "${MODE}" ]] || MODE="$(basename "${TRAINING_RUN}" | grep -oE 'cp|member' | head -1)"
[[ "${MODE}" =~ ^(cp|member)$ ]] || { echo "cannot determine Mini-A5 mode for ${TRAINING_RUN}" >&2; exit 2; }
LABEL="mini_a5_${MODE}_main"
ARCHIVE_ROOT="/tmp/blindgain_checkpoint_archive/$(basename "${TRAINING_RUN}")"

if pgrep -af "[w]atch_mini_a5_checkpoints.py" | grep -q "$(basename "${TRAINING_RUN}")"; then
  echo "a watcher for this Mini-A5 run is already active" >&2
  exit 73
fi

EXPECTED_HASH="$(PYTHONPATH=. .venv/bin/python -c \
  'from scripts.watch_mini_a5_checkpoints import mini_a5_code_bundle_hash; print(mini_a5_code_bundle_hash())')"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="mini_a5_checkpoint_watch_${MODE}_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"

COMMAND="PYTHONPATH=. .venv/bin/python scripts/watch_mini_a5_checkpoints.py --run-root ${RUN_ROOT} --archive-root ${ARCHIVE_ROOT} --run-manifest ${TRAINING_RUN}/run_manifest.json --node ${NODE} --run-label ${LABEL} --expected-code-hash ${EXPECTED_HASH}"
jq -n \
  --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg command "${COMMAND}" --arg start "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg parent "${TRAINING_RUN}" --arg node_arg "${NODE}" --arg hash "${EXPECTED_HASH}" \
  --arg log "${LOG}" --arg archive "${ARCHIVE_ROOT}" \
  '{schema_version:"blind-gains.run-manifest.v1",run_id:$run_id,
    job_type:"mini_a5_checkpoint_retention_watch",node:"login",compute_node:$node_arg,
    gpu_ids:[],git_hash:$git_hash,parent_training_run:$parent,
    archive_root:$archive,expected_code_hash:$hash,command:$command,
    start_time_utc:$start,end_time_utc:null,status:"running",
    stdout_stderr_log:$log,
    placement_justification:"CPU-only merge and off-quota raw relocation for every Mini-A5 save boundary; registered endpoints stay sealed until both arms complete."}' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${RUN_DIR}/pids/login.pid"
sleep 2
kill -0 "$(cat "${RUN_DIR}/pids/login.pid")" 2>/dev/null || {
  echo "Mini-A5 checkpoint watcher exited during startup" >&2
  exit 1
}
printf '%s\n' "${RUN_DIR}"
