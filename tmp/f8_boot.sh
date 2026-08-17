#!/usr/bin/env bash
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 90
RUN_TS="$(cat tmp/f8_run_ts.txt)"
BOOT_LOG="logs/mini_a5_f8_driver_boot_${RUN_TS}.log"
mkdir -p logs
setsid nohup bash "$ROOT/tmp/f8_driver.sh" > "$BOOT_LOG" 2>&1 < /dev/null &
echo $! > tmp/f8_driver.pid
sleep 2
echo "booted pid=$(cat tmp/f8_driver.pid) host=$(hostname) boot_log=${BOOT_LOG}"
ps -o pid,ppid,sid,cmd -p "$(cat tmp/f8_driver.pid)" || true
