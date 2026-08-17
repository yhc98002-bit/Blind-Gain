#!/bin/bash
# Commit ONLY the R3 readout script and its fixture tests.
# git commit --only <paths> so a concurrent session's staged files cannot be
# swept into this commit (deviations-log row 2026-07-30T15:52Z lesson).
set -u
cd /XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain
git branch --show-current
git commit --only scripts/build_m7_r3_readout.py tests/test_m7_r3_readout_fixture.py -F tmp/commit_msg_r3_readout.txt
echo "commit_exit=$?"
git log -1 --stat | head -20
