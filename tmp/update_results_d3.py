#!/usr/bin/env python3
from pathlib import Path

p = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/reports/RESULTS.md")
t = p.read_text()
if "## 4b. D3" in t:
    print("already present")
    raise SystemExit(0)

sec = """
---

## 4b. D3 — training condition vs test condition (COMPLETE, 36 cells)

Registered: `docs/registered_d3_condition_matrix_v1.md`. Acc_final by arm x test
condition, mean over three seeds (base row pinned: real 0.1747, gray 0.0899,
none 0.0682):

| arm (trained) | tested real | tested gray | tested none |
|---|---|---|---|
| A1 real | 0.4182 | 0.1093 | 0.1043 |
| A3 caption | 0.3494 | 0.1143 | 0.1054 |
| A2b no-image | 0.3034 | 0.1065 | 0.1143 |
| A2 gray | 0.2934 | 0.1059 | 0.1015 |

Recovery of the A1 gain, matched vs crossed evaluation (per seed):

| arm | matched recovery (own condition) | crossed recovery (tested with images) | ratio |
|---|---|---|---|
| A2 gray | 0.079 / 0.040 / 0.079 | 0.507 / 0.527 / 0.425 | 6.43 / 13.07 / 5.38 |
| A2b no-image | 0.119 / 0.223 / 0.230 | 0.572 / 0.493 / 0.518 | 4.83 / 2.21 / 2.25 |

**Registered branch (a) obtains** on the primary Acc_final criterion (ratio > 2
for both blind arms in all three seeds): the published low blind recovery
substantially reflects the *matched evaluation condition*. Per the pre-committed
consequence, the canonical claim carries the scope tag **"under matched
evaluation"**, with the crossed-condition figure reported alongside it.

**Format control, reported honestly.** Recomputed on Acc_strict with the
registered strict step-0 bases (real 0.0599, gray 0.0050, none 0.0017), the
ratios are 2.32 / 2.58 / 2.06 (A2 gray) and 2.69 / 1.95 / 1.96 (A2b). The
direction and rough magnitude reproduce, so the effect is not merely improved
answer formatting - but two of six seed-arm cells fall marginally BELOW the 2x
threshold, so the strict control does not cleanly clear the same bar. The
registration's format-control clause did not define "reproduce the pattern"
numerically; that ambiguity is resolved here by reporting both and qualifying
the claim, not by choosing the favourable reading.

Interpretation limit: A3's matched condition is `caption`, which is not part of
this matrix, so A3 is reported across real/gray/none only.
"""

anchor = "\n---\n\n## 5. The two-layer gap"
assert t.count(anchor) == 1, f"anchor count {t.count(anchor)}"
t = t.replace(anchor, sec + anchor, 1)
t = t.replace("| D3 train×test matrix | running, 19/36 cells |",
              "| D3 train×test matrix | **complete** - registered branch (a) |", 1)
p.write_text(t)
print("RESULTS.md updated in place")
