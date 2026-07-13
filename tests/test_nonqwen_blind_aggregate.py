from __future__ import annotations

import pytest

from scripts.aggregate_nonqwen_blind_sample import summarize


def _row(index: int, correct: bool) -> dict:
    return {
        "schema_version": "blind-gains.nonqwen-blind-sample.v1",
        "qid": f"q{index}",
        "row_index": index,
        "backend": "gemma3",
        "condition": "none",
        "source_manifest_sha256": "a" * 64,
        "format_prompt_sha256": "b" * 64,
        "caption_store_sha256": None,
        "parser_version": "canonical-v2",
        "prompt_contract_sha256": "c" * 64,
        "decoding": {"temperature": 0.0, "top_p": 1.0, "n": 1, "max_new_tokens": 2048},
        "runtime": {
            "backend": "gemma3",
            "generation_callable": True,
            "processor_use_fast": False,
        },
        "acc_final": correct,
        "acc_strict": correct,
        "extractor_valid": True,
        "contract_valid": True,
        "source_metadata": {"source": "s", "category": "c"},
    }


def test_blind_aggregate_computes_accuracy_and_strata() -> None:
    payload = summarize([_row(0, True), _row(1, False)], bootstrap=100)

    assert payload["n_rows"] == 2
    assert payload["acc_final"] == 0.5
    assert payload["per_source_category"]["s::c"] == {"n": 2, "acc_final": 0.5}


def test_blind_aggregate_rejects_duplicate_identity() -> None:
    row = _row(0, True)

    with pytest.raises(ValueError, match="duplicate"):
        summarize([row, dict(row)], bootstrap=10)


def test_blind_aggregate_rejects_mixed_conditions() -> None:
    left = _row(0, True)
    right = _row(1, False)
    right["condition"] = "real"

    with pytest.raises(ValueError, match="mixed condition"):
        summarize([left, right], bootstrap=10)
