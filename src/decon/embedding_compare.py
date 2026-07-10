from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import torch

from src.decon.core import DEFAULT_THRESHOLDS


def load_embeddings(path: str | Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as payload:
        identifiers = payload["identifiers"].astype(str).tolist()
        features = payload["features"].astype(np.float32)
    if len(identifiers) != len(features) or len(set(identifiers)) != len(identifiers):
        raise ValueError(f"invalid or duplicate embedding identifiers in {path}")
    return dict(zip(identifiers, features))


def cosine_candidates(
    train_rows: list[dict[str, Any]],
    eval_rows: list[dict[str, Any]],
    features: dict[str, np.ndarray],
    key_field: str,
    inspect_min: float,
    top_k: int = 10,
    device: str | None = None,
) -> list[tuple[int, int, float]]:
    train_indices = [index for index, row in enumerate(train_rows) if row[key_field] in features]
    eval_indices = [index for index, row in enumerate(eval_rows) if row[key_field] in features]
    if not train_indices or not eval_indices:
        raise ValueError(f"embedding coverage is empty for key field {key_field}")
    train = np.stack([features[train_rows[index][key_field]] for index in train_indices])
    evaluation = np.stack([features[eval_rows[index][key_field]] for index in eval_indices])
    train /= np.maximum(np.linalg.norm(train, axis=1, keepdims=True), 1e-12)
    evaluation /= np.maximum(np.linalg.norm(evaluation, axis=1, keepdims=True), 1e-12)
    target_device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    eval_tensor = torch.from_numpy(evaluation).to(target_device)
    candidates: list[tuple[int, int, float]] = []
    for start in range(0, len(train), 256):
        scores = torch.from_numpy(train[start : start + 256]).to(target_device) @ eval_tensor.T
        values, indices = torch.topk(scores, k=min(top_k, len(eval_indices)), dim=1)
        for local_index, (row_values, row_indices) in enumerate(zip(values.cpu(), indices.cpu())):
            train_index = train_indices[start + local_index]
            for score, eval_position in zip(row_values.tolist(), row_indices.tolist()):
                if score >= inspect_min:
                    candidates.append((train_index, eval_indices[eval_position], float(score)))
    return candidates


def merge_embedding_signals(
    baseline: dict[str, Any],
    train_rows: list[dict[str, Any]],
    eval_rows: list[dict[str, Any]],
    image_features: dict[str, np.ndarray],
    text_features: dict[str, np.ndarray],
    thresholds: dict[str, float] | None = None,
    device: str | None = None,
) -> dict[str, Any]:
    thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    edge_map = {
        (edge["train_record_id"], edge["eval_record_id"]): dict(edge)
        for edge in baseline.get("candidate_edges", [])
    }
    action_rank = {"none": 0, "inspect": 1, "remove": 2}

    def add(train_index: int, eval_index: int, signal: str, score: float, remove_min: float) -> None:
        train = train_rows[train_index]
        evaluation = eval_rows[eval_index]
        key = (train["record_id"], evaluation["record_id"])
        edge = edge_map.setdefault(
            key,
            {
                "train_record_id": key[0],
                "eval_record_id": key[1],
                "train_dataset": train["dataset"],
                "eval_dataset": evaluation["dataset"],
                "action": "none",
                "signals": {},
            },
        )
        edge["signals"][signal] = score
        action = "remove" if score >= remove_min else "inspect"
        if action_rank[action] > action_rank[edge["action"]]:
            edge["action"] = action

    for train_index, eval_index, score in cosine_candidates(
        train_rows,
        eval_rows,
        image_features,
        "image_sha256",
        float(thresholds["image_embedding_inspect_min"]),
        device=device,
    ):
        add(train_index, eval_index, "dinov2_cosine", score, float(thresholds["image_embedding_remove_min"]))
    for train_index, eval_index, score in cosine_candidates(
        train_rows,
        eval_rows,
        text_features,
        "record_id",
        float(thresholds["text_embedding_inspect_min"]),
        device=device,
    ):
        add(train_index, eval_index, "bge_question_cosine", score, float(thresholds["text_embedding_remove_min"]))

    edges = sorted(edge_map.values(), key=lambda row: (row["train_record_id"], row["eval_record_id"]))
    result = {key: value for key, value in baseline.items() if key not in {"candidate_edges", "pending_layers"}}
    result.update(
        {
            "schema_version": "blind-gains.decon-comparison.v2",
            "thresholds": thresholds,
            "n_candidate_edges": len(edges),
            "action_counts": dict(sorted(Counter(edge["action"] for edge in edges).items())),
            "signal_counts": dict(sorted(Counter(signal for edge in edges for signal in edge["signals"]).items())),
            "candidate_edges": edges,
            "completed_layers": [
                "sha256_and_provenance",
                "phash_dhash",
                "dinov2_image_embedding",
                "normalized_exact_text",
                "question_5gram_jaccard",
                "bge_text_embedding",
            ],
            "pending_layers": ["ocr_text_overlap"],
        }
    )
    return result


def write_comparison(result: dict[str, Any], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
