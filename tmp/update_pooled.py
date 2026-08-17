#!/usr/bin/env python3
from pathlib import Path

p = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/reports/RESULTS.md")
t = p.read_text()
if "## 2b. Pooled item-level equivalence" in t:
    print("already present")
    raise SystemExit(0)

sec = """
---

## 2b. Pooled item-level equivalence, contract validity, power (COMPLETE)

Artifacts: `reports/pooled_item_equivalence_v1.{md,json}`, built by
`scripts/build_pooled_item_equivalence.py`. This is the **primary** equivalence
statistic; the seed-level figure in `three_seed_summary_v1` is retained only as
a secondary. Method: per pair, the paired delta vs the pinned base is averaged
over three seeds, then a cluster bootstrap over the 600 pair_ids (20,000 draws).
Clustering is required — the same 600 pairs recur in every seed, so treating the
1,800 rows as independent understates the interval. TOST: the 90% CI must lie
inside +/-0.05. The pooled means reproduce the published per-seed values exactly;
only the aggregation changed.

| arm | pooled delta | 95% CI | 90% CI (TOST) | equivalent? |
|---|---|---|---|---|
| A1 real | +0.0056 | [-0.0189, +0.0294] | [-0.0150, +0.0256] | **yes** |
| A2 gray | -0.0422 | [-0.0689, -0.0161] | [-0.0644, -0.0206] | **NO** |
| A2b no-image | -0.0272 | [-0.0528, -0.0017] | [-0.0483, -0.0061] | marginal |
| A3 caption | -0.0050 | [-0.0289, +0.0189] | [-0.0244, +0.0150] | yes |

**A1's flat counterfactual endpoint survives its strongest test** — item-level
inference on the lenient endpoint, not merely n=3 seeds. **A2 gray is confirmed
outside the band** by a wholly independent route from the t(2) correction, so
two methods now agree the published "within band" verdict for A2 gray was an
artefact of the normal approximation (§9). A2b is inside but marginal (lower
limit -0.0483 against a -0.05 bound) and is reported as equivalence-*consistent*,
not equivalence-established.

**Contract validity, reported as a first-class result** (pair-level, geometry
slice, mean over seeds; base sourced from the 2026-07-27 re-measurement because
the pinned 2026-07-10 shards predate the field):

| base | A1 real | A2 gray | A2b no-image | A3 caption |
|---|---|---|---|---|
| 0.9500 | 0.8767 (-0.0733) | 0.6317 (-0.3183) | 0.7728 (-0.1772) | 0.7578 (-0.1922) |

Every trained arm ends **below** the frozen base, and the ordering tracks how
degraded the arm's endpoint is. RLVR on this task erodes answer-contract
compliance on the counterfactual probe even where it raises task accuracy — an
effect the lenient scorer's fallback extractor hides. This is a result in its
own right, not a caveat on another one.

**Power.** Minimum detectable effect at 80% power (two-sided alpha=0.05) is
0.0348 (A1), 0.0377 (A2 gray), 0.0360 (A2b), 0.0338 (A3) — all comfortably below
the +/-0.05 SESOI. The A1 null is therefore informative rather than underpowered:
the design could have detected an effect roughly half the size of the
equivalence bound.
"""

anchor = "\n---\n\n## 3."
assert t.count(anchor) == 1, f"anchor count {t.count(anchor)}"
p.write_text(t.replace(anchor, sec + anchor, 1))
print("RESULTS.md: section 2b added")
