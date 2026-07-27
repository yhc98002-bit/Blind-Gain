#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
r = json.loads((ROOT / "reports/gate0_stratification_v1.json").read_text())
hc = r["G0_2_headroom_control"]
g4 = r["G0_4_answer_vs_format"]["per_arm"]
LBL = {"a1_real": "A1 real", "a2b_noimage": "A2b no-image",
       "a2_gray": "A2 gray", "a3_caption": "A3 caption"}
L = []
A = L.append

A("# Gate 0 — stratification analyses (G0.1–G0.4)\n")
A("Required by `docs/EXPERIMENT_TODO.md` Part 2A and `docs/PAPER2_RESEARCH_DOC.md` §5.")
A("Cached predictions only, no GPU. Artifact: `reports/gate0_stratification_v1.json`,")
A("built by `scripts/build_gate0_stratification.py` and")
A("`scripts/build_g02_headroom_control.py`.\n")
A("**Provenance check.** Base per-item comes from the guarded-rescore runs the seed")
A("readouts name as `geo_baselines`; on the 601-item eval split they reproduce the")
A(f"registered step-0 values exactly — acc_final {r['base_check']['acc_final']:.4f},")
A(f"acc_strict {r['base_check']['acc_strict']:.4f}, contract_valid")
A(f"{r['base_check']['contract_valid']:.4f} against registered 0.1747 / 0.0599 / 0.4393.\n")
A("**Condition discipline.** Each arm's own geo audit is its *matched* training")
A("condition (A2b's is `none`, A2's is `gray`). Every Gate-0 question is about the")
A("**image-present** gain, so all four analyses use the D3 crossed cells with the arm")
A("evaluated under `real`, verified `status: complete` and `condition == real`. Using")
A("the matched cells instead would have reported A2b's gain as −0.0605 rather than")
A("+0.1287 — the same arithmetic error the D3 registration exists to prevent.\n")
A("| arm | image-present gain | matched-condition gain |")
A("|---|---|---|")
for a in ("a1_real", "a2b_noimage", "a2_gray", "a3_caption"):
    ip = r["mean_gain_image_present"][a]
    mc = r["mean_gain_matched_condition"][a]
    A(f"| {LBL[a]} | {ip['mean']:+.4f} [{ip['ci95'][0]:+.4f}, {ip['ci95'][1]:+.4f}] | {mc['mean']:+.4f} |")
A("")
A("A1's two columns agree because A1's matched condition *is* `real`, and its")
A("+0.2435 reproduces the published three-seed gain exactly — an end-to-end check")
A("that the join, the base source, and the crossed cells are all consistent.\n")

A("## G0.1 — do the gains concentrate on high-Δq items?\n")
A("Δq = q_real − q_blind per item, taken from the registered blind reward-opportunity")
A("audit's own `q_i`. Terciles of Δq, mean per-item image-present gain in each:\n")
A("| arm | low Δq | mid Δq | high Δq | Spearman ρ | perm p |")
A("|---|---|---|---|---|---|")
for k, a in (("G0_1_a1_gain_by_delta_q", "a1_real"), ("G0_1_a2b_gain_by_delta_q", "a2b_noimage")):
    b = [x for x in r[k]["bins"] if x]
    A(f"| {LBL[a]} | {b[0]['mean_gain']:+.3f} (n={b[0]['n']}) | {b[1]['mean_gain']:+.3f} (n={b[1]['n']}) | "
      f"{b[2]['mean_gain']:+.3f} (n={b[2]['n']}) | {r[k]['spearman_rho']:+.3f} | {r[k]['spearman_perm_p']:.4f} |")
A("")
A("**Answer: yes, and for both arms.** The gain rises monotonically across Δq")
A("terciles, ρ ≈ +0.19–0.20 with permutation p ≤ 0.0005. Improvement lands")
A("preferentially where the image carried reward opportunity the blind model lacked.")
A("**Consequence for Paper 2: H1 is supported and C1 (visual-necessity sampling)")
A("earns its place in the method** — item selection on Δq targets exactly the region")
A("where RLVR already delivers most of its gain, so concentrating sampling there is")
A("justified by measurement rather than by intuition. Note the effect is present in")
A("A2b too, so high-Δq items are not preferentially learned *because* the image was")
A("shown during training.\n")

A("## G0.2 — does A2b's image-present gain concentrate on low blind-solvability items?\n")
A("*This analysis freezes Paper 1's title claim.*\n")
A(f"`q_blind` is Jeffreys-smoothed, so items with no observed blind success sit at the")
A(f"floor {hc['jeffreys_floor']:.4f}. The split is therefore **blind-answerable**")
A(f"(≥1 observed blind success, n={hc['n_blind_answerable']}) versus **not**")
A(f"(n={hc['n_not_blind_answerable']}). Blind-answerable items are easier — base real")
A(f"accuracy {hc['base_accuracy_by_stratum']['blind_answerable']:.4f} vs")
A(f"{hc['base_accuracy_by_stratum']['not_blind_answerable']:.4f} — so the contrast is")
A("reported both raw and restricted to base-wrong items, where every arm faces an")
A("identical 0→1 headroom.\n")
A("| arm | all: blind-answerable | all: not | base-wrong: blind-answerable | base-wrong: not |")
A("|---|---|---|---|---|")
for a in ("a1_real", "a2b_noimage", "a2_gray", "a3_caption"):
    v = hc["arms"][a]
    A(f"| {LBL[a]} | {v['all_items']['blind_answerable']['mean']:+.4f} | "
      f"{v['all_items']['not_blind_answerable']['mean']:+.4f} | "
      f"{v['base_wrong_only']['blind_answerable']['mean']:+.4f} | "
      f"{v['base_wrong_only']['not_blind_answerable']['mean']:+.4f} |")
A("")
a1a = hc["arms"]["a1_real"]["all_items"]
a2a = hc["arms"]["a2b_noimage"]["all_items"]
sh_ans = a2a["blind_answerable"]["mean"] / a1a["blind_answerable"]["mean"]
sh_not = a2a["not_blind_answerable"]["mean"] / a1a["not_blind_answerable"]["mean"]
A("**Answer: no — it concentrates on blind-*answerable* items, the opposite of the")
A("hypothesis, and the effect survives the headroom control.** Expressed as the share")
A("of A1's gain that image-free training recovers:\n")
A(f"- on blind-answerable items, A2b recovers **{sh_ans:.0%}** of A1's gain;")
A(f"- on items with no observed blind success, only **{sh_not:.0%}**.\n")
A("Restricted to base-wrong items the same ordering holds (91% vs 61%), so this is")
A("not a ceiling artifact. Both blind-trained arms show the steep version of the")
A("pattern while A1 and A3 do not, which is the signature expected if blind training")
A("can only capture the blind-attainable component.\n")
A("**Consequence for the title claim.** The claim survives but acquires a scope")
A("qualifier. Image-free RLVR does produce a real image-dependent gain on items that")
A("*require* the image — +0.197 on base-wrong, not-blind-answerable items, which is")
A("far from zero — so the gain is not merely generic text-side improvement. But it is")
A("**disproportionately** the blind-attainable component: image-free training captures")
A("most of what was reachable without pixels and only about half of what was not.")
A("The honest headline is that roughly half the gain is image-free *on average*, with")
A("the image-free share falling as the item's dependence on the image rises. This is")
A("direct measured support for Paper 2's **H1**: reward opportunity attainable blind")
A("is what image-free training harvests.\n")

A("## G0.3 — overlap of the A1 and A2b newly-correct sets\n")
A("Newly correct = base wrong and arm right, both evaluated image-present. Jaccard")
A("against a permutation null that reshuffles A2b's newly-correct set among base-wrong")
A("items:\n")
A("| seed | A1 new | A2b new | ∩ | ∪ | Jaccard | null | p |")
A("|---|---|---|---|---|---|---|---|")
for s in r["G0_3_newly_correct_overlap"]["per_seed"]:
    A(f"| {s['seed']} | {s['n_a1_new']} | {s['n_a2b_new']} | {s['intersection']} | {s['union']} | "
      f"{s['jaccard']:.3f} | {s['null_mean']:.3f} | {s['p_ge']:.4f} |")
A("")
A("**Answer: substantially overlapping policies, not identical ones.** Jaccard")
A("0.363–0.423 against a null of 0.157–0.177, p ≤ 0.004 in all three seeds. Image-free")
A("training fixes a large, reliably shared subset of the items image-present training")
A("fixes — evidence that the two are moving much the same mechanism rather than two")
A("unrelated ones — while roughly 60% of the union is claimed by only one arm, so they")
A("are not interchangeable.\n")

A("## G0.4 — answer gain vs format gain\n")
A("AnswerGain = Δacc_final, StrictGain = Δacc_strict, FormatGain = StrictGain −")
A("AnswerGain, all image-present, mean over three seeds:\n")
A("| arm | answer gain | strict gain | format gain | contract-validity gain |")
A("|---|---|---|---|---|")
for a in ("a1_real", "a2b_noimage", "a2_gray", "a3_caption"):
    v = g4[a]
    A(f"| {LBL[a]} | {v['mean_answer_gain']:+.4f} | {v['mean_strict_gain']:+.4f} | "
      f"{v['mean_format_gain']:+.4f} | {v['mean_contract_valid_gain']:+.4f} |")
A("")
A("**Answer: the access-matrix result is not a formatting artifact, and the reason is")
A("an identity rather than a coincidence.** Format gain is *exactly* +0.1148 for all")
A("four arms. Every trained arm satisfies `acc_strict == acc_final` on every item —")
A("once trained, every correct answer is contract-valid — so FormatGain collapses to")
A("`base_acc_final − base_acc_strict` = 0.1747 − 0.0599 = 0.1148, a constant that")
A("depends only on the frozen base. The format channel is saturated identically by all")
A("four arms, including the two that never saw an image in training.\n")
A("Therefore every between-arm contrast in the access matrix — the entire F1 result —")
A("is format-free by construction: the formatting component cancels exactly in any")
A("arm-minus-arm comparison. What differs between arms is answer content alone.\n")
(ROOT / "reports/gate0_stratification_v1.md").write_text("\n".join(L))
print(f"A2b recovers {sh_ans:.1%} of A1 on blind-answerable, {sh_not:.1%} on not")
print("wrote reports/gate0_stratification_v1.md")
