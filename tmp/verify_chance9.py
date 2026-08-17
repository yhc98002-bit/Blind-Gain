import json, collections, re
import numpy as np
R="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
def load(p): return [json.loads(l) for l in open(R+p) if l.strip()]
ARM={("gemma3","none"):"m11_blind_gemma3_virl4096_none_gemma3_none_s0of1_an29_20260716T200132Z",
     ("gemma3","real"):"m11_blind_gemma3_virl4096_real_gemma3_real_s0of1_an29_20260716T191637Z",
     ("gemma3","caption"):"m11_blind_gemma3_virl4096_caption_gemma3_caption_s0of1_an29_20260716T231512Z",
     ("internvl3","none"):"m11_virl4096_retry1_internvl3_none_s0of1_an12_20260716T170739Z",
     ("internvl3","real"):"m11_virl4096_patchbudgetv2_internvl3_real_s0of1_an29_20260717T072527Z",
     ("internvl3","caption"):"m11_virl4096_retry1_internvl3_caption_s0of1_an12_20260716T170744Z"}
D={k:{r['qid']:r for r in load("experiments/runs/%s/per_item.jsonl"%v)} for k,v in ARM.items()}
meta=D[("gemma3","none")]; qids=sorted(meta)
at={q:meta[q]['source_metadata']['answer_type'] for q in qids}
mc=[q for q in qids if at[q]=='multiple_choice']

print("=== QUANTIFY MC LABEL-MATCH DEFECT ===")
lead=re.compile(r'^\s*\(?([A-H])\)?\s*[\.\):：、．]')
for arm in ARM:
    d=D[arm]; miss=0; hit=0
    for q in mc:
        gt=str(d[q]['ground_truth']).strip()
        ex=str(d[q]['extracted_answer'] or '')
        m=lead.match(ex)
        if m and len(ex.strip())>1:      # model emitted "X. <text>"
            if m.group(1)==gt and not d[q]['acc_final']: miss+=1
            if m.group(1)==gt and d[q]['acc_final']: hit+=1
    print("%-22s MC n=%d  'LABEL. text' outputs where leading label==gold but acc_final=False: %d  (scored True: %d)"%("|".join(arm),len(mc),miss,hit))
print()
print("=== effect on Gemma-3 real MC accuracy if leading-label match were credited ===")
d=D[("gemma3","real")]
asis=sum(d[q]['acc_final'] for q in mc)/len(mc)
fixed=0
for q in mc:
    gt=str(d[q]['ground_truth']).strip(); ex=str(d[q]['extracted_answer'] or '')
    m=lead.match(ex)
    fixed += 1 if (d[q]['acc_final'] or (m and m.group(1)==gt)) else 0
print("as-is %.4f   leading-label-credited %.4f  (chance floor ~0.268)"%(asis, fixed/len(mc)))
d=D[("gemma3","none")]
asis=sum(d[q]['acc_final'] for q in mc)/len(mc)
fixed=sum(1 for q in mc if d[q]['acc_final'] or (lead.match(str(d[q]['extracted_answer'] or '')) and lead.match(str(d[q]['extracted_answer'] or '')).group(1)==str(d[q]['ground_truth']).strip()))
print("gemma3 BLIND MC as-is %.4f  leading-label-credited %.4f"%(asis, fixed/len(mc)))
