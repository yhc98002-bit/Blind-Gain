#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import math
import re
import string
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.eval.fliptrack_metrics import match_tier
from src.eval.prompt_contract import (
    PromptContractLike,
    load_prompt_contract_from_run_manifest,
    prompt_contract_metadata,
    response_satisfies_contract,
)
from src.rewards.answer_reward import PARSER_VERSION, extract_answer_span


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
    prediction: Any,
    gold: Any,
    labels: list[str],
    options: dict[str, Any] | None = None,
    prompt_contract: PromptContractLike = None,
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
    if isinstance(gold, (list, tuple, set)):
        normalized_gold = sorted({str(label).strip().upper() for label in gold})
    else:
        normalized_gold = [str(gold).strip().upper()]
    if not normalized_gold or any(label not in labels for label in normalized_gold):
        raise ValueError(f"invalid MCQ gold labels: {normalized_gold}")
    ambiguous = len(winners) > 1 and not (explicit and sorted(winners) == normalized_gold)
    acc_final = sorted(winners) == normalized_gold
    contract_valid = response_satisfies_contract(prediction, prompt_contract)
    return {
        "extracted_answer": extracted.span,
        "extraction_level": extracted.extraction_level,
        "extraction_fallback_used": extracted.extraction_fallback_used,
        "extractor_valid": extracted.extractor_valid,
        "contract_valid": contract_valid,
        "format_valid": contract_valid,
        "parser_version": PARSER_VERSION,
        **prompt_contract_metadata(prompt_contract),
        "ambiguous": ambiguous,
        "winning_labels": winners,
        "gold_labels": normalized_gold,
        "match_tiers": tiers,
        "acc_final": acc_final,
        "acc_strict": contract_valid and acc_final,
    }


def score_open_prediction(
    prediction: Any, gold: Any, prompt_contract: PromptContractLike = None
) -> dict[str, Any]:
    extracted = extract_answer_span(prediction)
    tier = match_tier(extracted.span, gold)
    acc_final = tier > 0
    contract_valid = response_satisfies_contract(prediction, prompt_contract)
    return {
        "extracted_answer": extracted.span,
        "extraction_level": extracted.extraction_level,
        "extraction_fallback_used": extracted.extraction_fallback_used,
        "extractor_valid": extracted.extractor_valid,
        "contract_valid": contract_valid,
        "format_valid": contract_valid,
        "parser_version": PARSER_VERSION,
        **prompt_contract_metadata(prompt_contract),
        "ambiguous": False,
        "winning_labels": ["gold"] if acc_final else [],
        "match_tiers": {"gold": tier},
        "acc_final": acc_final,
        "acc_strict": contract_valid and acc_final,
    }


def _not_missing(value: Any) -> bool:
    if value is None:
        return False
    try:
        missing = pd.isna(value)
    except (TypeError, ValueError):
        return True
    return bool(not missing) if isinstance(missing, (bool, np.bool_)) else True


def _choice_payload(raw: dict[str, Any]) -> tuple[list[str], dict[str, Any], str | list[str]] | None:
    labels = [label for label in string.ascii_uppercase if label in raw and _not_missing(raw[label])]
    options = {label: raw[label] for label in labels}
    if not labels:
        serialized = raw.get("choices")
        if isinstance(serialized, str) and serialized.strip():
            try:
                parsed = ast.literal_eval(serialized)
            except (SyntaxError, ValueError):
                parsed = []
        elif isinstance(serialized, (list, tuple)):
            parsed = list(serialized)
        else:
            parsed = []
        labels = list(string.ascii_uppercase[: len(parsed)])
        options = dict(zip(labels, parsed))
    if not labels:
        return None

    answer_options = raw.get("answer_options")
    parsed_answer_options: list[str] = []
    if _not_missing(answer_options) and str(answer_options).strip():
        if isinstance(answer_options, str):
            try:
                parsed = ast.literal_eval(answer_options)
            except (SyntaxError, ValueError):
                parsed = []
        else:
            parsed = answer_options
        if isinstance(parsed, (list, tuple, set)):
            parsed_answer_options = [str(label).strip().upper() for label in parsed]
    answer_option = raw.get("answer_option")
    if parsed_answer_options:
        unknown = sorted(set(parsed_answer_options) - set(labels))
        if unknown:
            raise ValueError(f"answer_options contains unknown labels: {unknown}")
        gold: str | list[str] = sorted(set(parsed_answer_options))
    elif _not_missing(answer_option):
        gold = str(answer_option).strip().upper()
    else:
        raw_gold = str(raw["answer"]).strip()
        matching = [label for label, option in options.items() if str(option).strip() == raw_gold]
        gold = matching[0] if len(matching) == 1 else raw_gold.upper()
    return labels, options, gold


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, float]:
    if not rows:
        return {
            "n": 0.0,
            "Acc_strict": math.nan,
            "Acc_final": math.nan,
            "Format_valid": math.nan,
            "Extractor_valid": math.nan,
            "Contract_valid": math.nan,
            "Ambiguous_rate": math.nan,
            "Extraction_fallback_rate": math.nan,
        }
    n = len(rows)
    return {
        "n": float(n),
        "Acc_strict": sum(row["acc_strict"] for row in rows) / n,
        "Acc_final": sum(row["acc_final"] for row in rows) / n,
        "Format_valid": sum(row["format_valid"] for row in rows) / n,
        "Extractor_valid": sum(row["extractor_valid"] for row in rows) / n,
        "Contract_valid": sum(row["contract_valid"] for row in rows) / n,
        "Ambiguous_rate": sum(row["ambiguous"] for row in rows) / n,
        "Extraction_fallback_rate": sum(row["extraction_fallback_used"] for row in rows) / n,
    }


def _aggregate_pairs(rows: list[dict[str, Any]]) -> dict[str, float] | None:
    if not rows or not all(row.get("pair_id") is not None for row in rows):
        return None
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["pair_id"])].append(row)
    malformed = sorted(pair_id for pair_id, members in grouped.items() if len(members) != 2)
    if malformed:
        raise ValueError(f"paired benchmark contains non-binary groups: {malformed[:5]}")
    return {
        "n_pairs": float(len(grouped)),
        "Pair_accuracy": sum(all(member["acc_final"] for member in members) for members in grouped.values())
        / len(grouped),
        "Strict_pair_accuracy": sum(
            all(member["acc_strict"] for member in members) for members in grouped.values()
        )
        / len(grouped),
    }


def postprocess(
    input_path: Path,
    rows_output: Path,
    metrics_output: Path,
    prompt_contract: PromptContractLike = None,
) -> dict[str, Any]:
    frame = pd.read_excel(input_path)
    required = {"index", "answer", "prediction"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"VLMEval workbook missing columns: {sorted(missing)}")
    scored_rows: list[dict[str, Any]] = []
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for raw in frame.to_dict(orient="records"):
        choice_payload = _choice_payload(raw)
        if choice_payload is None:
            labels: list[str] = []
            scored = score_open_prediction(raw["prediction"], raw["answer"], prompt_contract)
            scoring_contract = "open_final_span"
            gold = str(raw["answer"])
        else:
            labels, options, gold = choice_payload
            scored = score_mcq_prediction(
                raw["prediction"], gold, labels, options, prompt_contract
            )
            scoring_contract = "multiple_choice_final_span"
        category = raw.get("category")
        if not _not_missing(category):
            category = raw.get("task", "unknown")
        record = {
            "index": str(raw["index"]),
            "gold": gold,
            "gold_value": str(raw["answer"]),
            "prediction": str(raw["prediction"]),
            "category": str(category),
            "l2_category": str(raw.get("l2_category", "unknown")),
            "question_type": str(raw.get("question_type", "unknown")),
            "answer_type": str(raw.get("answer_type", "unknown")),
            "scoring_contract": scoring_contract,
            "option_labels": labels,
            "pair_id": str(raw["pair_id"]) if _not_missing(raw.get("pair_id")) else None,
            "pair_member": str(raw["pair_member"]) if _not_missing(raw.get("pair_member")) else None,
            "visual_input": str(raw["visual_input"]) if _not_missing(raw.get("visual_input")) else None,
            "set_id": str(raw["set_id"]) if _not_missing(raw.get("set_id")) else None,
            "figure_id": str(raw["figure_id"]) if _not_missing(raw.get("figure_id")) else None,
            "question_id": str(raw["question_id"]) if _not_missing(raw.get("question_id")) else None,
            **scored,
        }
        scored_rows.append(record)
        by_category[record["category"]].append(record)
    payload = {
        "schema_version": "blind-gains.vlmeval-unified-scores.v2",
        "source_workbook": str(input_path),
        "parser_version": PARSER_VERSION,
        **prompt_contract_metadata(prompt_contract),
        "overall": _aggregate(scored_rows),
        "paired": _aggregate_pairs(scored_rows),
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
    parser.add_argument("--run-manifest", type=Path)
    args = parser.parse_args()
    contract = (
        load_prompt_contract_from_run_manifest(args.run_manifest)
        if args.run_manifest is not None
        else None
    )
    payload = postprocess(args.input, args.rows_output, args.metrics_output, contract)
    print(json.dumps(payload["overall"], sort_keys=True))


if __name__ == "__main__":
    main()
