from src.eval.fliptrack_metrics import aggregate_pair_metrics, mcnemar_exact, pair_score, permutation_null_pair_accuracy


def _row(pair_id, pa, pb, aa="left", ab="right"):
    return {"pair_id": pair_id, "prediction_a": pa, "prediction_b": pb, "answer_a": aa, "answer_b": ab}


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


def test_permutation_null_runs():
    rows = [_row("p1", "left", "right"), _row("p2", "left", "right")]
    out = permutation_null_pair_accuracy(rows, n_perm=20, seed=1)
    assert set(out) == {"observed", "null_mean", "p_ge"}
    assert out["observed"] == 1.0


def test_mcnemar_exact_counts_discordant_pairs():
    arm_a = [_row("p1", "left", "right"), _row("p2", "left", "right")]
    arm_b = [_row("p1", "left", "left"), _row("p2", "left", "right")]
    out = mcnemar_exact(arm_a, arm_b)
    assert out["n_common"] == 2
    assert out["b10"] == 1

