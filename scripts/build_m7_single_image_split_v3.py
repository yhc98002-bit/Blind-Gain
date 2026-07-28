#!/usr/bin/env python3
"""Build the single-image M7 splits (v3), per registered_m7_single_image_v2.md.

Writes _v3 alongside the registered _v2 rather than overwriting, so the original
split stays inspectable. Verifies the property the amendment rests on: that every
joint (source, category) stratum with >=30 held-out items under v2 still has >=30
under v3, so the registered rank statistic is computed on the same strata.
"""
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
MIN_STRATUM = 30


def load(p):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def stratum(r):
    m = r.get("metadata") or {}
    return (m.get("source"), m.get("category"))


summary = {"registration": "docs/registered_m7_single_image_v2.md", "splits": {}}

for split in ("train", "heldout"):
    src = ROOT / f"data/virl39k_m7_{split}_v2.jsonl"
    dst = ROOT / f"data/virl39k_m7_{split}_v3.jsonl"
    rows = load(src)
    keep = [r for r in rows if len(r.get("images") or []) <= 1]

    blob = "".join(json.dumps(r, sort_keys=True) + "\n" for r in keep)
    dst.write_text(blob)

    summary["splits"][split] = {
        "source": src.name, "output": dst.name,
        "rows_before": len(rows), "rows_after": len(keep),
        "retained_fraction": round(len(keep) / len(rows), 4),
        "sha256": hashlib.sha256(blob.encode()).hexdigest(),
    }
    print(f"{split}: {len(keep)}/{len(rows)} retained "
          f"({100*len(keep)/len(rows):.1f}%) -> {dst.name}")

# the property the amendment rests on
held_v2 = load(ROOT / "data/virl39k_m7_heldout_v2.jsonl")
held_v3 = load(ROOT / "data/virl39k_m7_heldout_v3.jsonl")
c2 = collections.Counter(stratum(r) for r in held_v2)
c3 = collections.Counter(stratum(r) for r in held_v3)
q2 = {k for k, v in c2.items() if v >= MIN_STRATUM}
q3 = {k for k, v in c3.items() if v >= MIN_STRATUM}
lost = sorted(q2 - q3)

summary["strata_check"] = {
    "min_items": MIN_STRATUM,
    "qualifying_v2": len(q2), "qualifying_v3": len(q3),
    "lost": [list(x) for x in lost],
    "passes": not lost,
}
print(f"\nstrata with >={MIN_STRATUM} held-out items: v2 {len(q2)} -> v3 {len(q3)}")
if lost:
    print(f"FAIL: {len(lost)} strata dropped below the threshold: {lost}")
    raise SystemExit(1)
print("PASS: no stratum falls below the registered rank-statistic threshold")

(ROOT / "reports/m7_single_image_split_v3.json").write_text(
    json.dumps(summary, indent=2, sort_keys=True) + "\n")
print("wrote reports/m7_single_image_split_v3.json")
