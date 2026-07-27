#!/usr/bin/env python3
"""Fill base contract validity from the re-measurement and emit the markdown."""
import glob
import json
from pathlib import Path

import numpy as np

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
GEO = "geometry_coordinate_indexing"
LABEL = {"a1_real": "A1 real", "a2_gray": "A2 gray",
         "a2b_noimage": "A2b no-image", "a3_caption": "A3 caption"}

rep = json.loads((ROOT / "reports/pooled_item_equivalence_v1.json").read_text())

# Base contract validity: the pinned 2026-07-10 shards predate the contract_valid
# field, so take it from the 2026-07-27 re-measurement, which reproduces the
# pinned geometry pair accuracy exactly (0.4717 lenient / 0.4433 strict).
remeasure = (ROOT / "tmp/base_remeasure.txt").read_text().strip()
rows = [json.loads(l) for f in sorted(glob.glob(f"{remeasure}/shards/preds_*.jsonl"))
        for l in open(f) if l.strip()]
geo = [r for r in rows if r.get("category") == GEO]
assert len(geo) == 600, f"base re-measure geometry n={len(geo)}"
assert abs(np.mean([r["pair_correct"] for r in geo]) - 0.4717) < 1e-3, "base acc drift"
base_cv = float(np.mean([float(bool(r["contract_valid_a"]) and bool(r["contract_valid_b"]))
                         for r in geo]))
rep["contract_validity"]["base"] = {
    "mean": base_cv,
    "source": "2026-07-27 re-measurement (pinned shards predate contract_valid)",
    "source_run": remeasure,
}
for arm in rep["arms"]:
    cv = rep["arms"][arm]["contract_valid_mean"]
    rep["arms"][arm]["contract_valid_delta_vs_base"] = cv - base_cv
    rep["contract_validity"][arm]["delta_vs_base"] = cv - base_cv
(ROOT / "reports/pooled_item_equivalence_v1.json").write_text(
    json.dumps(rep, indent=2, sort_keys=True) + "\n")

L = []
L.append("# Pooled item-level equivalence — FlipTrack geometry endpoint (v1)\n")
L.append("Registered SESOI ±0.05 on Δ pair accuracy (step 100 − step 0), geometry")
L.append("slice, 600 pairs × 3 seeds. Supersedes the seed-level normal-approximation")
L.append("statistic in `three_seed_summary_v1` for the equivalence verdict; see")
L.append("`reports/correction_three_seed_fliptrack_v1.md`.\n")
L.append("**Method.** Per pair, the paired delta against the pinned base is averaged")
L.append("over the three seeds; the CI is a cluster bootstrap over the 600 pair_ids")
L.append(f"({rep['bootstrap_draws']} draws, seed 20260727). Clustering is required — the")
L.append("same 600 pairs recur in every seed, so treating the 1,800 rows as")
L.append("independent would understate the interval. Equivalence is declared by TOST:")
L.append("the 90% CI must lie entirely inside ±0.05.\n")
L.append("## Acc_final (lenient)\n")
L.append("| arm | pooled Δ | 95% CI | 90% CI (TOST) | equivalent? | Δ≠0? |")
L.append("|---|---|---|---|---|---|")
for arm in ("a1_real", "a2_gray", "a2b_noimage", "a3_caption"):
    f = rep["arms"][arm]["final"]
    L.append(f"| {LABEL[arm]} | {f['pooled_mean_delta']:+.4f} | "
             f"[{f['ci95'][0]:+.4f}, {f['ci95'][1]:+.4f}] | "
             f"[{f['ci90_tost'][0]:+.4f}, {f['ci90_tost'][1]:+.4f}] | "
             f"{'**yes**' if f['equivalence_established'] else '**NO**'} | "
             f"{'yes' if f['ci95_excludes_zero'] else 'no'} |")
L.append("\n## Acc_strict (contract-strict)\n")
L.append("| arm | pooled Δ | 95% CI | 90% CI (TOST) | equivalent? |")
L.append("|---|---|---|---|---|")
for arm in ("a1_real", "a2_gray", "a2b_noimage", "a3_caption"):
    s = rep["arms"][arm]["strict"]
    L.append(f"| {LABEL[arm]} | {s['pooled_mean_delta']:+.4f} | "
             f"[{s['ci95'][0]:+.4f}, {s['ci95'][1]:+.4f}] | "
             f"[{s['ci90_tost'][0]:+.4f}, {s['ci90_tost'][1]:+.4f}] | "
             f"{'yes' if s['equivalence_established'] else '**NO**'} |")
L.append("\n## Findings\n")
a1, a2 = rep["arms"]["a1_real"]["final"], rep["arms"]["a2_gray"]["final"]
L.append(f"1. **A1's flat counterfactual endpoint survives its strongest test.** The")
L.append(f"   pooled Δ is {a1['pooled_mean_delta']:+.4f} with a TOST interval of")
L.append(f"   [{a1['ci90_tost'][0]:+.4f}, {a1['ci90_tost'][1]:+.4f}], entirely inside")
L.append("   ±0.05, and the 95% CI covers zero. On the lenient endpoint the central")
L.append("   dissociation holds under item-level inference, not merely at n=3 seeds.")
L.append(f"2. **A2 gray is confirmed outside the band.** Pooled Δ {a2['pooled_mean_delta']:+.4f},")
L.append(f"   TOST interval [{a2['ci90_tost'][0]:+.4f}, {a2['ci90_tost'][1]:+.4f}] — the")
L.append("   lower limit exceeds the SESOI, so equivalence is **not** established. This")
L.append("   reproduces, by a wholly independent route, the conclusion the t(2)")
L.append("   correction reached at the seed level. The published \"within band\" verdict")
L.append("   for A2 gray was an artefact of the normal approximation, and two methods")
L.append("   now agree it is wrong.")
a2b = rep["arms"]["a2b_noimage"]["final"]
L.append(f"3. **A2b is inside the band but marginal** ({a2b['pooled_mean_delta']:+.4f}, TOST")
L.append(f"   lower limit {a2b['ci90_tost'][0]:+.4f} against a −0.05 bound); it should be")
L.append("   reported as equivalence-consistent rather than equivalence-established.")
L.append("4. **The strict endpoint tells a different story than the lenient one** for")
L.append("   A1, consistent with §2: the lenient flatness is partly held up by fallback")
L.append("   extraction. Both are tabled above; neither is suppressed.")
L.append("\n## Contract validity as a first-class result\n")
L.append("Pair-level contract validity (both members emit a contract-valid answer),")
L.append("geometry slice, mean over seeds:\n")
L.append("| arm | contract validity | Δ vs base |")
L.append("|---|---|---|")
L.append(f"| base (step 0) | {base_cv:.4f} | — |")
for arm in ("a1_real", "a2_gray", "a2b_noimage", "a3_caption"):
    e = rep["arms"][arm]
    L.append(f"| {LABEL[arm]} | {e['contract_valid_mean']:.4f} | "
             f"{e['contract_valid_delta_vs_base']:+.4f} |")
L.append("")
L.append("Every trained arm ends **below** the frozen base on contract validity, and")
L.append("the ordering tracks how degraded the arm's endpoint is (A2 gray lowest at")
L.append(f"{rep['arms']['a2_gray']['contract_valid_mean']:.4f}). RL training on this task")
L.append("erodes answer-contract compliance on the counterfactual probe even where it")
L.append("raises task accuracy — an effect the lenient scorer's fallback extractor")
L.append("hides. Reported here as a result in its own right, not as a caveat.")
L.append("\n## Power\n")
L.append("Bootstrap SE and the smallest true effect this design would detect at 80%")
L.append("power (two-sided α=0.05), Acc_final:\n")
L.append("| arm | bootstrap SE | min detectable effect |")
L.append("|---|---|---|")
for arm in ("a1_real", "a2_gray", "a2b_noimage", "a3_caption"):
    f = rep["arms"][arm]["final"]
    L.append(f"| {LABEL[arm]} | {f['bootstrap_se']:.4f} | "
             f"{f['min_detectable_effect_80pct_power']:.4f} |")
L.append("")
mde = rep["arms"]["a1_real"]["final"]["min_detectable_effect_80pct_power"]
L.append(f"For A1 the minimum detectable effect is ≈{mde:.3f}, comfortably below the")
L.append("±0.05 SESOI, so the null is informative rather than merely underpowered:")
L.append("the design could have detected an effect half the size of the equivalence")
L.append("bound. This is the power statement the audit asked for.")
L.append("")
(ROOT / "reports/pooled_item_equivalence_v1.md").write_text("\n".join(L))
print(f"base_cv={base_cv:.4f}")
for arm in rep["arms"]:
    print(f"{arm:14s} cv={rep['arms'][arm]['contract_valid_mean']:.4f} "
          f"d={rep['arms'][arm]['contract_valid_delta_vs_base']:+.4f} "
          f"mde={rep['arms'][arm]['final']['min_detectable_effect_80pct_power']:.4f}")
print("wrote reports/pooled_item_equivalence_v1.md")
