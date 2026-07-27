#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
r = json.loads((ROOT / "reports/d3_trainshare_v1.json").read_text())
LBL = {"a2_gray": "A2 gray", "a2b_noimage": "A2b no-image", "a3_caption": "A3 caption"}
L = []
A = L.append
A("# D3 TrainShare with paired item-level CIs\n")
A("Estimand from `docs/PAPER1_RESEARCH_DOC.md` §8:\n")
A("    TrainShare = [Acc(train-blind, test-real) − Acc(base, test-real)]")
A("                 / [Acc(A1, test-real) − Acc(base, test-real)]\n")
A("Branches: ≥0.35 headline at full strength · 0.15–0.35 \"a substantial minority of")
A("the gain is image-free\" · <0.15 training-time access dominates.\n")
A("> **Ordering disclosure.** All 36 D3 cells were read under")
A("> `docs/registered_d3_condition_matrix_v1.md`, whose branches are ratio-based,")
A("> *before* this estimand was computed. TrainShare here is a **declared post-hoc")
A("> recomputation of already-read data** — it does not satisfy I9 and must not be")
A("> presented as a sealed pre-registered reading. It is reported because PAPER1 §8")
A("> names this estimand and the paper will quote it.\n")
A("| arm | seed 1 | seed 2 | seed 3 | pooled | 95% CI (paired item-level) | branch |")
A("|---|---|---|---|---|---|---|")
for a in ("a2_gray", "a2b_noimage", "a3_caption"):
    ps = r["per_seed"][a]
    p = r["pooled"][a]
    A(f"| {LBL[a]} | {ps[0]['train_share']:.3f} | {ps[1]['train_share']:.3f} | "
      f"{ps[2]['train_share']:.3f} | **{p['train_share']:.3f}** | "
      f"[{p['ci95'][0]:.3f}, {p['ci95'][1]:.3f}] | {p['branch']} |")
A("")
A("**Branch: headline at full strength, and not marginally.** Every arm's pooled")
A("TrainShare clears 0.35 with a paired item-level interval lying *entirely* above")
A("the threshold — the nearest lower bound is A2 gray at 0.383 — and all nine")
A("seed-arm values fall in the same branch. The bootstrap resamples the 601 items and")
A("recomputes numerator and denominator together, so the ratio's correlation")
A("structure is preserved rather than assumed away.\n")
A("These reproduce the crossed recoveries already reported from D3 (A2 gray")
A("0.507/0.527/0.424; A2b 0.572/0.493/0.518), so nothing new is being claimed — the")
A("contribution is the interval and the branch evaluation.\n")
A("## Read this together with G0.2\n")
A("The pooled figure conceals real structure. `reports/gate0_stratification_v1.md`")
A("shows A2b's share of A1's gain is **84%** on items with at least one observed")
A("blind success and **42%** on items with none. TrainShare ≈ 0.53 is the average")
A("over that gradient, not a constant. The honest formulation for the paper is that")
A("roughly half of the gain is image-free *on average*, with the image-free share")
A("falling as an item's dependence on the image rises — a headline at full strength")
A("that carries its own scope qualifier rather than needing one bolted on.\n")
(ROOT / "reports/d3_trainshare_v1.md").write_text("\n".join(L))
print("wrote reports/d3_trainshare_v1.md")
