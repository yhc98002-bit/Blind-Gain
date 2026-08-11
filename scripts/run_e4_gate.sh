#!/usr/bin/env bash
# Track-4 premise-v2 E4 (attacker check) — the registered section-7 command, run under
# guard + claim on an29 GPU 2. Runs and records only; the registered pass criterion
# (every attacker's side-prediction 95% CI includes 0.5) is judged from the emitted
# report, not here.
#
# E4's reader src/fliptrack/artifact_attackers.py consumes exactly:
#   release manifest: pair_id, members[].member_id, members[].image_path
#   key file:         pair_id, template_id, members[].member_id, members[].source_side
# all of which the packaged dev batch already carries.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
LOG="$ROOT/logs/track4_gates/e4_attacker_gate.log"
mkdir -p "$(dirname "$LOG")"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
NODE=an29; GPU=2
CLAIMS=/dev/shm/blind-gains/gpu_claims
DATA=data/track4_premise_v2_dev_v1
OUT=reports/track4_premise_v2_attacker_gate_v1.json
log "E4 start: node=$NODE gpu=$GPU git=$(git rev-parse --short HEAD)"

[[ -e "$OUT" ]] && { log "output already exists ($OUT); refusing to overwrite"; exit 1; }

.venv/bin/python scripts/m7_gpu_occupancy_guard.py --node "$NODE" --gpus "$GPU" >> "$LOG" 2>&1 \
  || { log "guard denied $NODE:$GPU; abort"; exit 1; }
payload=$(jq -nc --argjson gpu "$GPU" --arg run_id t4v2_e4_attacker_gate --argjson pid null \
  --arg dir "" --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{gpu:$gpu, run_id:$run_id, pid:$pid, eval_run_dir:$dir, written_utc:$ts, written_by:"scripts/run_e4_gate.sh"}')
printf '%s\n' "$payload" | ssh -o BatchMode=yes -o ConnectTimeout=25 "$NODE" \
  "mkdir -p '$CLAIMS' && cat > '$CLAIMS/${NODE}_gpu${GPU}.claim'" || { log "claim write failed"; exit 1; }
.venv/bin/python scripts/m7_gpu_occupancy_guard.py --node "$NODE" --gpus "$GPU" \
  --ignore-claim-run-id t4v2_e4_attacker_gate >> "$LOG" 2>&1 \
  || { ssh -o ConnectTimeout=25 "$NODE" "rm -f '$CLAIMS/${NODE}_gpu${GPU}.claim'"; log "post-claim re-check denied; abort"; exit 1; }
log "guard+claim ok"

log "launching registered E4 command"
out=$(bash scripts/launch_artifact_gate_v02.sh "$NODE" "$GPU" "$DATA/attacker_release" "$DATA/attacker_key.jsonl" "$OUT" 2>&1 | tail -1)
log "launcher -> $out"
rundir=$(printf '%s\n' "$out" | tail -1)

for i in $(seq 1 120); do
  sleep 60
  [[ -f "$OUT" ]] && { log "E4 report written: $OUT"; break; }
  if [[ -d "$rundir" ]]; then
    s=$(grep -oE '"status": *"[a-z]+"' "$rundir/run_manifest.json" 2>/dev/null | tail -1)
    [[ "$s" == *fail* ]] && { log "E4 run FAILED ($rundir)"; break; }
  fi
done
ssh -o ConnectTimeout=25 "$NODE" "rm -f '$CLAIMS/${NODE}_gpu${GPU}.claim'" 2>/dev/null || true
log "claim released"
[[ -f "$OUT" ]] && log "*** E4 COMPLETE — report at $OUT (verdict read separately against the registered criterion) ***" || log "E4 did not produce its report"
