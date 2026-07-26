#!/usr/bin/env python3
"""Build the registered M7 held-out evaluation split.

Implements docs/registered_m7_heldout_split_v1.md exactly: joint
(source, category) stratification, deterministic hash ordering, 15% held out
per stratum with a floor of one for strata of size >= 2, fail-closed partition
checks, and a manifest recording hashes, per-stratum counts, eligibility
counts, and the descriptive train/held-out image overlap.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
SALT = "|m7-heldout-v1"
HELDOUT_FRACTION = 0.15
ELIGIBILITY_MIN = 30


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _order_key(qid: str) -> str:
    return hashlib.sha256(f"{qid}{SALT}".encode("utf-8")).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subset", type=Path, default=ROOT / "data/virl39k_main_filtered.jsonl")
    parser.add_argument("--train-out", type=Path, default=ROOT / "data/virl39k_m7_train.jsonl")
    parser.add_argument("--heldout-out", type=Path, default=ROOT / "data/virl39k_m7_heldout.jsonl")
    parser.add_argument("--manifest-out", type=Path, default=ROOT / "data/virl39k_m7_split_manifest.json")
    args = parser.parse_args()
    for path in (args.train_out, args.heldout_out, args.manifest_out):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite frozen split artifact: {path}")

    rows = [
        json.loads(line)
        for line in args.subset.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    qids = [str(row["qid"]) for row in rows]
    if len(set(qids)) != len(qids):
        raise ValueError("frozen subset contains duplicate qids")

    strata: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        metadata = row.get("metadata") or {}
        key = (str(metadata.get("source")), str(metadata.get("category")))
        strata[key].append(row)

    heldout_qids: set[str] = set()
    stratum_records: list[dict[str, Any]] = []
    for key in sorted(strata):
        group = sorted(strata[key], key=lambda item: _order_key(str(item["qid"])))
        n = len(group)
        if n < 2:
            take = 0
        else:
            take = max(1, math.ceil(HELDOUT_FRACTION * n))
        chosen = group[:take]
        heldout_qids.update(str(item["qid"]) for item in chosen)
        stratum_records.append(
            {
                "source": key[0],
                "category": key[1],
                "n_items": n,
                "n_heldout": take,
                "n_train": n - take,
                "rank_statistic_eligible": take >= ELIGIBILITY_MIN,
            }
        )

    train_rows = [row for row in rows if str(row["qid"]) not in heldout_qids]
    heldout_rows = [row for row in rows if str(row["qid"]) in heldout_qids]
    if len(train_rows) + len(heldout_rows) != len(rows):
        raise AssertionError("partition does not cover the frozen subset")
    if set(str(r["qid"]) for r in train_rows) & set(str(r["qid"]) for r in heldout_rows):
        raise AssertionError("train and held-out qid sets intersect")

    def _write(path: Path, items: list[dict[str, Any]]) -> None:
        with path.open("x", encoding="utf-8") as handle:
            for item in items:
                handle.write(json.dumps(item, sort_keys=True, ensure_ascii=True) + "\n")

    _write(args.train_out, train_rows)
    _write(args.heldout_out, heldout_rows)

    def _images(items: list[dict[str, Any]]) -> set[str]:
        found: set[str] = set()
        for item in items:
            digests = (item.get("metadata") or {}).get("image_sha256")
            if isinstance(digests, list):
                found.update(str(value) for value in digests)
            elif isinstance(digests, str):
                found.add(digests)
        return found

    train_images = _images(train_rows)
    heldout_images = _images(heldout_rows)
    overlap = train_images & heldout_images

    manifest = {
        "schema_version": "blind-gains.m7-heldout-split.v1",
        "registration": "docs/registered_m7_heldout_split_v1.md",
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_subset": str(args.subset.relative_to(ROOT)),
        "source_subset_sha256": _sha256_file(args.subset),
        "heldout_fraction_target": HELDOUT_FRACTION,
        "salt": SALT,
        "n_items": len(rows),
        "n_train": len(train_rows),
        "n_heldout": len(heldout_rows),
        "train_output": str(args.train_out.relative_to(ROOT)),
        "train_sha256": _sha256_file(args.train_out),
        "heldout_output": str(args.heldout_out.relative_to(ROOT)),
        "heldout_sha256": _sha256_file(args.heldout_out),
        "n_strata": len(stratum_records),
        "n_strata_rank_eligible": sum(1 for r in stratum_records if r["rank_statistic_eligible"]),
        "image_integrity": {
            "train_unique_images": len(train_images),
            "heldout_unique_images": len(heldout_images),
            "shared_images": len(overlap),
            "note": "descriptive: ViRL items may share images across strata; endpoints are item-level",
        },
        "strata": stratum_records,
    }
    args.manifest_out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in (
        "n_items", "n_train", "n_heldout", "n_strata", "n_strata_rank_eligible",
        "train_sha256", "heldout_sha256")}, sort_keys=True))
    print(json.dumps(manifest["image_integrity"], sort_keys=True))


if __name__ == "__main__":
    main()
