import json
from src.eval.conditioned_inputs import build_conditioned_messages, load_caption_map, load_geometry_rows

src = [json.loads(l) for l in open("data/virl39k_m7_heldout_v3.jsonl")]
dst = [json.loads(l) for l in open("data/virl39k_m7_heldout_v3_eval.jsonl")]
assert len(src) == len(dst), (len(src), len(dst))

# Equivalence: everything except images/schema_version is unchanged; images re-shaped losslessly.
bad = 0
for a, b in zip(src, dst):
    ka = {k: v for k, v in a.items() if k not in ("images", "schema_version")}
    kb = {k: v for k, v in b.items() if k not in ("images", "schema_version")}
    if ka != kb:
        bad += 1
    if [i["path"] for i in b["images"]] != list(a["images"]):
        bad += 1
    if [i["sha256"] for i in b["images"]] != list(a["metadata"]["image_sha256"]):
        bad += 1
print("equivalence violations:", bad)

rows = load_geometry_rows("data/virl39k_m7_heldout_v3_eval.jsonl", ["train"])
print("load_geometry_rows(splits=train) ->", len(rows), "rows")

fp = open("artifacts/repos/EasyR1/examples/format_prompt/r1v.jinja").read()
cm = load_caption_map(["data/virl39k_caption_store_3b_main_v2.jsonl"])
for cond in ["real", "gray", "none", "caption"]:
    ok = 0
    for row in rows[:25]:
        msgs, _ = build_conditioned_messages(row, fp, cond, "/dev/shm/blind-gains/_smoke/cc", captions=cm if cond == "caption" else None)
        # the harness also does this for every condition:
        _ = [im["sha256"] for im in row.get("images", [])]
        ok += 1
    print(f"{cond}: built {ok}/25 prompts OK")

# caption coverage over the whole eval manifest
need = {im["sha256"] for r in rows for im in r["images"]}
print("caption coverage:", len(need & set(cm)), "/", len(need))
