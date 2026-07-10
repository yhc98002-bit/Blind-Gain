from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Iterable

from jinja2 import Template

from src.rewards.answer_reward import answer_reward, extract_answer_span


def load_geometry_examples(manifest: str | Path, split: str, limit: int) -> list[dict[str, Any]]:
    rows = []
    with Path(manifest).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["split"] != split:
                continue
            rows.append(row)
            if len(rows) == limit:
                break
    if len(rows) != limit:
        raise ValueError(f"requested {limit} {split} examples, found {len(rows)}")
    return rows


def build_r1v_messages(row: dict[str, Any], format_prompt: str) -> list[dict[str, Any]]:
    prompt = Template(format_prompt.strip()).render(content=str(row["problem"]))
    parts = prompt.split("<image>")
    images = [str(image["path"]) for image in row["images"]]
    if len(parts) - 1 != len(images):
        raise ValueError(
            f"row {row['row_index']} has {len(parts) - 1} image markers but {len(images)} images"
        )
    content: list[dict[str, Any]] = []
    for index, part in enumerate(parts):
        if index:
            content.append({"type": "image", "image": images[index - 1]})
        if part:
            content.append({"type": "text", "text": part})
    return [{"role": "user", "content": content}]


def format_prompt_sha256(format_prompt: str) -> str:
    return hashlib.sha256(format_prompt.encode("utf-8")).hexdigest()


def agreement_rows(
    generations: Iterable[dict[str, Any]],
    reference_accuracy: Callable[[str, str], float],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = []
    for raw in generations:
        response = str(raw["response"])
        ground_truth = str(raw["ground_truth"])
        ours = bool(answer_reward(response, ground_truth))
        reference = bool(reference_accuracy(response, ground_truth))
        extracted = extract_answer_span(response)
        rows.append(
            {
                **raw,
                "canonical_correct": ours,
                "easyr1_correct": reference,
                "agree": ours == reference,
                "extracted_answer": extracted.span,
                "extraction_level": extracted.extraction_level,
                "format_valid": extracted.format_valid,
                "disagreement_direction": (
                    "canonical_only" if ours and not reference else "easyr1_only" if reference and not ours else None
                ),
            }
        )
    if len(rows) < 300:
        raise ValueError(f"parser agreement requires at least 300 generations, found {len(rows)}")
    n = len(rows)
    metrics = {
        "schema_version": "blind-gains.parser-agreement.v1",
        "n": n,
        "agreement": sum(row["agree"] for row in rows) / n,
        "canonical_accuracy": sum(row["canonical_correct"] for row in rows) / n,
        "easyr1_accuracy": sum(row["easyr1_correct"] for row in rows) / n,
        "disagreements": sum(not row["agree"] for row in rows),
        "canonical_only": sum(row["disagreement_direction"] == "canonical_only" for row in rows),
        "easyr1_only": sum(row["disagreement_direction"] == "easyr1_only" for row in rows),
    }
    return rows, metrics
