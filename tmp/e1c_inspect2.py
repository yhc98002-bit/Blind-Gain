import pandas as pd, string, re, collections
base = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/data/vlmevalkit/"
pat = re.compile(r"<image\s*\d*\s*>")
for name in ["MMStar_VLMEVAL","MathVista_LOCAL","BLINK_LOCAL","MMVP_LOCAL_V2","HallusionBench_LOCAL_V2","MathVerse_LOCAL","MMMU_LOCAL_V2"]:
    df = pd.read_csv(base+name+".tsv", sep="\t")
    hits = collections.Counter()
    forms = collections.Counter()
    for _, r in df.iterrows():
        cells = [str(r["question"])]
        for c in string.ascii_uppercase:
            if c in r and not pd.isna(r[c]): cells.append(str(r[c]))
        blob = "\n".join(cells)
        if "<image" in blob:
            hits["any_<image"] += 1
            for m in pat.findall(blob): forms[m] += 1
            if not pat.search(blob): hits["unmatched_form"] += 1
        if "<|vision_" in blob: hits["vision_tok"] += 1
    print(name, dict(hits), "| marker forms:", dict(sorted(forms.items())[:14]))
