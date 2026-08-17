"""Fixture for the permanent file_size attacker (dispatch 2026-08-16b): a
release whose edited side is systematically larger must fail the gate under
the file_size key; a size-balanced release must pass it."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.fliptrack.artifact_attackers import (  # noqa: E402
    _evaluate_all_scopes,
    _file_size_features,
    compute_gate,
)


def _fake_sizes(tmp_path, sizes):
    paths = []
    for index, size in enumerate(sizes):
        path = tmp_path / f"member_{index}.png"
        path.write_bytes(b"\x89PNG" + b"0" * (size - 4))
        paths.append(path)
    return paths


def _run_file_size(tmp_path, sizes, labels):
    paths = _fake_sizes(tmp_path, sizes)
    features = np.stack([_file_size_features(p) for p in paths])
    pair_ids = [f"p{i // 2}" for i in range(len(paths))]
    templates = ["cell_a" if i < len(paths) // 2 else "cell_b"
                 for i in range(len(paths))]
    scopes = _evaluate_all_scopes(features, np.asarray(labels), pair_ids,
                                  templates, n_splits=5, seed=0,
                                  n_bootstrap=200, include_scores=False)
    return compute_gate({"file_size": scopes})


def test_size_separated_release_fails_gate(tmp_path):
    # edited members (label 1) always 1 KiB larger — the hier-chart leak class
    sizes, labels = [], []
    for pair in range(40):
        base = 8000 + 13 * pair
        sizes += [base, base + 1024]
        labels += [0, 1]
    gate = _run_file_size(tmp_path, sizes, labels)
    assert gate["status"] is False
    assert any(f.startswith("file_size:") for f in gate["point_failures"])


def test_size_balanced_release_passes_gate(tmp_path):
    rng = np.random.default_rng(7)
    sizes, labels = [], []
    for pair in range(40):
        base = 8000 + 13 * pair
        delta = int(rng.integers(-40, 41))
        sizes += [base, base + delta if delta else base + 1]
        labels += [0, 1]
        if pair % 2:  # alternate which side is larger
            sizes[-2], sizes[-1] = sizes[-1], sizes[-2]
    gate = _run_file_size(tmp_path, sizes, labels)
    assert gate["status"] is True


def test_extractor_is_exact_byte_size(tmp_path):
    path = tmp_path / "x.png"
    path.write_bytes(b"a" * 12345)
    assert _file_size_features(path).tolist() == [12345.0]
