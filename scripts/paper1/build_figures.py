#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


PENDING_TOKEN = "{result-pending"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _contains_pending(value: Any) -> bool:
    if isinstance(value, str):
        return PENDING_TOKEN in value
    if isinstance(value, dict):
        return any(_contains_pending(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_pending(item) for item in value)
    return False


def validate_spec(root: Path, figure: str, spec: dict[str, Any]) -> None:
    if spec.get("status") != "ready":
        raise ValueError(f"figure {figure} is not ready")
    if _contains_pending(spec):
        raise ValueError(f"figure {figure} still contains a pending result slot")
    inputs = spec.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        raise ValueError(f"figure {figure} has no registered inputs")
    for record in inputs:
        if not isinstance(record, dict):
            raise ValueError(f"figure {figure} input is not an object")
        path = root / str(record.get("path", ""))
        expected_hash = str(record.get("sha256", ""))
        if not path.is_file():
            raise FileNotFoundError(f"figure {figure} input is absent: {path}")
        if len(expected_hash) != 64 or _sha256(path) != expected_hash:
            raise ValueError(f"figure {figure} input hash mismatch: {path}")


def _grouped_bar(ax: Any, plot: dict[str, Any]) -> None:
    labels = list(plot["labels"])
    series = list(plot["series"])
    x = np.arange(len(labels), dtype=float)
    width = 0.78 / len(series)
    for index, record in enumerate(series):
        values = np.asarray(record["values"], dtype=float)
        if len(values) != len(labels):
            raise ValueError("grouped-bar series length does not match labels")
        offset = (index - (len(series) - 1) / 2) * width
        ax.bar(x + offset, values, width, label=record["label"])
    ax.set_xticks(x, labels)
    ax.legend(frameon=False)


def _scatter(ax: Any, plot: dict[str, Any]) -> None:
    for record in plot["series"]:
        x = np.asarray(record["x"], dtype=float)
        y = np.asarray(record["y"], dtype=float)
        if len(x) != len(y):
            raise ValueError("scatter x/y lengths differ")
        ax.scatter(x, y, label=record["label"], s=38)
    ax.axhline(0, color="#666666", linewidth=1)
    ax.axvline(0, color="#666666", linewidth=1)
    ax.legend(frameon=False)


def _hurdle(ax: Any, plot: dict[str, Any]) -> None:
    labels = list(plot["labels"])
    estimates = np.asarray(plot["estimates"], dtype=float)
    lower = np.asarray(plot["lower"], dtype=float)
    upper = np.asarray(plot["upper"], dtype=float)
    if not (len(labels) == len(estimates) == len(lower) == len(upper)):
        raise ValueError("hurdle estimate and interval lengths differ")
    y = np.arange(len(labels))
    errors = np.vstack((estimates - lower, upper - estimates))
    ax.errorbar(estimates, y, xerr=errors, fmt="o", color="#1b6b5f", capsize=3)
    ax.axvline(0, color="#666666", linewidth=1)
    ax.set_yticks(y, labels)


PLOTTERS = {
    "grouped_bar": _grouped_bar,
    "scatter": _scatter,
    "hurdle": _hurdle,
}


def build_figure(root: Path, figure: str, spec: dict[str, Any], output: Path) -> None:
    validate_spec(root, figure, spec)
    plot = spec.get("plot")
    if not isinstance(plot, dict) or plot.get("type") not in PLOTTERS:
        raise ValueError(f"figure {figure} has an unsupported plot specification")
    fig, ax = plt.subplots(figsize=(7.2, 4.4), constrained_layout=True)
    PLOTTERS[str(plot["type"])](ax, plot)
    ax.set_title(str(plot["title"]))
    ax.set_xlabel(str(plot.get("xlabel", "")))
    ax.set_ylabel(str(plot.get("ylabel", "")))
    ax.grid(axis="y", alpha=0.2)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=220)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("figure")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--spec", type=Path, default=Path("docs/paper1/figure_specs.json")
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads((args.root / args.spec).read_text(encoding="utf-8"))
    figures = payload.get("figures", {})
    if args.figure not in figures:
        raise KeyError(f"unknown figure: {args.figure}")
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite figure: {args.output}")
    build_figure(args.root, args.figure, figures[args.figure], args.output)


if __name__ == "__main__":
    main()
