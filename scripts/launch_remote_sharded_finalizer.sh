#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 NODE RUN_DIR" >&2
  exit 2
fi

NODE="$1"
RUN_DIR="$2"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FINALIZER_LOG="${RUN_DIR}/logs/finalizer.log"
FINALIZER_PID="${RUN_DIR}/pids/finalizer.pid"

# Tool-launched login shells may reap local background children. Keep the
# finalizer beside the scientific worker on the compute node instead.
ssh "${NODE}" "cd '${ROOT}' && mkdir -p '${RUN_DIR}/logs' '${RUN_DIR}/pids' && (nohup '${ROOT}/.venv/bin/python' scripts/finalize_sharded_run.py '${RUN_DIR}/run_manifest.json' --wait > '${FINALIZER_LOG}' 2>&1 < /dev/null & echo \$! > '${FINALIZER_PID}')"
echo "${NODE} finalizer_pid_file=${FINALIZER_PID} log=${FINALIZER_LOG}"
