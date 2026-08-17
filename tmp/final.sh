#!/usr/bin/env bash
export PATH=$HOME/.local/bin:$PATH
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
echo "=== storage usage snapshot (gates checkpoint writes) ==="
stat -c '%y %n' reports/storage_usage_snapshot.json
jq -r 'to_entries|map("\(.key)=\(.value)")|join("  ")' reports/storage_usage_snapshot.json 2>/dev/null | head -3
echo "=== quota root usage ==="
du -sh --exclude=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/artifacts /XYFS02/HDD_POOL/paratera_xy/pxy1289 2>/dev/null | tail -1 || echo "du skipped"
echo "=== push to remote ==="
git push origin HEAD:agent/gate2-recovery 2>&1 | tail -5
echo "=== post-push ==="
git log --oneline -1
git rev-parse HEAD origin/agent/gate2-recovery
