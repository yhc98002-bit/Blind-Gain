from __future__ import annotations

import math
import re
from fractions import Fraction
from typing import Any


ANSWER_TAG_RE = re.compile(r"<answer>\s*(.*?)\s*</answer>", re.IGNORECASE | re.DOTALL)
FINAL_RE = re.compile(r"(?:final answer|answer)\s*[:：]\s*(.+)$", re.IGNORECASE)
BOXED_RE = re.compile(r"\\boxed\{([^{}]+)\}")


def extract_final_answer(text: Any) -> str:
    text = str(text).strip()
    tagged = ANSWER_TAG_RE.findall(text)
    if tagged:
        return tagged[-1].strip()
    boxed = BOXED_RE.findall(text)
    if boxed:
        return boxed[-1].strip()
    for line in reversed([line.strip() for line in text.splitlines() if line.strip()]):
        match = FINAL_RE.search(line)
        if match:
            return match.group(1).strip()
    return text.splitlines()[-1].strip() if text else ""


def _numeric_value(text: str) -> float | None:
    cleaned = text.strip().lower().replace(",", "")
    cleaned = cleaned.replace("$", "")
    percent = cleaned.endswith("%")
    cleaned = cleaned[:-1] if percent else cleaned
    try:
        value = float(Fraction(cleaned))
        return value / 100.0 if percent else value
    except Exception:
        return None


def normalize_answer(value: Any) -> str:
    text = extract_final_answer(value)
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"^[\"'`]+|[\"'`]+$", "", text)
    text = re.sub(r"[.,;:!?]+$", "", text)
    return text


def answers_match(prediction: Any, gold: Any, numeric_tol: float = 1e-4) -> bool:
    pred = normalize_answer(prediction)
    target = normalize_answer(gold)
    if pred == target:
        return True
    pred_num = _numeric_value(pred)
    target_num = _numeric_value(target)
    if pred_num is not None and target_num is not None:
        return math.isclose(pred_num, target_num, rel_tol=numeric_tol, abs_tol=numeric_tol)
    return False


def answer_reward(prediction: Any, gold: Any) -> float:
    return 1.0 if answers_match(prediction, gold) else 0.0


def batch_answer_reward(predictions: list[Any], golds: list[Any]) -> list[float]:
    if len(predictions) != len(golds):
        raise ValueError("predictions and golds must have the same length")
    return [answer_reward(pred, gold) for pred, gold in zip(predictions, golds)]

