#!/usr/bin/env bash
# Detached launcher for the D4 caption column across the free an12 GPUs.
# Uses setsid so the orchestrator survives the SSH session that starts it.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
export PATH="$HOME/.local/bin:$PATH"
cd "$ROOT"

GPUS="${1:-4 5 6 7}"

# refuse to start a second orchestrator; in_flight_cells() protects against
# duplicate cells but two schedulers racing for the same pending cell is the
# failure mode that already cost a duplicated run this session.
if pgrep -f "run_d2_testtime_ablatio[n]" > /dev/null; then
  echo "orchestrator already running; not starting a second"
  pgrep -af "run_d2_testtime_ablatio[n]" | head -3
  exit 0
fi

setsid nohup .venv/bin/python scripts/run_d2_testtime_ablation.py \
  --node an12 --gpu-ids $GPUS --conditions caption \
  > logs/d4_caption_orch.log 2>&1 < /dev/null &
disown || true
sleep 8
echo "orchestrator pid(s): $(pgrep -f "run_d2_testtime_ablatio[n]" | tr '\n' ' ')"
echo "gpus: $GPUS"
