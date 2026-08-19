#!/usr/bin/env bash
# ST3 arm-1 endpoint readout chain: merge -> evaluate, across an12 GPUs 4-7.
#
# Arm 1 (st3_std, 30-step budget) banked checkpoints at steps 10/20/30. This
# evaluates each on the FROZEN r2 hierarchy instrument in both the real and the
# matched gray (blind) condition, so the arm-1 side of the arm-1 vs arm-2
# comparison is ready the moment arm 2 lands. Step 30 is the registered
# terminal-step endpoint; 10 and 20 give the trajectory.
#
# GPUs 0-3 on an12 belong to LH2 and are never touched. Each eval is launched
# DETACHED with a settle delay: run_hier_p2_openform.sh loops 12 cells in the
# foreground, so a launch that shares an ssh session dies with it (this cost a
# readout at 8/12 cells on 2026-08-18).
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
LOG="$ROOT/logs/st3_arm1_readout_chain_$(date -u +%Y%m%dT%H%M%SZ).log"
DATA_DIR=data/hier_v1_dev_r2
TAG=hier_d1_st3

say() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$LOG"; }

ckpt_hf() { echo "checkpoints/st3/st3_std_seed1_7b/global_step_$1/actor/huggingface"; }

wait_merge() {  # $1=step  -> 0 when merged, 1 on timeout
  local hf; hf=$(ckpt_hf "$1")
  for _ in $(seq 1 180); do            # up to 90 min
    [ -f "$hf/model.safetensors.index.json" ] && { say "merge step_$1 READY"; return 0; }
    sleep 30
  done
  say "merge step_$1 TIMEOUT"; return 1
}

launch_eval() {  # $1=step $2=gpu $3=mode
  local hf; hf=$(ckpt_hf "$1")
  say "launch eval step_$1 mode=$3 gpu=$2"
  ( setsid nohup bash scripts/run_hier_p2_openform.sh \
      "st3_std30_step$1" "$hf" an12 "$2" "$3" "$DATA_DIR" "$TAG" \
      >/dev/null 2>&1 </dev/null & )
  sleep 25                              # let it establish before the caller moves on
}

wait_evals() {  # wait until every hier_d1_st3_st3_std30_* run dir has 12 cells
  for _ in $(seq 1 180); do
    local pending=0
    for d in experiments/runs/${TAG}_st3_std30_step*; do
      [ -d "$d" ] || continue
      [ "$(ls "$d"/*/metrics.json 2>/dev/null | wc -l)" -eq 12 ] || pending=$((pending+1))
    done
    [ "$pending" -eq 0 ] && { say "all evals complete"; return 0; }
    sleep 60
  done
  say "eval wait TIMEOUT"; return 1
}

# Wave 1: terminal step 30 (gpu4/5) and step 20 (gpu6/7)
wait_merge 30 && { launch_eval 30 4 real; launch_eval 30 5 gray; }
wait_merge 20 && { launch_eval 20 6 real; launch_eval 20 7 gray; }
wait_evals

# Wave 2: step 10 reuses gpu4/5
wait_merge 10 && { launch_eval 10 4 real; launch_eval 10 5 gray; }
wait_evals
say "chain complete"
