#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT}"

SOURCE_MANIFEST="${1:-data/fliptrack_v02_source_manifest.jsonl}"
RELEASE_DIR="${2:-data/fliptrack_v02}"
KEY_FILE="${3:-.private/fliptrack_v02_key.jsonl}"
SALT_FILE="${4:-.private/fliptrack_v02_salt.bin}"
LINT_REPORT="${5:-reports/fliptrack_v02_lint.json}"
RUN_ID="fliptrack_v02_package_$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="experiments/runs/${RUN_ID}"
LOG_PATH="${RUN_DIR}/logs/login.log"
PID_PATH="${RUN_DIR}/pids/login.pid"
MANIFEST_PATH="${RUN_DIR}/run_manifest.json"
COMMAND="python -m src.fliptrack.package_v02 --source-manifest ${SOURCE_MANIFEST} --release-dir ${RELEASE_DIR} --key-file ${KEY_FILE} --salt-file ${SALT_FILE} && python -m src.fliptrack.manifest_linter --release-dir ${RELEASE_DIR} --key-file ${KEY_FILE} --output ${LINT_REPORT}"

mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids" .private
GIT_HASH="$(git rev-parse HEAD)"
CONFIG_HASH="$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')"
DATA_HASH="$(sha256sum "${SOURCE_MANIFEST}" | awk '{print $1}')"

cat > "${MANIFEST_PATH}" <<JSON
{
  "run_id": "${RUN_ID}",
  "job_type": "p1_4_fliptrack_v02_package_and_lint",
  "node": "$(hostname)",
  "gpu_allocation": [],
  "git_hash": "${GIT_HASH}",
  "config_hash": "${CONFIG_HASH}",
  "seed": null,
  "data_manifest": "${SOURCE_MANIFEST}",
  "data_manifest_hash": "${DATA_HASH}",
  "command": "${COMMAND}",
  "start_time_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "end_time_utc": null,
  "status": "running",
  "expected_artifacts": ["${RELEASE_DIR}/manifest.jsonl", "${KEY_FILE}", "${LINT_REPORT}"]
}
JSON

tmux new-session -d -s "${RUN_ID}" \
  "${ROOT}/.venv/bin/python '${ROOT}/scripts/run_manifest_job.py' '${ROOT}/${MANIFEST_PATH}' '${ROOT}/${LOG_PATH}'"
tmux list-panes -t "${RUN_ID}" -F '#{pane_pid}' > "${PID_PATH}"
printf '%s\n' "${RUN_ID}" > "${RUN_DIR}/tmux_session"
printf '%s\n' "${RUN_DIR}" > experiments/runs/latest_fliptrack_v02_package_run.txt
echo "${RUN_DIR}"
echo "pid_file=${PID_PATH}"
echo "log=${LOG_PATH}"
