#!/usr/bin/env bash
set -euo pipefail

KIND="${1:?usage: scripts/run_dir.sh KIND NAME}"
NAME="${2:?usage: scripts/run_dir.sh KIND NAME}"
ROOT="${RUN_ROOT:-experiments/logs}"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
GIT_HASH="$(git rev-parse --short HEAD 2>/dev/null || echo no-git)"
DIR="$ROOT/${TS}_${KIND}_${NAME}_${GIT_HASH}"

mkdir -p "$DIR"
printf '%s\n' "$DIR"

