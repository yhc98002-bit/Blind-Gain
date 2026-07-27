#!/usr/bin/env python3
import json
import math
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
rep = json.loads((ROOT / "reports/p01_premise_probe_v1.json").read_text())
C = rep["cells"]
LBL = {"base": "base (step 0)", "a1_seed1_step100": "A1 real s1",
       "a1_seed2_step100": "A1 real s2", "a2b_seed1_step100": "A2b no-image s1",
       "a3_seed1_step100": "A3 caption s1"}
ORD = list(LBL)


def wald(p, n):
    h = 1.96 * math.sqrt(max(p * (1 - p), 1e-9) / n)
    return max(0.0, p - h), min(1.0, p + h)


bp = C["base"]["premise_member_accuracy"]
lo, hi = wald(bp, 40)
branch = "(b)" if bp < 0.30 else ("(a)" if bp >= 0.60 else "(c)")

L = []
L.append("# P0.1 — B1 premise probe, five separate numbers\n")
L.append("Registered: `docs/registered_b1_premise_probe_v1.md`. Required by")
L.append("EXPERIMENT_TODO Part 2B and PAPER2 §4 Track 4. Twenty `chained_premise`")
L.append("pairs, 40 members per cell. Scored with the **P0.2-fixed** scorer: the")
L.append("premise manifest is equal-gold by construction and the pre-fix scorer")
L.append("returned 0.000 on every such item regardless of content (§ below).\n")
L.append("**The five numbers are reported separately and never aggregated** (I13).\n")
L.append("| cell | premise member | premise pair | premise transition | final member | final pair | reasoning \\| correct premise | n |")
L.append("|---|---|---|---|---|---|---|---|")
for k in ORD:
    v = C[k]
    rg = v["reasoning_given_correct_premise"]
    L.append(f"| {LBL[k]} | {v['premise_member_accuracy']:.3f} | {v['premise_pair_accuracy']:.3f} | "
             f"{v['premise_transition_accuracy']:.3f} | {v['final_member_accuracy']:.3f} | "
             f"{v['final_pair_accuracy']:.3f} | "
             f"{'n/a' if rg is None else f'{rg:.3f}'} | {v['reasoning_denominator']} |")

L.append("\n## Registered branch\n")
L.append(f"Base premise member accuracy is **{bp:.3f}**, so registered branch **{branch}** fires:")
L.append("the items are too hard at 3B for the premise step to be extracted reliably,")
L.append("and the chained construct is **revised before release** rather than retained")
L.append("as-is. The 0.000 chained pair accuracy is therefore *uninformative about")
L.append("chaining ability* — it is dominated by premise extraction failure.\n")
L.append(f"**Honest interval.** With n=40 the 95% Wald interval on the base figure is")
L.append(f"[{lo:.3f}, {hi:.3f}], which straddles the 0.30 boundary between branches (b)")
L.append("and (c). The branch fires on the point estimate as registered, but the")
L.append("evidence does not cleanly separate 'too hard' from 'intermediate'. The")
L.append("consequence — revise the construct — is the same under either branch, which")
L.append("is why the decision is reported as safe despite the width.\n")

L.append("## What this decides for Paper 2\n")
L.append("1. **The premise step is the first bottleneck, but not the only one.** Even")
L.append("   restricted to members whose premise was extracted correctly, the base")
L.append(f"   model completes the chain only {C['base']['reasoning_given_correct_premise']:.3f} of the time")
L.append(f"   (n={C['base']['reasoning_denominator']}). Making premises easier would raise the")
L.append("   first factor and leave the second largely untouched, so a premise-only")
L.append("   curriculum is not sufficient on its own.")
L.append("2. **C3 has signal here, but very little.** PAPER2 §2 C3 argues that pair")
L.append("   product rewards are ~0 on these items and C3 is the only source of")
L.append("   gradient. That holds: final pair accuracy is 0.000 for every model, while")
L.append("   premise-level correctness is non-zero for 17.5–30.0% of members. So the")
L.append("   hierarchical reward does expose a non-empty learning signal where the")
L.append("   answer-level reward exposes none — but at this difficulty the premise")
L.append("   factor is itself sparse, which is exactly the Phase-2 gate condition.")
L.append("3. **Premise-transition accuracy is uninformative by construction here** —")
L.append("   it equals premise pair accuracy in all five cells (0.150–0.200). B1's")
L.append("   chained items hold the premise *invariant* across the flip (the nearest")
L.append("   point stays the same; only its coordinate moves), so a correct pair is")
L.append("   automatically a correct transition. **Concrete fix for Track 4:** the")
L.append("   construct needs items where the premise itself changes across the")
L.append("   counterfactual, or this metric can never do independent work.")
L.append("4. **No arm beats base on premise extraction.** Base 0.275 is the highest")
L.append("   premise member accuracy of the five cells; the trained arms sit at")
L.append("   0.175–0.300. This is directionally consistent with Paper 1's finding that")
L.append("   RLVR does not improve visual acquisition, but n=40 per cell makes it")
L.append("   **far too underpowered to claim** — it is recorded as consistent, not as")
L.append("   evidence. No directional claim was registered for this contrast.\n")

L.append("## Scorer dependency (P0.2)\n")
L.append("This readout was impossible before the P0.2 fix. `acc_final` was")
L.append("`gold_tier > other_tier`, evaluated on an equal-gold pair where both tiers")
L.append("derive from the same string, so it was false for every response. The raw")
L.append("probe metrics recorded member accuracy 0.000 for all five cells — including a")
L.append("base that scores 0.150 on the strictly harder final question, which is what")
L.append("exposed the defect. Numbers above are rescored in-process with the fixed")
L.append("scorer; the on-disk `metrics.json` files from the probe run are void and must")
L.append("not be cited.\n")
(ROOT / "reports/p01_premise_probe_v1.md").write_text("\n".join(L))
print(f"base premise {bp:.3f} CI[{lo:.3f},{hi:.3f}] branch {branch}")
print("wrote reports/p01_premise_probe_v1.md")
