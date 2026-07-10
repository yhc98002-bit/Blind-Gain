#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import string
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from src.eval.fliptrack_metrics import match_tier
from src.rewards.answer_reward import extract_answer_span


def _explicit_choice_labels(span: str, labels: list[str]) -> list[str]:
    stripped = span.strip()
    upper = stripped.upper()
    if upper in labels:
        return [upper]
    label_class = "".join(re.escape(label) for label in labels)
    prefixed = re.match(
        rf"^(?:option|answer)\s*[\[(]?([{label_class}])[\])]?\s*(?:[.:,-]|$)", stripped, re.IGNORECASE
    )
    marked = re.match(rf"^[\[(]?([{label_class}])[\]).:,-]", stripped)
    if prefixed or marked:
        return [(prefixed or marked).group(1).upper()]
    mentioned = sorted(set(re.findall(rf"(?<![A-Za-z0-9])([{label_class}])(?![A-Za-z0-9])", stripped)))
    return [label.upper() for label in mentioned]


def score_mcq_prediction(
    prediction: Any, gold: Any, labels: list[str], options: dict[str, Any] | None = None
) -> dict[str, Any]:
    extracted = extract_answer_span(prediction)
    explicit = _explicit_choice_labels(extracted.span, labels)
    if explicit:
        tiers = {label: (2 if label in explicit else 0) for label in labels}
        winners = explicit
    else:
        options = options or {label: label for label in labels}
        tiers = {
            label: match_tier(extracted.span, options[label])
            if len(str(options[label]).strip()) > 1
            else 0
            for label in labels
        }
        highest = max(tiers.values(), default=0)
        winners = sorted(label for label, tier in tiers.items() if tier == highest and tier > 0)
    normalized_gold = str(gold).strip().upper()
    ambiguous = len(winners) > 1
    acc_final = len(winners) == 1 and winners[0] == normalized_gold
    return {
        "extracted_answer": extracted.span,
        "extraction_level": extracted.extraction_level,
        "extraction_fallback_used": extracted.extraction_fallback_used,
        "format_valid": extracted.format_valid,
        "ambiguous": ambiguous,
        "winning_labels": winners,
        "match_tiers": tiers,
        "acc_final": acc_final,
        "acc_strict": extracted.format_valid and acc_final,
    }


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, float]:
    if not rows:
        return {
            "n": 0.0,
            "Acc_strict": math.nan,
            "Acc_final": math.nan,
            "Format_valid": math.nan,
            "Ambiguous_rate": math.nan,
            "Extraction_fallback_rate": math.nan,
        }
    n = len(rows)
    return {
        "n": float(n),
        "Acc_strict": sum(row["acc_strict"] for row in rows) / n,
        "Acc_final": sum(row["acc_final"] for row in rows) / n,
        "Format_valid": sum(row["format_valid"] for row in rows) / n,
        "Ambiguous_rate": sum(row["ambiguous"] for row in rows) / n,
        "Extraction_fallback_rate": sum(row["extraction_fallback_used"] for row in rows) / n,
    }


def postprocess(input_path: Path, rows_output: Path, metrics_output: Path) -> dict[str, Any]:
    frame = pd.read_excel(input_path)
    required = {"index", "answer", "prediction"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"VLMEval workbook missing columns: {sorted(missing)}")
    scored_rows: list[dict[str, Any]] = []
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for raw in frame.to_dict(orient="records"):
        labels = [label for label in string.ascii_uppercase if label in raw and not pd.isna(raw[label])]
        if not labels:
            raise ValueError(f"row {raw['index']} has no option columns")
        options = {label: raw[label] for label in labels}
        scored = score_mcq_prediction(raw["prediction"], raw["answer"], labels, options)
        record = {
            "index": str(raw["index"]),
            "gold": str(raw["answer"]),
            "prediction": str(raw["prediction"]),
            "category": str(raw.get("category", "unknown")),
            "l2_category": str(raw.get("l2_category", "unknown")),
            "option_labels": labels,
            **scored,
        }
        scored_rows.append(record)
        by_category[record["category"]].append(record)
    payload = {
        "schema_version": "blind-gains.vlmeval-unified-scores.v2",
        "source_workbook": str(input_path),
        "overall": _aggregate(scored_rows),
        "per_category": {key: _aggregate(value) for key, value in sorted(by_category.items())},
    }
    rows_output.parent.mkdir(parents=True, exist_ok=True)
    with rows_output.open("w", encoding="utf-8") as handle:
        for row in scored_rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
    metrics_output.parent.mkdir(parents=True, exist_ok=True)
    metrics_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--rows-output", type=Path, required=True)
    parser.add_argument("--metrics-output", type=Path, required=True)
    args = parser.parse_args()
    payload = postprocess(args.input, args.rows_output, args.metrics_output)
    print(json.dumps(payload["overall"], sort_keys=True))


if __name__ == "__main__":
    main()
