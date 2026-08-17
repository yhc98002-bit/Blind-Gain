#!/usr/bin/env bash
set -euo pipefail
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain

git add reports/f8_secondaries_v1.md \
        reports/mini_a5_s1_ranking_vs_generation_v1.json \
        scripts/analyze_mini_a5_s1.py

cat > /tmp/bg_commit_msg.txt <<'MSG'
F8 secondaries: run the one Mini-A5 secondary with an instrument, document the two without

Secondary 1 (free-generation vs candidate-ranking) RUN for both arms at step 120,
condition real, 1200/1200 rows each, exit 0, on an29:4 and an29:5. an29 was idle;
an12 GPUs 0-3 (M7 arm 1) untouched. Numbers reported per R19 template and never
pooled (I13), at both severities on both layers (I7). On the primary visual anchor
the ranking layer separates the arms under neither severity; the generation layer
separates them under contract-strict scoring only. All 12 ranking-minus-generation
intervals exclude zero positively.

Secondary 2 (catch-trial stability) reported INSTRUMENT-ABSENT on two verified
grounds: audit_mini_a5_catch.py instantiates no checkpoint (grep-clean across all
four transitive imports), and no existing metric field equals the invariance
criterion -- pair_score's `collapsed` is gated on answer_a != answer_b and is
therefore identically False on all 300 equal-gold catch pairs, confirmed by running
the metric on a case that agrees but is wrong. Scorer specified, not built.

Secondary 3 ("the registered task benchmark") reported UNRESOLVABLE: one binding
occurrence, four self-references, zero referents; both training configs carry
val_freq 0 / val_before_train false at the registered hashes; "benchmark" absent
from both PAPER research docs. Geometry3K named as nearest convention referent and
explicitly NOT adopted -- the convention arms train on Geometry3K, the Mini-A5 arms
do not.

Verification: every rate recomputed independently from the raw score files;
pair_success re-derived from raw margins; generation rates cross-checked against the
published F8 readout; McNemar checked against scipy.stats.binomtest (max diff
5.6e-17); the four shared config blocks verified byte-identical to the x5 config.
Disclosed deviation: bootstrap seeds derived from the pinned base 20260729, which
moves one CI lower bound by one pair-width (0.0433 vs 0.0417) against the F8 file
with no change to point estimate, p-value or conclusion.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG

git commit -F /tmp/bg_commit_msg.txt
rm -f /tmp/bg_commit_msg.txt
git log --oneline -1
