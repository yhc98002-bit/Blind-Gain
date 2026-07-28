#!/usr/bin/env bash
# Detached D4 orchestrator, running ON an12 rather than the login node.
#
# The login node kills or breaks long-lived orchestrators: earlier in this
# project the same pattern died repeatedly with
#   RuntimeError: GPU query failed an12:N: /usr/bin/ssh: error while loading
#   shared libraries: libkrb5.so.3
# The established fix was to relocate the orchestrator onto the compute node and
# run it unbuffered so failures are visible in the log rather than silent.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
GPUS="${1:-4 5 6 7}"

if ssh an12 "pgrep -f 'run_d2_testtime_ablatio[n]' > /dev/null"; then
  echo "orchestrator already running on an12; not starting a second"
  ssh an12 "pgrep -af 'run_d2_testtime_ablatio[n]' | head -2"
  exit 0
fi

ssh an12 "cd '$ROOT' && export PATH=\$HOME/.local/bin:\$PATH && \
setsid nohup env PYTHONUNBUFFERED=1 .venv/bin/python scripts/run_d2_testtime_ablation.py \
--node an12 --gpu-ids $GPUS --conditions caption \
> logs/d4_caption_orch.log 2>&1 < /dev/null & disown" 2>/dev/null

sleep 10
echo "orchestrator on an12: $(ssh an12 "pgrep -f 'run_d2_testtime_ablatio[n]' | tr '\n' ' '")"
echo "gpus: $GPUS"
