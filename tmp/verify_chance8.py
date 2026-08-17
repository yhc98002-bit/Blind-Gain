import json, collections, re
R="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/"
def load(p): return [json.loads(l) for l in open(R+p) if l.strip()]
g_real=load("experiments/runs/m11_blind_gemma3_virl4096_real_gemma3_real_s0of1_an29_20260716T191637Z/per_item.jsonl")
g_none=load("experiments/runs/m11_blind_gemma3_virl4096_none_gemma3_none_s0of1_an29_20260716T200132Z/per_item.jsonl")
i_real=load("experiments/runs/m11_virl4096_patchbudgetv2_internvl3_real_s0of1_an29_20260717T072527Z/per_item.jsonl")
GR={r['qid']:r for r in g_real}; GN={r['qid']:r for r in g_none}; IR={r['qid']:r for r in i_real}
meta=GN
mc=[q for q in meta if meta[q]['source_metadata']['answer_type']=='multiple_choice']
ff_t=[q for q in meta if meta[q]['source_metadata']['answer_type']=='text_or_expression']
print("=== Gemma-3 REAL arm, MC items: acc + extraction diagnostics ===")
print("MC n:",len(mc),"acc_final:",sum(GR[q]['acc_final'] for q in mc)/len(mc))
print("extraction_level census (MC):", dict(collections.Counter(GR[q]['extraction_level'] for q in mc)))
print("extractor_valid (MC):", dict(collections.Counter(GR[q]['extractor_valid'] for q in mc)))
print("contract_valid (MC):", dict(collections.Counter(GR[q]['contract_valid'] for q in mc)))
print("ground_truth sample (MC):", [GR[q]['ground_truth'] for q in mc[:15]])
print("extracted_answer sample (MC):")
for q in mc[:8]:
    print("   gt=%r extracted=%r acc=%s"%(GR[q]['ground_truth'], str(GR[q]['extracted_answer'])[:90], GR[q]['acc_final']))
print()
print("=== Gemma-3 REAL, free-form: acc ===")
ffall=[q for q in meta if meta[q]['source_metadata']['answer_type'] in ('numeric','text_or_expression')]
print("ff n:",len(ffall),"acc_final:",sum(GR[q]['acc_final'] for q in ffall)/len(ffall))
print("ff extraction_level:", dict(collections.Counter(GR[q]['extraction_level'] for q in ffall)))
print()
print("=== InternVL3 REAL arm, MC ===")
print("MC acc_final:",sum(IR[q]['acc_final'] for q in mc)/len(mc))
print("extraction_level census (MC):", dict(collections.Counter(IR[q]['extraction_level'] for q in mc)))
print()
print("=== text_or_expression ground-truth census (is null=0 justified?) ===")
c=collections.Counter(str(meta[q]['ground_truth']).strip().lower() for q in ff_t)
print("n distinct gt:", len(c), "of", len(ff_t))
print("top 30:", c.most_common(30))
binlike=sum(v for k,v in c.items() if k in ('yes','no','true','false','a','b','c','d','right','left','up','down','positive','negative','increase','decrease'))
print("binary/label-like gt count:", binlike)
print()
print("=== numeric ground-truth census ===")
ff_n=[q for q in meta if meta[q]['source_metadata']['answer_type']=='numeric']
cn=collections.Counter(str(meta[q]['ground_truth']).strip() for q in ff_n)
print("n distinct:", len(cn), "of", len(ff_n), "top15:", cn.most_common(15))
