#!/usr/bin/env bash
set -uo pipefail
ROOT=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$ROOT"

git add \
  src/eval/layer1_blind.py \
  tests/test_layer1_blind.py \
  configs/eval/layer1_blind_blink_3b.json configs/eval/layer1_blind_blink_7b.json \
  configs/eval/layer1_blind_hallusion_3b.json configs/eval/layer1_blind_hallusion_7b.json \
  configs/eval/layer1_blind_mmvp_3b.json configs/eval/layer1_blind_mmvp_7b.json \
  configs/eval/layer1_blind_mathverse_3b.json configs/eval/layer1_blind_mathverse_7b.json \
  configs/eval/layer1_blind_mmmu_3b.json configs/eval/layer1_blind_mmmu_7b.json \
  scripts/run_e1c_blind_queue.py \
  scripts/e1c_blind_columns.py \
  scripts/render_e1c_blind_columns_md.py \
  scripts/verify_e1c_blind_cells.py \
  reports/e1c_blind_columns_v1.json \
  reports/e1c_blind_columns_v1.md

git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -F - <<'MSG'
E1c: blind columns for the five benchmarks that had none

reports/chance_corrected_retention_v1.json recorded BLINK, HallusionBench,
MMVP, MathVerse and MMMU as having an image-present column but no
image-removed run anywhere, so no retention figure existed for them. This
adds the blind column at both scales, taking the F0 visual-necessity audit
from 2 benchmarks to 7.

src/eval/layer1_blind.py grew five dataset types. Each blind builder mirrors
the VLMEvalKit class that produced the paired with-image column:
ImageMCQDataset for BLINK/MMVP (the same builder MMStar already used),
ImageBaseDataset for HallusionBench and MathVerse, and for MMMU
ImageMCQDataset followed by the "<image N>" marker deletion that split_MMMU
performs when it interleaves real images. MMStar deliberately keeps those
markers, because plain ImageMCQDataset leaves them in its text.

10 cells ran on an29 GPU 6/7, all exit 0, all image_removed=true, all row
counts equal to the paired with-image column. option_labels and gold agree
with the with-image artifacts on every row of every benchmark, and the k
distributions reproduce the with_image_run_k_availability block of the
chance report exactly.

Null rule carried forward unchanged: per-item 1/k for MC, 0 for free-form,
0 when the gold label is absent. MathVerse and MMMU are split by format and
never given a single global null (I18). HallusionBench is reported as
free-form (null=0) as the primary, since zero option labels are presented,
with a labelled null=0.5 sensitivity for its binary Yes/No answer space.

Three findings recorded rather than smoothed over:
- 178 of the 1129 HallusionBench rows are text-only in the source and were
  given a deterministic blank image, so the blind condition removes nothing
  for them. Split out, they show naive retention 1.011 (3B), which doubles
  as a positive control on the pipeline; the real-image rows retain 0.761.
- MathVerse items 2956-2960 carry a with-image gold of '0' where the pinned
  TSV has '=\frac{7}{4}': Excel coerced the leading '=' into a formula when
  VLMEvalKit wrote the xlsx. They are excluded from the paired primary.
- Where mean(with_image) equals mean(null) the corrected denominator is 0 and
  landed on ~1e-16, which produced a ~1e15 ratio; guarded, and those cells
  now report corrected_retention=null.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG

echo "=== commit ==="
git log --oneline -1
git rev-parse HEAD
