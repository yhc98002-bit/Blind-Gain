#!/bin/bash
set -euo pipefail
R=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$R"
rm -f tmp/probe_g02.py tmp/probe2.py
git add scripts/build_g02_necessity_refinement.py \
        reports/g02_necessity_refinement_v1.json \
        reports/g02_necessity_refinement_v1.md
git status --short -- scripts/build_g02_necessity_refinement.py reports/g02_necessity_refinement_v1.json reports/g02_necessity_refinement_v1.md
git commit -F - <<'MSG'
G0.2 necessity refinement addendum: ratio CIs, B1/B2 split, label fix

Addendum to Gate 0 G0.2. Frozen reports/gate0_stratification_v1.json is NOT
modified. CPU only, cached predictions, no GPU job.

- Reproduces the published 84% / 42% (and base-wrong 91% / 61%) exactly from
  G0_2_headroom_control; max abs deviation 2.8e-17.
- First intervals ON THE RATIOS anywhere in the repo (10,000 draws, seed
  20260730, paired on items, percentile 2.5/97.5). Lenient 0.8435
  [0.68, 1.01] vs 0.4167 [0.28, 0.54]; strict 0.8971 [0.79, 1.01] vs 0.5987
  [0.52, 0.68]. Intervals do NOT overlap under either scoring.
- Label defect: the n=484 stratum published as "items requiring pixels" is
  defined only by absence of blind success. 252/484 have zero observed
  successes WITH the image too. Decomposed: B1 (n=232, image demonstrably buys
  reward opportunity) recovery 0.5252 [0.38, 0.66]; B2 (n=252, never solved
  under any condition) 0.1163 [-0.26, 0.36], interval includes zero.
- Difficulty-standardised pair (common q_real distribution, all five bins have
  support, weight mass 1.0000, min cell n=18): lenient 0.8045 [0.59, 1.03] vs
  0.4472 [0.32, 0.56]. Reported as sensitivity; the c_real=0 bin carries 0.463
  of the target weight off only 26 blind-answerable items.
- Split-rule audit: q_i = 1 - p^g - (1-p)^g is symmetric in p, so the builder's
  numeric floor rule misclassifies one item with 16/16 blind successes as
  not-blind-answerable. Registered rule (prereg: floor is exactly c_i=0) gives
  118/483 rather than 117/484. Lenient ratios unchanged (the item has zero
  lenient gain); strict ratios shift in the fourth decimal. Reported, not
  applied -- re-running Gate 0 is a PI decision.
- Lenient and strict reported throughout (I7). Never merged with the Delta-q
  tercile analysis (I13).
- Old 42% marked SUPERSEDED AS LABELLED, RETAINED AS A NUMBER; proposed
  replacement wording supplied for the PI. No doc prose edited.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
git log --oneline -1
git rev-parse --abbrev-ref HEAD
