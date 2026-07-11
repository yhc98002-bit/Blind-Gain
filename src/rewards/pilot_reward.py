from __future__ import annotations

import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import os
import sys
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any

from mathruler.grader import grade_answer

from src.eval.prompt_contract import response_satisfies_contract
from src.rewards.answer_reward import (
    PARSER_VERSION,
    answers_match,
    extract_answer_span,
)


REWARD_NAME = "blind_gains_pilot_v1"
REWARD_TYPE = "sequential"
PILOT_REWARD_VERSION = "pilot-reward-v1"
ROOT = Path(__file__).resolve().parents[2]
NATIVE_R1V_PATH = ROOT / "artifacts" / "repos" / "EasyR1" / "examples" / "reward_function" / "r1v.py"
REASON_CODES = {
    "none": 0.0,
    "canonical_correct_mathruler_incorrect": 1.0,
    "mathruler_correct_canonical_incorrect": 2.0,
    "mathruler_error_canonical_incorrect": 3.0,
    "mathruler_error_canonical_correct": 4.0,
}


@lru_cache(maxsize=1)
def load_native_r1v() -> ModuleType:
    if not NATIVE_R1V_PATH.is_file():
        raise FileNotFoundError(f"native EasyR1 r1v reward is absent: {NATIVE_R1V_PATH}")
    spec = importlib.util.spec_from_file_location("blind_gains_native_r1v_shadow", NATIVE_R1V_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load native EasyR1 r1v reward: {NATIVE_R1V_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _mathruler_grade(answer: str, ground_truth: str) -> tuple[bool, str | None]:
    try:
        return bool(grade_answer(answer, ground_truth)), None
    except Exception as error:  # pragma: no cover - depends on symbolic parser internals
        return False, type(error).__name__


def _disagreement_reason(
    *, mathruler_correct: bool, canonical_correct: bool, mathruler_error: str | None
) -> str:
    if mathruler_error is not None:
        return (
            "mathruler_error_canonical_correct"
            if canonical_correct
            else "mathruler_error_canonical_incorrect"
        )
    if mathruler_correct == canonical_correct:
        return "none"
    return (
        "mathruler_correct_canonical_incorrect"
        if mathruler_correct
        else "canonical_correct_mathruler_incorrect"
    )


def _append_shadow(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
    with path.open("a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def compute_score(
    reward_input: dict[str, Any],
    format_weight: float = 0.5,
    shadow_log_path: str | None = None,
    require_shadow_log: bool = False,
) -> dict[str, float]:
    """Compute the pilot reward with mathruler precedence and canonical-v2 shadows.

    Precedence rule: canonical-v2 extracts the answer span; mathruler grades that
    extracted span; if mathruler and canonical numeric equivalence disagree,
    mathruler's verdict is the training accuracy reward and the disagreement is logged.
    """

    if not 0.0 <= format_weight <= 1.0:
        raise ValueError(f"format_weight must be in [0, 1], found {format_weight}")
    response = str(reward_input["response"])
    ground_truth = str(reward_input["ground_truth"]).strip()
    extracted = extract_answer_span(response)
    mathruler_correct, mathruler_error = _mathruler_grade(extracted.span, ground_truth)
    canonical_correct = bool(answers_match(extracted.span, ground_truth))
    contract_valid = bool(response_satisfies_contract(response))
    reason = _disagreement_reason(
        mathruler_correct=mathruler_correct,
        canonical_correct=canonical_correct,
        mathruler_error=mathruler_error,
    )
    accuracy_reward = float(mathruler_correct)
    format_reward = float(contract_valid)
    training_reward = (1.0 - format_weight) * accuracy_reward + format_weight * format_reward
    native_score = load_native_r1v().compute_score(
        {"response": response, "ground_truth": ground_truth}, format_weight=format_weight
    )
    native_shadow = float(native_score["overall"])
    canonical_shadow = float(canonical_correct)

    resolved_shadow_path = shadow_log_path or os.environ.get("BLIND_GAINS_REWARD_SHADOW_LOG")
    if require_shadow_log and not resolved_shadow_path:
        raise RuntimeError(
            "pilot reward requires BLIND_GAINS_REWARD_SHADOW_LOG or shadow_log_path"
        )
    if resolved_shadow_path:
        _append_shadow(
            Path(resolved_shadow_path),
            {
                "schema_version": "blind-gains.pilot-reward-shadow.v1",
                "timestamp_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "pid": os.getpid(),
                "pilot_reward_version": PILOT_REWARD_VERSION,
                "parser_version": PARSER_VERSION,
                "response_sha256": hashlib.sha256(response.encode("utf-8")).hexdigest(),
                "ground_truth": ground_truth,
                "extracted_answer": extracted.span,
                "extraction_level": extracted.extraction_level,
                "extractor_valid": extracted.extractor_valid,
                "contract_valid": contract_valid,
                "mathruler_accuracy_reward": accuracy_reward,
                "mathruler_error": mathruler_error,
                "training_reward": training_reward,
                "native_r1v_shadow_reward": native_shadow,
                "canonical_eval_reward": canonical_shadow,
                "reward_disagreement_reason": reason,
            },
        )

    return {
        "overall": training_reward,
        "format": format_reward,
        "accuracy": accuracy_reward,
        "training_reward": training_reward,
        "native_r1v_shadow_reward": native_shadow,
        "canonical_eval_reward": canonical_shadow,
        "reward_disagreement": float(reason != "none"),
        "reward_disagreement_reason_code": REASON_CODES[reason],
    }
