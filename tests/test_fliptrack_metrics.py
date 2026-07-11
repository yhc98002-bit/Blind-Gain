import random

import src.eval.fliptrack_metrics as metrics_module
from src.eval.fliptrack_metrics import (
    aggregate_pair_metrics,
    aggregate_pair_metrics_by_template,
    mcnemar_exact,
    pair_score,
    permutation_null_pair_accuracy,
    template_key_shuffle_null_pair_accuracy,
)


def _row(pair_id, pa, pb, aa="left", ab="right"):
    return {"pair_id": pair_id, "prediction_a": pa, "prediction_b": pb, "answer_a": aa, "answer_b": ab}


def _reference_permutation_null(rows, n_perm, seed):
    rng = random.Random(seed)
    observed = aggregate_pair_metrics(rows)["pair_accuracy"]
    null = []
    for _ in range(n_perm):
        shuffled = []
        for source in rows:
            row = dict(source)
            if rng.random() < 0.5:
                row["prediction_a"], row["prediction_b"] = (
                    row.get("prediction_b", ""),
                    row.get("prediction_a", ""),
                )
            shuffled.append(row)
        null.append(aggregate_pair_metrics(shuffled)["pair_accuracy"])
    p_ge = (sum(value >= observed for value in null) + 1) / (len(null) + 1)
    return {
        "observed": observed,
        "null_mean": sum(null) / len(null),
        "p_ge": p_ge,
    }


def _reference_template_key_shuffle_null(rows, n_perm, seed):
    rows = [dict(row) for row in rows]
    rng = random.Random(seed)
    observed = aggregate_pair_metrics(rows)["pair_accuracy"]
    by_template = {}
    for index, row in enumerate(rows):
        by_template.setdefault(str(row.get("template_id", "")), []).append(index)
    null = []
    for _ in range(n_perm):
        shuffled = [dict(row) for row in rows]
        for indices in by_template.values():
            keys = [(rows[index]["answer_a"], rows[index]["answer_b"]) for index in indices]
            rng.shuffle(keys)
            for index, (answer_a, answer_b) in zip(indices, keys):
                shuffled[index]["answer_a"] = answer_a
                shuffled[index]["answer_b"] = answer_b
        null.append(aggregate_pair_metrics(shuffled)["pair_accuracy"])
    p_ge = (sum(value >= observed for value in null) + 1) / (len(null) + 1)
    return {
        "observed": observed,
        "null_mean": sum(null) / len(null),
        "p_ge": p_ge,
    }


def test_pair_score_requires_both_correct():
    score = pair_score(_row("p1", "left", "left"))
    assert score["correct_a"] is True
    assert score["correct_b"] is False
    assert score["pair_correct"] is False
    assert score["collapsed"] is True


def test_aggregate_pair_metrics():
    rows = [_row("p1", "left", "right"), _row("p2", "left", "left")]
    metrics = aggregate_pair_metrics(rows)
    assert metrics["n_pairs"] == 2
    assert metrics["member_accuracy"] == 0.75
    assert metrics["pair_accuracy"] == 0.5
    assert metrics["collapse_rate"] == 0.5


def test_aggregate_pair_metrics_by_template_keeps_templates_separate():
    rows = [
        {"pair_id": "a", "template_id": "t1", "answer_a": "red", "answer_b": "blue", "prediction_a": "red", "prediction_b": "blue"},
        {"pair_id": "b", "template_id": "t2", "answer_a": "up", "answer_b": "down", "prediction_a": "up", "prediction_b": "up"},
    ]
    metrics = aggregate_pair_metrics_by_template(rows)
    assert metrics["t1"]["pair_accuracy"] == 1.0
    assert metrics["t2"]["pair_accuracy"] == 0.0


def test_permutation_null_runs():
    rows = [_row("p1", "left", "right"), _row("p2", "left", "right")]
    out = permutation_null_pair_accuracy(rows, n_perm=20, seed=1)
    assert set(out) == {"observed", "null_mean", "p_ge"}
    assert out["observed"] == 1.0


def test_template_key_shuffle_null_runs():
    rows = [
        {"template_id": "t", **_row("p1", "left", "right")},
        {"template_id": "t", **_row("p2", "up", "down", "up", "down")},
    ]
    out = template_key_shuffle_null_pair_accuracy(rows, n_perm=20, seed=1)
    assert set(out) == {"observed", "null_mean", "p_ge"}
    assert out["observed"] == 1.0


def test_mcnemar_exact_counts_discordant_pairs():
    arm_a = [_row("p1", "left", "right"), _row("p2", "left", "right")]
    arm_b = [_row("p1", "left", "left"), _row("p2", "left", "right")]
    out = mcnemar_exact(arm_a, arm_b)
    assert out["n_common"] == 2
    assert out["b10"] == 1


def test_permutation_null_precomputes_scores_instead_of_rescoring_each_draw(monkeypatch):
    rows = [_row(f"p{index}", "left", "right") for index in range(6)]
    original = metrics_module.pair_score
    calls = 0

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(metrics_module, "pair_score", counted)
    permutation_null_pair_accuracy(rows, n_perm=100, seed=3)
    assert calls == 2 * len(rows)


def test_key_shuffle_null_precomputes_template_score_matrix(monkeypatch):
    rows = [
        {"template_id": "t", **_row(f"p{index}", f"a{index}", f"b{index}", f"a{index}", f"b{index}")}
        for index in range(5)
    ]
    original = metrics_module.pair_score
    calls = 0

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(metrics_module, "pair_score", counted)
    template_key_shuffle_null_pair_accuracy(rows, n_perm=100, seed=3)
    assert calls == len(rows) + len(rows) ** 2


def test_permutation_null_matches_seeded_reference_implementation():
    rows = [
        _row("p1", "left", "right"),
        _row("p2", "right", "left"),
        _row("p3", "left", "left"),
        _row("p4", "unknown", "right"),
    ]
    expected = _reference_permutation_null(rows, n_perm=37, seed=11)
    assert permutation_null_pair_accuracy(rows, n_perm=37, seed=11) == expected


def test_key_shuffle_null_matches_seeded_reference_implementation():
    rows = [
        {"template_id": "t1", **_row("p1", "red", "blue", "red", "blue")},
        {"template_id": "t1", **_row("p2", "up", "down", "up", "down")},
        {"template_id": "t1", **_row("p3", "cat", "dog", "cat", "dog")},
        {"template_id": "t2", **_row("p4", "5", "6", "5", "6")},
        {"template_id": "t2", **_row("p5", "8", "7", "7", "8")},
    ]
    expected = _reference_template_key_shuffle_null(rows, n_perm=41, seed=13)
    assert template_key_shuffle_null_pair_accuracy(rows, n_perm=41, seed=13) == expected
