#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any


STEP0_PER_TEMPLATE = 64
PLUMBING_VAL_PER_TEMPLATE = 8


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def select_pair_ids(
    pairs: list[dict[str, Any]],
) -> tuple[list[str], list[str], dict[str, dict[str, int]]]:
    by_template: dict[str, list[str]] = defaultdict(list)
    for pair in pairs:
        by_template[str(pair["template_id"])].append(str(pair["pair_group_uid"]))
    if len(by_template) != 3:
        raise ValueError(f"expected exactly three training templates, found {sorted(by_template)}")

    step0_ids: list[str] = []
    val_ids: list[str] = []
    counts: dict[str, dict[str, int]] = {}
    for template, raw_ids in sorted(by_template.items()):
        ids = sorted(raw_ids)
        if len(ids) < STEP0_PER_TEMPLATE + PLUMBING_VAL_PER_TEMPLATE:
            raise ValueError(f"template {template!r} has too few pairs: {len(ids)}")
        if len(ids) != len(set(ids)):
            raise ValueError(f"template {template!r} contains duplicate pair ids")
        selected_step0 = ids[:STEP0_PER_TEMPLATE]
        selected_val = ids[
            STEP0_PER_TEMPLATE : STEP0_PER_TEMPLATE + PLUMBING_VAL_PER_TEMPLATE
        ]
        step0_ids.extend(selected_step0)
        val_ids.extend(selected_val)
        counts[template] = {
            "step0_pairs": len(selected_step0),
            "plumbing_val_pairs": len(selected_val),
        }
    if set(step0_ids) & set(val_ids):
        raise ValueError("step-0 and plumbing-validation pair selections overlap")
    return step0_ids, val_ids, counts


def build_fixed_subsets(
    pairs: list[dict[str, Any]], train_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    step0_ids, val_ids, template_counts = select_pair_ids(pairs)
    pair_by_id = {str(row["pair_group_uid"]): row for row in pairs}
    if len(pair_by_id) != len(pairs):
        raise ValueError("pair manifest contains duplicate pair_group_uid values")

    rows_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in train_rows:
        rows_by_id[str(row["pair_group_uid"])].append(row)
    malformed = {
        uid: sorted(str(row.get("pair_member")) for row in rows_by_id.get(uid, []))
        for uid in val_ids
        if sorted(str(row.get("pair_member")) for row in rows_by_id.get(uid, []))
        != ["a", "b"]
    }
    if malformed:
        raise ValueError(f"plumbing validation pairs are malformed: {malformed}")

    step0_pairs = [pair_by_id[uid] for uid in step0_ids]
    val_rows: list[dict[str, Any]] = []
    for uid in val_ids:
        val_rows.extend(sorted(rows_by_id[uid], key=lambda row: str(row["pair_member"])))
    return {
        "step0_pairs": step0_pairs,
        "plumbing_val_rows": val_rows,
        "step0_pair_ids": step0_ids,
        "plumbing_val_pair_ids": val_ids,
        "template_counts": template_counts,
    }


def atomic_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite fixed subset: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite fixed subset manifest: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial.{os.getpid()}")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pairs", type=Path, default=Path("data/mini_a5_train_v1/pairs.jsonl")
    )
    parser.add_argument(
        "--train", type=Path, default=Path("data/mini_a5_train_v1/train.jsonl")
    )
    parser.add_argument(
        "--step0-output", type=Path, default=Path("data/mini_a5_step0_sample_v1.jsonl")
    )
    parser.add_argument(
        "--val-output", type=Path, default=Path("data/mini_a5_plumbing_val_v1.jsonl")
    )
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=Path("data/mini_a5_fixed_subsets_v1_manifest.json"),
    )
    args = parser.parse_args()

    pairs = read_jsonl(args.pairs)
    train_rows = read_jsonl(args.train)
    selected = build_fixed_subsets(pairs, train_rows)
    atomic_jsonl(args.step0_output, selected["step0_pairs"])
    atomic_jsonl(args.val_output, selected["plumbing_val_rows"])
    payload = {
        "schema_version": "blind-gains.mini-a5-fixed-subsets.v1",
        "status": "pass",
        "source": {
            "pairs_path": str(args.pairs),
            "pairs_sha256": sha256_file(args.pairs),
            "train_path": str(args.train),
            "train_sha256": sha256_file(args.train),
        },
        "step0": {
            "path": str(args.step0_output),
            "sha256": sha256_file(args.step0_output),
            "pairs": len(selected["step0_pairs"]),
            "samples_per_pair": 5,
        },
        "plumbing_validation": {
            "path": str(args.val_output),
            "sha256": sha256_file(args.val_output),
            "pairs": len(selected["plumbing_val_pair_ids"]),
            "rows": len(selected["plumbing_val_rows"]),
        },
        "pair_id_overlap": len(
            set(selected["step0_pair_ids"]) & set(selected["plumbing_val_pair_ids"])
        ),
        "template_counts": selected["template_counts"],
    }
    atomic_json(args.manifest_output, payload)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
