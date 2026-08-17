#!/usr/bin/env bash
set -uo pipefail
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain || exit 1
git add reports/mini_a5_f8_run_provenance_v1.json reports/mini_a5_f8_cell_verification_v1.json
echo "--- staged ---"
git diff --cached --name-only
git commit -q -F - <<'MSG'
F8: run the 6 Mini-A5 endpoint evaluation cells on an29

All six cells (cp/member x R19/R20/chart-v08) ran on an29 via
scripts/launch_fliptrack_eval_shards.sh on the unbound path, 4 TP1 shards
each, real images, 32 new tokens, eval seed 0, per reports/f8_eval_plan_v1.json.
an12 GPUs 0-3 (M7 arm 1) untouched.

All six reached status complete with the expected row counts
(1200/1200/1200/1200/100/100) and launcher exit code 0.

Known limitation, predicted by the plan and confirmed here: the launcher has
no provenance branch for job_type m6_mini_a5_registered_main, so every
run_manifest.json records checkpoint_index_sha256 as null. data_manifest_hash
IS recorded and matches a fresh sha256 in all six. The checkpoint index
sha256 is recomputed from disk and carried in
reports/mini_a5_f8_run_provenance_v1.json instead. No contract file modified.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
echo "commit_rc=$?"
git log --oneline -1
echo "--- push ---"
git push origin HEAD 2>&1 | tail -5
echo "push_rc=$?"
git status --porcelain reports/ | head
