#!/usr/bin/env bash
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT" || exit 1
export PATH="$HOME/.local/bin:$PATH"

echo "host=$(hostname)"
git add scripts/launch_virl39k_blind_v1_condition.sh \
        scripts/build_m7_heldout_eval_manifest.py \
        reports/virl39k_m7_heldout_v3_sample.json || exit 1

git commit -F - <<'MSG'
R3: parameterise ViRL39K blind launcher for the M7 held-out step-0 evals

scripts/launch_virl39k_blind_v1_condition.sh gains four env overrides in the
idiom already used by VIRL_MODEL_PATH / VIRL_CAPTION_RUN / VIRL_RUN_PREFIX:

  VIRL_MANIFEST        eval manifest        (default data/virl39k_blind_sample_4096.jsonl)
  VIRL_SAMPLE_SPEC     sample spec          (default reports/virl39k_blind_sample_4096.json)
  VIRL_SPLITS          --splits value       (default audit)
  VIRL_CAPTION_SHARDS  explicit caption files; when set, the sharded
                       CAPTION_RUN layout is not consulted
                       (default empty -> unchanged sharded behaviour)

The recorded run manifest now names the data it actually used (data_manifest /
sample_spec were hardcoded string literals) and records `splits` and
`caption_shards`.

Every default is unchanged. Verified by capturing the generated COMMAND from an
instrumented copy of the launcher, with a pinned timestamp, for all five
conditions before and after the change: both captures hash to
ebdcbb420e156df60957e8888f6b93ef4d879a55c22afd5ed741ebf9fc74b2e4.

scripts/build_m7_heldout_eval_manifest.py derives an eval-harness-schema
manifest from the frozen held-out split. data/virl39k_m7_heldout_v3.jsonl is
written in the *training* schema, where `images` is a list of path strings and
the digests live in metadata.image_sha256. The eval harness requires
`images[i]["path"]` and `images[i]["sha256"]`
(src/eval/conditioned_inputs.py::build_conditioned_messages, and
scripts/run_blind_solvability_v2.py which emits image_sha256 for *every*
condition). Feeding the training-schema file directly raises
`TypeError: string indices must be integers` -- confirmed empirically for
real/gray/caption; `none` fails later at the same field.

The derivation is a lossless re-shape: all other fields and the row order are
unchanged, and every digest is re-verified against the bytes on disk.
  source data/virl39k_m7_heldout_v3.jsonl
         sha256 50f3b85c11c4046ef2512c544faec04286648688bb6d47548995f18cab40716c
  output data/virl39k_m7_heldout_v3_eval.jsonl
         sha256 c0097102496b3d979f77fb1f19e4c277d0de6886f57683917613c4e03a898432
  4239 rows, all split=train, max_images_per_item=1, 3657 unique images,
  4239/4239 digests verified, caption coverage 3657/3657.

data/ is gitignored, so the manifest is committed as its generator plus
reports/virl39k_m7_heldout_v3_sample.json, which pins both hashes.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
rc=$?
echo "commit rc=${rc}"
git log --oneline -1
echo "=== push ==="
git -c http.proxy=http://127.0.0.1:7890 push origin agent/gate2-recovery
echo "push branch rc=$?"
git -c http.proxy=http://127.0.0.1:7890 push origin agent/gate2-recovery:master
echo "push master rc=$?"
