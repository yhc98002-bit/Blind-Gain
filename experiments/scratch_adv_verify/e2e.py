#!/usr/bin/env python3
"""Run the REAL consumer over the REAL derived caption-QA release/key with a
synthetic caption store, then assert every emitted (image, answer) pair matches
the source manifest's own (image_{side}_sha256, answer_{side}) binding."""
import json
import sys
from pathlib import Path

sys.path.insert(0, "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
from src.captioning.qa_pairs import build_caption_qa_rows  # noqa: E402

DATA = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/data/track4_premise_v2_dev_v1")
OUT = DATA / "caption_qa_inputs"


def rj(p):
    return [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]


src = {r["pair_id"]: r for r in rj(DATA / "manifest_causal_pairs.jsonl")}
release = rj(OUT / "manifest.jsonl")
key = rj(OUT / "key.jsonl")
captions = [
    {"image_sha256": m["image_sha256"], "caption": "cap:" + m["member_id"]}
    for r in release
    for m in r["members"]
]
qa = build_caption_qa_rows(release, key, captions, OUT)
print("qa rows:", len(qa))

bad = 0
for row in qa:
    s = src[row["pair_id"]]
    for side in ("a", "b"):
        # the answer the consumer emits for this side must be the source answer
        # for the IMAGE the consumer emits for this side
        h = row["image_%s_sha256" % side]
        if h == s["image_a_sha256"]:
            expect = str(s["answer_a"])
            expect_path = s["image_a_path"]
        elif h == s["image_b_sha256"]:
            expect = str(s["answer_b"])
            expect_path = s["image_b_path"]
        else:
            print("HASH NOT IN SOURCE", row["pair_id"], side, h)
            bad += 1
            continue
        if row["answer_%s" % side] != expect:
            print("BROKEN BINDING", row["pair_id"], side, row["answer_%s" % side], expect)
            bad += 1
        if Path(row["image_%s_path" % side]).resolve() != Path(expect_path).resolve():
            print("PATH/HASH DISAGREE", row["pair_id"], side, row["image_%s_path" % side], expect_path)
            bad += 1
        if row["caption_%s" % side] != "cap:%s" % row["member_id_%s" % side]:
            print("CAPTION JOIN WRONG", row["pair_id"], side)
            bad += 1
    if row["question"] != s["question"]:
        print("QUESTION MISMATCH", row["pair_id"])
        bad += 1
    if row["source_pair_id"] != row["pair_id"]:
        print("SPID", row["pair_id"], row["source_pair_id"])
        bad += 1
print("broken bindings:", bad)

# also confirm the real store (all 480 image hashes) would be refused w/o the flag
allh = set()
import hashlib
for p in sorted((DATA / "images").iterdir()):
    allh.add(hashlib.sha256(p.read_bytes()).hexdigest())
wide = [{"image_sha256": h, "caption": "c"} for h in sorted(allh)]
try:
    build_caption_qa_rows(release, key, wide, OUT)
    print("WIDE STORE ACCEPTED (unexpected)")
except ValueError as exc:
    print("wide store refused as expected:", exc)
try:
    build_caption_qa_rows(release, key, wide, OUT, allow_extra_captions=True)
    print("wide store accepted with allow_extra_captions=True")
except Exception as exc:
    print("wide store STILL refused with flag:", type(exc).__name__, exc)
sys.exit(1 if bad else 0)
