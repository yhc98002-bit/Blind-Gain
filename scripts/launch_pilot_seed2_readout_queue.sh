#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

CONFIG="experiments/manifests/pilot_4arm_seed2_readout_v1.json"
CRITICAL=(
  scripts/build_pilot_4arm_seed1_readout.py
  scripts/run_pilot_fourarm_readout_queue.py
  scripts/launch_pilot_seed2_readout_queue.sh
  "${CONFIG}"
)
for FILE in "${CRITICAL[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || {
    echo "untracked readout-critical file: ${FILE}" >&2
    exit 2
  }
done
git diff --quiet HEAD -- "${CRITICAL[@]}" || {
  echo "readout-critical code differs from HEAD" >&2
  exit 2
}

jq -e '
  (.schema_version == "blind-gains.pilot-fourarm-followup-readout-config.v1") and
  (.seed == 2) and (.bootstrap_draws == 5000) and
  (.support_sharpening_candidates == false)
' "${CONFIG}" >/dev/null || {
  echo "seed-2 readout config identity mismatch" >&2
  exit 2
}

while IFS= read -r MANIFEST; do
  [[ "$(jq -r '.job_type // ""' "${MANIFEST}" 2>/dev/null)" == "pilot_fourarm_seed2_unified_readout" ]] || continue
  [[ "$(jq -r '.status // ""' "${MANIFEST}" 2>/dev/null)" == "running" ]] || continue
  echo "an active seed-2 unified readout already exists: $(dirname "${MANIFEST}")" >&2
  exit 73
done < <(find experiments/runs -mindepth 2 -maxdepth 2 -name run_manifest.json -print)

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="pilot_4arm_seed2_readout_queue_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
STATE="${RUN_DIR}/state.json"
GATE="${RUN_DIR}/readout_open_gate.json"
ARTIFACT_DIR="${RUN_DIR}/artifacts"
JSON_OUTPUT="reports/pilot_4arm_seed2_results_v1.json"
MARKDOWN_OUTPUT="reports/pilot_4arm_seed2_results_v1.md"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
CONFIG_HASH="$(sha256sum "${CONFIG}" | awk '{print $1}')"
LIFECYCLE="$(jq -r '.evaluation_lifecycle_manifest' "${CONFIG}")"
CHILDREN_HASH="$(jq -r '.evaluation_lifecycle_children_sha256' "${CONFIG}")"

[[ ! -e "${JSON_OUTPUT}" && ! -e "${MARKDOWN_OUTPUT}" ]] || {
  echo "seed-2 report already exists; refusing overwrite" >&2
  exit 2
}
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_pilot_fourarm_readout_queue.py --config '${CONFIG}' --config-sha256 '${CONFIG_HASH}' --state '${STATE}' --artifact-dir '${ARTIFACT_DIR}' --json-output '${JSON_OUTPUT}' --markdown-output '${MARKDOWN_OUTPUT}' --poll-seconds 60"
jq -n \
  --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config "${CONFIG}" --arg config_hash "${CONFIG_HASH}" \
  --arg lifecycle "${LIFECYCLE}" --arg children_hash "${CHILDREN_HASH}" \
  --arg command "${COMMAND}" --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg log "${LOG}" --arg state "${STATE}" --arg gate "${GATE}" \
  --arg artifacts "${ARTIFACT_DIR}" --arg json "${JSON_OUTPUT}" \
  --arg markdown "${MARKDOWN_OUTPUT}" '
  {
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "pilot_fourarm_seed2_unified_readout",
    pilot_seed: 2,
    node: "login",
    gpu_ids: [],
    gpu_allocation: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "CPU-only queue validates the sealed eight-endpoint lifecycle before opening any cached prediction and computes all four arms in one invocation.",
    git_hash: $git_hash,
    config_path: $config,
    config_hash: $config_hash,
    data_manifest: $lifecycle,
    data_manifest_hash: $children_hash,
    seed: 2,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    expected_artifacts: [$state, $gate, $artifacts, $json, $markdown],
    performance_values_opened: false,
    performance_open_policy: "Only state.json may transition to true, after readout_open_gate.json records a complete sealed 8/8 lifecycle.",
    scientific_gate_decision: null,
    deviations: []
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo "$!" > "${RUN_DIR}/pids/login.pid"
sleep 2
kill -0 "$(cat "${RUN_DIR}/pids/login.pid")" 2>/dev/null || {
  echo "seed-2 unified readout queue exited during startup" >&2
  exit 1
}
printf '%s\n' "${RUN_DIR}"
