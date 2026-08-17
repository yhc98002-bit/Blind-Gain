#!/usr/bin/env python3
"""Independent field-by-field verification of the derived caption-QA release/key
against data/track4_premise_v2_dev_v1/manifest_causal_pairs.jsonl.

Written by the adversarial verifier; does NOT import the exporter.
"""
import hashlib
import json
import os
import sys

ROOT = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"
DATA = os.path.join(ROOT, "data/track4_premise_v2_dev_v1")
SRC = os.path.join(DATA, "manifest_causal_pairs.jsonl")
REL = os.path.join(DATA, "caption_qa_inputs/manifest.jsonl")
KEY = os.path.join(DATA, "caption_qa_inputs/key.jsonl")
RELDIR = os.path.join(DATA, "caption_qa_inputs")


def load(p):
    out = []
    with open(p, "rb") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


src = load(SRC)
rel = load(REL)
key = load(KEY)

print("counts src=%d rel=%d key=%d" % (len(src), len(rel), len(key)))

src_by = {}
for r in src:
    src_by[r["pair_id"]] = r
rel_by = {r["pair_id"]: r for r in rel}
key_by = {r["pair_id"]: r for r in key}

problems = []
checked = 0
sample_dump = []

# what source keys exist at all
allkeys = set()
for r in src:
    allkeys |= set(r.keys())
print("source top-level keys:", sorted(allkeys))
print("has source_pair_id in any row:", any("source_pair_id" in r for r in src))
print("has catch_twin_id in any row:", any("catch_twin_id" in r for r in src))
print("catch_twin_id values non-null:", sum(1 for r in src if r.get("catch_twin_id") is not None))

for pid, s in src_by.items():
    R = rel_by.get(pid)
    K = key_by.get(pid)
    if R is None:
        problems.append("MISSING release row %s" % pid)
        continue
    if K is None:
        problems.append("MISSING key row %s" % pid)
        continue
    checked += 1
    # release: question byte-identical
    if R.get("question") != s.get("question"):
        problems.append("QUESTION MISMATCH %s: rel=%r src=%r" % (pid, R.get("question"), s.get("question")))
    if R.get("pair_id") != s.get("pair_id"):
        problems.append("PAIR_ID MISMATCH %s" % pid)
    if K.get("template_id") != s.get("template_id"):
        problems.append("TEMPLATE MISMATCH %s: key=%r src=%r" % (pid, K.get("template_id"), s.get("template_id")))
    if K.get("category") != s.get("category"):
        problems.append("CATEGORY MISMATCH %s: key=%r src=%r" % (pid, K.get("category"), s.get("category")))
    if K.get("catch_twin_id") != s.get("catch_twin_id"):
        problems.append("CATCHTWIN MISMATCH %s: key=%r src=%r" % (pid, K.get("catch_twin_id"), s.get("catch_twin_id")))
    # source_pair_id fallback
    spid = K.get("source_pair_id")
    if "source_pair_id" in s and s["source_pair_id"] is not None:
        if spid != str(s["source_pair_id"]):
            problems.append("SOURCE_PAIR_ID MISMATCH %s" % pid)
    else:
        if spid != pid:
            problems.append("SOURCE_PAIR_ID FALLBACK WRONG %s: %r" % (pid, spid))

    relm = {m["member_id"]: m for m in R["members"]}
    keym = {m["member_id"]: m for m in K["members"]}
    if set(relm) != set(keym):
        problems.append("MEMBER SET MISMATCH %s" % pid)
        continue
    if len(relm) != 2:
        problems.append("MEMBER COUNT %s = %d" % (pid, len(relm)))
        continue
    for side in ("a", "b"):
        mid = "%s_%s" % (pid, side)
        if mid not in relm:
            problems.append("MEMBER ID CONVENTION BROKEN %s side %s (have %r)" % (pid, side, sorted(relm)))
            continue
        rm = relm[mid]
        km = keym[mid]
        # sha256 verbatim
        if rm.get("image_sha256") != s.get("image_%s_sha256" % side):
            problems.append("SHA MISMATCH %s %s: rel=%r src=%r" % (pid, side, rm.get("image_sha256"), s.get("image_%s_sha256" % side)))
        # image path resolves to the same file
        resolved = os.path.normpath(os.path.join(RELDIR, rm["image_path"]))
        srcpath = os.path.normpath(s["image_%s_path" % side])
        if not os.path.isabs(srcpath):
            srcpath = os.path.normpath(os.path.join(ROOT, srcpath))
        if resolved != srcpath:
            problems.append("PATH MISMATCH %s %s: resolved=%r src=%r" % (pid, side, resolved, srcpath))
        if not os.path.exists(resolved):
            problems.append("PATH NOT ON DISK %s %s: %r" % (pid, side, resolved))
        # answer verbatim
        if km.get("answer") != str(s.get("answer_%s" % side)):
            problems.append("ANSWER MISMATCH %s %s: key=%r src=%r" % (pid, side, km.get("answer"), s.get("answer_%s" % side)))
        if km.get("source_side") != side:
            problems.append("SIDE BINDING %s: member %s has source_side=%r" % (pid, mid, km.get("source_side")))

    if len(sample_dump) < 12:
        sample_dump.append(pid)

print("checked pairs:", checked)
print("problems:", len(problems))
for p in problems[:60]:
    print("  ", p)

# extra rows?
extra_rel = set(rel_by) - set(src_by)
extra_key = set(key_by) - set(src_by)
print("extra release pair_ids:", sorted(extra_rel)[:5], len(extra_rel))
print("extra key pair_ids:", sorted(extra_key)[:5], len(extra_key))

# release-level constraints the consumer enforces
hashes = {}
for R in rel:
    for m in R["members"]:
        h = m["image_sha256"]
        if h in hashes:
            print("REUSED RELEASE HASH", h, hashes[h], R["pair_id"])
        hashes[h] = R["pair_id"]
print("distinct release hashes:", len(hashes))

# verify sha256 against actual bytes for a sample of 24 members
import random
random.seed(0)
allm = [(R["pair_id"], m) for R in rel for m in R["members"]]
bad = 0
for pid, m in random.sample(allm, 24):
    p = os.path.normpath(os.path.join(RELDIR, m["image_path"]))
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    if h != m["image_sha256"]:
        print("DISK SHA MISMATCH", pid, m["member_id"], h, m["image_sha256"])
        bad += 1
print("disk sha sample bad:", bad, "of 24")

print("SAMPLE PAIRS:", sample_dump)
sys.exit(1 if problems else 0)
