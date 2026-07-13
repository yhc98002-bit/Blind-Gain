#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 4 ]]; then
  echo "usage: $0 <a1-run-dir> <a2-gray-run-dir> <a2b-noimage-run-dir> <a3-caption-run-dir>" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

if ! git diff --quiet HEAD -- \
  scripts/watch_m2_pilot_completion.py \
  scripts/launch_m2_completion_watchdog.sh; then
  echo "M2 watchdog code must be committed at HEAD before launch" >&2
  exit 2
fi
git ls-files --error-unmatch scripts/watch_m2_pilot_completion.py >/dev/null 2>&1 || {
  echo "M2 watchdog runtime is not tracked at HEAD" >&2
  exit 2
}
git ls-files --error-unmatch scripts/launch_m2_completion_watchdog.sh >/dev/null 2>&1 || {
  echo "M2 watchdog launcher is not tracked at HEAD" >&2
  exit 2
}

EXPECTED_ARMS=(a1_real a2_gray a2b_noimage a3_caption)
EXPECTED_NODES=(an12 an12 an29 an29)
INPUTS=("$@")
ARM_ENTRIES='[]'

for INDEX in 0 1 2 3; do
  ARM="${EXPECTED_ARMS[${INDEX}]}"
  NODE="${EXPECTED_NODES[${INDEX}]}"
  INPUT="${INPUTS[${INDEX}]}"
  if [[ "${INPUT}" = /* ]]; then
    ABS_RUN="$(realpath -m "${INPUT}")"
  else
    ABS_RUN="$(realpath -m "${ROOT}/${INPUT}")"
  fi
  case "${ABS_RUN}" in
    "${ROOT}"/experiments/runs/*) ;;
    *) echo "pilot run directory is outside experiments/runs: ${INPUT}" >&2; exit 2 ;;
  esac
  MANIFEST="${ABS_RUN}/run_manifest.json"
  if [[ ! -f "${MANIFEST}" ]]; then
    echo "pilot run manifest is absent: ${MANIFEST}" >&2
    exit 2
  fi
  if [[ "$(jq -r '.job_type' "${MANIFEST}")" != "l13_mechanical_pilot_arm" ]] || \
     [[ "$(jq -r '.arm' "${MANIFEST}")" != "${ARM}" ]] || \
     [[ "$(jq -r '.node' "${MANIFEST}")" != "${NODE}" ]]; then
    echo "pilot run identity mismatch for ${ARM}: ${MANIFEST}" >&2
    exit 2
  fi
  REL_MANIFEST="${MANIFEST#"${ROOT}"/}"
  RUN_ID="$(jq -er '.run_id' "${MANIFEST}")"
  ENTRY="$(jq -n \
    --arg arm "${ARM}" --arg node "${NODE}" --arg run_id "${RUN_ID}" \
    --arg manifest "${REL_MANIFEST}" \
    '{arm: $arm, node: $node, run_id: $run_id, manifest: $manifest}')"
  ARM_ENTRIES="$(jq -c --argjson entry "${ENTRY}" '. + [$entry]' <<< "${ARM_ENTRIES}")"
done

while IFS= read -r ACTIVE_MANIFEST; do
  [[ -n "${ACTIVE_MANIFEST}" ]] || continue
  [[ "$(jq -r '.job_type // ""' "${ACTIVE_MANIFEST}" 2>/dev/null)" == "m2_pilot_completion_watchdog" ]] || continue
  [[ "$(jq -r '.status // ""' "${ACTIVE_MANIFEST}" 2>/dev/null)" == "running" ]] || continue
  PID_FILE="$(dirname "${ACTIVE_MANIFEST}")/pids/login.pid"
  if [[ -f "${PID_FILE}" ]] && kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
    echo "active M2 completion watchdog already exists: $(dirname "${ACTIVE_MANIFEST}")" >&2
    exit 73
  fi
done < <(find experiments/runs -mindepth 2 -maxdepth 2 -name run_manifest.json -print)

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
WATCHDOG_ID="m2_pilot_completion_watchdog_login_${STAMP}"
RUN_DIR="experiments/runs/${WATCHDOG_ID}"
CONFIG="${RUN_DIR}/config.json"
STATE="${RUN_DIR}/watchdog_state.json"
TERMINAL_JSON="${RUN_DIR}/terminal_notification.json"
TERMINAL_MD="${RUN_DIR}/terminal_notification.md"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
PID_FILE="${RUN_DIR}/pids/login.pid"
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"

jq -n \
  --argjson arms "${ARM_ENTRIES}" \
  --arg state "${STATE}" --arg terminal_json "${TERMINAL_JSON}" \
  --arg terminal_markdown "${TERMINAL_MD}" \
  '{
    schema_version: "blind-gains.m2-completion-watchdog-config.v1",
    poll_interval_seconds: 120,
    arms: $arms,
    state_path: $state,
    terminal_json: $terminal_json,
    terminal_markdown: $terminal_markdown
  }' > "${CONFIG}"

CONFIG_HASH="$(sha256sum "${CONFIG}" | awk '{print $1}')"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/watch_m2_pilot_completion.py --config '${CONFIG}'"
jq -n \
  --arg run_id "${WATCHDOG_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" --arg command "${COMMAND}" \
  --arg config "${CONFIG}" --arg state "${STATE}" \
  --arg terminal_json "${TERMINAL_JSON}" --arg terminal_md "${TERMINAL_MD}" \
  --arg log "${LOG}" --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --argjson parents "${ARM_ENTRIES}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m2_pilot_completion_watchdog",
    node: "login",
    gpu_ids: [],
    gpu_allocation: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only login-node watchdog reads four pinned pilot manifests; it sends no signals and allocates no GPU resources.",
    git_hash: $git_hash,
    config_path: $config,
    config_hash: $config_hash,
    data_manifest_hash: $config_hash,
    seed: null,
    parent_training_runs: $parents,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    expected_artifacts: [$state, $terminal_json, $terminal_md],
    notification_semantics: "Mechanical all-arm completion/failure only; no scientific gate decision and no automatic GPU action.",
    deviations: []
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" \
  > "${ROOT}/${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${PID_FILE}"
sleep 2
if ! kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
  if [[ "$(jq -r '.status // ""' "${MANIFEST}")" != "complete" ]]; then
    echo "M2 completion watchdog exited during startup; inspect ${LOG}" >&2
    exit 1
  fi
fi
printf '%s\n' "${RUN_DIR}"
printf 'state=%s\n' "${STATE}"
printf 'terminal_notification=%s\n' "${TERMINAL_MD}"
