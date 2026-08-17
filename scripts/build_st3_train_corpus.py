#!/usr/bin/env python3
"""ST3-7B training corpus — HB coordinate training bucket into the EasyR1
row schema used by the Mini-A5 corpora.

Registered by `docs/registered_stage3_7b_v1.md` §3 + Launch amendment 1
(coord-only split, cells n8/n12, training bucket only). One group per
mother-item, four members in fixed order:

    <mother>__l3 a · <mother>__l3 b · <mother>__probe a · <mother>__probe b

The probe members are what makes C3 ("premise-verified hierarchical reward")
expressible: the IGPO arm's joint reward requires the model to identify the
right target AND read the right value, on BOTH sides of the counterfactual, in
the same group. The std arm consumes the identical corpus and scores members
independently — so the two arms differ in the reward and the grouping mode,
never in the data (§4 matching).

Emitted columns are exactly the seven the trainer reads, plus the group
bookkeeping the patched reward manager forwards:

    problem · answer · images · pair_group_uid · pair_member ·
    template_id · category

Rows are pre-shuffled at GROUP granularity and written group-adjacent, because
pair-grouped training requires `data.shuffle=false` and an intact group per
rollout batch. Image paths are emitted repo-relative (house style; the
absolute paths in the manifests would bake in the cluster root). Refuses to
overwrite.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "hier_coord_v1"
TRAIN_CELLS = ("n8", "n12")          # n20 excluded (EXPERIMENT_TODO PART 6)
MEMBER_ORDER = (("l3", "a"), ("l3", "b"), ("probe", "a"), ("probe", "b"))
CORPUS_SEED = 20260817


def rel(path: str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def build_rows(data_dir: Path) -> tuple[list[dict], dict]:
    groups: list[list[dict]] = []
    stats = {"cells": {}, "n_groups": 0, "n_rows": 0}
    for cell in TRAIN_CELLS:
        by_layer = {}
        for layer in ("l3", "probe"):
            path = data_dir / f"manifest_{FAMILY}_{cell}_{layer}.jsonl"
            by_layer[layer] = {r["mother_item_id"]: r for r in
                               (json.loads(l) for l in
                                path.read_text().splitlines() if l.strip())}
        mothers = sorted(set(by_layer["l3"]) & set(by_layer["probe"]))
        for mother in mothers:
            members = []
            ok = True
            for layer, side in MEMBER_ORDER:
                row = by_layer[layer][mother]
                if row["split"] != "training":
                    ok = False
                    break
                members.append({
                    "problem": f"<image>{row['question']}",
                    "answer": str(row[f"answer_{side}"]),
                    "images": [rel(row[f"image_{side}_path"])],
                    "pair_group_uid": mother,
                    "pair_member": f"{layer}_{side}",
                    "template_id": row["template_id"],
                    "category": "hier_v1_st3",
                })
            if ok and len(members) == len(MEMBER_ORDER):
                groups.append(members)
        stats["cells"][cell] = len(mothers)
    rng = random.Random(CORPUS_SEED)
    rng.shuffle(groups)                      # shuffle GROUPS, keep members adjacent
    rows = [row for group in groups for row in group]
    stats["n_groups"] = len(groups)
    stats["n_rows"] = len(rows)
    return rows, stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/hier_train_v1")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "data/st3_train_v1")
    parser.add_argument("--report", type=Path,
                        default=ROOT / "reports/st3_train_corpus_v1.json")
    args = parser.parse_args()
    args.out_dir = args.out_dir.resolve()
    args.report = args.report.resolve()
    if args.report.exists():
        raise FileExistsError(args.report)
    args.out_dir.mkdir(parents=True, exist_ok=False)

    rows, stats = build_rows(args.data_dir.resolve())
    if not rows:
        raise SystemExit("no training rows built")

    # invariants the trainer depends on
    group_size = len(MEMBER_ORDER)
    for index in range(0, len(rows), group_size):
        block = rows[index:index + group_size]
        uids = {r["pair_group_uid"] for r in block}
        if len(uids) != 1:
            raise AssertionError(f"group not adjacent at row {index}: {uids}")
        if [r["pair_member"] for r in block] != [f"{l}_{s}" for l, s in MEMBER_ORDER]:
            raise AssertionError(f"member order wrong at row {index}")
    for row in rows:
        if not (ROOT / row["images"][0]).is_file():
            raise FileNotFoundError(row["images"][0])
        if row["problem"].count("<image>") != len(row["images"]):
            raise AssertionError(f"image marker/count mismatch: {row['pair_group_uid']}")

    jsonl = args.out_dir / "train.jsonl"
    blob = "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)
    jsonl.write_text(blob, encoding="utf-8")
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        schema = pa.schema([("problem", pa.string()), ("answer", pa.string()),
                            ("images", pa.list_(pa.string())),
                            ("pair_group_uid", pa.string()),
                            ("pair_member", pa.string()),
                            ("template_id", pa.string()), ("category", pa.string())])
        table = pa.Table.from_pylist(rows, schema=schema)
        pq.write_table(table, args.out_dir / "train.parquet")
        parquet = True
    except Exception as error:            # noqa: BLE001 - reported, not swallowed
        parquet = f"unavailable: {error}"

    report = {
        "schema_version": "blind-gains.st3-train-corpus.v1",
        "registration": "docs/registered_stage3_7b_v1.md §3 + Launch amendment 1",
        "split": "training",
        "family": FAMILY,
        "cells": TRAIN_CELLS,
        "group_definition": "one mother-item = one intervention group of 4 members "
                            "(L3 a/b + discovery probe a/b), adjacent, fixed order",
        "group_size": group_size,
        "corpus_seed": CORPUS_SEED,
        "n_groups": stats["n_groups"],
        "n_rows": stats["n_rows"],
        "mothers_per_cell": stats["cells"],
        "train_jsonl_sha256": hashlib.sha256(blob.encode()).hexdigest(),
        "parquet": parquet,
        "out_dir": str(args.out_dir),
    }
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({k: report[k] for k in
                      ("n_groups", "n_rows", "mothers_per_cell", "parquet",
                       "train_jsonl_sha256")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
