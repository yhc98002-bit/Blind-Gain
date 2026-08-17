#!/usr/bin/env python3
"""Compare an independent replay of the seed-1 invocation against the PUBLISHED
reports/m7_r3_readout_v1.{json,md}.  Only the output-path strings the CLI itself
chose may differ; every value, every sha256 and every interval must be identical.
"""
import hashlib
import json
import sys
from pathlib import Path

repo = Path(sys.argv[1])
pub_json = repo / "reports/m7_r3_readout_v1.json"
pub_md = repo / "reports/m7_r3_readout_v1.md"
rep_json = repo / "experiments/scratch_verify_twoseed/replay/replay.json"
rep_md = repo / "experiments/scratch_verify_twoseed/replay/replay.md"

PUB_PREFIX = "reports/m7_r3_readout_v1"
REP_PREFIX = "experiments/scratch_verify_twoseed/replay/replay"
PUB_ART = "reports/m7_r3_readout_v1_artifacts"
REP_ART = "experiments/scratch_verify_twoseed/replay/arts"

a = pub_json.read_text()
b = rep_json.read_text()
b_norm = b.replace(REP_ART, PUB_ART).replace(REP_PREFIX + ".json", PUB_PREFIX + ".json")
print("JSON identical after normalising ONLY the CLI output paths:", a == b_norm)
if a != b_norm:
    da, db = json.loads(a), json.loads(b_norm)

    def walk(x, y, p=""):
        out = []
        if type(x) is not type(y):
            return [f"{p}: type {type(x)} vs {type(y)}"]
        if isinstance(x, dict):
            for k in sorted(set(x) | set(y)):
                if k not in x:
                    out.append(f"{p}/{k}: only in replay")
                elif k not in y:
                    out.append(f"{p}/{k}: only in published")
                else:
                    out += walk(x[k], y[k], f"{p}/{k}")
        elif isinstance(x, list):
            if len(x) != len(y):
                out.append(f"{p}: len {len(x)} vs {len(y)}")
            else:
                for i, (u, v) in enumerate(zip(x, y)):
                    out += walk(u, v, f"{p}[{i}]")
        elif x != y:
            out.append(f"{p}: {x!r} vs {y!r}")
        return out

    diffs = walk(da, db)
    print(f"  {len(diffs)} differing leaves; first 25:")
    for d in diffs[:25]:
        print("   ", d)

ma = pub_md.read_text()
mb = rep_md.read_text().replace(REP_ART, PUB_ART).replace(
    REP_PREFIX + ".json", PUB_PREFIX + ".json"
)
print("MD identical after the same normalisation:", ma == mb)
if ma != mb:
    la, lb = ma.split("\n"), mb.split("\n")
    n = 0
    for i, (u, v) in enumerate(zip(la, lb), 1):
        if u != v:
            n += 1
            if n <= 10:
                print(f"  line {i}:\n    pub: {u}\n    rep: {v}")
    print(f"  total differing lines: {n} (len {len(la)} vs {len(lb)})")

# artifacts
pub_art_dir = repo / PUB_ART
rep_art_dir = repo / REP_ART
for f in sorted(pub_art_dir.glob("*")):
    g = rep_art_dir / f.name
    if not g.exists():
        print(f"artifact MISSING in replay: {f.name}")
        continue
    h1 = hashlib.sha256(f.read_bytes()).hexdigest()
    h2 = hashlib.sha256(g.read_bytes()).hexdigest()
    print(f"artifact {f.name}: {'same' if h1 == h2 else 'DIFFERENT'}")
