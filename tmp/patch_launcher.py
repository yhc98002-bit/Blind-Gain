#!/usr/bin/env python3
"""Add VIRL_* env overrides to scripts/launch_virl39k_blind_v1_condition.sh.

Every default is unchanged, so a default invocation generates a byte-identical
COMMAND (verified by tmp/capture_default_commands.sh before/after).
"""
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")


def sub(old: str, new: str) -> None:
    global text
    if text.count(old) != 1:
        raise SystemExit(f"expected exactly 1 occurrence, found {text.count(old)}:\n{old}")
    text = text.replace(old, new)


# 1. Manifest / sample spec / splits / caption shards become overridable.
sub(
    'MANIFEST="data/virl39k_blind_sample_4096.jsonl"\n'
    'SAMPLE_SPEC="reports/virl39k_blind_sample_4096.json"\n',
    'MANIFEST="${VIRL_MANIFEST:-data/virl39k_blind_sample_4096.jsonl}"\n'
    'SAMPLE_SPEC="${VIRL_SAMPLE_SPEC:-reports/virl39k_blind_sample_4096.json}"\n'
    'SPLITS="${VIRL_SPLITS:-audit}"\n',
)
sub(
    'CAPTION_EXPECTED_SHARDS="${VIRL_CAPTION_EXPECTED_SHARDS:-3}"\n',
    'CAPTION_EXPECTED_SHARDS="${VIRL_CAPTION_EXPECTED_SHARDS:-3}"\n'
    '# Space-separated caption-store files. When set, these are used verbatim and the\n'
    '# sharded CAPTION_RUN layout (run_manifest.json + shards/) is not consulted.\n'
    'CAPTION_SHARDS="${VIRL_CAPTION_SHARDS:-}"\n',
)

# 2. Validate the new knobs alongside the existing validation block.
sub(
    'if [[ ! "${CAPTION_EXPECTED_SHARDS}" =~ ^[1-9][0-9]*$ ]]; then\n'
    '  echo "VIRL_CAPTION_EXPECTED_SHARDS must be positive" >&2\n'
    '  exit 2\n'
    'fi\n',
    'if [[ ! "${CAPTION_EXPECTED_SHARDS}" =~ ^[1-9][0-9]*$ ]]; then\n'
    '  echo "VIRL_CAPTION_EXPECTED_SHARDS must be positive" >&2\n'
    '  exit 2\n'
    'fi\n'
    'if [[ -z "${SPLITS// }" ]]; then\n'
    '  echo "VIRL_SPLITS must name at least one split" >&2\n'
    '  exit 2\n'
    'fi\n',
)

# 3. Caption sources: honour an explicit shard list, else the sharded run dir.
sub(
    'if [[ "${CONDITION}" == "caption" ]]; then\n'
    '  if ! jq -e \'(.status == "complete") and (.max_new_tokens == 384)\' "${CAPTION_RUN}/run_manifest.json" >/dev/null; then\n'
    '    echo "Fixed ViRL39K caption store is not complete" >&2\n'
    '    exit 2\n'
    '  fi\n'
    "  mapfile -t CAPTION_FILES < <(find \"${CAPTION_RUN}/shards\" -maxdepth 1 -type f -name 'store_shard_*.jsonl' -size +0c | sort)\n"
    '  if [[ "${#CAPTION_FILES[@]}" -ne "${CAPTION_EXPECTED_SHARDS}" ]]; then\n'
    '    echo "Fixed ViRL39K caption store has ${#CAPTION_FILES[@]} shards; expected ${CAPTION_EXPECTED_SHARDS}" >&2\n'
    '    exit 2\n'
    '  fi\n'
    '  printf -v CAPTION_ARGS \' %q\' "${CAPTION_FILES[@]}"\n'
    '  CAPTION_ARGS="--caption-shards${CAPTION_ARGS}"\n'
    '  DATA_FILES+=("${CAPTION_RUN}/run_manifest.json" "${CAPTION_FILES[@]}")\n'
    'fi\n',
    'if [[ "${CONDITION}" == "caption" ]]; then\n'
    '  if [[ -n "${CAPTION_SHARDS}" ]]; then\n'
    '    read -r -a CAPTION_FILES <<< "${CAPTION_SHARDS}"\n'
    '    if [[ "${#CAPTION_FILES[@]}" -eq 0 ]]; then\n'
    '      echo "VIRL_CAPTION_SHARDS is set but names no files" >&2\n'
    '      exit 2\n'
    '    fi\n'
    '    for shard in "${CAPTION_FILES[@]}"; do\n'
    '      if [[ ! -s "${shard}" ]]; then\n'
    '        echo "VIRL_CAPTION_SHARDS entry is absent or empty: ${shard}" >&2\n'
    '        exit 2\n'
    '      fi\n'
    '    done\n'
    '    printf -v CAPTION_ARGS \' %q\' "${CAPTION_FILES[@]}"\n'
    '    CAPTION_ARGS="--caption-shards${CAPTION_ARGS}"\n'
    '    DATA_FILES+=("${CAPTION_FILES[@]}")\n'
    '  else\n'
    '    if ! jq -e \'(.status == "complete") and (.max_new_tokens == 384)\' "${CAPTION_RUN}/run_manifest.json" >/dev/null; then\n'
    '      echo "Fixed ViRL39K caption store is not complete" >&2\n'
    '      exit 2\n'
    '    fi\n'
    "    mapfile -t CAPTION_FILES < <(find \"${CAPTION_RUN}/shards\" -maxdepth 1 -type f -name 'store_shard_*.jsonl' -size +0c | sort)\n"
    '    if [[ "${#CAPTION_FILES[@]}" -ne "${CAPTION_EXPECTED_SHARDS}" ]]; then\n'
    '      echo "Fixed ViRL39K caption store has ${#CAPTION_FILES[@]} shards; expected ${CAPTION_EXPECTED_SHARDS}" >&2\n'
    '      exit 2\n'
    '    fi\n'
    '    printf -v CAPTION_ARGS \' %q\' "${CAPTION_FILES[@]}"\n'
    '    CAPTION_ARGS="--caption-shards${CAPTION_ARGS}"\n'
    '    DATA_FILES+=("${CAPTION_RUN}/run_manifest.json" "${CAPTION_FILES[@]}")\n'
    '  fi\n'
    'fi\n',
)

# 4. COMMAND honours the split override.
sub("--splits audit --batch-size 2", "--splits ${SPLITS} --batch-size 2")

# 5. The recorded manifest must name the data it actually used.
sub(
    '    data_manifest: "data/virl39k_blind_sample_4096.jsonl",\n',
    "    data_manifest: $data_manifest,\n",
)
sub(
    '    sample_spec: "reports/virl39k_blind_sample_4096.json",\n',
    "    sample_spec: $sample_spec,\n",
)
sub(
    '  --arg caption_run "${CAPTION_RUN}" \\\n',
    '  --arg caption_run "${CAPTION_RUN}" \\\n'
    '  --arg caption_shards "${CAPTION_SHARDS}" \\\n'
    '  --arg data_manifest "${MANIFEST}" \\\n'
    '  --arg sample_spec "${SAMPLE_SPEC}" \\\n'
    '  --arg splits "${SPLITS}" \\\n',
)
sub(
    "    caption_source_run: (if $condition == \"caption\" then $caption_run else null end),\n",
    "    splits: ($splits | split(\" \") | map(select(length > 0))),\n"
    "    caption_source_run: (if $condition == \"caption\" and $caption_shards == \"\" then $caption_run else null end),\n"
    "    caption_shards: (if $condition == \"caption\" and $caption_shards != \"\"\n"
    "                     then ($caption_shards | split(\" \") | map(select(length > 0)))\n"
    "                     else null end),\n",
)

path.write_text(text, encoding="utf-8")
print("patched", path)
