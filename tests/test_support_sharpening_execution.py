from __future__ import annotations

import subprocess
import stat
from pathlib import Path

import pytest

from scripts.run_support_sharpening_followup import (
    SCHEMA_VERSION,
    expected_draw_identities,
    validate_resume_prefix,
)
from src.analysis.support_sharpening import registered_sampling_kwargs
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT
from src.rewards.answer_reward import PARSER_VERSION
from src.rewards.pilot_reward import PILOT_REWARD_VERSION


ROOT = Path(__file__).resolve().parents[1]


def _candidate(row_index: int = 5) -> dict:
    return {
        "split": "test",
        "row_index": row_index,
        "source_item_fingerprint": f"fingerprint-{row_index}",
    }


def _draw(candidate: dict, draw_index: int, response: str = "same text") -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "arm": "a2_gray",
        "condition": "gray",
        "row_index": candidate["row_index"],
        "draw_index": draw_index,
        "seed": 20260716 + draw_index,
        "source_item_fingerprint": candidate["source_item_fingerprint"],
        "parser_version": PARSER_VERSION,
        "pilot_reward_version": PILOT_REWARD_VERSION,
        "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
        "decoding": registered_sampling_kwargs(draw_index),
        "response": response,
        "pilot_accuracy_correct": False,
    }


def test_resume_accepts_identical_text_from_distinct_registered_seeds(tmp_path: Path) -> None:
    candidate = _candidate()
    partial = tmp_path / "draws.jsonl.partial"
    partial.write_text(
        "\n".join(
            __import__("json").dumps(_draw(candidate, draw_index))
            for draw_index in (16, 17)
        )
        + "\n",
        encoding="utf-8",
    )

    rows = validate_resume_prefix(partial, [candidate], "a2_gray", "gray")

    assert len(rows) == 2
    assert rows[0]["response"] == rows[1]["response"]
    assert rows[0]["seed"] != rows[1]["seed"]


def test_resume_rejects_seed_stream_reuse_even_when_text_differs(tmp_path: Path) -> None:
    candidate = _candidate()
    row = _draw(candidate, 16, response="unique text")
    row["seed"] = 20260710
    partial = tmp_path / "draws.jsonl.partial"
    partial.write_text(__import__("json").dumps(row) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="seed"):
        validate_resume_prefix(partial, [candidate], "a2_gray", "gray")


def test_expected_execution_order_contains_each_item_once_per_draw() -> None:
    candidates = [_candidate(3), _candidate(7)]
    identities = expected_draw_identities(candidates)

    assert len(identities) == 128
    assert identities[:4] == [(16, 3), (16, 7), (17, 3), (17, 7)]
    assert identities[-2:] == [(79, 3), (79, 7)]


def test_launcher_is_valid_shell_and_enforces_merged_head() -> None:
    launcher = ROOT / "scripts/launch_support_sharpening_followup.sh"
    result = subprocess.run(
        ["bash", "-n", str(launcher)], text=True, capture_output=True, check=False
    )
    source = launcher.read_text(encoding="utf-8")

    assert result.returncode == 0, result.stderr
    assert launcher.stat().st_mode & stat.S_IXUSR
    assert "git diff --quiet HEAD" in source
    assert "Registration state: merged-at-HEAD" in source
    assert "n_per_call: 1" in source
    assert "first: 20260732" in source and "last: 20260795" in source
