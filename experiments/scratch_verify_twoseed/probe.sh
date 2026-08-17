#!/usr/bin/env bash
# Adversarial probes against the two-seed gates.  Each probe MUST fail.
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
R=experiments/scratch_verify_twoseed/fix
SHA=00317d1babc4dde5165c844effc94f67a20607a26b314a5fea8d32920fbb9605
BASE="--root $R --heldout data/fixture_heldout.jsonl --expected-heldout-sha256 $SHA --expected-heldout-rows 95 --expected-eligible-strata 3 --expected-small-n-strata 1 --step0 a1_real=runs/step0_a1_real --step0 a2_gray=runs/step0_a2_gray --step0 a2b_noimage=runs/step0_a2b_noimage --step0 a3_caption=runs/step0_a3_caption --step100 a1_real=runs/step100_a1_real_seed1 --step100 a2_gray=runs/step100_a2_gray_seed1 --step100 a2b_noimage=runs/step100_a2b_noimage_seed1 --step100 a3_caption=runs/step100_a3_caption_seed1"

probe () {
  name="$1"; shift
  out="$R/probe_${name}"
  rm -rf "$out"
  set +e
  msg=$(.venv/bin/python scripts/build_m7_r3_readout.py $BASE "$@" \
      --json-output "probe_${name}/r.json" --markdown-output "probe_${name}/r.md" \
      --artifact-dir "probe_${name}/arts" 2>&1)
  rc=$?
  set -e
  if [ $rc -eq 0 ]; then
    echo "PROBE $name: *** ACCEPTED (rc=0) -- GATE HOLE ***"
  else
    echo "PROBE $name: refused rc=$rc :: $(echo "$msg" | grep -Ei 'error|Error|refus|gate|mixed|repeat|double|status|mismatch|label' | head -2 | tr '\n' ' ')"
  fi
}

# 1. seed 2 for three arms only (mixed-seed denominator)
probe missing_arm \
  --step100-seed2 a1_real=runs/step100_a1_real_seed2 \
  --step100-seed2 a2_gray=runs/step100_a2_gray_seed2 \
  --step100-seed2 a2b_noimage=runs/step100_a2b_noimage_seed2

# 2. seed 2 == seed 1 exact path (double counting)
probe same_dir_exact \
  --step100-seed2 a1_real=runs/step100_a1_real_seed1 \
  --step100-seed2 a2_gray=runs/step100_a2_gray_seed1 \
  --step100-seed2 a2b_noimage=runs/step100_a2b_noimage_seed1 \
  --step100-seed2 a3_caption=runs/step100_a3_caption_seed1

# 3. seed 2 == seed 1 with a trailing slash (string compare defeated)
probe same_dir_slash \
  --step100-seed2 a1_real=runs/step100_a1_real_seed1/ \
  --step100-seed2 a2_gray=runs/step100_a2_gray_seed1/ \
  --step100-seed2 a2b_noimage=runs/step100_a2b_noimage_seed1/ \
  --step100-seed2 a3_caption=runs/step100_a3_caption_seed1/

# 4. seed 2 == seed 1 via ./ prefix
probe same_dir_dot \
  --step100-seed2 a1_real=./runs/step100_a1_real_seed1 \
  --step100-seed2 a2_gray=./runs/step100_a2_gray_seed1 \
  --step100-seed2 a2b_noimage=./runs/step100_a2b_noimage_seed1 \
  --step100-seed2 a3_caption=./runs/step100_a3_caption_seed1

# 5. seed-2 run whose manifest status is "running"
probe running_status \
  --step100-seed2 a1_real=runs/bad_running_a1_real_seed2 \
  --step100-seed2 a2_gray=runs/step100_a2_gray_seed2 \
  --step100-seed2 a2b_noimage=runs/step100_a2b_noimage_seed2 \
  --step100-seed2 a3_caption=runs/step100_a3_caption_seed2

# 6. seed-2 run with one item missing (cross-seed pairing)
probe short_items \
  --step100-seed2 a1_real=runs/bad_short_a1_real_seed2 \
  --step100-seed2 a2_gray=runs/step100_a2_gray_seed2 \
  --step100-seed2 a2b_noimage=runs/step100_a2b_noimage_seed2 \
  --step100-seed2 a3_caption=runs/step100_a3_caption_seed2

# 7. seed-2 run whose checkpoint label says global_step_60
probe wrong_step \
  --step100-seed2 a1_real=runs/bad_step60_a1_real_seed2 \
  --step100-seed2 a2_gray=runs/step100_a2_gray_seed2 \
  --step100-seed2 a2b_noimage=runs/step100_a2b_noimage_seed2 \
  --step100-seed2 a3_caption=runs/step100_a3_caption_seed2

# 8. seed-2 dirs swapped between arms a2_gray <-> a2b_noimage
probe swapped_arms \
  --step100-seed2 a1_real=runs/step100_a1_real_seed2 \
  --step100-seed2 a2_gray=runs/step100_a2b_noimage_seed2 \
  --step100-seed2 a2b_noimage=runs/step100_a2_gray_seed2 \
  --step100-seed2 a3_caption=runs/step100_a3_caption_seed2

# 9. --partial with seed 2
rm -rf "$R/probe_partial"
set +e
msg=$(.venv/bin/python scripts/build_m7_r3_readout.py --root $R \
  --heldout data/fixture_heldout.jsonl --expected-heldout-sha256 $SHA \
  --expected-heldout-rows 95 --expected-eligible-strata 3 --expected-small-n-strata 1 \
  --step0 a1_real=runs/step0_a1_real --step0 a2_gray=runs/step0_a2_gray \
  --step0 a2b_noimage=runs/step0_a2b_noimage --step0 a3_caption=runs/step0_a3_caption \
  --partial --step100-seed2 a1_real=runs/step100_a1_real_seed2 \
  --json-output probe_partial/r.json --markdown-output probe_partial/r.md 2>&1)
rc=$?
set -e
if [ $rc -eq 0 ]; then echo "PROBE partial_seed2: *** ACCEPTED -- GATE HOLE ***";
else echo "PROBE partial_seed2: refused rc=$rc :: $(echo "$msg" | tail -1)"; fi
