#!/usr/bin/env python3
"""ST3 arm-2 (C1) necessity-sampled corpus.

Registered by `docs/registered_stage3_7b_v1.md` §2 arm `st3_igpo` (C1:
necessity enters through the SAMPLING PROBABILITY only — never a reward term,
loss weight or advantage transform, I1). The weight law is carried over
verbatim from the Mini-A5 necessity corpus:

    q_real_g  := mean p_sample of the group's members, `real` pass (16 samples, T=1)
    q_blind_g := mean p_sample of the same members, `none` pass
    dq_g      := q_real_g - q_blind_g
    w_g       := max(dq_g, 0) + 1/16        (registered floor keeps every group drawable)
    p_g       := w_g / sum(w)

The draw unit is the GROUP, not the row: an intervention group must reach the
trainer intact (all four members, adjacent, in fixed order), so drawing rows
independently would shred it. The same number of groups as the base corpus is
drawn WITH replacement, so arm 2 sees the identical item set and the identical
rollout budget as arm 1 — only the visit frequencies differ, which is exactly
what §4 permits to differ between the arms.

Refuses to overwrite. Audits the weight law, support completeness, the
empirical draw frequencies against p_g, group adjacency and member order.
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
GROUP_SIZE = 4


def load_pass(run_glob: str) -> dict[int, float]:
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
            out[index] = float(row["p_sample"])
    if not out:
        raise SystemExit(f"no per-item rows matched {run_glob}")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path,
                        default=ROOT / "data/st3_train_v1/train.jsonl")
    parser.add_argument("--real-glob", default="experiments/runs/st3_delta_q_real_*")
    parser.add_argument("--none-glob", default="experiments/runs/st3_delta_q_none_*")
    parser.add_argument("--out-dir", type=Path,
                        default=ROOT / "data/st3_necessity_train_v1")
    parser.add_argument("--report", type=Path,
                        default=ROOT / "reports/st3_necessity_corpus_v1.json")
    args = parser.parse_args()
    args.out_dir = args.out_dir.resolve()
    args.report = args.report.resolve()
    if args.report.exists():
        raise FileExistsError(args.report)
    args.out_dir.mkdir(parents=True, exist_ok=False)

    rows = [json.loads(l) for l in args.corpus.read_text().splitlines() if l.strip()]
    real = load_pass(args.real_glob)
    none = load_pass(args.none_glob)
    if set(real) != set(none) or len(real) != len(rows):
        raise AssertionError(
            f"pass coverage mismatch: real {len(real)}, none {len(none)}, "
            f"corpus {len(rows)}")

    # group the corpus, preserving order and member sequence
    groups: list[list[int]] = []
    for start in range(0, len(rows), GROUP_SIZE):
        block = list(range(start, start + GROUP_SIZE))
        uids = {rows[i]["pair_group_uid"] for i in block}
        if len(uids) != 1:
            raise AssertionError(f"group not adjacent at row {start}")
        groups.append(block)

    records = []
    weights = []
    for group in groups:
        q_real = float(np.mean([real[i] for i in group]))
        q_blind = float(np.mean([none[i] for i in group]))
        delta_q = q_real - q_blind
        weight = max(delta_q, 0.0) + FLOOR_WEIGHT
        weights.append(weight)
        records.append({"pair_group_uid": rows[group[0]]["pair_group_uid"],
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
    draws = rng.choice(len(groups), size=len(groups), replace=True, p=probs)

    out_rows = []
    for slot, group_index in enumerate(draws):
        uid = f"{SYNTHETIC_PREFIX}{slot:06d}"
        for row_index in groups[int(group_index)]:
            source = rows[row_index]
            out_rows.append({**source, "pair_group_uid": uid})
    # audits
    for start in range(0, len(out_rows), GROUP_SIZE):
        block = out_rows[start:start + GROUP_SIZE]
        if len({r["pair_group_uid"] for r in block}) != 1:
            raise AssertionError(f"emitted group not adjacent at {start}")
        if [r["pair_member"] for r in block] != [rows[i]["pair_member"]
                                                 for i in groups[0]]:
            raise AssertionError(f"member order drift at {start}")
    counts = np.bincount(draws, minlength=len(groups)) / len(draws)
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
        "registration": "docs/registered_stage3_7b_v1.md §2 arm st3_igpo (C1)",
        "weight_law": "w = max(delta_q, 0) + 1/16; p = w / sum(w); "
                      "draw unit = intervention GROUP, with replacement",
        "draw_seed": DRAW_SEED,
        "n_groups": len(groups),
        "n_rows": len(out_rows),
        "group_size": GROUP_SIZE,
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
                      ("n_groups", "n_rows", "q_real_mean", "q_blind_mean",
                       "delta_q_mean", "max_min_draw_ratio",
                       "distinct_groups_drawn", "train_jsonl_sha256")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
