#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


def _rate(rows: list[dict[str, Any]], field: str) -> float:
    return sum(bool(row[field]) for row in rows) / len(rows)


def _bootstrap_ci(
    rows: list[dict[str, Any]], field: str, *, samples: int, seed: int
) -> tuple[float, float]:
    rng = random.Random(seed)
    values = [float(bool(row[field])) for row in rows]
    estimates = []
    for _ in range(samples):
        estimates.append(sum(values[rng.randrange(len(values))] for _ in values) / len(values))
    estimates.sort()
    return estimates[int(0.025 * samples)], estimates[min(samples - 1, int(0.975 * samples))]


def summarize(rows: list[dict[str, Any]], *, bootstrap: int = 2000) -> dict[str, Any]:
    if not rows:
        raise ValueError("non-Qwen blind aggregate requires rows")
    identities = [(str(row.get("qid")), int(row["row_index"])) for row in rows]
    if len(identities) != len(set(identities)):
        raise ValueError("duplicate non-Qwen blind-sample row identity")
    input_schema = rows[0].get("schema_version")
    if any(row.get("schema_version") != input_schema for row in rows):
        raise ValueError("non-Qwen blind aggregate has mixed schema_version")
    constant_fields = (
        "backend",
        "condition",
        "source_manifest_sha256",
        "format_prompt_sha256",
        "caption_store_sha256",
        "parser_version",
        "prompt_contract_sha256",
        "decoding",
    )
    constants = {field: rows[0].get(field) for field in constant_fields}
    for field, expected in constants.items():
        if any(row.get(field) != expected for row in rows):
            raise ValueError(f"non-Qwen blind aggregate has mixed {field}")
    lo, hi = _bootstrap_ci(rows, "acc_final", samples=bootstrap, seed=0)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        metadata = row.get("source_metadata") or {}
        key = f"{metadata.get('source', 'unknown')}::{metadata.get('category', 'unknown')}"
        grouped[key].append(row)
    return {
        "schema_version": "blind-gains.nonqwen-blind-aggregate.v1",
        "input_schema_version": input_schema,
        **constants,
        "n_rows": len(rows),
        "row_identity_sha256": hashlib.sha256(
            json.dumps(sorted(identities), separators=(",", ":")).encode()
        ).hexdigest(),
        "acc_final": _rate(rows, "acc_final"),
        "acc_final_ci95_low": lo,
        "acc_final_ci95_high": hi,
        "acc_strict": _rate(rows, "acc_strict"),
        "extractor_valid_rate": _rate(rows, "extractor_valid"),
        "contract_valid_rate": _rate(rows, "contract_valid"),
        "per_source_category": {
            key: {"n": len(group), "acc_final": _rate(group, "acc_final")}
            for key, group in sorted(grouped.items())
        },
    }


def load_inputs(patterns: Iterable[str]) -> list[dict[str, Any]]:
    rows = []
    matched = []
    for pattern in patterns:
        for path in sorted(Path().glob(pattern)):
            matched.append(path)
            with path.open(encoding="utf-8") as handle:
                rows.extend(json.loads(line) for line in handle if line.strip())
    if not matched:
        raise ValueError("non-Qwen blind aggregate matched no inputs")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-rows", type=int, default=4096)
    parser.add_argument("--bootstrap", type=int, default=2000)
    args = parser.parse_args()
    rows = load_inputs(args.inputs)
    if len(rows) != args.expected_rows:
        raise ValueError(
            f"non-Qwen blind aggregate expected {args.expected_rows} rows, found {len(rows)}"
        )
    payload = summarize(rows, bootstrap=args.bootstrap)
    if args.output.exists() or Path(f"{args.output}.partial").exists():
        raise FileExistsError(f"refusing to overwrite non-Qwen blind aggregate: {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    partial = Path(f"{args.output}.partial")
    partial.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(partial, args.output)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
