#!/usr/bin/env bash
# read-only dry-proof of FIX 2: the deviations array is derived from the config.
# Re-executes the exact derivation lines now in scripts/launch_m7_virl_arm.sh.
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "${ROOT}"
for EFFECTIVE in configs/train/m7_virl_a1_real_seed1_3b.yaml \
                 configs/train/m7_virl_a2_gray_seed1_3b.yaml \
                 configs/train/m7_virl_a2b_noimage_seed1_3b.yaml \
                 configs/train/m7_virl_a3_caption_seed1_3b.yaml; do
SAVE_MODEL_ONLY="$(python3 -c 'import yaml,sys; print(str(bool(yaml.safe_load(open(sys.argv[1]))["trainer"].get("save_model_only", False))).lower())' "${EFFECTIVE}")"
SAVE_FREQ="$(python3 -c 'import yaml,sys; print(int(yaml.safe_load(open(sys.argv[1]))["trainer"]["save_freq"]))' "${EFFECTIVE}")"
if [[ "${SAVE_MODEL_ONLY}" == "true" ]]; then
  DEVIATIONS="$(jq -n --argjson freq "${SAVE_FREQ}" \
    '[{field:"trainer.save_model_only",value:true,
       registration:"docs/registered_m7_seed_scope_v1.md",section:"1(b)",
       sanctioned_in:"scripts/build_m7_configs.py:SANCTIONED_DEVIATIONS",
       save_freq_unchanged:$freq,
       effect:"Checkpoints hold HF weights only (~7.6 GB) instead of full FSDP state including optimizer shards (~38.5 GB). save_freq is unchanged, so the registered matched checkpoint CADENCE holds and only the on-disk FORMAT differs; the cost is that this arm cannot be resumed mid-run."}]')"
else
  DEVIATIONS='[]'
fi
echo "== ${EFFECTIVE}: save_model_only=${SAVE_MODEL_ONLY} save_freq=${SAVE_FREQ}"
printf '   manifest deviations -> %s\n' "$(printf '%s' "${DEVIATIONS}" | jq -c .)"
done
echo "== REGISTRATIONS gate list now at HEAD-check time:"
grep -n "registered_m7_seed_scope_v1.md" scripts/launch_m7_virl_arm.sh
echo "== jq availability: $(command -v jq)"
