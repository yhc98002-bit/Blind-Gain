#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
r = json.loads((ROOT / "reports/f2d_template_decomposition_v1.json").read_text())
ANCHOR = "coordinate_register_twenty_point_x_v02"
HEADER = "header_cued_table_code_v02"
NINE = "starred_series_value_nine_v07"
SHORT = {ANCHOR: "coordinate survey register", HEADER: "header-cued verification table",
         NINE: "nine-series calibration trace"}
ARMS = ("a1_real", "a2_gray", "a2b_noimage", "a3_caption")
LBL = {"a1_real": "A1 real", "a2_gray": "A2 gray", "a2b_noimage": "A2b no-image",
       "a3_caption": "A3 caption"}
L = []
A = L.append

A("# F2d — template decomposition of the overall R19 movement\n")
A("Serves PAPER1 §3 **F2**. Cached per-item predictions, no new inference. Each task")
A("is reported in its own scientific role and **no aggregate is computed across")
A("roles** (I13); the 'overall' column exists only because F2 quotes an overall")
A("number, and it is reported as an accounting identity, not as a capability score.\n")
A("Artifact: `reports/f2d_template_decomposition_v1.json`.\n")

A("## Base rates by task\n")
A("| task | role | n | pair acc | strict pair acc | member acc |")
A("|---|---|---|---|---|---|")
for t in (ANCHOR, HEADER, NINE):
    b = r["base"][t]
    A(f"| {SHORT[t]} | {r['roles'][t]} | {b['n_pairs']} | {b['pair_accuracy']:.4f} | "
      f"{b['strict_pair_accuracy']:.4f} | {b['member_accuracy']:.4f} |")
A("")

A("## Correction to PAPER1 §5 and §3\n")
hb = r["base"][HEADER]
A(f"**The header-cued verification table is not saturated.** PAPER1 §5 describes it as")
A(f"\"saturated at 1.000 for every model including base\" and as a control that")
A(f"\"cannot show improvement\", and §3 F2 builds the mechanism on it contributing")
A(f"\"nothing to any delta\". Measured on R19 the base sits at **{hb['pair_accuracy']:.4f}**")
A(f"pair accuracy, not 1.000, and it moves in **every** arm:")
for a in ARMS:
    c = r["arms"][a]["per_template"][HEADER]
    A(f"{LBL[a]} {c['mean_delta']:+.4f} [{c['ci95'][0]:+.4f}, {c['ci95'][1]:+.4f}]" +
      ("," if a != ARMS[-1] else "."))
A("")
A("A2 gray's interval excludes zero. It contributes **18.7%** of A1's overall")
A("movement, not 0%. The retention-canary function still works — nothing here")
A("*drops* — but the premise that it is pinned at ceiling and arithmetically inert")
A("is false and must be corrected in both sections before the claim is written up.\n")
A(f"Note also the lenient/strict split on this task: pair accuracy")
A(f"{hb['pair_accuracy']:.4f} against strict {hb['strict_pair_accuracy']:.4f}. The")
A("header table is the R19 task most dependent on fallback extraction, which is")
A("worth stating wherever it is used as a control.\n")

A("## Where the movement actually lands\n")
A("Mean per-item delta over three seeds, with the contribution each task makes to the")
A("overall figure (delta x n/1200):\n")
A("| arm | overall | anchor Δ (contrib) | header Δ (contrib) | nine-series Δ (contrib) |")
A("|---|---|---|---|---|")
for a in ARMS:
    e = r["arms"][a]
    cells = []
    for t in (ANCHOR, HEADER, NINE):
        c = e["per_template"][t]
        cells.append(f"{c['mean_delta']:+.4f} ({c['contribution_to_overall']:+.4f})")
    A(f"| {LBL[a]} | {e['overall_delta_mean']:+.4f} | " + " | ".join(cells) + " |")
A("")
a1 = r["arms"]["a1_real"]["per_template"]
A("**For A1 the F2 mechanism holds, with the header correction applied.** The")
A(f"oracle-localized readout control moves {a1[NINE]['mean_delta']:+.4f}")
A(f"(CI [{a1[NINE]['ci95'][0]:+.4f}, {a1[NINE]['ci95'][1]:+.4f}], excludes zero) and")
A(f"supplies **{a1[NINE]['share_of_overall_pct']:.0f}%** of the overall movement, while the")
A(f"primary visual anchor — the only R19 task requiring search and binding — moves")
A(f"{a1[ANCHOR]['mean_delta']:+.4f} with an interval")
A(f"[{a1[ANCHOR]['ci95'][0]:+.4f}, {a1[ANCHOR]['ci95'][1]:+.4f}] that spans zero, supplying")
A(f"{a1[ANCHOR]['share_of_overall_pct']:.0f}%. **The gain lands where localization has")
A("already been supplied by the cue.**\n")

A("## The blind arms separate the layers more sharply than A1 does\n")
A("Percentage shares are omitted for A2 gray and A2b: their overall deltas are")
A("≈0 (−0.0014 and −0.0019), so a share of that denominator is meaningless. The")
A("per-task deltas are what carry the result, and they are opposite in sign:\n")
A("| arm | primary visual anchor | oracle-localized readout control |")
A("|---|---|---|")
for a in ("a2_gray", "a2b_noimage"):
    e = r["arms"][a]["per_template"]
    A(f"| {LBL[a]} | {e[ANCHOR]['mean_delta']:+.4f} "
      f"[{e[ANCHOR]['ci95'][0]:+.4f}, {e[ANCHOR]['ci95'][1]:+.4f}] | "
      f"{e[NINE]['mean_delta']:+.4f} [{e[NINE]['ci95'][0]:+.4f}, {e[NINE]['ci95'][1]:+.4f}] |")
A("")
A("Both blind-trained arms **decline on the search-and-binding anchor** with")
A("intervals excluding zero, while **rising on the cued readout control**. Their")
A("flat overall numbers are therefore not inertness: they are two real effects of")
A("opposite sign cancelling inside an aggregate that should never have been read as")
A("a single capability score.\n")
A("This localizes F5. Blind-reward corrosion is not diffuse damage — it is specific")
A("to the task that requires locating a label and binding it to a point, and it")
A("coexists with genuine improvement on the task where the target is already marked.")
A("A cue that supplies localization is enough to protect a blind-trained model from")
A("its own corrosion, which is a sharper statement of the utilization thesis than")
A("the overall numbers can express, and a concrete prediction for the cue ladder")
A("(F4b): the damage should appear at the search rungs and vanish at the exact-cue rung.\n")
(ROOT / "reports/f2d_template_decomposition_v1.md").write_text("\n".join(L))
print("wrote reports/f2d_template_decomposition_v1.md")
