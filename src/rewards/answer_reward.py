from __future__ import annotations

from dataclasses import dataclass
import math
import re
from fractions import Fraction
from typing import Any


ANSWER_TAG_RE = re.compile(r"<answer>\s*(.*?)\s*</answer>", re.IGNORECASE | re.DOTALL)
FINAL_RE = re.compile(r"(?:final answer|answer)\s*[:：]\s*(.*)$", re.IGNORECASE)


@dataclass(frozen=True)
class ExtractedAnswer:
    span: str
    extraction_level: str
    extraction_fallback_used: bool
    format_valid: bool


def _balanced_boxed_spans(text: str) -> list[str]:
    spans: list[str] = []
    needle = r"\boxed{"
    start = 0
    while True:
        idx = text.find(needle, start)
        if idx < 0:
            return spans
        pos = idx + len(needle)
        depth = 1
        out: list[str] = []
        while pos < len(text):
            char = text[pos]
            if char == "{":
                depth += 1
                out.append(char)
            elif char == "}":
                depth -= 1
                if depth == 0:
                    spans.append("".join(out).strip())
                    break
                out.append(char)
            else:
                out.append(char)
            pos += 1
        start = idx + len(needle)


def extract_answer_span(text: Any) -> ExtractedAnswer:
    text = str(text).strip()
    tagged = ANSWER_TAG_RE.findall(text)
    if tagged:
        return ExtractedAnswer(tagged[-1].strip(), "tag", False, True)
    boxed = _balanced_boxed_spans(text)
    if boxed:
        return ExtractedAnswer(boxed[-1].strip(), "boxed", False, True)
    for line in reversed([line.strip() for line in text.splitlines() if line.strip()]):
        match = FINAL_RE.search(line)
        if match:
            return ExtractedAnswer(match.group(1).strip(), "line", False, True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        return ExtractedAnswer(lines[-1], "lastline", True, False)
    return ExtractedAnswer(text, "fulltext", True, False)


def extract_final_answer(text: Any) -> str:
    return extract_answer_span(text).span


def numeric_value(text: str) -> float | None:
    cleaned = text.strip().lower().replace(",", "")
    cleaned = cleaned.replace("$", "")
    percent = cleaned.endswith("%")
    cleaned = cleaned[:-1] if percent else cleaned
    frac_match = re.fullmatch(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", cleaned)
    if frac_match:
        try:
            numerator = float(Fraction(frac_match.group(1)))
            denominator = float(Fraction(frac_match.group(2)))
            if denominator == 0:
                return None
            value = numerator / denominator
            return value / 100.0 if percent else value
        except Exception:
            return None
    try:
        value = float(Fraction(cleaned))
        return value / 100.0 if percent else value
    except Exception:
        return None


def normalize_text(value: Any) -> str:
    text = str(value)
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"^[\"'`]+|[\"'`]+$", "", text)
    text = re.sub(r"[.,;:!?]+$", "", text)
    return text


def normalize_answer(value: Any) -> str:
    return normalize_text(extract_final_answer(value))


def answers_match(prediction: Any, gold: Any, numeric_tol: float = 1e-4) -> bool:
    pred = normalize_answer(prediction)
    target = normalize_text(gold)
    if pred == target:
        return True
    pred_num = numeric_value(pred)
    target_num = numeric_value(target)
    if pred_num is not None and target_num is not None:
        return math.isclose(pred_num, target_num, rel_tol=numeric_tol, abs_tol=numeric_tol)
    return False


def answer_reward(prediction: Any, gold: Any) -> float:
    return 1.0 if answers_match(prediction, gold) else 0.0


def batch_answer_reward(predictions: list[Any], golds: list[Any]) -> list[float]:
    if len(predictions) != len(golds):
        raise ValueError("predictions and golds must have the same length")
    return [answer_reward(pred, gold) for pred, gold in zip(predictions, golds)]
