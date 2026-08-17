#!/usr/bin/env bash
# Adversarial byte-stability check, independent of the implementer's harness.
# git-HEAD script vs working-tree script, IDENTICAL CLI, IDENTICAL output paths.
set -euo pipefail
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain

ADV=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/tmp/adv_r3_verify
rm -rf "$ADV" adv_old_src adv_new_src
mkdir -p "$ADV/run" adv_old_src adv_new_src

git show HEAD:scripts/build_m7_r3_readout.py > adv_old_src/build_m7_r3_readout.py
cp scripts/build_m7_r3_readout.py adv_new_src/build_m7_r3_readout.py
sha256sum adv_old_src/build_m7_r3_readout.py adv_new_src/build_m7_r3_readout.py

run_one () {
  local SRC="$1"
  local TAG="$2"
  rm -rf "$ADV/run/artifacts" "$ADV/run/out.json" "$ADV/run/out.md"
  PYTHONPATH=. .venv/bin/python "$SRC/build_m7_r3_readout.py" \
    --step0 a1_real=experiments/runs/m7_step0_heldout_base_real_an29_20260730T154447Z \
    --step0 a2_gray=experiments/runs/m7_step0_heldout_base_gray_an29_20260730T154458Z \
    --step0 a2b_noimage=experiments/runs/m7_step0_heldout_base_none_an29_20260730T154501Z \
    --step0 a3_caption=experiments/runs/m7_step0_heldout_base_caption_an29_20260730T154503Z \
    --step100 a1_real=experiments/runs/m7_step100_heldout_a1_real_an29_20260731T161352Z \
    --step100 a2_gray=experiments/runs/m7_step100_heldout_a2_gray_gray_an12_20260803T151508Z \
    --step100 a2b_noimage=experiments/runs/m7_step100_heldout_a2b_none_an29_20260801T014325Z \
    --step100 a3_caption=experiments/runs/m7_step100_heldout_a3_caption_caption_an12_20260803T151440Z \
    --json-output "$ADV/run/out.json" \
    --markdown-output "$ADV/run/out.md" \
    --artifact-dir "$ADV/run/artifacts" > "$ADV/run/$TAG.stdout" 2>&1
  mkdir -p "$ADV/$TAG"
  mv "$ADV/run/out.json" "$ADV/$TAG/out.json"
  mv "$ADV/run/out.md" "$ADV/$TAG/out.md"
  cp -r "$ADV/run/artifacts" "$ADV/$TAG/artifacts"
}

echo "=== RUN OLD (git HEAD) ==="
run_one adv_old_src old
echo "=== RUN NEW (working tree) ==="
run_one adv_new_src new

echo "=== BYTE DIFF old vs new ==="
if diff -q "$ADV/old/out.json" "$ADV/new/out.json"; then echo "JSON: BYTE-IDENTICAL"; else echo "JSON: DIFFERS"; diff "$ADV/old/out.json" "$ADV/new/out.json" | head -40; fi
if diff -q "$ADV/old/out.md" "$ADV/new/out.md"; then echo "MD: BYTE-IDENTICAL"; else echo "MD: DIFFERS"; diff "$ADV/old/out.md" "$ADV/new/out.md" | head -40; fi
echo "=== artifact listings ==="
ls "$ADV/old/artifacts"; echo "--"; ls "$ADV/new/artifacts"
if diff -r -q "$ADV/old/artifacts" "$ADV/new/artifacts"; then echo "ARTIFACTS: IDENTICAL"; else echo "ARTIFACTS: DIFFER"; fi

echo "=== NEW vs PUBLISHED json ==="
PYTHONPATH=. .venv/bin/python experiments/scratch_twoseed/compare_replay.py reports/m7_r3_readout_v1.json "$ADV/new/out.json" | tail -20
echo "=== NEW md vs PUBLISHED md (artifact path normalized) ==="
sed "s#$ADV/run/artifacts#reports/m7_r3_readout_v1_artifacts#g" "$ADV/new/out.md" > "$ADV/new/out.norm.md"
if diff -q reports/m7_r3_readout_v1.md "$ADV/new/out.norm.md"; then echo "MD-vs-PUBLISHED: IDENTICAL AFTER PATH NORMALIZATION"; else echo "MD-vs-PUBLISHED: DIFFERS"; diff reports/m7_r3_readout_v1.md "$ADV/new/out.norm.md" | head -40; fi
echo "=== published artifact jsonl vs replay artifact jsonl ==="
for f in reports/m7_r3_readout_v1_artifacts/*.jsonl; do
  b=$(basename "$f")
  if [ -f "$ADV/new/artifacts/$b" ]; then
    if diff -q "$f" "$ADV/new/artifacts/$b" >/dev/null; then echo "SAME  $b"; else echo "DIFF  $b"; fi
  else
    echo "MISSING-IN-REPLAY  $b"
  fi
done
rm -rf adv_old_src adv_new_src
echo "ADV_DONE"
