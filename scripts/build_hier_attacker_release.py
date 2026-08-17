#!/usr/bin/env python3
"""Package hier_v1 attacker releases (P2.3 attacker checks, per the standard
pipeline): one release per family over the L3 causal pairs of every cell —
release manifest (pair_id + members with release-relative image paths) and a
private-style key (pair_id, template_id, members with semantic source_side).
Images are hard-linked (fallback copy) so the release is self-contained
without duplicating bytes. Mirrors the premise-v2 attacker packaging exactly
(source_side is the SEMANTIC side, honoring the recorded swap).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = {
    "hier_coord_v1": ("n8", "n12", "n20"),
    "hier_chart_v1": ("s5_low", "s5_high", "s9_low", "s9_high"),
    "hier_chart_v2": ("s5_low", "s5_high", "s9_low", "s9_high"),
    "hier_chart_v3": ("s9_low", "s9_high"),
}


def link_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        raise FileExistsError(dst)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/hier_v1_dev")
    parser.add_argument("--families", nargs="+", choices=sorted(FAMILIES),
                        default=sorted(FAMILIES))
    args = parser.parse_args()
    args.data_dir = args.data_dir.resolve()
    summary = {}
    for family, cells in ((f, FAMILIES[f]) for f in args.families):
        release_dir = args.data_dir / f"attacker_release_{family}"
        if release_dir.exists():
            raise FileExistsError(release_dir)
        release_rows, key_rows = [], []
        for cell in cells:
            manifest = args.data_dir / f"manifest_{family}_{cell}_l3.jsonl"
            for line in manifest.read_text().splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                if row["role"] == "invariance":
                    continue  # attacker check reads causal pairs, like premise-v2
                swapped = bool(row["provenance"]["semantic_side_assignment_swapped"])
                members, key_members = [], []
                for side in ("a", "b"):
                    member_id = f"{row['pair_id']}_{side}"
                    src = Path(row[f"image_{side}_path"])
                    rel = Path("images") / src.name
                    link_or_copy(src, release_dir / rel)
                    members.append({"member_id": member_id,
                                    "image_path": str(rel)})
                    semantic = {"a": "b", "b": "a"}[side] if swapped else side
                    key_members.append({"member_id": member_id,
                                        "source_side": semantic})
                release_rows.append({"pair_id": row["pair_id"], "members": members})
                key_rows.append({"pair_id": row["pair_id"],
                                 "template_id": row["template_id"],
                                 "members": key_members})
        (release_dir / "manifest.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in release_rows), encoding="utf-8")
        key_path = args.data_dir / f"attacker_key_{family}.jsonl"
        if key_path.exists():
            raise FileExistsError(key_path)
        key_path.write_text(
            "".join(json.dumps(r) + "\n" for r in key_rows), encoding="utf-8")
        summary[family] = {"pairs": len(release_rows),
                           "release_dir": str(release_dir.relative_to(ROOT)),
                           "key": str(key_path.relative_to(ROOT))}
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
