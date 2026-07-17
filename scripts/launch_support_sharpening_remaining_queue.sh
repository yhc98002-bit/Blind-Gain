#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

CRITICAL=(
  configs/eval/support_sharpening_v2.json
  reports/support_sharpening_registry_v3.md
  scripts/run_support_sharpening_queue.py
  scripts/launch_support_sharpening_remaining_queue.sh
  scripts/run_support_sharpening_followup.py
  scripts/launch_support_sharpening_followup.sh
  src/analysis/support_sharpening.py
)
git diff --quiet HEAD -- "${CRITICAL[@]}" || {
  echo "remaining-arm M10 queue critical code differs from HEAD" >&2
  exit 2
}
for FILE in "${CRITICAL[@]}"; do
  git ls-files --error-unmatch "${FILE}" >/dev/null 2>&1 || {
    echo "untracked remaining-arm M10 queue critical file: ${FILE}" >&2
    exit 2
  }
done
while IFS= read -r ACTIVE_MANIFEST; do
  if jq -e '(.job_type == "m10_support_sharpening_remaining_queue") and (.status == "running")' \
    "${ACTIVE_MANIFEST}" >/dev/null 2>&1; then
    echo "active remaining-arm M10 queue already exists: ${ACTIVE_MANIFEST}" >&2
    exit 73
  fi
done < <(find experiments/runs -mindepth 2 -maxdepth 2 -name run_manifest.json -type f | sort)

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ID="m10_support_seed1_remaining_queue_login_${STAMP}"
RUN_DIR="experiments/runs/${RUN_ID}"
MANIFEST="${RUN_DIR}/run_manifest.json"
LOG="${RUN_DIR}/logs/login.log"
STATE="${RUN_DIR}/queue_state.json"
.venv/bin/python scripts/storage_guard.py --tier S --path "${RUN_DIR}" \
  --operation m10_support_remaining_queue --required-bytes 100000000
mkdir -p "${RUN_DIR}/logs" "${RUN_DIR}/pids"
COMMAND="PYTHONPATH=. .venv/bin/python scripts/run_support_sharpening_queue.py --run-dir '${RUN_DIR}' --node an12 --allowed-gpus 4,5,6,7 --arms a2_gray,a2b_noimage --poll-seconds 60 --stable-polls 2"
CONFIG_HASH="$(sha256sum configs/eval/support_sharpening_v2.json | awk '{print $1}')"
COMMAND_HASH="$(printf '%s' "${COMMAND}" | sha256sum | awk '{print $1}')"
DATA_HASH="$({
  sha256sum configs/eval/support_sharpening_v2.json reports/support_sharpening_registry_v3.md
  sha256sum scripts/run_support_sharpening_queue.py scripts/launch_support_sharpening_followup.sh scripts/run_support_sharpening_followup.py
} | sort -k2 | sha256sum | awk '{print $1}')"

jq -n \
  --arg run_id "${RUN_ID}" --arg git_hash "$(git rev-parse HEAD)" \
  --arg config_hash "${CONFIG_HASH}" --arg command_hash "${COMMAND_HASH}" \
  --arg data_hash "${DATA_HASH}" --arg command "${COMMAND}" \
  --arg started "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg log "${LOG}" --arg state "${STATE}" \
  '{
    schema_version: "blind-gains.run-manifest.v1",
    run_id: $run_id,
    job_type: "m10_support_sharpening_remaining_queue",
    node: "login",
    gpu_allocation: [],
    gpu_ids: [],
    tensor_parallel_width: 0,
    replica_count: 0,
    placement_justification: "GPU-inert queue launches only remaining A2/A2b jobs on whichever an12 GPU 4-7 releases first; A1/A3 are already active and an29 remains reserved.",
    placement_policy_version: "pi-2026-07-11",
    git_hash: $git_hash,
    config_path: "configs/eval/support_sharpening_v2.json",
    config_hash: $config_hash,
    launcher_command_hash: $command_hash,
    data_manifest: "frozen A2-gray/A2b-no-image M10 candidate sets",
    data_manifest_hash: $data_hash,
    seed: null,
    command: $command,
    start_time_utc: $started,
    end_time_utc: null,
    status: "running",
    stdout_stderr_log: $log,
    expected_artifacts: [$state],
    performance_values_opened: false,
    scientific_gate_decision: null,
    deviations: [],
    supersedes_empty_queue: "experiments/runs/m10_support_seed1_queue_login_20260717T072835Z"
  }' > "${MANIFEST}"

nohup setsid "${ROOT}/.venv/bin/python" "${ROOT}/scripts/run_manifest_job.py" \
  "${ROOT}/${MANIFEST}" "${ROOT}/${LOG}" > "${RUN_DIR}/logs/wrapper.log" 2>&1 < /dev/null &
echo $! > "${RUN_DIR}/pids/login.pid"
sleep 2
kill -0 "$(cat "${RUN_DIR}/pids/login.pid")" 2>/dev/null || {
  echo "remaining-arm M10 queue exited during startup" >&2
  exit 1
}
printf '%s\n' "${RUN_DIR}"
