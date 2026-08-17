import json, sys, pathlib
root = pathlib.Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
sys.path.insert(0, str(root))
import pandas as pd
from src.eval.layer1_blind import load_rows, score_predictions

rows = load_rows(str(root/"data/vlmevalkit/MathVerse_LOCAL.tsv"), "mathverse")
scored, _ = score_predictions(rows, ["<answer>ZZZ</answer>"]*len(rows), "mathverse")
wi = {}
with open(root/"experiments/runs/vlmevalkit_postprocess_l10_mathverse3b_canonicalv2_v2_20260711T143923Z/rows.jsonl") as fh:
    for line in fh:
        r = json.loads(line); wi[str(r["index"])] = r
tsv = {str(r["index"]): r for r in rows}
n = 0
for r in scored:
    w = wi[r["index"]]
    if json.dumps(w["gold"], sort_keys=True) != json.dumps(r["gold"], sort_keys=True):
        n += 1
        t = tsv[r["index"]]
        print("### index", r["index"])
        print("  blind gold      :", repr(r["gold"]), "| labels", r["option_labels"], "| contract", r["scoring_contract"])
        print("  withimg gold    :", repr(w["gold"]), "| labels", w["option_labels"], "| contract", w["scoring_contract"])
        print("  TSV answer      :", repr(t["answer"]))
        print("  TSV answer_option :", repr(t.get("answer_option")))
        print("  TSV answer_options:", repr(t.get("answer_options")))
        print("  TSV choice_source :", repr(t.get("choice_source")), "choice_labels_inferred:", repr(t.get("choice_labels_inferred")))
        print("  TSV A..F         :", {c: t.get(c) for c in "ABCDEF" if c in t and not pd.isna(t[c])})
        print("  withimg gold_value:", repr(w.get("gold_value")))
print("total mismatches:", n)
