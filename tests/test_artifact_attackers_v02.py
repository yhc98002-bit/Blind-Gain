from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

from src.fliptrack.artifact_attackers import (
    _fit_fold_scores,
    auc,
    compute_gate,
    grouped_folds,
    univariate_feature_diagnosis,
)


ROOT = Path(__file__).resolve().parents[1]


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


def test_chart_v08_launcher_rejects_released_node_before_remote_query() -> None:
    launcher = ROOT / "scripts/launch_chart_v08_artifact_gate.sh"
    result = subprocess.run(
        ["bash", str(launcher), "an21", "4"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "permanent nodes" in result.stderr


def test_chart_v08_launcher_records_placement_and_has_occupied_gpu_preflight() -> None:
    launcher = ROOT / "scripts/launch_chart_v08_artifact_gate.sh"
    subprocess.run(["bash", "-n", str(launcher)], check=True)
    source = launcher.read_text(encoding="utf-8")

    assert "--query-compute-apps=pid" in source
    assert "flock -n" in source
    assert 'tensor_parallel_width: 1' in source
    assert 'replica_count: 1' in source
    assert "os.kill" not in source


# --- 2026-08-16 dispatch item 3: unfolded per-attacker CIs (I10 fixtures) ---

import math
import random

from src.fliptrack.artifact_attackers import _pair_bootstrap_ci, evaluate_features


def _noise_problem(seed: int = 20260816, n_pairs: int = 40):
    rng = np.random.default_rng(seed)
    pair_ids = [f"p{index}" for index in range(n_pairs) for _ in (0, 1)]
    labels = np.asarray([0, 1] * n_pairs, dtype=np.int64)
    features = rng.normal(size=(2 * n_pairs, 6))
    return features, labels, pair_ids


def test_unfolded_ci_can_include_half_where_folded_cannot() -> None:
    """The registered prose criterion is "CI includes 0.5"; the folded
    interval lives on [0.5, 1] BY CONSTRUCTION and can never include it.
    The unfolded directed interval can — for pure noise it must. The pre-fix
    code has no unfolded field and fails here with KeyError."""
    features, labels, pair_ids = _noise_problem()
    result = evaluate_features(features, labels, pair_ids, n_splits=5, seed=3, n_bootstrap=200)

    folded = result["pair_bootstrap_ci_95"]
    unfolded = result["directed_oof_auc_unfolded_ci_95"]
    assert folded[0] >= 0.5, "folded interval left of 0.5 is structurally impossible"
    assert unfolded[0] < 0.5 < unfolded[1], (
        f"noise attacker's unfolded CI should span 0.5, got {unfolded}"
    )


def _reference_folded_ci(labels, scores, pair_ids, *, n_bootstrap, seed):
    """The pre-fix bootstrap, verbatim: folded-only, same rng consumption."""
    indices_by_pair = {}
    pair_array = np.asarray(pair_ids)
    for pair_id in sorted(set(pair_ids)):
        indices_by_pair[pair_id] = np.flatnonzero(pair_array == pair_id)
    pairs = sorted(indices_by_pair)
    rng = random.Random(seed)
    values = []
    for _ in range(n_bootstrap):
        sampled = [rng.choice(pairs) for _ in pairs]
        indices = np.concatenate([indices_by_pair[pair_id] for pair_id in sampled])
        value = auc(labels[indices], scores[indices])
        if not math.isnan(value):
            values.append(max(value, 1.0 - value))
    from src.fliptrack.artifact_attackers import np as _np
    return float(_np.quantile(values, 0.025)), float(_np.quantile(values, 0.975))


def test_folded_ci_reproduces_the_prefix_bootstrap_exactly() -> None:
    """Adding the unfolded interval must not move a single folded digit: both
    intervals are quantiles of the SAME draws (v1-reproduction guarantee)."""
    rng = np.random.default_rng(7)
    n_pairs = 25
    pair_ids = [f"p{index}" for index in range(n_pairs) for _ in (0, 1)]
    labels = np.asarray([0, 1] * n_pairs, dtype=np.int64)
    scores = rng.normal(size=2 * n_pairs)

    folded_lo, folded_hi, _, _ = _pair_bootstrap_ci(
        labels, scores, pair_ids, n_bootstrap=300, seed=1234
    )
    ref_lo, ref_hi = _reference_folded_ci(
        labels, scores, pair_ids, n_bootstrap=300, seed=1234
    )
    assert (folded_lo, folded_hi) == (ref_lo, ref_hi)


def test_per_item_scores_are_off_by_default() -> None:
    features, labels, pair_ids = _noise_problem(seed=5, n_pairs=20)
    result = evaluate_features(features, labels, pair_ids, n_splits=5, seed=3, n_bootstrap=50)
    assert "oof_scores" not in result

    with_scores = evaluate_features(
        features, labels, pair_ids, n_splits=5, seed=3, n_bootstrap=50, include_scores=True
    )
    assert len(with_scores["oof_scores"]) == len(labels)
    assert with_scores["directed_oof_auc"] == result["directed_oof_auc"]
