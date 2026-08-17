import pandas as pd, string, collections, re
base = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/data/vlmevalkit/"

def labels_of(row):
    return [c for c in string.ascii_uppercase if c in row and not pd.isna(row[c])]

print("########## HallusionBench_LOCAL_V2")
df = pd.read_csv(base+"HallusionBench_LOCAL_V2.tsv", sep="\t")
print("answer value_counts:\n", df["answer"].value_counts(dropna=False))
print("question endswith 'yes or no' count:", df["question"].astype(str).str.lower().str.contains("yes or no").sum())
for i in range(3):
    print("---q:", repr(df.iloc[i]["question"])[:400], "| ans=", repr(df.iloc[i]["answer"]))
print("visual_input vc:", df["visual_input"].value_counts(dropna=False).to_dict())
print("image_is_placeholder vc:", df["image_is_placeholder"].value_counts(dropna=False).to_dict())

print("\n########## MMMU_LOCAL_V2")
df = pd.read_csv(base+"MMMU_LOCAL_V2.tsv", sep="\t")
q = df["question"].astype(str)
print("rows with '<image' in question:", q.str.contains(r"<image", regex=True).sum())
opt_hits = 0
for _, r in df.iterrows():
    for c in labels_of(r):
        if "<image" in str(r[c]): opt_hits += 1; break
print("rows with '<image' in an option:", opt_hits)
print("answer_type vc:", df["answer_type"].value_counts(dropna=False).to_dict())
print("question_type vc:", df["question_type"].value_counts(dropna=False).to_dict())
kd = collections.Counter(len(labels_of(r)) for _, r in df.iterrows())
print("k dist:", dict(sorted(kd.items())))
print("split vc:", df["split"].value_counts(dropna=False).to_dict())
ex = df[q.str.contains("<image")].iloc[0]
print("example q:", repr(ex["question"])[:500])

print("\n########## MathVerse_LOCAL")
df = pd.read_csv(base+"MathVerse_LOCAL.tsv", sep="\t")
kd = collections.Counter(len(labels_of(r)) for _, r in df.iterrows())
print("k dist:", dict(sorted(kd.items())))
print("answer_type vc:", df["answer_type"].value_counts(dropna=False).to_dict())
print("question_type vc:", df["question_type"].value_counts(dropna=False).to_dict())
print("choice_source vc:", df["choice_source"].value_counts(dropna=False).to_dict())
print("rows with '<image' in question:", df["question"].astype(str).str.contains("<image").sum())
print("example q (k>0):")
for _, r in df.iterrows():
    if len(labels_of(r))>0:
        print(repr(r["question"])[:600]); print("  answer=",repr(r["answer"]),"answer_option=",repr(r.get("answer_option")),"answer_options=",repr(r.get("answer_options"))); break
print("example q (k=0):")
for _, r in df.iterrows():
    if len(labels_of(r))==0:
        print(repr(r["question"])[:400]); print("  answer=",repr(r["answer"])); break

print("\n########## BLINK_LOCAL")
df = pd.read_csv(base+"BLINK_LOCAL.tsv", sep="\t")
kd = collections.Counter(len(labels_of(r)) for _, r in df.iterrows())
print("k dist:", dict(sorted(kd.items())))
print("rows with '<image' in question:", df["question"].astype(str).str.contains("<image").sum())
print("has hint col:", "hint" in df.columns)
print("example q:", repr(df.iloc[0]["question"])[:300], "ans=", repr(df.iloc[0]["answer"]))
print("answer vc head:", df["answer"].value_counts().head(6).to_dict())

print("\n########## MMVP_LOCAL_V2")
df = pd.read_csv(base+"MMVP_LOCAL_V2.tsv", sep="\t")
kd = collections.Counter(len(labels_of(r)) for _, r in df.iterrows())
print("k dist:", dict(sorted(kd.items())))
print("has hint col:", "hint" in df.columns)
print("example q:", repr(df.iloc[0]["question"])[:300], "ans=", repr(df.iloc[0]["answer"]))
