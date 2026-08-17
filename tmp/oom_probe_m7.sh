#!/usr/bin/env bash
export PATH=$HOME/.local/bin:$PATH
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
echo "NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "== an29 current per-GPU compute apps (index resolved) =="
ssh -o ConnectTimeout=25 an29 'bash -s' <<'EOF'
nvidia-smi --query-gpu=index,uuid --format=csv,noheader,nounits > /tmp/idx.$$
nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader,nounits > /tmp/apps.$$
while IFS=, read -r uuid pid mem; do
  uuid=$(echo "$uuid"|tr -d ' '); pid=$(echo "$pid"|tr -d ' '); mem=$(echo "$mem"|tr -d ' ')
  idx=$(grep -F "$uuid" /tmp/idx.$$ | cut -d, -f1 | tr -d ' ')
  owner=$(ps -o user=,args= --pid "$pid" 2>/dev/null | cut -c1-110)
  echo "  gpu$idx pid=$pid mem=${mem}MiB  $owner"
done < /tmp/apps.$$
rm -f /tmp/idx.$$ /tmp/apps.$$
echo "  -- process 1475268:"
ps -o pid,ppid,user,etime,args --pid 1475268 --no-headers 2>/dev/null | cut -c1-160 || echo "     gone"
echo "  -- all python procs referencing a3_caption or mini_a5 / ranking:"
pgrep -a -f 'a3_caption|mini_a5|rank' 2>/dev/null | cut -c1-160 | sed 's/^/     /'
EOF

echo "== first OOM occurrence + surrounding context in a3_caption log =="
grep -n -m1 -B4 'OutOfMemoryError' "$ROOT/experiments/runs/m7_virl_a3_caption_seed1_an29_20260730T121906Z/logs/an29.log" | cut -c1-200 | sed 's/^/  /'
echo "== full OOM line =="
grep -o 'GPU [0-9] has a total capacity[^.]*\.[^.]*\.' "$ROOT/experiments/runs/m7_virl_a3_caption_seed1_an29_20260730T121906Z/logs/an29.log" | head -2 | sed 's/^/  /'
grep -o 'Process [0-9]* has [0-9.]* GiB memory in use' "$ROOT/experiments/runs/m7_virl_a3_caption_seed1_an29_20260730T121906Z/logs/an29.log" | sort -u | sed 's/^/  /'
echo "== CUDA_VISIBLE_DEVICES recorded in a3_caption manifest command =="
jq -r '.command' "$ROOT/experiments/runs/m7_virl_a3_caption_seed1_an29_20260730T121906Z/run_manifest.json" | grep -o "CUDA_VISIBLE_DEVICES='[^']*'" | sed 's/^/  /'
echo "== a2b_noimage CUDA_VISIBLE_DEVICES =="
jq -r '.command' "$ROOT/experiments/runs/m7_virl_a2b_noimage_seed1_an29_20260730T121834Z/run_manifest.json" | grep -o "CUDA_VISIBLE_DEVICES='[^']*'" | sed 's/^/  /'
echo "== any Mini-A5 / eval run dirs touched today =="
ls -1dt "$ROOT"/experiments/runs/*mini_a5* 2>/dev/null | head -5 | sed 's/^/  /'
find "$ROOT/experiments/runs" -maxdepth 1 -newermt '2026-07-30 18:00' -type d 2>/dev/null | head -12 | sed 's/^/  /'
