#!/usr/bin/env bash
export PATH=$HOME/.local/bin:$PATH
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
echo "NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "== arm 1 liveness, kill -0 executed ON an12 =="
ssh -o ConnectTimeout=25 an12 'bash -s' <<'EOF'
if kill -0 687841 2>/dev/null; then echo "  pid 687841: ALIVE"; else echo "  pid 687841: DEAD"; fi
ps -o pid,etime,stat,pcpu --pid 687841 --no-headers | sed 's/^/  ps: /'
EOF

echo "== all four M7 arm run statuses (manifest + live process) =="
for d in m7_virl_a1_real_seed1_an12_20260728T102036Z \
         m7_virl_a2_gray_seed1_an12_20260730T121803Z \
         m7_virl_a2b_noimage_seed1_an29_20260730T121834Z \
         m7_virl_a3_caption_seed1_an29_20260730T121906Z; do
  m="$ROOT/experiments/runs/$d/run_manifest.json"
  if [ ! -f "$m" ]; then echo "  $d: NO MANIFEST"; continue; fi
  node=$(jq -r .node "$m"); gp=$(jq -c .gpu_ids "$m"); st=$(jq -r .status "$m")
  ndev=$(jq '.deviations|length' "$m")
  pid=$(cat "$ROOT/experiments/runs/$d/pids/$node.pid" 2>/dev/null)
  alive=$(ssh -o ConnectTimeout=25 "$node" "kill -0 $pid 2>/dev/null && echo ALIVE || echo GONE" 2>/dev/null)
  printf '  %-50s node=%s gpus=%s status=%s devs=%s pid=%s proc=%s\n' \
    "$d" "$node" "$gp" "$st" "$ndev" "$pid" "$alive"
  stat -c "       log mtime: %y" "$ROOT/experiments/runs/$d/logs/$node.log" 2>/dev/null
done

echo "== a3_caption log tail (absent from an29 pgrep a moment ago) =="
tail -4 "$ROOT/experiments/runs/m7_virl_a3_caption_seed1_an29_20260730T121906Z/logs/an29.log" 2>&1 | cut -c1-180 | sed 's/^/  /'
