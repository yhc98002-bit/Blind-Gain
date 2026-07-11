from __future__ import annotations

import hashlib
import json
import math
import string
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from scripts.postprocess_vlmeval_predictions import _choice_payload, score_mcq_prediction, score_open_prediction
from src.eval.prompt_contract import PromptContractLike, prompt_contract_metadata
from src.rewards.answer_reward import PARSER_VERSION


PROTOCOL_VERSION = "blind-gains.layer1-image-removed.v1"


def mmstar_text_prompt(row: dict[str, Any]) -> str:
    options = {
        label: row[label]
        for label in string.ascii_uppercase
        if label in row and not pd.isna(row[label])
    }
    prompt = f"Question: {row['question']}\n"
    if options:
        prompt += "Options:\n"
        prompt += "".join(f"{label}. {value}\n" for label, value in options.items())
        prompt += "Please select the correct answer from the options above. \n"
    return prompt


def mathvista_text_prompt(row: dict[str, Any]) -> str:
    return str(row["question"])


def build_text_prompt(row: dict[str, Any], dataset_type: str) -> str:
    if dataset_type == "mmstar":
        return mmstar_text_prompt(row)
    if dataset_type == "mathvista":
        return mathvista_text_prompt(row)
    raise ValueError(f"unsupported blind Layer-1 dataset type: {dataset_type}")


def load_rows(path: str | Path, dataset_type: str) -> list[dict[str, Any]]:
    frame = pd.read_csv(path, sep="\t")
    required = {"index", "question", "answer"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{dataset_type} blind input missing columns: {sorted(missing)}")
    rows = frame.to_dict(orient="records")
    for row in rows:
        prompt = build_text_prompt(row, dataset_type)
        if "<image>" in prompt or "<|vision_" in prompt:
            raise ValueError(f"row {row['index']} retains an image token in the blind prompt")
    return rows


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
    count = len(rows)
    return {
        "n": float(count),
        "Acc_strict": sum(row["acc_strict"] for row in rows) / count,
        "Acc_final": sum(row["acc_final"] for row in rows) / count,
        "Format_valid": sum(row["format_valid"] for row in rows) / count,
        "Extractor_valid": sum(row["extractor_valid"] for row in rows) / count,
        "Contract_valid": sum(row["contract_valid"] for row in rows) / count,
        "Ambiguous_rate": sum(row["ambiguous"] for row in rows) / count,
        "Extraction_fallback_rate": sum(row["extraction_fallback_used"] for row in rows) / count,
    }


def score_predictions(
    rows: list[dict[str, Any]],
    predictions: Iterable[str],
    dataset_type: str,
    prompt_contract: PromptContractLike = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    predictions = list(predictions)
    if len(rows) != len(predictions):
        raise ValueError("prediction count does not match blind input rows")
    scored_rows: list[dict[str, Any]] = []
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row, prediction in zip(rows, predictions):
        if dataset_type == "mmstar":
            labels = [
                label
                for label in string.ascii_uppercase
                if label in row and not pd.isna(row[label])
            ]
            options = {label: row[label] for label in labels}
            gold = str(row["answer"]).strip().upper()
            scored = score_mcq_prediction(
                prediction, gold, labels, options, prompt_contract
            )
            category = str(row.get("category", "unknown"))
            grading_contract = "multiple_choice_final_span"
        else:
            payload = _choice_payload(row)
            if payload is None:
                labels = []
                gold = str(row["answer"])
                scored = score_open_prediction(prediction, gold, prompt_contract)
                grading_contract = "open_final_span"
            else:
                labels, options, gold = payload
                scored = score_mcq_prediction(
                    prediction, gold, labels, options, prompt_contract
                )
                grading_contract = "multiple_choice_final_span"
            category = str(row.get("task", "unknown"))
        prompt = build_text_prompt(row, dataset_type)
        record = {
            "index": str(row["index"]),
            "dataset_type": dataset_type,
            "image_removed": True,
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "gold": gold,
            "gold_value": str(row["answer"]),
            "prediction": prediction,
            "category": category,
            "scoring_contract": grading_contract,
            "option_labels": labels,
            **scored,
        }
        scored_rows.append(record)
        by_category[category].append(record)
    metrics = {
        "schema_version": PROTOCOL_VERSION,
        "dataset_type": dataset_type,
        "image_removed": True,
        "parser_version": PARSER_VERSION,
        **prompt_contract_metadata(prompt_contract),
        "overall": _aggregate(scored_rows),
        "per_category": {key: _aggregate(value) for key, value in sorted(by_category.items())},
    }
    return scored_rows, metrics


def write_results(rows: list[dict[str, Any]], metrics: dict[str, Any], output: Path, metrics_output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
    metrics_output.parent.mkdir(parents=True, exist_ok=True)
    metrics_output.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
