#!/usr/bin/env bash
# Gate-1 T7 continuation + main-arm chain. Supersedes scripts/gate1_t7_runner.sh,
# which exited after the std plumbing smoke completed cleanly: its audit stanza
# used a per-mode CLI (--run-dir/--mode) that the registered audit script does
# not have. The real audit is combined (--std-manifest + --necessity-manifest)
# and must run as a module (-m) so its `scripts.*` imports resolve.
#
# Sequence: sanity(std smoke complete) -> necessity smoke -> combined audit
# -> step-0 std (an29 GPU 0) + step-0 necessity (an29 GPU 1) -> summaries
# -> T7 COMPLETE -> launch Gate-1 MAIN ARM std (an29, 8 GPU, ~20 h)
# -> on completion, launch MAIN ARM necessity -> log final marker.
# Every wait is fail-closed: manifest "fail", launch refusal, loop expiry,
# or a nonzero audit/summary exit stops the chain with a log line.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
LOG="$ROOT/logs/gate1_t7_continue.log"
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }
log "T7 continuation start (supersedes gate1_t7_runner.sh)"
CLAIMDIR=/dev/shm/blind-gains/gpu_claims
STD_SMOKE=experiments/runs/mini_a5_std_plumbing_smoke_an29_20260807T005652Z

clean_an29_claims() { ssh -o ConnectTimeout=15 an29 "rm -f $CLAIMDIR/an29_gpu*.claim" 2>/dev/null || true; }

manifest_status() { grep -oE '"status": *"[a-z]+"' "$1/run_manifest.json" 2>/dev/null | tail -1; }

# wait_run RUN_DIR MAX_ITER SLEEP LABEL -> 0 complete, 1 otherwise (logged)
wait_run() {
  local d="$1" n="$2" slp="$3" lbl="$4" s i
  for i in $(seq 1 "$n"); do
    s=$(manifest_status "$d")
    [[ "$s" == *complete* ]] && { log "[$lbl] complete"; return 0; }
    [[ "$s" == *fail* ]] && { log "[$lbl] FAILED ($d)"; return 1; }
    sleep "$slp"
  done
  log "[$lbl] wait expired (last status: ${s:-none}) ($d)"
  return 1
}

# 0) sanity: std smoke really complete
s=$(manifest_status "$STD_SMOKE")
[[ "$s" == *complete* ]] || { log "std smoke not complete ($s); abort"; exit 1; }
log "std smoke verified complete: $STD_SMOKE"

# 1) necessity plumbing smoke, 8 GPUs on an29
log "[necessity-smoke] launching on an29"
out=$(bash scripts/launch_mini_a5_gate1_plumbing_smoke.sh necessity an29 0,1,2,3,4,5,6,7 2>&1 | tail -1)
log "[necessity-smoke] -> $out"
[[ "$out" == experiments/runs/* ]] || { log "LAUNCH REFUSED: $out"; clean_an29_claims; exit 1; }
NEC_SMOKE="$out"
wait_run "$NEC_SMOKE" 30 120 necessity-smoke || { clean_an29_claims; exit 1; }
clean_an29_claims

# 2) combined registered audit (exit 1 on any failed check)
.venv/bin/python -m scripts.audit_mini_a5_gate1_plumbing_smoke \
  --std-manifest "$STD_SMOKE/run_manifest.json" \
  --necessity-manifest "$NEC_SMOKE/run_manifest.json" \
  --json-output reports/mini_a5_gate1_smoke_audit_v1.json \
  --markdown-output reports/mini_a5_gate1_smoke_audit_v1.md >> "$LOG" 2>&1 \
  || { log "SMOKE AUDIT FAILED — see reports/mini_a5_gate1_smoke_audit_v1.json; stopping"; exit 1; }
log "smoke audit PASS (combined, both arms)"

# 3) step-0 reward diagnostics, GPUs 0 and 1 (staggered to avoid claim races)
log "[step0-std] launching on an29 gpu 0"
s0std=$(bash scripts/launch_mini_a5_gate1_step0.sh std an29 0 2>&1 | tail -1)
log "[step0-std] -> $s0std"
[[ "$s0std" == experiments/runs/* ]] || { log "STEP0 STD LAUNCH REFUSED: $s0std"; clean_an29_claims; exit 1; }
sleep 45
log "[step0-necessity] launching on an29 gpu 1"
s0nec=$(bash scripts/launch_mini_a5_gate1_step0.sh necessity an29 1 2>&1 | tail -1)
log "[step0-necessity] -> $s0nec"
[[ "$s0nec" == experiments/runs/* ]] || { log "STEP0 NECESSITY LAUNCH REFUSED: $s0nec"; clean_an29_claims; exit 1; }
wait_run "$s0std" 45 120 step0-std || { clean_an29_claims; exit 1; }
wait_run "$s0nec" 45 120 step0-necessity || { clean_an29_claims; exit 1; }
clean_an29_claims

# 4) summaries (exit 1 on refusal)
.venv/bin/python -m scripts.summarize_mini_a5_gate1_step0 \
  --arm std --predictions "$s0std/predictions.jsonl" \
  --run-manifest "$s0std/run_manifest.json" \
  --json-output reports/mini_a5_gate1_step0_summary_std_v1.json \
  --markdown-output reports/mini_a5_gate1_step0_summary_std_v1.md >> "$LOG" 2>&1 \
  || { log "STEP0 SUMMARY std FAILED; stopping"; exit 1; }
.venv/bin/python -m scripts.summarize_mini_a5_gate1_step0 \
  --arm necessity --predictions "$s0nec/predictions.jsonl" \
  --run-manifest "$s0nec/run_manifest.json" \
  --json-output reports/mini_a5_gate1_step0_summary_necessity_v1.json \
  --markdown-output reports/mini_a5_gate1_step0_summary_necessity_v1.md >> "$LOG" 2>&1 \
  || { log "STEP0 SUMMARY necessity FAILED; stopping"; exit 1; }
log "*** T7 COMPLETE: smokes audited (combined PASS), both step-0 summaries written ***"

# 5) Gate-1 MAIN ARM std — an29 is the first fully-free 8-GPU node
#    (contention rule: Gate-1 arms take the first fully-free node).
log "[arm-std] launching Gate-1 main arm std on an29 (8 GPUs)"
armstd=$(bash scripts/launch_mini_a5_main.sh std an29 0,1,2,3,4,5,6,7 2>&1 | tail -1)
log "[arm-std] -> $armstd"
[[ "$armstd" == experiments/runs/* ]] || { log "ARM STD LAUNCH REFUSED: $armstd"; clean_an29_claims; exit 1; }
wait_run "$armstd" 156 600 arm-std || { clean_an29_claims; exit 1; }   # 26 h cap
clean_an29_claims

# 6) Gate-1 MAIN ARM necessity
log "[arm-necessity] launching Gate-1 main arm necessity on an29 (8 GPUs)"
armnec=$(bash scripts/launch_mini_a5_main.sh necessity an29 0,1,2,3,4,5,6,7 2>&1 | tail -1)
log "[arm-necessity] -> $armnec"
[[ "$armnec" == experiments/runs/* ]] || { log "ARM NECESSITY LAUNCH REFUSED: $armnec"; clean_an29_claims; exit 1; }
wait_run "$armnec" 156 600 arm-necessity || { clean_an29_claims; exit 1; }
clean_an29_claims

log "*** GATE-1 BOTH MAIN ARMS COMPLETE: std=$armstd necessity=$armnec — four-arm endpoint readout is next (manual, registered extension) ***"
