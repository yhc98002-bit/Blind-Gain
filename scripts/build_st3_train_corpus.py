#!/usr/bin/env python3
"""ST3-7B training corpus — HB coordinate training bucket into the EasyR1
row schema used by the Mini-A5 corpora.

Registered by `docs/registered_stage3_7b_v1.md` §3 + Launch amendment 1
(coord-only split, cells n8/n12, training bucket only) and Launch amendment 2
(group structure). Two grouping modes are emitted from the same mother-items:

`mother4` — one group per mother-item, four members in fixed order:

    <mother>__l3 a · <mother>__l3 b · <mother>__probe a · <mother>__probe b

`side2` — two groups per mother-item, one per side of the counterfactual:

    <mother>#a__l3 · <mother>#a__probe   and   <mother>#b__l3 · <mother>#b__probe

`side2` is what Launch amendment 2 pins for the IGPO arm. The k=4 product was
measured at 2.41% of groups able to produce a GRPO gradient at base competence
(against 42.2% for the Mini-A5 k=2 arm the registration names as C2's reference
implementation), so the joint reward at k=4 is below the trainable threshold;
`reports/st3_joint_feasibility_v1.md` carries the measurement. At k=2 the group
is the C3 statement directly: a side's read counts only when that side's
discovery probe was right in the same rollout.

In BOTH modes the shuffle is at MOTHER granularity and a mother's groups are
written adjacently, so `side2` keeps both sides of the counterfactual inside the
same rollout batch (I2-I5 invariance-group presence) even though they are scored
as separate groups, and both modes visit mothers in the identical order.

Emitted columns are exactly the seven the trainer reads, plus the group
bookkeeping the patched reward manager forwards:

    problem · answer · images · pair_group_uid · pair_member ·
    template_id · category

Rows are pre-shuffled and written group-adjacent, because pair-grouped training
requires `data.shuffle=false` and an intact group per rollout batch. Image paths
are emitted repo-relative (house style; the absolute paths in the manifests would
bake in the cluster root). Refuses to overwrite.
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
SIDE_MEMBER_ORDER = ("l3", "probe")  # within one side's k=2 group
GROUP_MODES = ("mother4", "side2")
CORPUS_SEED = 20260817


def rel(path: str) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def group_shape(group_mode: str) -> tuple[int, tuple[str, ...]]:
    """(rows per group, expected member order) for a mode."""
    if group_mode == "mother4":
        return len(MEMBER_ORDER), tuple(f"{l}_{s}" for l, s in MEMBER_ORDER)
    return len(SIDE_MEMBER_ORDER), tuple(SIDE_MEMBER_ORDER)


def build_rows(data_dir: Path, group_mode: str) -> tuple[list[dict], dict]:
    # A "unit" is one mother-item: one group in mother4, two in side2. Shuffling
    # units rather than groups keeps a mother's two sides adjacent and makes the
    # mother order identical across modes.
    units: list[list[list[dict]]] = []
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
            base: dict[tuple[str, str], dict] = {}
            ok = True
            for layer, side in MEMBER_ORDER:
                row = by_layer[layer][mother]
                if row["split"] != "training":
                    ok = False
                    break
                base[(layer, side)] = {
                    "problem": f"<image>{row['question']}",
                    "answer": str(row[f"answer_{side}"]),
                    "images": [rel(row[f"image_{side}_path"])],
                    "template_id": row["template_id"],
                    "category": "hier_v1_st3",
                }
            if not ok or len(base) != len(MEMBER_ORDER):
                continue
            if group_mode == "mother4":
                units.append([[{**base[(layer, side)],
                                "pair_group_uid": mother,
                                "pair_member": f"{layer}_{side}"}
                               for layer, side in MEMBER_ORDER]])
            else:
                units.append([[{**base[(layer, side)],
                                "pair_group_uid": f"{mother}#{side}",
                                "pair_member": layer}
                               for layer in SIDE_MEMBER_ORDER]
                              for side in ("a", "b")])
        stats["cells"][cell] = len(mothers)
    rng = random.Random(CORPUS_SEED)
    rng.shuffle(units)                   # shuffle MOTHERS, keep their groups adjacent
    groups = [group for unit in units for group in unit]
    rows = [row for group in groups for row in group]
    stats["n_groups"] = len(groups)
    stats["n_rows"] = len(rows)
    stats["n_mothers"] = len(units)
    return rows, stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/hier_train_v1")
    parser.add_argument("--group-mode", choices=GROUP_MODES, default="mother4")
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--dev-dir", type=Path, default=ROOT / "data/hier_v1_dev_r2",
                        help="development bucket, used only for the inert "
                             "plumbing val file EasyR1 requires")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    suffix = "" if args.group_mode == "mother4" else f"_{args.group_mode}"
    if args.out_dir is None:
        args.out_dir = ROOT / f"data/st3_train{suffix}_v1"
    if args.report is None:
        args.report = ROOT / f"reports/st3_train_corpus{suffix}_v1.json"
    args.out_dir = args.out_dir.resolve()
    args.report = args.report.resolve()
    if args.report.exists():
        raise FileExistsError(args.report)
    args.out_dir.mkdir(parents=True, exist_ok=False)

    rows, stats = build_rows(args.data_dir.resolve(), args.group_mode)
    if not rows:
        raise SystemExit("no training rows built")

    # invariants the trainer depends on
    group_size, member_labels = group_shape(args.group_mode)
    for index in range(0, len(rows), group_size):
        block = rows[index:index + group_size]
        uids = {r["pair_group_uid"] for r in block}
        if len(uids) != 1:
            raise AssertionError(f"group not adjacent at row {index}: {uids}")
        if tuple(r["pair_member"] for r in block) != member_labels:
            raise AssertionError(f"member order wrong at row {index}")
    if args.group_mode == "side2":
        # both sides of a mother must land in the same rollout batch
        for index in range(0, len(rows), 2 * group_size):
            block = rows[index:index + 2 * group_size]
            mothers = {r["pair_group_uid"].split("#")[0] for r in block}
            sides = [r["pair_group_uid"].split("#")[1] for r in block]
            if len(mothers) != 1 or sides != ["a", "a", "b", "b"]:
                raise AssertionError(f"sides not paired at row {index}: {sides}")
    for row in rows:
        if not (ROOT / row["images"][0]).is_file():
            raise FileNotFoundError(row["images"][0])
        if row["problem"].count("<image>") != len(row["images"]):
            raise AssertionError(f"image marker/count mismatch: {row['pair_group_uid']}")

    # EasyR1 requires data.val_files to be a string even when validation is
    # disabled (val_freq 0). Emit a tiny plumbing file drawn from the
    # DEVELOPMENT bucket so a stray validation pass can never read training or
    # confirmatory items. Mini-A5 used the same device.
    val_rows = []
    dev = args.dev_dir.resolve()
    for cell in TRAIN_CELLS:
        path = dev / f"manifest_{FAMILY}_{cell}_l3.jsonl"
        if not path.exists():
            continue
        for line in path.read_text().splitlines()[:2]:
            row = json.loads(line)
            if row["split"] != "development":
                continue
            for side in ("a", "b"):
                val_rows.append({
                    "problem": f"<image>{row['question']}",
                    "answer": str(row[f"answer_{side}"]),
                    "images": [rel(row[f"image_{side}_path"])],
                    "pair_group_uid": row["mother_item_id"],
                    "pair_member": f"l3_{side}",
                    "template_id": row["template_id"],
                    "category": "hier_v1_st3_plumbing_val",
                })
    if not val_rows:
        raise SystemExit("no plumbing val rows built")
    val_blob = "".join(json.dumps(r, sort_keys=True) + "\n" for r in val_rows)
    (args.out_dir / "plumbing_val.jsonl").write_text(val_blob, encoding="utf-8")

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

    definitions = {
        "mother4": "one mother-item = one intervention group of 4 members "
                   "(L3 a/b + discovery probe a/b), adjacent, fixed order",
        "side2": "one SIDE of a mother-item = one intervention group of 2 members "
                 "(that side's L3 read + its discovery probe); both sides written "
                 "adjacently so they share a rollout batch",
    }
    report = {
        "schema_version": "blind-gains.st3-train-corpus.v1",
        "registration": "docs/registered_stage3_7b_v1.md §3 + Launch amendments 1, 2",
        "split": "training",
        "family": FAMILY,
        "cells": TRAIN_CELLS,
        "group_mode": args.group_mode,
        "group_definition": definitions[args.group_mode],
        "group_size": group_size,
        "member_order": list(member_labels),
        "corpus_seed": CORPUS_SEED,
        "n_groups": stats["n_groups"],
        "n_rows": stats["n_rows"],
        "n_mothers": stats["n_mothers"],
        "mothers_per_cell": stats["cells"],
        "train_jsonl_sha256": hashlib.sha256(blob.encode()).hexdigest(),
        "plumbing_val_rows": len(val_rows),
        "plumbing_val_sha256": hashlib.sha256(val_blob.encode()).hexdigest(),
        "plumbing_val_note": "development-bucket rows; validation is disabled "
                             "(val_freq 0) and this file exists only to satisfy "
                             "EasyR1's non-null val_files requirement",
        "parquet": parquet,
        "out_dir": str(args.out_dir),
    }
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({k: report[k] for k in
                      ("group_mode", "n_groups", "n_rows", "n_mothers",
                       "mothers_per_cell", "parquet", "train_jsonl_sha256")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
