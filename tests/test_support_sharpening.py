from __future__ import annotations

import pytest

from src.analysis.support_sharpening import (
    EXTRA_SAMPLE_COUNT,
    TOTAL_SAMPLE_COUNT,
    build_resampling_candidates,
    summarize_resampling,
)


def _base(row_index: int, correct_count: int = 0) -> dict:
    return {
        "split": "test",
        "row_index": row_index,
        "condition": "gray",
        "sample_count": 16,
        "sample_correct_count": correct_count,
        "problem": "<image>Find x.",
        "ground_truth": "3",
        "image_sha256": ["a" * 64],
        "source_manifest_sha256": "b" * 64,
        "decoding": {
            "sampled": {"n": 16, "temperature": 1.0, "top_p": 1.0},
            "max_tokens": 2048,
        },
        "prompt_contract_sha256": "c" * 64,
        "parser_version": "canonical-v2",
        "pilot_reward_version": "pilot-reward-v1",
    }


def _readout(row_index: int, step0: bool, target: bool, target_step: int = 100) -> dict:
    return {
        "split": "test",
        "row_index": row_index,
        "arm": "a2_gray",
        "condition": "gray",
        "step0_acc_final": step0,
        "target_step": target_step,
        "target_acc_final": target,
    }


def test_candidate_requires_zero_of_16_and_a_greedy_wrong_to_correct_flip() -> None:
    baseline = [_base(0), _base(1, 1), _base(2), _base(3)]
    readout = [
        _readout(0, False, True),
        _readout(1, False, True),
        _readout(2, True, True),
        _readout(3, False, False),
    ]

    selected = build_resampling_candidates(
        baseline, readout, arm="a2_gray", condition="gray", target_step=100
    )

    assert [row["row_index"] for row in selected] == [0]
    assert selected[0]["extra_sample_count"] == EXTRA_SAMPLE_COUNT
    assert selected[0]["planned_total_sample_count"] == TOTAL_SAMPLE_COUNT


def test_identity_or_condition_mismatch_fails_closed() -> None:
    with pytest.raises(ValueError, match="identities differ"):
        build_resampling_candidates(
            [_base(0)],
            [_readout(1, False, True)],
            arm="a2_gray",
            condition="gray",
            target_step=100,
        )
    wrong_condition = _readout(0, False, True)
    wrong_condition["condition"] = "none"
    with pytest.raises(ValueError, match="arm/condition mismatch"):
        build_resampling_candidates(
            [_base(0)],
            [wrong_condition],
            arm="a2_gray",
            condition="gray",
            target_step=100,
        )
    with pytest.raises(ValueError, match="target step mismatch"):
        build_resampling_candidates(
            [_base(0)],
            [_readout(0, False, True, target_step=400)],
            arm="a2_gray",
            condition="gray",
            target_step=100,
        )


def test_high_confidence_label_requires_no_success_in_all_64_extra_samples() -> None:
    candidate = build_resampling_candidates(
        [_base(0)],
        [_readout(0, False, True)],
        arm="a2_gray",
        condition="gray",
        target_step=100,
    )[0]

    absent = summarize_resampling(candidate, [False] * 64)
    observed = summarize_resampling(candidate, [True] + [False] * 63)

    assert absent["total_sample_count"] == 80
    assert absent["classification"] == "high-confidence support-expansion candidate"
    assert absent["registered_language"] == "not observed in the base K-sample set"
    assert observed["classification"] == "observed in support-sharpening samples"
    assert observed["registered_language"] == "mass sharpening within observed support"
    assert not absent["causal_capability_claim_permitted"]


def test_resampling_rejects_63_or_non_boolean_followups() -> None:
    candidate = build_resampling_candidates(
        [_base(0)],
        [_readout(0, False, True)],
        arm="a2_gray",
        condition="gray",
        target_step=100,
    )[0]
    with pytest.raises(ValueError, match="exactly 64"):
        summarize_resampling(candidate, [False] * 63)
    with pytest.raises(ValueError, match="exactly 64"):
        summarize_resampling(candidate, [False] * 63 + [0])
