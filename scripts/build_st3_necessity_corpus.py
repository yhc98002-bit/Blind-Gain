#!/usr/bin/env python3
"""ST3 arm-2 (C1) necessity-sampled corpus.

Registered by `docs/registered_stage3_7b_v1.md` §2 arm `st3_igpo` (C1:
necessity enters through the SAMPLING PROBABILITY only -- never a reward term,
loss weight or advantage transform, I1) and Launch amendment 2 (group
structure). The weight law is carried over verbatim from the Mini-A5 necessity
corpus:

    q_real_g  := mean p_sample of the group's members, `real` pass (16 samples, T=1)
    q_blind_g := mean p_sample of the same members, `none` pass
    dq_g      := q_real_g - q_blind_g
    w_g       := max(dq_g, 0) + 1/16        (registered floor keeps every group drawable)
    p_g       := w_g / sum(w)

The draw unit is the GROUP, not the row: an intervention group must reach the
trainer intact (all members, adjacent, in fixed order), so drawing rows
independently would shred it. The same number of groups as the base corpus is
drawn WITH replacement, so arm 2 sees the identical item set and the identical
rollout budget as arm 1 -- only the visit frequencies differ, which is exactly
what §4 permits to differ between the arms.

Per-member `p_sample` is joined by MEMBER IDENTITY, not by row position. The Δq
passes were scored against the `mother4` corpus, whose row order differs from
`side2` within each mother, so a positional join would silently mis-assign
probabilities. A `side2` uid `<mother>#a` with member `l3` resolves to the
mother4 member `l3_a` of `<mother>`.

Group size is read from the corpus rather than assumed. Refuses to overwrite.
Audits the weight law, support completeness, the empirical draw frequencies
against p_g, group adjacency and member order.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FLOOR_WEIGHT = 1.0 / 16.0
DRAW_SEED = 20260817
SYNTHETIC_PREFIX = "st3nec_"


def load_pass(run_glob: str, field: str = "p_sample") -> dict[int, float]:
    out: dict[int, float] = {}
    for run_dir in sorted(ROOT.glob(run_glob)):
        path = run_dir / "per_item.jsonl"
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            index = int(row["row_index"])
            if index in out:
                raise AssertionError(f"duplicate row_index {index} across shards")
            out[index] = float(row[field])
    if not out:
        raise SystemExit(f"no per-item rows matched {run_glob}")
    return out


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def source_key(uid: str, member: str) -> tuple[str, str]:
    """Resolve a corpus row to its identity in the scored `mother4` corpus."""
    if "#" in uid:
        mother, side = uid.rsplit("#", 1)
        return mother, f"{member}_{side}"
    return uid, member


def group_blocks(rows: list[dict]) -> list[list[int]]:
    """Contiguous runs of one pair_group_uid, verified to be uniform in size."""
    blocks: list[list[int]] = []
    current: list[int] = []
    for index, row in enumerate(rows):
        if current and rows[current[0]]["pair_group_uid"] != row["pair_group_uid"]:
            blocks.append(current)
            current = []
        current.append(index)
    if current:
        blocks.append(current)
    sizes = {len(b) for b in blocks}
    if len(sizes) != 1:
        raise AssertionError(f"groups are not uniform in size: {sorted(sizes)}")
    return blocks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path,
                        default=ROOT / "data/st3_train_side2_v1/train.jsonl",
                        help="corpus to resample (the arm-2 grouping)")
    parser.add_argument("--scored-corpus", type=Path,
                        default=ROOT / "data/st3_train_v1/train.jsonl",
                        help="corpus the Delta-q passes were scored against; "
                             "supplies row_index -> member identity")
    parser.add_argument("--real-glob", default="experiments/runs/st3_delta_q_real_*")
    parser.add_argument("--none-glob", default="experiments/runs/st3_delta_q_none_*")
    parser.add_argument("--out-dir", type=Path,
                        default=ROOT / "data/st3_necessity_train_side2_v1")
    parser.add_argument("--report", type=Path,
                        default=ROOT / "reports/st3_necessity_corpus_side2_v1.json")
    args = parser.parse_args()
    args.out_dir = args.out_dir.resolve()
    args.report = args.report.resolve()
    if args.report.exists():
        raise FileExistsError(args.report)
    args.out_dir.mkdir(parents=True, exist_ok=False)

    rows = read_jsonl(args.corpus)
    scored_rows = read_jsonl(args.scored_corpus)
    real = load_pass(args.real_glob)
    none = load_pass(args.none_glob)
    if set(real) != set(none) or len(real) != len(scored_rows):
        raise AssertionError(
            f"pass coverage mismatch: real {len(real)}, none {len(none)}, "
            f"scored corpus {len(scored_rows)}")

    # member identity -> (p_real, p_blind)
    probability: dict[tuple[str, str], tuple[float, float]] = {}
    for index, row in enumerate(scored_rows):
        key = source_key(str(row["pair_group_uid"]), str(row["pair_member"]))
        if key in probability:
            raise AssertionError(f"duplicate member identity {key}")
        probability[key] = (real[index], none[index])

    blocks = group_blocks(rows)
    group_size = len(blocks[0])
    member_order = [rows[i]["pair_member"] for i in blocks[0]]

    records = []
    weights = []
    for block in blocks:
        if [rows[i]["pair_member"] for i in block] != member_order:
            raise AssertionError(f"member order drift at row {block[0]}")
        keys = [source_key(str(rows[i]["pair_group_uid"]), str(rows[i]["pair_member"]))
                for i in block]
        missing = [k for k in keys if k not in probability]
        if missing:
            raise AssertionError(f"unscored members: {missing[:3]}")
        q_real = float(np.mean([probability[k][0] for k in keys]))
        q_blind = float(np.mean([probability[k][1] for k in keys]))
        delta_q = q_real - q_blind
        weight = max(delta_q, 0.0) + FLOOR_WEIGHT
        weights.append(weight)
        records.append({"pair_group_uid": rows[block[0]]["pair_group_uid"],
                        "q_real": q_real, "q_blind": q_blind,
                        "delta_q": delta_q, "weight": weight})
    weights_arr = np.asarray(weights, dtype=np.float64)
    probs = weights_arr / weights_arr.sum()
    for record, prob in zip(records, probs):
        record["draw_probability"] = float(prob)
        expected = max(record["delta_q"], 0.0) + FLOOR_WEIGHT
        if abs(record["weight"] - expected) > 1e-12:
            raise AssertionError("weight law violated")

    rng = np.random.default_rng(DRAW_SEED)
    draws = rng.choice(len(blocks), size=len(blocks), replace=True, p=probs)

    out_rows = []
    for slot, group_index in enumerate(draws):
        uid = f"{SYNTHETIC_PREFIX}{slot:06d}"
        for row_index in blocks[int(group_index)]:
            out_rows.append({**rows[row_index], "pair_group_uid": uid})

    # audits on the emitted corpus
    for start in range(0, len(out_rows), group_size):
        block = out_rows[start:start + group_size]
        if len({r["pair_group_uid"] for r in block}) != 1:
            raise AssertionError(f"emitted group not adjacent at {start}")
        if [r["pair_member"] for r in block] != member_order:
            raise AssertionError(f"emitted member order drift at {start}")
    counts = np.bincount(draws, minlength=len(blocks)) / len(draws)
    freq_error = float(np.abs(counts - probs).max())

    blob = "".join(json.dumps(r, sort_keys=True) + "\n" for r in out_rows)
    (args.out_dir / "train.jsonl").write_text(blob, encoding="utf-8")
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        schema = pa.schema([("problem", pa.string()), ("answer", pa.string()),
                            ("images", pa.list_(pa.string())),
                            ("pair_group_uid", pa.string()),
                            ("pair_member", pa.string()),
                            ("template_id", pa.string()), ("category", pa.string())])
        pq.write_table(pa.Table.from_pylist(out_rows, schema=schema),
                       args.out_dir / "train.parquet")
        parquet = True
    except Exception as error:                     # noqa: BLE001
        parquet = f"unavailable: {error}"
    (args.out_dir / "delta_q.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in records),
        encoding="utf-8")

    dq = np.asarray([r["delta_q"] for r in records])
    report = {
        "schema_version": "blind-gains.st3-necessity-corpus.v1",
        "registration": "docs/registered_stage3_7b_v1.md §2 arm st3_igpo (C1) "
                        "+ Launch amendment 2",
        "weight_law": "w = max(delta_q, 0) + 1/16; p = w / sum(w); "
                      "draw unit = intervention GROUP, with replacement",
        "join": "per-member p_sample joined by member identity, not row position",
        "draw_seed": DRAW_SEED,
        "corpus": str(args.corpus),
        "scored_corpus": str(args.scored_corpus),
        "n_groups": len(blocks),
        "n_rows": len(out_rows),
        "group_size": group_size,
        "member_order": member_order,
        "q_real_mean": float(np.mean([r["q_real"] for r in records])),
        "q_blind_mean": float(np.mean([r["q_blind"] for r in records])),
        "delta_q_mean": float(dq.mean()),
        "delta_q_positive_groups": int((dq > 0).sum()),
        "max_min_draw_ratio": float(probs.max() / probs.min()),
        "empirical_frequency_max_abs_error": freq_error,
        "distinct_groups_drawn": int(len(set(draws.tolist()))),
        "train_jsonl_sha256": hashlib.sha256(blob.encode()).hexdigest(),
        "parquet": parquet,
        "out_dir": str(args.out_dir),
    }
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({k: report[k] for k in
                      ("n_groups", "n_rows", "group_size", "member_order",
                       "q_real_mean", "q_blind_mean", "delta_q_mean",
                       "max_min_draw_ratio", "distinct_groups_drawn",
                       "train_jsonl_sha256")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
