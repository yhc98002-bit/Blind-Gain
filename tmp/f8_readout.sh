#!/usr/bin/env bash
set -euo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
export PATH=$HOME/.local/bin:$PATH
cd "$ROOT"
RUN_TS=20260730T004031Z
PY="$ROOT/.venv/bin/python"

echo "=== PAIRED COMPARISONS (registered interval) ==="
for SET in r19 r20 chartv08; do
  OUT="reports/mini_a5_f8_${SET}_paired_comparison_v1.json"
  if [ -f "$OUT" ]; then
    echo "SKIP-EXISTS $OUT"
    continue
  fi
  PYTHONPATH=. "$PY" scripts/compare_fliptrack_runs.py \
    --left "experiments/runs/mini_a5_f8_${SET}_member_step120_real_an29_${RUN_TS}/shards/shard_*.jsonl" \
    --right "experiments/runs/mini_a5_f8_${SET}_cp_step120_real_an29_${RUN_TS}/shards/shard_*.jsonl" \
    --left-label mini_a5_same_data_seed1_step120 \
    --right-label mini_a5_cp_seed1_step120 \
    --output "$OUT" \
    --bootstrap-draws 10000 --seed 20260729
  echo "WROTE $OUT rc=$?"
done

echo "=== PER-CELL AGGREGATES ==="
declare -A DIRS=(
  [r19_cp]="mini_a5_f8_r19_cp_step120_real_an29_${RUN_TS}"
  [r19_member]="mini_a5_f8_r19_member_step120_real_an29_${RUN_TS}"
  [r20_cp]="mini_a5_f8_r20_cp_step120_real_an29_${RUN_TS}"
  [r20_member]="mini_a5_f8_r20_member_step120_real_an29_${RUN_TS}"
  [chartv08_cp]="mini_a5_f8_chartv08_cp_step120_real_an29_${RUN_TS}"
  [chartv08_member]="mini_a5_f8_chartv08_member_step120_real_an29_${RUN_TS}"
)
for K in r19_cp r19_member r20_cp r20_member chartv08_cp chartv08_member; do
  OUT="reports/mini_a5_f8_${K}_aggregate_v1.json"
  if [ -f "$OUT" ]; then
    echo "SKIP-EXISTS $OUT"
    continue
  fi
  PYTHONPATH=. "$PY" scripts/aggregate_fliptrack_eval.py \
    --inputs "experiments/runs/${DIRS[$K]}/shards/shard_*.jsonl" \
    --output "$OUT" --bootstrap 10000 --permutations 1000
  echo "WROTE $OUT"
done
echo "=== DONE ==="
