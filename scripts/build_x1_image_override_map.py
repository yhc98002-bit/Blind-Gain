#!/usr/bin/env python3
"""Build the registered X1 mismatched-real image override map.

Per docs/registered_x1_matrix_v1.md: a fixed within-template derangement,
seeded 20260724, recorded per item. Side-preserving: member a of pair p
receives the member-a image of pair sigma(p), likewise for member b, where
sigma is a Sattolo cyclic derangement over the template's pairs sorted by
pair_id (cyclic => no pair maps to itself).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

SEED = 20260724
SCHEMA = "blind-gains.x1-mismatched-derangement.v1"


def sattolo(n: int, rng: np.random.Generator) -> list[int]:
    perm = list(range(n))
    for i in range(n - 1, 0, -1):
        j = int(rng.integers(0, i))
        perm[i], perm[j] = perm[j], perm[i]
    return perm


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")

    rows = [
        json.loads(line)
        for line in args.registry.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_template: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_template[str(row["template_id"])].append(row)

    rng = np.random.default_rng(SEED)
    per_pair: dict[str, dict] = {}
    for template_id in sorted(by_template):
        group = sorted(by_template[template_id], key=lambda r: str(r["pair_id"]))
        if len(group) < 2:
            raise ValueError(f"template {template_id} too small for a derangement")
        perm = sattolo(len(group), rng)
        for idx, row in enumerate(group):
            source = group[perm[idx]]
            if source["pair_id"] == row["pair_id"]:
                raise AssertionError("derangement produced a fixed point")
            per_pair[str(row["pair_id"])] = {
                "a": str(source["image_a_path"]),
                "b": str(source["image_b_path"]),
                "source_pair_id": str(source["pair_id"]),
                "template_id": template_id,
            }
            if per_pair[str(row["pair_id"])]["a"] == str(row["image_a_path"]):
                raise AssertionError("override equals own member-a image")
            if per_pair[str(row["pair_id"])]["b"] == str(row["image_b_path"]):
                raise AssertionError("override equals own member-b image")

    if len(per_pair) != len(rows):
        raise AssertionError("override map does not cover every pair exactly once")
    for template_id, group in by_template.items():
        sources = [per_pair[str(r["pair_id"])]["source_pair_id"] for r in group]
        if len(set(sources)) != len(group):
            raise AssertionError(f"sigma is not a bijection within {template_id}")

    payload = {
        "schema_version": SCHEMA,
        "seed": SEED,
        "method": "sattolo_cyclic_derangement_within_template_sorted_by_pair_id_side_preserving",
        "registry": str(args.registry),
        "registry_sha256": hashlib.sha256(args.registry.read_bytes()).hexdigest(),
        "n_pairs": len(per_pair),
        "per_pair": {key: per_pair[key] for key in sorted(per_pair)},
    }
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    args.output.write_text(text, encoding="utf-8")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print(json.dumps({"output": str(args.output), "sha256": digest, "n_pairs": len(per_pair)}))


if __name__ == "__main__":
    main()
