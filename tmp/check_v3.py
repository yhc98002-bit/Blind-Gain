import hashlib, json, random
rows = [json.loads(l) for l in open("data/virl39k_m7_heldout_v3.jsonl")]
random.seed(0)
sample = random.sample(rows, 12)
bad = 0
n = 0
for r in sample:
    for p, s in zip(r["images"], r["metadata"]["image_sha256"]):
        n += 1
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if h != s:
            bad += 1
            print("MISMATCH", p, h, s)
print("sha spot-check bad:", bad, "of", n)
print("all rows path/sha length-aligned:", {len(r["images"]) == len(r["metadata"]["image_sha256"]) for r in rows})
print("rows:", len(rows))
print("dup row_index:", len(rows) - len({r["row_index"] for r in rows}))
print("dup qid:", len(rows) - len({r["qid"] for r in rows}))
print("row_index min/max:", min(r["row_index"] for r in rows), max(r["row_index"] for r in rows))
