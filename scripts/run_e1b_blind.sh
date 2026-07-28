#!/usr/bin/env bash
# E1b blind-column orchestrator — an12 GPUs 4-7 ONLY.
#
# M7 holds GPUs 0-3 at its registered 4-GPU width. This script must never place
# work there. It shards the 24 blind cells across GPUs 4,5,6,7 and runs each
# shard sequentially, so at most four cells are resident at once.
#
# Registered in docs/registered_e1b_external_access_matrix_v1.md.
set -uo pipefail

ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PY="$ROOT/artifacts/envs/vlmevalkit/bin/python"
GIT_HASH="$(git rev-parse HEAD 2>/dev/null || echo unknown)"
LOGDIR="$ROOT/logs/e1b_blind_$STAMP"
mkdir -p "$LOGDIR"

# --- isolation guard: refuse to start if GPUs 4-7 are not free ---------------
for g in 4 5 6 7; do
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$g" 2>/dev/null || echo 0)
  if [[ "${used:-0}" -gt 5000 ]]; then
    echo "ABORT: GPU $g already holds ${used} MiB; E1b will not contend." >&2
    exit 3
  fi
done
# M7 must still be on 0-3; if it is gone, that is a separate problem, but E1b
# still must not expand onto them.
echo "isolation OK: GPUs 4-7 free, M7 untouched on 0-3" | tee "$LOGDIR/orchestrator.log"

mapfile -t QUEUE < <(ls configs/eval/e1b/e1b_*_blind.json | sort)
echo "queue: ${#QUEUE[@]} blind cells" | tee -a "$LOGDIR/orchestrator.log"

run_cell() {
  local cfg="$1" gpu="$2"
  local base name run_id run_dir
  base="$(basename "$cfg" .json)"          # e1b_<arm>_seed<n>_<bench>_blind
  run_id="${base}_an12_${STAMP}"
  run_dir="experiments/runs/${run_id}"
  mkdir -p "$run_dir/logs"

  local cfg_hash
  cfg_hash="$(sha256sum "$cfg" | awk '{print $1}')"

  local cmd="TRANSFORMERS_OFFLINE=1 HF_HOME=$ROOT/artifacts/hf_home CUDA_VISIBLE_DEVICES=$gpu $PY scripts/eval_layer1_blind.py --config $cfg --output $run_dir/predictions.jsonl --metrics-output $run_dir/metrics.json"

  "$PY" - "$run_dir/run_manifest.json" "$cfg" "$cfg_hash" "$GIT_HASH" "$run_id" "$gpu" "$cmd" <<'PYEOF'
import json, sys
out, cfg, cfg_hash, git_hash, run_id, gpu, cmd = sys.argv[1:8]
c = json.load(open(cfg))
json.dump({
    "run_id": run_id, "node": "an12", "job_type": "e1b_blind_external_access_matrix",
    "registration": "docs/registered_e1b_external_access_matrix_v1.md",
    "config_path": cfg, "config_hash": cfg_hash, "git_hash": git_hash,
    "gpu_allocation": [gpu],
    "resource_isolation": c["_e1b"]["resource_isolation"],
    "e1b_cell": {k: c["_e1b"][k] for k in ("arm", "seed", "benchmark", "condition")},
    "checkpoint": c["_e1b"]["checkpoint"],
    "model_path": c.get("model_path"),
    "data_manifest": c.get("input_tsv"),
    "seed": c.get("seed"),
    "command": cmd,
    "image_protocol": ("remove image message, image token, and image tensor; "
                       "retain question text and options verbatim"),
    "status": "running",
}, open(out, "w"), indent=2, sort_keys=True)
PYEOF

  TRANSFORMERS_OFFLINE=1 HF_HOME="$ROOT/artifacts/hf_home" CUDA_VISIBLE_DEVICES="$gpu" \
    "$PY" scripts/eval_layer1_blind.py --config "$cfg" \
      --output "$run_dir/predictions.jsonl" \
      --metrics-output "$run_dir/metrics.json" \
      > "$run_dir/logs/an12.log" 2>&1
  local rc=$?

  "$PY" - "$run_dir/run_manifest.json" "$rc" <<'PYEOF'
import json, sys
p, rc = sys.argv[1], int(sys.argv[2])
m = json.load(open(p))
m["exit_code"] = rc
m["status"] = "complete" if rc == 0 else "fail"
json.dump(m, open(p, "w"), indent=2, sort_keys=True)
PYEOF

  echo "$(date -u +%H:%M:%SZ) gpu$gpu rc=$rc $base" >> "$LOGDIR/orchestrator.log"
}

# --- shard round-robin across the four permitted GPUs -----------------------
for shard in 0 1 2 3; do
  gpu=$((shard + 4))
  (
    for ((i = shard; i < ${#QUEUE[@]}; i += 4)); do
      run_cell "${QUEUE[$i]}" "$gpu"
    done
    echo "shard $shard (gpu $gpu) DONE" >> "$LOGDIR/orchestrator.log"
  ) &
done
wait

echo "ALL E1b BLIND CELLS FINISHED $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOGDIR/orchestrator.log"
