#!/usr/bin/env bash
# Dry-probe of the C5 reservation-claim mechanism against real node state.
# Creates a fake claim on an12 gpu0 (already busy with M7, so nothing can be
# granted or denied that was not already), checks the guard lists and refuses
# it, backdates it past expiry, checks the claim disappears from claim
# occupancy, and removes it. NOTHING IS LAUNCHED.
set -uo pipefail
ROOT="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
cd "${ROOT}"
CLAIM_DIR="/dev/shm/blind-gains/gpu_claims"
CLAIM="${CLAIM_DIR}/an12_gpu0.claim"

echo "=== step 1: place fresh fake claim on an12 gpu0"
ssh -o ConnectTimeout=25 an12 "mkdir -p '${CLAIM_DIR}' && printf '%s\n' '{\"schema_version\":\"blind-gains.gpu-claim.v1\",\"run_id\":\"c5_dryprobe_claim_test\",\"node\":\"an12\",\"gpu\":0,\"pid\":null,\"created_utc\":\"probe\",\"purpose\":\"dry-probe, delete on sight\"}' > '${CLAIM}'"

echo "=== step 2: guard must refuse gpu0 and list the claim"
.venv/bin/python scripts/m7_gpu_occupancy_guard.py --node an12 --gpus 0
RC_FRESH=$?
echo "guard exit (expect 75): ${RC_FRESH}"

echo "=== step 3: backdate the claim 40 minutes"
ssh -o ConnectTimeout=25 an12 "touch -d '40 minutes ago' '${CLAIM}'"

echo "=== step 4: guard runs again; claim-file occupancy must be empty now"
.venv/bin/python scripts/m7_gpu_occupancy_guard.py --node an12 --gpus 0
RC_EXPIRED=$?
echo "guard exit (expect 75, from compute apps only): ${RC_EXPIRED}"

echo "=== step 5: remove the fake claim"
ssh -o ConnectTimeout=25 an12 "rm -f '${CLAIM}'"
echo "probe done"
