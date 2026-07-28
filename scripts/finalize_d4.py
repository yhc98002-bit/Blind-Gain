#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
r = json.loads((ROOT / "reports/d4_caption_column_v1.json").read_text())
c = r["caption_column"]
LBL = {"a1": "A1 real", "a3": "A3 caption", "a2b": "A2b no-image", "a2": "A2 gray"}

L = []
A = L.append
A("# D4 — caption test column, completing the access matrix to 4×4\n")
A("Registered before any cell ran: `docs/registered_d3_caption_column_v1.md` plus")
A("`docs/registered_d4_ordering_addendum_v1.md`, which fixes the **primary**")
A("estimand as the arm *ordering* under caption-at-test — is the readout policy")
A("pixel-specific or evidence-general?\n")
A(f"12 cells (4 arms × 3 seeds), n={r['n_items']} items, base caption row pinned at")
A(f"**{r['base_caption_pinned']:.4f}** from the registered arm step-0 evaluations, not")
A("re-measured. Artifact: `reports/d4_caption_column_v1.json`.\n")
A("## The caption column\n")
A("| arm | caption accuracy | gain over base | 95% CI |")
A("|---|---|---|---|")
for a in ("a1", "a3", "a2b", "a2"):
    v = c[a]
    A(f"| {LBL[a]} | {v['raw_accuracy']:.4f} | **{v['mean']:+.4f}** | "
      f"[{v['ci95'][0]:+.4f}, {v['ci95'][1]:+.4f}] |")
A("")
A("*A1 and A3 tie at +0.1048.* This is a coincidence of the three-seed mean, not a")
A("cell mix-up: the runs use distinct checkpoints, their per-seed accuracies differ")
A("(A1 0.3161 / 0.2995 / 0.3278 vs A3 0.3195 / 0.2928 / 0.3311), and they agree on")
A("only ~40% of extracted answers. Both means happen to land on 0.31447.\n")
A("## Registered primary: branch (a) — evidence-general\n")
A(f"- Ordering under caption: {' > '.join(LBL[k] for k in sorted(c, key=lambda k: -c[k]['mean']))}")
A("- Ordering under real: A1 real > A3 caption > A2b no-image > A2 gray")
A(f"- Spearman ρ(caption, real) = **{r['spearman_caption_vs_real']:+.3f}** (threshold ≥ +0.70)")
A(f"- Spread: caption **{r['spreads']['caption']:.4f}** vs gray {r['spreads']['gray']:.4f} and")
A(f"  none {r['spreads']['none']:.4f} — **{r['spreads']['caption']/max(r['spreads']['gray'], r['spreads']['none']):.1f}×**")
A("  the larger blind spread (threshold ≥ 2×)\n")
A("Both conditions of branch (a) are met, so the registered reading is that **the")
A("readout policy is not pixel-specific**. It exploits task-relevant evidence")
A("through whatever channel supplies it: given frozen textual descriptions instead")
A("of pixels, the arms re-order themselves the same way they do with images, and")
A("they spread apart four times more than they do under a blind condition.\n")
A("The one discrepancy in the ordering is A1 and A3 swapping at the top, which is")
A("the tie above rather than a real inversion; ρ = +0.800 rather than +1.000 is")
A("entirely that swap.\n")
A("**What this licenses.** F1's two-regime split is about *information presence*,")
A("not *modality*. That in turn supports the broader-claim paragraph: if the policy")
A("reads evidence generally, the representational-ceiling argument is not specific")
A("to pixels and should extend to any frozen non-text encoder.\n")
A("## Secondary: A3 matched vs crossed — does NOT clear the bar\n")
s = r["a3_matched_vs_crossed"]
A(f"A3 matched (tested caption, its own training condition): **{s['matched_caption']:+.4f}**.")
A(f"A3 crossed (tested real): **{s['crossed_real']:+.4f}**. Ratio **{s['ratio']:.2f}**.\n")
A("The registered bar for joining the protocol-effect finding was a ratio > 2 with")
A("non-overlapping CIs. **1.67 does not clear it.** So F1 states the")
A("matched-versus-crossed protocol effect for **two arms (A2 gray, A2b no-image),")
A("not three** — A3 is an exception and is reported as one. This is the registered")
A("branch (c) outcome for the secondary: descriptive, no claim change.\n")
A("That A3 is the exception is unsurprising in hindsight — its training condition")
A("already carried task information, so it has less to gain from being moved to a")
A("richer test channel than an arm trained on gray rectangles does.\n")
(ROOT / "reports/d4_caption_column_v1.md").write_text("\n".join(L))
print("wrote reports/d4_caption_column_v1.md")

# ---- patch RESULTS.md -------------------------------------------------------
p = ROOT / "reports/RESULTS.md"
t = p.read_text()
t = t.replace(
    "| D4 caption test column (4×3 → 4×4) | F1 | **running** — 4/12 cells done |",
    "| D4 caption test column (4×3 → 4×4) | F1 | **complete** — branch (a), evidence-general |", 1)
anchor = "\n---\n\n## 3. F3 — The exchange rate, and where it lands"
sec = """
---

## 2b. D4 — the caption test column (completes the matrix to 4×4)

`reports/d4_caption_column_v1.*`. Registered primary, filed before any cell ran:
is the readout policy pixel-specific or evidence-general? Base caption row pinned
at 0.2097; 12 cells, n=601.

| arm | caption accuracy | gain over base | 95% CI |
|---|---|---|---|
| A1 real | 0.3145 | **+0.1048** | [+0.0727, +0.1370] |
| A3 caption | 0.3145 | **+0.1048** | [+0.0732, +0.1375] |
| A2b no-image | 0.2751 | +0.0654 | [+0.0361, +0.0965] |
| A2 gray | 0.2629 | +0.0532 | [+0.0233, +0.0837] |

**Branch (a) fires — evidence-general.** Spearman ρ(caption, real) = **+0.800**
(threshold ≥ +0.70) and the caption column's spread is **4.0×** the larger blind
spread (0.0516 vs 0.0130; threshold ≥ 2×). Given frozen textual descriptions
instead of pixels the arms re-order as they do with images and spread apart four
times more than under a blind condition, so **the readout policy is not
pixel-specific**. F1's two-regime split is about information presence, not
modality — which is what licenses generalising the ceiling argument beyond pixels.

The A1/A3 tie at +0.1048 is a coincidence of the three-seed mean (distinct
checkpoints, per-seed accuracies differ, ~40% answer agreement); ρ = +0.800
rather than +1.000 is entirely that swap.

**Secondary — A3 does not clear the protocol-effect bar.** A3 matched (caption)
+0.1048 vs crossed (real) +0.1747 is a ratio of **1.67**, below the registered
2× threshold. So the matched-versus-crossed protocol effect is stated for **two
arms, not three**; A3 is an exception, reported as such under branch (c).
"""
assert t.count(anchor) == 1
t = t.replace(anchor, sec + anchor, 1)
p.write_text(t)
print("patched reports/RESULTS.md")
