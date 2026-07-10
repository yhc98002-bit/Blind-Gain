from __future__ import annotations

import json

import numpy as np

from src.fliptrack.artifact_attackers import (
    _fit_fold_scores,
    auc,
    compute_gate,
    grouped_folds,
    univariate_feature_diagnosis,
)


def test_grouped_folds_never_split_pair_members() -> None:
    pair_ids = [f"p{index}" for index in range(10) for _ in range(2)]
    for train, test in grouped_folds(pair_ids, n_splits=5, seed=7):
        for pair_id in set(pair_ids):
            indices = [index for index, value in enumerate(pair_ids) if value == pair_id]
            assert len({bool(test[index]) for index in indices}) == 1
            assert not any(train[index] and test[index] for index in indices)


def test_auc_uses_average_ranks_for_ties() -> None:
    labels = np.asarray([0, 1, 0, 1])
    scores = np.zeros(4)
    assert auc(labels, scores) == 0.5


def test_fold_direction_depends_only_on_training_fold() -> None:
    features = np.asarray([[-2.0], [-1.0], [1.0], [2.0], [-3.0], [3.0]])
    labels = np.asarray([0, 0, 1, 1, 0, 1])
    train = np.asarray([True, True, True, True, False, False])
    test = ~train
    scores_a, direction_a, train_auc_a = _fit_fold_scores(features, labels, train, test)
    flipped_test_labels = labels.copy()
    flipped_test_labels[test] = 1 - flipped_test_labels[test]
    scores_b, direction_b, train_auc_b = _fit_fold_scores(features, flipped_test_labels, train, test)
    assert direction_a == direction_b
    assert train_auc_a == train_auc_b
    assert np.array_equal(scores_a, scores_b)


def test_gate_is_and_of_availability_point_and_ci_rules() -> None:
    passing = {
        "pooled": {"gate_statistic": 0.52, "pair_bootstrap_ci_95": [0.50, 0.60]},
        "per_template": {"t": {"gate_statistic": 0.54, "pair_bootstrap_ci_95": [0.50, 0.61]}},
    }
    assert compute_gate({"metadata": passing, "frequency": passing, "dinov2": passing})["status"] is True
    point_fail = json.loads(json.dumps(passing))
    point_fail["pooled"]["gate_statistic"] = 0.56
    assert compute_gate({"metadata": point_fail, "frequency": passing, "dinov2": passing})["status"] is False
    ci_fail = json.loads(json.dumps(passing))
    ci_fail["per_template"]["t"]["pair_bootstrap_ci_95"][1] = 0.63
    assert compute_gate({"metadata": passing, "frequency": ci_fail, "dinov2": passing})["status"] is False
    assert compute_gate({"metadata": passing, "frequency": passing, "dinov2": None})["status"] is False


def test_univariate_diagnosis_identifies_planted_feature() -> None:
    labels = np.asarray([0, 0, 0, 0, 1, 1, 1, 1])
    features = np.asarray(
        [
            [0.0, 1.0],
            [0.0, 0.0],
            [0.0, 1.0],
            [0.0, 0.0],
            [1.0, 0.0],
            [1.0, 1.0],
            [1.0, 0.0],
            [1.0, 1.0],
        ]
    )
    result = univariate_feature_diagnosis(features, labels, ("planted", "noise"))
    assert result["planted"]["gate_statistic"] == 1.0
    assert result["noise"]["gate_statistic"] < 0.6
