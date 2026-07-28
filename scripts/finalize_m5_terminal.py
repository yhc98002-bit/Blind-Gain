#!/usr/bin/env python3
import glob
import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
r = json.loads((ROOT / "reports/m5_terminal_readout_v1.json").read_text())

# overall (all-template) step-400 figure, for the descriptive trajectory only
shards = sorted(glob.glob(str(ROOT / Path(r["step400_shards"]).parent / "*.jsonl")))
rows = [json.loads(l) for f in shards for l in open(f) if l.strip()]
overall400 = sum(bool(x["pair_correct"]) for x in rows) / len(rows)

L = []
A = L.append
A("# M5 terminal readout — ladder rung R2\n")
A("Rule: `docs/MAIN_PHASE_RULING_20260716.md` R1. Endpoint is **R19 geometry pair")
A("accuracy** — the primary visual anchor, the only R19 task requiring search and")
A("binding — at step 400 minus step 100, with an item-paired bootstrap 95% CI.\n")
A(f"Artifact: `reports/m5_terminal_readout_v1.json`. n={r['n_pairs']} pairs.\n")
A("## Result\n")
A(f"| | step 100 | step 400 | Δ | 95% CI |")
A("|---|---|---|---|---|")
A(f"| lenient pair acc | {r['step100_pair_accuracy']:.4f} | {r['step400_pair_accuracy']:.4f} | "
  f"**{r['delta']:+.4f}** | [{r['ci95'][0]:+.4f}, {r['ci95'][1]:+.4f}] |")
s = r["strict_secondary"]
A(f"| contract-strict | {r['step100_strict']:.4f} | {r['step400_strict']:.4f} | "
  f"{s['delta']:+.4f} | [{s['ci95'][0]:+.4f}, {s['ci95'][1]:+.4f}] |")
A("")
A(f"## Registered verdict: **{r['verdict']}**\n")
A("The rule declares FALLING iff Δ ≤ −0.05 **and** the CI upper bound is below")
A(f"zero. Both hold: Δ = {r['delta']:+.4f} and the interval is")
A(f"[{r['ci95'][0]:+.4f}, {r['ci95'][1]:+.4f}], entirely negative. This is not a")
A("borderline call and required no discretion.\n")
A("**Step 400 is terminal. There is no extension or rerun under any outcome**, so")
A("this is the R2 result as it stands.\n")
A("## What it says\n")
A("Extending RLVR from 100 to 400 steps does not build visual competence on the")
A("certified anchor — it **erodes** it. The step-400 checkpoint scores 0.4133,")
A("which is below not only its own step-100 value (0.4800) but also the **frozen")
A("base** (0.4717): four times the training leaves the model worse on the primary")
A("visual anchor than no RL training at all.\n")
A("Two features make this hard to dismiss as noise or as a scoring artifact:\n")
A("1. **The strict and lenient endpoints move identically** (both −0.0667). Every")
A("   correct answer is contract-valid at both checkpoints, so the decline is")
A("   answer content, not formatting or extraction. This matches the identity G0.4")
A("   established: trained arms satisfy `acc_strict == acc_final`.")
A("2. **The descriptive trajectory is monotone.** Overall R19 pair accuracy at")
A(f"   steps 150 / 200 / 300 / 400 is {r['descriptive_only_steps']['150']['overall_pair_accuracy']:.4f} / "
  f"{r['descriptive_only_steps']['200']['overall_pair_accuracy']:.4f} / "
  f"{r['descriptive_only_steps']['300']['overall_pair_accuracy']:.4f} / {overall400:.4f}. The")
A("   endpoint does not wander; it declines steadily. Per the ruling these steps are")
A("   **descriptive only and cannot select the endpoint** — they are reported here")
A("   as trajectory context, not as evidence for the verdict.\n")
A("## How it bears on the paper's thesis\n")
A("This strengthens rather than complicates the readout-policy account. If RLVR")
A("were acquiring visual distinctions, more of it should buy more competence on the")
A("anchor. Instead the task reward keeps rising while the certified counterfactual")
A("endpoint falls, which is what a policy optimising a proxy it can satisfy without")
A("the image looks like when it is run for longer.\n")
A("It also extends F6 (blind-reward corrosion) along the *time* axis: F6 shows blind")
A("reward corroding grounding across training **conditions**; R2 shows the same")
A("endpoint corroding across training **duration**, in the arm trained on real")
A("images. The corrosion is not exclusive to information-starved arms.\n")
A("**Scope.** One long-horizon run, one corpus, one scale. The verdict is about this")
A("anchor arm's trajectory, not a general law about RLVR duration; §9 language locks")
A("apply.\n")
(ROOT / "reports/m5_terminal_readout_v1.md").write_text("\n".join(L))
print(f"overall step400 = {overall400:.4f}")
print("wrote reports/m5_terminal_readout_v1.md")
