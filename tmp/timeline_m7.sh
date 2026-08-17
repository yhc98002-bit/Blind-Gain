#!/usr/bin/env bash
export PATH=$HOME/.local/bin:$PATH
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
echo "NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "== start times / GPUs of the four M7 arms and the two M5C evals =="
for d in m7_virl_a3_caption_seed1_an29_20260730T121906Z \
         m7_virl_a2b_noimage_seed1_an29_20260730T121834Z \
         m5c_sampled_m5c-taskb-step400_an29_gpu4_20260730T122620Z \
         m5c_sampled_m5c-taskb-step100-repro_an29_gpu5_20260730T122701Z; do
  m="$ROOT/experiments/runs/$d/run_manifest.json"
  if [ -f "$m" ]; then
    printf '  %-58s start=%s node=%s gpus=%s\n' "$d" \
      "$(jq -r '.start_time_utc // "n/a"' "$m")" "$(jq -r '.node // "n/a"' "$m")" \
      "$(jq -c '.gpu_ids // .gpu_id // "n/a"' "$m")"
  else
    printf '  %-58s (no run_manifest.json)\n' "$d"
    ls -1 "$ROOT/experiments/runs/$d" 2>/dev/null | head -4 | sed 's/^/       /'
  fi
done
echo "== arm 1 final liveness (kill -0 on an12) =="
ssh -o ConnectTimeout=25 an12 'kill -0 687841 2>/dev/null && echo "  pid 687841 ALIVE" || echo "  pid 687841 DEAD"; ps -o pid,etime,pcpu --pid 687841 --no-headers | sed "s/^/  /"'
echo "== an12 GPU 0-3 still arm 1 only =="
ssh -o ConnectTimeout=25 an12 'nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader | head -8 | sed "s/^/  /"'
echo "== pushed state =="
git log --oneline -1 | cat
git branch -r --contains ed4aa962f2bd945638b0183316be73137299cbcd | cat
