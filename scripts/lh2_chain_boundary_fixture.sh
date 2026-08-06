#!/usr/bin/env bash
# I10 adversarial fixture for the LH2 chain's hash-verified boundary gate
# (scripts/lh2_segment_chain.sh audit_boundary). Exercises
# scripts/audit_easyr1_resume_checkpoint.py plus the exact jq contract the
# chain enforces, against synthetic checkpoints under tmp/ (never repo state):
#   1. clean synthetic step-50 checkpoint  -> audit exit 0 AND jq contract 0
#   2. missing optimizer shard (rank 3)    -> audit exit != 0
#   3. wrong expected step (100 vs dir 50) -> audit exit != 0
# Verdict artifact: reports/lh2_chain_boundary_fixture_v1.json; exit 0 iff pass.
set -u
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"
PY="$ROOT/.venv/bin/python"
FIX="$ROOT/tmp/lh2_chain_boundary_fixture"
rm -rf "$FIX"
mkdir -p "$FIX"

mk_ckpt() {  # dir
  local d="$1" r
  mkdir -p "$d/actor"
  for r in 0 1 2 3; do
    printf 'model%s' "$r" > "$d/actor/model_world_size_4_rank_${r}.pt"
    printf 'optim%s' "$r" > "$d/actor/optim_world_size_4_rank_${r}.pt"
    printf 'extra%s' "$r" > "$d/actor/extra_state_world_size_4_rank_${r}.pt"
  done
  printf 'dl' > "$d/dataloader.pt"
}

contract() {  # json step  — byte-identical predicate to the chain's gate
  jq -e --argjson step "$2" '
      (.status=="pass") and (.expected_step==$step) and (.world_size==4) and
      (.model_rank_count==4) and (.optimizer_rank_count==4) and
      (.extra_state_rank_count==4) and (.files_stable_during_hash==true)
    ' "$1" >/dev/null
}

mk_ckpt "$FIX/clean/global_step_50"
"$PY" scripts/audit_easyr1_resume_checkpoint.py \
  --checkpoint-dir "$FIX/clean/global_step_50" --expected-step 50 \
  --expected-world-size 4 --output-json "$FIX/clean_audit.json" \
  --output-sha256 "$FIX/clean_audit.sha256" >/dev/null 2>"$FIX/clean_err.txt"
clean_exit=$?
contract "$FIX/clean_audit.json" 50
clean_contract=$?

mk_ckpt "$FIX/missing/global_step_50"
rm "$FIX/missing/global_step_50/actor/optim_world_size_4_rank_3.pt"
"$PY" scripts/audit_easyr1_resume_checkpoint.py \
  --checkpoint-dir "$FIX/missing/global_step_50" --expected-step 50 \
  --expected-world-size 4 --output-json "$FIX/missing_audit.json" \
  --output-sha256 "$FIX/missing_audit.sha256" >/dev/null 2>"$FIX/missing_err.txt"
missing_exit=$?

mk_ckpt "$FIX/wrongstep/global_step_50"
"$PY" scripts/audit_easyr1_resume_checkpoint.py \
  --checkpoint-dir "$FIX/wrongstep/global_step_50" --expected-step 100 \
  --expected-world-size 4 --output-json "$FIX/wrong_audit.json" \
  --output-sha256 "$FIX/wrong_audit.sha256" >/dev/null 2>"$FIX/wrong_err.txt"
wrong_exit=$?

status=fail
if [[ $clean_exit -eq 0 && $clean_contract -eq 0 && $missing_exit -ne 0 && $wrong_exit -ne 0 ]]; then
  status=pass
fi
jq -n --arg status "$status" --argjson clean "$clean_exit" \
  --argjson clean_contract "$clean_contract" --argjson missing "$missing_exit" \
  --argjson wrong "$wrong_exit" \
  '{schema:"blind-gains.lh2-chain-boundary-fixture.v1",
    exit_codes:{clean_audit:$clean, clean_jq_contract:$clean_contract,
                missing_optim_shard:$missing, wrong_expected_step:$wrong},
    expected:{clean_audit:0, clean_jq_contract:0,
              missing_optim_shard:"nonzero", wrong_expected_step:"nonzero"},
    status:$status}' | tee "$ROOT/reports/lh2_chain_boundary_fixture_v1.json"
[[ $status == pass ]]
