#!/usr/bin/env bash
# Show that the Mini-A5 ranking worker.sh is the prior completed run's worker.sh
# with only the run dir, config path and model key substituted.
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain || exit 1

PRIOR=experiments/runs/d1_visual_evidence_a1_seed2_step100_real_an29_gpu4_x5_ranking_matrix_queue_login_20260725T021220Z
MINE=experiments/runs/mini_a5_s1_ranking_cp_step120_real_an29_gpu4_20260730T011842Z

normalize() {
  sed -E \
    -e 's@experiments/runs/[A-Za-z0-9_.-]+@RUNDIR@g' \
    -e 's@configs/eval/[A-Za-z0-9_.-]+\.json@CONFIG@g' \
    -e 's@a1_seed2_step100@MODELKEY@g' \
    -e 's@mini_a5_cp_step120@MODELKEY@g' \
    "$1"
}

normalize "${PRIOR}/worker.sh" > /tmp/w_prior.$$
normalize "${MINE}/worker.sh"  > /tmp/w_mine.$$

if diff -u /tmp/w_prior.$$ /tmp/w_mine.$$; then
  echo "RESULT: worker.sh STRUCTURALLY IDENTICAL after normalizing run dir / config path / model key"
else
  echo "RESULT: differences shown above"
fi
rm -f /tmp/w_prior.$$ /tmp/w_mine.$$
