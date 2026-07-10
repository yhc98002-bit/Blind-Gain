from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_blind_solvability import load_validated_resume_prefix


def _rows(count: int = 4) -> list[dict[str, object]]:
    return [
        {
            "split": "audit",
            "row_index": index,
            "qid": f"q{index}",
            "problem": f"problem {index}",
            "answer": str(index),
            "images": [{"sha256": f"sha{index}"}],
            "metadata": {"source": "test"},
        }
        for index in range(count)
    ]


def _result(row: dict[str, object], condition: str = "noise") -> dict[str, object]:
    sampled_correct = [False] * 16
    return {
        "schema_version": "blind-gains.blind-solvability.v1",
        "split": row["split"],
        "row_index": row["row_index"],
        "qid": row["qid"],
        "problem": row["problem"],
        "ground_truth": row["answer"],
        "image_sha256": [image["sha256"] for image in row["images"]],
        "condition": condition,
        "source_metadata": row["metadata"],
        "greedy_response": "answer",
        "sampled_responses": ["answer"] * 16,
        "p_greedy": 0.0,
        "greedy_correct": False,
        "greedy_extracted_answer": None,
        "greedy_format_valid": False,
        "sample_count": 16,
        "sample_correct_count": 0,
        "sample_correct": sampled_correct,
        "p_sample": 0.0,
        "pass_at_g": 0.0,
        "pass_at_k16": 0.0,
        "variance_proxy": 0.0,
        "decoding": {
            "greedy": {"temperature": 0.0, "top_p": 1.0, "n": 1},
            "sampled": {"temperature": 1.0, "top_p": 1.0, "n": 16},
            "max_tokens": 512,
            "seed": 20260710,
        },
    }


def _write(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _validate(path: Path, rows: list[dict[str, object]], batch_size: int = 2) -> list[str]:
    return load_validated_resume_prefix(
        path,
        rows,
        condition="noise",
        batch_size=batch_size,
        max_tokens=512,
        sample_count=16,
        sample_temperature=1.0,
        seed=20260710,
    )


def test_resume_accepts_canonical_batch_aligned_prefix(tmp_path: Path) -> None:
    rows = _rows()
    path = tmp_path / "partial.jsonl"
    _write(path, [_result(row) for row in rows[:2]])

    raw_lines = _validate(path, rows)

    assert len(raw_lines) == 2
    assert json.loads(raw_lines[1])["qid"] == "q1"


def test_resume_rejects_manifest_or_condition_mismatch(tmp_path: Path) -> None:
    rows = _rows()
    records = [_result(row) for row in rows[:2]]
    records[1]["condition"] = "gray"
    path = tmp_path / "partial.jsonl"
    _write(path, records)

    with pytest.raises(ValueError, match="condition"):
        _validate(path, rows)


def test_resume_rejects_non_batch_aligned_prefix(tmp_path: Path) -> None:
    rows = _rows()
    path = tmp_path / "partial.jsonl"
    _write(path, [_result(rows[0])])

    with pytest.raises(ValueError, match="not aligned"):
        _validate(path, rows)


def test_resume_rejects_reordered_prefix(tmp_path: Path) -> None:
    rows = _rows()
    path = tmp_path / "partial.jsonl"
    _write(path, [_result(rows[1]), _result(rows[0])])

    with pytest.raises(ValueError, match="row_index"):
        _validate(path, rows)
