#!/bin/bash
set -euo pipefail
R=/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
cd "$R"
git add scripts/build_g02_necessity_refinement.py \
        reports/g02_necessity_refinement_v1.json \
        reports/g02_necessity_refinement_v1.md
git status --short
git commit -F - <<'MSG'
G0.2 addendum: record prose-target drift in the wording proposal

docs/PAPER1_RESEARCH_DOC.md was modified in the working tree by a concurrent
session at 2026-07-30 15:39Z, while this addendum was being built. The change is
uncommitted. In that modified copy the Gate-0 paragraph quoted as "current" in
the wording proposal no longer exists; the only surviving anchor is the summary
clause "the access matrix plus the 84%/42% stratification".

Records the drift in d5_wording_proposal.prose_target_drift_observed and in the
report so the PI applies the wording to current text rather than to a stale
quote. The EXPERIMENT_TODO.md:52 target is unaffected and its quote is accurate.
Numbers and conclusions are unchanged.

This analysis edited no doc: the builder has exactly two write targets,
reports/g02_necessity_refinement_v1.{json,md}. The concurrent docs changes are
left uncommitted and untouched.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
MSG
git log --oneline -2
PROXY="http://127.0.0.1:7890"
git -c http.proxy=$PROXY push origin agent/gate2-recovery 2>&1 | tail -3
git -c http.proxy=$PROXY push origin agent/gate2-recovery:master 2>&1 | tail -3
git -c http.proxy=$PROXY ls-remote origin agent/gate2-recovery master 2>&1 | tail -3
