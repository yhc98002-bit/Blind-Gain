import json, collections, os
R="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
D={"BLINK-3B":"experiments/runs/vlmevalkit_postprocess_l10_blink3b_canonicalv2_final_20260711T132325Z",
   "HallusionBench-3B":"experiments/runs/vlmevalkit_postprocess_l10_hallusion3b_canonicalv2_final_20260711T132325Z",
   "MMVP-3B":"experiments/runs/vlmevalkit_postprocess_l10_mmvp3b_canonicalv2_final_20260711T132326Z",
   "MathVerse-3B":"experiments/runs/vlmevalkit_postprocess_l10_mathverse3b_canonicalv2_v2_20260711T143923Z",
   "MMMU-3B":"experiments/runs/vlmevalkit_postprocess_l10_mmmu3b_v2_canonicalv2_20260711T145554Z"}
for n,d in D.items():
    for c in ("rows.jsonl","postprocessed_v2/rows.jsonl"):
        p=R+d+"/"+c
        if os.path.exists(p):
            rows=[json.loads(l) for l in open(p) if l.strip()]
            kd=collections.Counter(len(r.get('option_labels') or []) for r in rows)
            print("%-20s n=%-5d %s   [%s]"%(n,len(rows),dict(sorted(kd.items())),c)); break
    else: print(n,"NO rows.jsonl")
