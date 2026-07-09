from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _image_stats(path: str | Path) -> np.ndarray:
    with Image.open(path) as image:
        arr = np.asarray(image.convert("RGB").resize((224, 224)), dtype=np.float32) / 255.0
    means = arr.mean(axis=(0, 1))
    stds = arr.std(axis=(0, 1))
    gray = arr.mean(axis=2)
    fft = np.fft.rfft2(gray)
    mag = np.log1p(np.abs(fft))
    bands = []
    h, w = mag.shape
    for lo, hi in [(0.0, 0.15), (0.15, 0.35), (0.35, 0.65), (0.65, 1.0)]:
        y0, y1 = int(h * lo), max(int(h * hi), int(h * lo) + 1)
        x0, x1 = int(w * lo), max(int(w * hi), int(w * lo) + 1)
        bands.append(float(mag[y0:y1, x0:x1].mean()))
    edges = np.abs(np.diff(gray, axis=0)).mean() + np.abs(np.diff(gray, axis=1)).mean()
    return np.asarray([*means, *stds, *bands, float(edges)], dtype=np.float32)


def _metadata_features(path: str | Path) -> np.ndarray:
    p = Path(path)
    stem = p.stem.encode("utf-8")
    return np.asarray(
        [
            float(p.stat().st_size),
            float(len(str(p))),
            float(sum(stem) % 997),
            float(p.name.endswith("_a.png")),
            float(p.name.endswith("_b.png")),
        ],
        dtype=np.float32,
    )


def _try_dinov2_features(paths: list[str], model_name: str, batch_size: int) -> tuple[np.ndarray | None, str]:
    try:
        import torch
        from transformers import AutoImageProcessor, AutoModel
    except Exception as exc:  # pragma: no cover - environment dependent
        return None, f"unavailable: import failed: {exc}"

    try:
        processor = AutoImageProcessor.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
    except Exception as exc:  # pragma: no cover - environment dependent
        return None, f"unavailable: model load failed: {exc}"

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device).eval()
    feats: list[np.ndarray] = []
    with torch.inference_mode():
        for start in range(0, len(paths), batch_size):
            images = [Image.open(path).convert("RGB") for path in paths[start : start + batch_size]]
            inputs = processor(images=images, return_tensors="pt").to(device)
            outputs = model(**inputs)
            pooled = outputs.last_hidden_state[:, 0].detach().float().cpu().numpy()
            feats.append(pooled)
            for image in images:
                image.close()
    return np.concatenate(feats, axis=0), "pass"


def _auc(labels: np.ndarray, scores: np.ndarray) -> float:
    order = np.argsort(scores)
    ranks = np.empty_like(order, dtype=np.float64)
    ranks[order] = np.arange(1, len(scores) + 1)
    pos = labels == 1
    n_pos = float(pos.sum())
    n_neg = float((~pos).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    return float((ranks[pos].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def _fit_linear_auc(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray, y_test: np.ndarray) -> float:
    x_mean = x_train.mean(axis=0, keepdims=True)
    x_std = x_train.std(axis=0, keepdims=True) + 1e-6
    xt = (x_train - x_mean) / x_std
    xv = (x_test - x_mean) / x_std
    y = y_train.astype(np.float32) * 2 - 1
    # Ridge-regularized least-squares classifier. This is intentionally simple and deterministic.
    reg = 1e-2
    lhs = xt.T @ xt + reg * np.eye(xt.shape[1], dtype=np.float32)
    rhs = xt.T @ y
    weights = np.linalg.solve(lhs, rhs)
    scores = xv @ weights
    return _auc(y_test, scores)


def build_member_table(rows: list[dict[str, Any]]) -> tuple[list[str], np.ndarray, list[str]]:
    paths: list[str] = []
    labels: list[int] = []
    groups: list[str] = []
    for row in rows:
        group = row.get("template_id", "") + ":" + row.get("pair_id", "")[:12]
        paths.extend([row["image_a_path"], row["image_b_path"]])
        labels.extend([0, 1])
        groups.extend([group, group])
    return paths, np.asarray(labels, dtype=np.int64), groups


def group_split(groups: list[str], test_fraction: float = 0.3) -> tuple[np.ndarray, np.ndarray]:
    unique = sorted(set(groups))
    test_count = max(1, int(math.ceil(len(unique) * test_fraction)))
    test_groups = set(unique[:: max(1, len(unique) // test_count)][:test_count])
    test = np.asarray([group in test_groups for group in groups], dtype=bool)
    train = ~test
    return train, test


def run(input_jsonl: str | Path, output: str | Path, dinov2_model: str, batch_size: int) -> dict[str, Any]:
    rows = _read_jsonl(input_jsonl)
    paths, labels, groups = build_member_table(rows)
    train, test = group_split(groups)

    stat_features = np.stack([_image_stats(path) for path in paths])
    metadata = np.stack([_metadata_features(path) for path in paths])

    metrics: dict[str, Any] = {
        "input_jsonl": str(input_jsonl),
        "n_pairs": len(rows),
        "n_members": len(paths),
        "split": "by_pair_template_group",
        "train_members": int(train.sum()),
        "test_members": int(test.sum()),
    }
    metrics["frequency_stat_auc"] = _fit_linear_auc(stat_features[train], labels[train], stat_features[test], labels[test])
    metrics["metadata_auc"] = _fit_linear_auc(metadata[train], labels[train], metadata[test], labels[test])

    dino_features, dino_status = _try_dinov2_features(paths, dinov2_model, batch_size)
    metrics["dinov2_status"] = dino_status
    if dino_features is not None:
        metrics["dinov2_auc"] = _fit_linear_auc(dino_features[train], labels[train], dino_features[test], labels[test])
    else:
        metrics["dinov2_auc"] = None
    aucs = [v for k, v in metrics.items() if k.endswith("_auc") and isinstance(v, float) and not math.isnan(v)]
    metrics["best_attacker_auc"] = max(aucs) if aucs else None

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-jsonl", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--dinov2-model", default="facebook/dinov2-small")
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    print(json.dumps(run(args.input_jsonl, args.output, args.dinov2_model, args.batch_size), sort_keys=True))


if __name__ == "__main__":
    main()
