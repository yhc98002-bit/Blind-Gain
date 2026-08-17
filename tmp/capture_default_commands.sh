#!/usr/bin/env bash
# Capture the generated COMMAND for a DEFAULT (no VIRL_* overrides) invocation,
# for every condition, from an instrumented copy of the launcher.
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"

SRC="$1"   # launcher to instrument
OUT="$2"   # output file of captured COMMANDs

.venv/bin/python tmp/instrument.py "$SRC" tmp/_instrumented_launcher.sh >&2
chmod +x tmp/_instrumented_launcher.sh
: > "$OUT"
for cond in real gray noise none caption; do
  printf '### condition=%s\n' "$cond" >> "$OUT"
  env -u VIRL_MANIFEST -u VIRL_SAMPLE_SPEC -u VIRL_SPLITS -u VIRL_CAPTION_SHARDS \
      -u VIRL_MODEL_PATH -u VIRL_CAPTION_RUN -u VIRL_RUN_PREFIX -u VIRL_JOB_TYPE \
      bash tmp/_instrumented_launcher.sh an29 4 "$cond" dryrun >> "$OUT" 2>>"$OUT.err"
  printf 'exit=%s\n' "$?" >> "$OUT"
done
rm -f tmp/_instrumented_launcher.sh
wc -l "$OUT" >&2
