#!/usr/bin/env python3
"""Derive per-family caption-stress QA inputs for hier_v1 (HB P2.3) from the
L3 dev manifests: a release dir (manifest.jsonl + hard-linked images/) and a
private key file, shaped exactly for src/captioning/qa_pairs.py::
build_caption_qa_rows (the E3 caption-stress consumer).

SIDE BINDING (mirrors build_track4_premise_v2_caption_qa_inputs.py):
source_side is the FILE-SUFFIX side. answer_{side} in the L3 manifest already
describes image_{side}_path, so the answer always travels with the member
whose own image it describes. The attacker key's semantic
side_assignment_swapped is deliberately NOT applied here — applying it would
invert the answers of every swapped pair.

Population: causal pairs only (role != invariance), the same rows the
artifact-attacker release packages. Every image hash is re-computed from disk
and must match the manifest. Refuses to overwrite any existing output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = {
    "hier_coord_v1": ("n8", "n12", "n20"),
    "hier_chart_v1": ("s5_low", "s5_high", "s9_low", "s9_high"),
}


def link_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        raise FileExistsError(dst)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def build_family(data_dir: Path, family: str, cells: tuple[str, ...]) -> dict:
    release_dir = data_dir / f"caption_stress_{family}"
    key_path = data_dir / f"caption_stress_key_{family}.jsonl"
    for path in (release_dir, key_path):
        if path.exists():
            raise FileExistsError(path)
    release_rows, key_rows = [], []
    seen_hashes: set[str] = set()
    per_cell: dict[str, int] = {}
    for cell in cells:
        manifest = data_dir / f"manifest_{family}_{cell}_l3.jsonl"
        for line in manifest.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row["role"] == "invariance":
                continue
            pair_id = str(row["pair_id"])
            members, key_members = [], []
            for side in ("a", "b"):
                src = Path(row[f"image_{side}_path"])
                if not src.is_file():
                    raise FileNotFoundError(src)
                digest = sha256_file(src)
                if digest != row[f"image_{side}_sha256"]:
                    raise ValueError(
                        f"on-disk sha mismatch for {pair_id} side {side}")
                if digest in seen_hashes:
                    raise ValueError(f"duplicate image hash in {family}: {digest}")
                seen_hashes.add(digest)
                rel = Path("images") / f"{pair_id}_{side}.png"
                link_or_copy(src, release_dir / rel)
                members.append({"member_id": f"{pair_id}_{side}",
                                "image_path": str(rel),
                                "image_sha256": digest})
                key_members.append({"member_id": f"{pair_id}_{side}",
                                    "source_side": side,
                                    "answer": str(row[f"answer_{side}"])})
            release_rows.append({"pair_id": pair_id,
                                 "question": str(row["question"]),
                                 "members": members})
            key_rows.append({"pair_id": pair_id,
                             "source_pair_id": pair_id,
                             "category": family,
                             "template_id": row["template_id"],
                             "members": key_members})
            per_cell[cell] = per_cell.get(cell, 0) + 1
    (release_dir / "manifest.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in release_rows), encoding="utf-8")
    key_path.write_text(
        "".join(json.dumps(r) + "\n" for r in key_rows), encoding="utf-8")
    return {"pairs": len(release_rows),
            "per_cell": per_cell,
            "release_dir": str(release_dir),
            "release_manifest_sha256": sha256_file(release_dir / "manifest.jsonl"),
            "key": str(key_path),
            "key_sha256": sha256_file(key_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/hier_v1_dev")
    parser.add_argument("--families", nargs="+", choices=sorted(FAMILIES),
                        default=sorted(FAMILIES))
    parser.add_argument("--report", type=Path,
                        default=ROOT / "reports/hier_caption_stress_inputs_v1.json")
    args = parser.parse_args()
    if args.report.exists():
        raise FileExistsError(args.report)
    summary = {"schema_version": "blind-gains.hier-caption-stress-inputs.v1",
               "side_binding": "file-suffix (answers travel with their own image; "
                               "semantic swap NOT applied)",
               "population": "L3 causal pairs (role != invariance)",
               "families": {}}
    for family, cells in ((f, FAMILIES[f]) for f in args.families):
        summary["families"][family] = build_family(args.data_dir, family, cells)
    args.report.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(summary["families"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
