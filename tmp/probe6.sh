#!/bin/bash
R=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd $R
for d in experiments/runs/m7_virl_a1_real_seed1_an12_20260728T102036Z experiments/runs/m7_virl_a2_gray_seed1_an12_20260730T121803Z experiments/runs/m7_virl_a2b_noimage_seed1_an29_20260730T121834Z; do
  echo "########## $d"
  L=$(ls $d/logs/*.log 2>/dev/null | head -1)
  echo "log: $L  size=$(stat -c%s $L 2>/dev/null)  mtime=$(stat -c%y $L 2>/dev/null)"
  echo "-- step lines (last 6):"
  grep -oE "step:?[ =]?[0-9]+" "$L" 2>/dev/null | tail -6
  echo "-- any 'Training Progress' / tqdm-ish tail:"
  tail -c 3000 "$L" 2>/dev/null | tr '\r' '\n' | grep -vE "^\s*$" | tail -8
  echo "-- checkpoints on disk:"
  CP=$(python3 -c "import yaml,sys;print(yaml.safe_load(open('$d/effective_config.yaml'))['trainer']['save_checkpoint_path'])" 2>/dev/null)
  echo "path: $CP"
  ls -la "$CP" 2>&1 | head -12
  du -sh "$CP" 2>/dev/null
  echo "-- reward_shadow lines:"
  wc -l $d/reward_shadow.jsonl 2>/dev/null
done
