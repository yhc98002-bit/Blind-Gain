import json, os, re, collections
R="/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
def load(p): return [json.loads(l) for l in open(p) if l.strip()]
D=load(os.path.join(R,"experiments/runs/m11_blind_gemma3_virl4096_none_gemma3_none_s0of1_an29_20260716T200132Z/per_item.jsonl"))
mc=[r for r in D if r['source_metadata']['answer_type']=='multiple_choice']
OPT=re.compile(r'^\s*([A-Z])[\.\)、:]\s')
def parse_k(prob):
    labs=[]
    for line in prob.split("\n"):
        m=OPT.match(line)
        if m: labs.append(m.group(1))
    if len(labs)<2:
        labs=re.findall(r'(?:^|\s)([A-Z])[\.\)]\s', prob)
    seq=[]
    for L in labs:
        if L not in seq: seq.append(L)
    return seq
fails=[r for r in mc if not (parse_k(r['problem'])==[chr(65+i) for i in range(len(parse_k(r['problem'])))] and len(parse_k(r['problem']))>=2)]
print("n fails", len(fails))
print("gt dist of fails:", collections.Counter(r['ground_truth'] for r in fails).most_common(10))
print("source dist of fails:", collections.Counter(r['source_metadata']['source'] for r in fails).most_common())
for r in fails[:6]:
    print("======== GT:", r['ground_truth'], "src:", r['source_metadata']['source'])
    print(repr(r['problem'][:900]))
