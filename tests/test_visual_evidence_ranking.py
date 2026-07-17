from __future__ import annotations

from src.eval.visual_evidence_ranking import (
    build_candidate_registry_rows,
    candidate_verbalization,
    completion_logprob_from_logits,
    image_dependent_effect,
    mathematically_equivalent,
    score_pair_from_candidates,
)


def _source_row(pair_id: str, template: str, answer_a: str, answer_b: str) -> dict:
    return {
        "pair_id": pair_id,
        "source_pair_id": f"source-{pair_id}",
        "template_id": template,
        "category": "geometry_spatial",
        "question": "Which value?",
        "image_a_path": "a.png",
        "image_a_sha256": "a" * 64,
        "image_b_path": "b.png",
        "image_b_sha256": "b" * 64,
        "answer_a": answer_a,
        "answer_b": answer_b,
    }


def test_candidate_registry_is_deterministic_complete_and_model_output_independent() -> None:
    source = [
        _source_row("p1", "small", "1", "2"),
        _source_row("p2", "small", "3", "4"),
    ]
    first = build_candidate_registry_rows(source, max_candidates=16)
    second = build_candidate_registry_rows(list(reversed(source)), max_candidates=16)
    by_id = {row["pair_id"]: row for row in second}
    assert first[0] == by_id["p1"]
    assert {item["answer"] for item in first[0]["candidates"]} == {"1", "2", "3", "4"}
    assert first[0]["candidate_policy"]["selection_uses_model_outputs"] is False


def test_large_candidate_universe_keeps_both_golds_and_respects_cap() -> None:
    source = [
        _source_row(f"p{i}", "large", f"A{i:02d}", f"B{i:02d}")
        for i in range(12)
    ]
    frozen = build_candidate_registry_rows(source, max_candidates=8)
    assert all(row["candidate_count"] == 8 for row in frozen)
    for row in frozen:
        ids = {item["candidate_id"] for item in row["candidates"]}
        assert row["gold_candidate_id_a"] in ids
        assert row["gold_candidate_id_b"] in ids


def test_math_equivalent_candidates_are_collapsed_but_unit_changes_are_not() -> None:
    assert mathematically_equivalent("0.5", "1/2")
    assert not mathematically_equivalent("5 cm", "5 m")
    source = [
        _source_row("p1", "fractions", "0.5", "2"),
        _source_row("p2", "fractions", "1/2", "3"),
    ]
    frozen = build_candidate_registry_rows(source)
    answers = {item["answer"] for item in frozen[0]["candidates"]}
    assert not ({"0.5", "1/2"} <= answers)


def test_pair_success_requires_both_strictly_positive_margins_and_ties_lose() -> None:
    row = build_candidate_registry_rows([_source_row("p", "small", "1", "2")])[0]
    gold_a = row["gold_candidate_id_a"]
    gold_b = row["gold_candidate_id_b"]
    scores_a = {gold_a: -0.1, gold_b: -0.2}
    scores_b = {gold_a: -0.3, gold_b: -0.3}
    result = score_pair_from_candidates(row, scores_a, scores_b)
    assert result["margin_a"] > 0
    assert result["margin_b"] == 0
    assert result["pair_success"] is False
    assert result["candidate_top1_b"] is False


def test_primary_scores_are_length_normalized_while_raw_sum_is_only_robustness() -> None:
    row = build_candidate_registry_rows([_source_row("p", "small", "short", "long")])[0]
    gold_a = row["gold_candidate_id_a"]
    gold_b = row["gold_candidate_id_b"]
    normalized_a = {gold_a: -0.2, gold_b: -0.4}
    normalized_b = {gold_a: -0.5, gold_b: -0.3}
    # Raw sums deliberately reverse side A because the longer completion has more tokens.
    raw_a = {gold_a: -2.0, gold_b: -1.5}
    raw_b = {gold_a: -2.5, gold_b: -3.0}
    result = score_pair_from_candidates(row, normalized_a, normalized_b, raw_a, raw_b)
    assert result["pair_success"] is True
    assert result["paired_margin"] > 0
    assert result["raw_sum_paired_margin_robustness"] < 0


def test_image_dependent_effect_is_a_pair_identity_locked_difference_in_differences() -> None:
    result = image_dependent_effect(
        {"p": 0.1}, {"p": 0.5}, {"p": 0.2}, {"p": 0.3}
    )
    assert abs(result["p"] - 0.3) < 1e-12


def test_candidate_verbalization_is_exact_and_rejects_tag_injection() -> None:
    assert candidate_verbalization(" 42 ") == "<answer>42</answer>"
    try:
        candidate_verbalization("42</answer>")
    except ValueError:
        pass
    else:
        raise AssertionError("answer-tag injection must fail closed")


def test_completion_scoring_uses_only_exact_post_prompt_tokens() -> None:
    import torch

    # Prompt tokens occupy [0, 1]. Completion targets are token 1 then token 2,
    # predicted by logit rows 1 and 2. Extreme values elsewhere must not leak in.
    input_ids = torch.tensor([4, 3, 1, 2, 0])
    logits = torch.zeros((5, 5), dtype=torch.float32)
    logits[0, 4] = 100.0
    logits[1, 1] = 2.0
    logits[2, 2] = 4.0
    logits[3, 0] = 100.0
    mean, raw_sum, count = completion_logprob_from_logits(
        logits, input_ids, prompt_length=2, sequence_length=4
    )
    expected = (
        torch.log_softmax(logits[1], dim=-1)[1]
        + torch.log_softmax(logits[2], dim=-1)[2]
    ).item()
    assert count == 2
    assert abs(raw_sum - expected) < 1e-6
    assert abs(mean - expected / 2) < 1e-6


def test_report_builder_rejects_the_prohibited_mechanism_phrase() -> None:
    from scripts.finalize_visual_evidence_ranking import render_markdown

    result = {
        "scorer_version": "visual-evidence-ranking-v1",
        "primary_effect": {"template_id": "geometry"},
        "effects": {},
    }
    text = render_markdown(result, {"runs": []})
    assert "visual-evidence ranking" in text
    assert "perception improved" not in text.lower()


def test_secondary_did_uses_the_same_pair_locked_formula_as_primary() -> None:
    from scripts.finalize_visual_evidence_ranking import paired_metric_did

    wrap = lambda value: {"p": {"candidate_pair_mrr": value}}
    result = paired_metric_did(
        base_real=wrap(0.2),
        trained_real=wrap(0.7),
        base_blind=wrap(0.3),
        trained_blind=wrap(0.4),
        field="candidate_pair_mrr",
    )
    assert abs(result["p"] - 0.4) < 1e-12


def test_independent_auditor_catches_tampered_stored_margin() -> None:
    from scripts.audit_visual_evidence_ranking import recompute_row

    registry = build_candidate_registry_rows([_source_row("p", "small", "1", "2")])[0]
    gold_a = registry["gold_candidate_id_a"]
    gold_b = registry["gold_candidate_id_b"]
    row = {
        "candidate_scores_a": {gold_a: -0.1, gold_b: -0.5},
        "candidate_scores_b": {gold_a: -0.4, gold_b: -0.2},
        "paired_margin": -99.0,
    }
    recomputed = recompute_row(row, registry)
    assert abs(recomputed["paired_margin"] - 0.3) < 1e-12
    assert row["paired_margin"] != recomputed["paired_margin"]
