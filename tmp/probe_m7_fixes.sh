#!/usr/bin/env bash
# Dry-proof of FIX 1 (guard granularity) and FIX 2 (manifest deviation).
# Starts NO trainer. Only reads state and runs the guard in isolation.
export PATH=$HOME/.local/bin:$PATH
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
PY="$ROOT/.venv/bin/python"
GUARD="$ROOT/scripts/m7_gpu_occupancy_guard.py"

probe () {
  local node="$1" gpus="$2" expect="$3"
  echo "---- probe node=$node gpus=$gpus (expect $expect)"
  "$PY" "$GUARD" --node "$node" --gpus "$gpus" 2>&1 | sed 's/^/    /'
  local rc=${PIPESTATUS[0]}
  echo "    EXIT=$rc  -> $([ "$rc" -eq 0 ] && echo ALLOW || echo REFUSE)  (expected $expect)"
}

echo "===== 2. FIX 1 DRY-PROOF: guard in isolation ====="
probe an12 4,5,6,7 ALLOW
probe an12 0,1,2,3 REFUSE
probe an12 2,3,4,5 REFUSE
probe an12 3,4,5,6 REFUSE
probe an29 0,1,2,3 "?"
probe an29 4,5,6,7 "?"
echo "---- fail-closed: unreachable node"
"$PY" "$GUARD" --node an99 --gpus 0,1,2,3 2>&1 | sed 's/^/    /'
echo "    EXIT=${PIPESTATUS[0]} (expect 75 = fail-closed)"

echo
echo "===== 2b. SELF-MATCH PROTECTION: does the probe's own cmdline match? ====="
echo "-- literal test: python regex 'verl.trainer.mai[n]' vs the probe's own remote cmdline"
"$PY" - <<'PYEOF'
import re
pat = "verl.trainer.mai[n]"
own = "bash -c pgrep -a -f 'verl.trainer.mai[n]'"
real = "/path/.venv/bin/python -u -m verl.trainer.main config=/path/effective_config.yaml"
print("   regex matches OWN probe cmdline :", bool(re.search(pat, own)), "(must be False)")
print("   regex matches REAL trainer argv :", bool(re.search(pat, real)), "(must be True)")
PYEOF
echo "-- live check: run the guard's exact pgrep on an12 and show every matched line"
ssh -o ConnectTimeout=25 an12 "pgrep -a -f 'verl.trainer.mai[n]'" 2>&1 | sed 's/^/    /'

echo
echo "===== 4. FIX 2 DRY-PROOF: deviation derivation, using the launcher's OWN code text ====="
echo "-- save_model_only per registered arm config:"
for c in configs/train/m7_virl_*_3b.yaml; do
  printf '   %-46s save_model_only=%s save_freq=%s\n' "$(basename "$c")" \
    "$("$PY" -c 'import yaml,sys; print((yaml.safe_load(open(sys.argv[1]))["trainer"]).get("save_model_only","<absent>"))' "$c")" \
    "$("$PY" -c 'import yaml,sys; print((yaml.safe_load(open(sys.argv[1]))["trainer"])["save_freq"])' "$c")"
done

# extract the real derivation block from the launcher, verbatim, and run it
awk '/^SAVE_MODEL_ONLY=/,/^fi$/' scripts/launch_m7_virl_arm.sh > tmp/_dev_block.sh
echo "-- extracted block from launcher ($(wc -l < tmp/_dev_block.sh) lines):"
sed 's/^/     | /' tmp/_dev_block.sh | cut -c1-150
for c in configs/train/m7_virl_a1_real_seed1_3b.yaml configs/train/m7_virl_a2_gray_seed1_3b.yaml configs/train/m7_virl_a2b_noimage_seed1_3b.yaml configs/train/m7_virl_a3_caption_seed1_3b.yaml; do
  [ -f "$c" ] || { echo "   MISSING $c"; continue; }
  ( set -euo pipefail
    EFFECTIVE="$c"
    # shellcheck disable=SC1091
    source tmp/_dev_block.sh
    echo "   $(basename "$c"):"
    printf '%s' "$DEVIATIONS" | jq -c '[.[]|{field,value,registration,section}]' | sed 's/^/       /'
  )
done
rm -f tmp/_dev_block.sh

echo
echo "===== FIX 2: REGISTRATIONS gate list as the launcher defines it ====="
awk '/^REGISTRATIONS=\(/,/^\)/' scripts/launch_m7_virl_arm.sh | sed 's/^/   /'

echo
echo "===== registration requirement text, 1(b) ====="
grep -n -A4 -B2 'SANCTIONED_DEVIATIONS' docs/registered_m7_seed_scope_v1.md | sed 's/^/   /'
grep -n 'SANCTIONED_DEVIATIONS' -A12 scripts/build_m7_configs.py | head -30 | sed 's/^/   /'

echo
echo "===== 3b. ARM 1 STILL ALIVE AFTER ALL PROBES ====="
ssh -o ConnectTimeout=25 an12 "pgrep -a -f 'verl.trainer.mai[n]'; echo '-- kill -0 687841:'; kill -0 687841 && echo ALIVE || echo DEAD; echo '-- etime:'; ps -o pid,etime,stat,pcpu --pid 687841 --no-headers" 2>&1 | sed 's/^/   /'
echo "-- latest checkpoint step for arm 1:"
ls -1d experiments/runs/m7_virl_a1_real_seed1_an12_20260728T102036Z/../../../ >/dev/null 2>&1
"$PY" - <<'PYEOF'
import glob, os, re
cands = glob.glob("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/**/m7_virl_a1_real_seed1*/global_step_*", recursive=True)
steps = sorted({int(re.search(r"global_step_(\d+)", c).group(1)) for c in cands if re.search(r"global_step_(\d+)", c)})
print("   global_step dirs:", steps[-8:] if steps else "none found")
PYEOF
tail -3 experiments/runs/m7_virl_a1_real_seed1_an12_20260728T102036Z/logs/an12.log 2>&1 | sed 's/^/   /'
