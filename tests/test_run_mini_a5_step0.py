from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_mini_a5_step0 import (
    SCHEMA_VERSION,
    expected_row_identities,
    pair_reward_inputs,
    validate_resume_prefix,
)


def _pair(uid: str = "p1") -> dict[str, str]:
    return {
        "pair_group_uid": uid,
        "answer_a": "A",
        "answer_b": "B",
    }


def test_pair_reward_inputs_have_explicit_aligned_pair_identity() -> None:
    rows = pair_reward_inputs(_pair(), ["a"] * 5, ["b"] * 5)
    assert len(rows) == 10
    assert [(row["pair_member"], row["pair_rollout_index"]) for row in rows] == [
        (member, index) for member in ("a", "b") for index in range(5)
    ]


def test_resume_rejects_old_positional_or_reordered_rows(tmp_path: Path) -> None:
    pairs = [_pair()]
    identities = expected_row_identities(pairs)
    output = tmp_path / "predictions.jsonl"
    rows = []
    for uid, member, index in identities:
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "pair_group_uid": uid,
                "pair_member": member,
                "pair_rollout_index": index,
                "sample_manifest_sha256": "sample",
                "format_prompt_sha256": "prompt",
                "model_revision": "model",
                "seed": 1,
                "rollout_n": 5,
                "temperature": 1.0,
                "top_p": 1.0,
                "max_tokens": 2048,
                "parser_version": "canonical-v2",
                "pilot_reward_version": "pilot-reward-v1",
                "cp_reward_version": "cp-grpo-reward-v1",
            }
        )
    rows[0], rows[1] = rows[1], rows[0]
    output.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    with pytest.raises(ValueError, match="identity mismatch"):
        validate_resume_prefix(
            output,
            pairs,
            sample_sha256="sample",
            format_prompt_sha256="prompt",
            model_revision="model",
            seed=1,
        )


def test_resume_accepts_empty_crash_prefix_as_zero_pairs(tmp_path: Path) -> None:
    output = tmp_path / "predictions.jsonl"
    output.touch()
    assert (
        validate_resume_prefix(
            output,
            [_pair()],
            sample_sha256="sample",
            format_prompt_sha256="prompt",
            model_revision="model",
            seed=1,
        )
        == 0
    )
