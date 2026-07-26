#!/usr/bin/env python3
"""Build the registered image-disjoint M7 held-out split (v2).

Implements docs/registered_m7_heldout_split_v2.md: connected components under
shared image hashes, joint (source, category) stratification by the component's
smallest qid, deterministic hash ordering, >=15% of stratum items held out by
whole components, and a fail-closed zero-shared-image guarantee.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
SALT = "|m7-heldout-v2"
HELDOUT_FRACTION = 0.15
ELIGIBILITY_MIN = 30


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _images(row: dict[str, Any]) -> list[str]:
    digests = (row.get("metadata") or {}).get("image_sha256")
    if isinstance(digests, list):
        return [str(value) for value in digests]
    if isinstance(digests, str):
        return [digests]
    return []


class Union:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, key: str) -> str:
        self.parent.setdefault(key, key)
        root = key
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[key] != root:
            self.parent[key], key = root, self.parent[key]
        return root

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subset", type=Path, default=ROOT / "data/virl39k_main_filtered.jsonl")
    parser.add_argument("--train-out", type=Path, default=ROOT / "data/virl39k_m7_train_v2.jsonl")
    parser.add_argument("--heldout-out", type=Path, default=ROOT / "data/virl39k_m7_heldout_v2.jsonl")
    parser.add_argument("--manifest-out", type=Path, default=ROOT / "data/virl39k_m7_split_manifest_v2.json")
    args = parser.parse_args()
    for path in (args.train_out, args.heldout_out, args.manifest_out):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite frozen split artifact: {path}")

    rows = [
        json.loads(line)
        for line in args.subset.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_qid = {str(row["qid"]): row for row in rows}
    if len(by_qid) != len(rows):
        raise ValueError("frozen subset contains duplicate qids")

    union = Union()
    image_owner: dict[str, str] = {}
    for row in rows:
        qid = str(row["qid"])
        union.find(qid)
        for digest in _images(row):
            if digest in image_owner:
                union.union(qid, image_owner[digest])
            else:
                image_owner[digest] = qid

    components: dict[str, list[str]] = defaultdict(list)
    for qid in by_qid:
        components[union.find(qid)].append(qid)

    stratum_components: dict[tuple[str, str], list[tuple[str, list[str]]]] = defaultdict(list)
    for root, members in components.items():
        key_qid = min(members)
        metadata = by_qid[key_qid].get("metadata") or {}
        label = (str(metadata.get("source")), str(metadata.get("category")))
        stratum_components[label].append((key_qid, sorted(members)))

    heldout_qids: set[str] = set()
    stratum_records: list[dict[str, Any]] = []
    for label in sorted(stratum_components):
        comps = sorted(
            stratum_components[label],
            key=lambda item: hashlib.sha256(f"{item[0]}{SALT}".encode("utf-8")).hexdigest(),
        )
        n_items = sum(len(members) for _, members in comps)
        target = HELDOUT_FRACTION * n_items
        taken = 0
        taken_components = 0
        for _, members in comps:
            if taken >= target and not (taken_components == 0 and len(comps) >= 2):
                break
            heldout_qids.update(members)
            taken += len(members)
            taken_components += 1
        stratum_records.append(
            {
                "source": label[0],
                "category": label[1],
                "n_items": n_items,
                "n_components": len(comps),
                "n_heldout": taken,
                "n_train": n_items - taken,
                "realized_heldout_share": round(taken / n_items, 4) if n_items else 0.0,
                "rank_statistic_eligible": taken >= ELIGIBILITY_MIN,
            }
        )

    train_rows = [row for row in rows if str(row["qid"]) not in heldout_qids]
    heldout_rows = [row for row in rows if str(row["qid"]) in heldout_qids]
    if len(train_rows) + len(heldout_rows) != len(rows):
        raise AssertionError("partition does not cover the frozen subset")

    train_images = {d for row in train_rows for d in _images(row)}
    heldout_images = {d for row in heldout_rows for d in _images(row)}
    shared = train_images & heldout_images
    if shared:
        raise AssertionError(f"image-disjointness violated: {len(shared)} shared images")

    def _write(path: Path, items: list[dict[str, Any]]) -> None:
        with path.open("x", encoding="utf-8") as handle:
            for item in items:
                handle.write(json.dumps(item, sort_keys=True, ensure_ascii=True) + "\n")

    _write(args.train_out, train_rows)
    _write(args.heldout_out, heldout_rows)

    manifest = {
        "schema_version": "blind-gains.m7-heldout-split.v2",
        "registration": "docs/registered_m7_heldout_split_v2.md",
        "supersedes": "docs/registered_m7_heldout_split_v1.md",
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_subset": str(args.subset.relative_to(ROOT)),
        "source_subset_sha256": _sha256_file(args.subset),
        "allocation_unit": "connected component under shared image sha256",
        "heldout_fraction_target": HELDOUT_FRACTION,
        "salt": SALT,
        "n_items": len(rows),
        "n_components": len(components),
        "n_train": len(train_rows),
        "n_heldout": len(heldout_rows),
        "realized_heldout_share": round(len(heldout_rows) / len(rows), 4),
        "train_output": str(args.train_out.relative_to(ROOT)),
        "train_sha256": _sha256_file(args.train_out),
        "heldout_output": str(args.heldout_out.relative_to(ROOT)),
        "heldout_sha256": _sha256_file(args.heldout_out),
        "n_strata": len(stratum_records),
        "n_strata_rank_eligible": sum(1 for r in stratum_records if r["rank_statistic_eligible"]),
        "image_integrity": {
            "train_unique_images": len(train_images),
            "heldout_unique_images": len(heldout_images),
            "shared_images": 0,
            "guarantee": "image-disjoint by construction; builder refuses to write otherwise",
        },
        "strata": stratum_records,
    }
    args.manifest_out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in (
        "n_items", "n_components", "n_train", "n_heldout", "realized_heldout_share",
        "n_strata", "n_strata_rank_eligible", "train_sha256", "heldout_sha256")}, sort_keys=True))


if __name__ == "__main__":
    main()
