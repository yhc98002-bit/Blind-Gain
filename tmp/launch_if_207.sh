#!/usr/bin/env bash
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
if [ "$(hostname)" != "ln207" ]; then
  echo "SKIP: landed on $(hostname)"
  exit 3
fi
if pgrep -f 'push_m7_bg.sh' >/dev/null 2>&1; then
  echo "ALREADY_RUNNING on $(hostname)"
  exit 0
fi
rm -f logs/m7_fix_push.log
setsid nohup bash tmp/push_m7_bg.sh > /dev/null 2>&1 < /dev/null &
echo "LAUNCHED on $(hostname) pid=$!"
exit 0
