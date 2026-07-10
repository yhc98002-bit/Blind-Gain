from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Iterable

from jinja2 import Template

from src.captioning.store import merge_caption_rows
from src.eval.image_conditions import materialize_image
from src.rewards.answer_reward import answer_reward, extract_answer_span


CONDITIONS = ("real", "gray", "noise", "none", "caption")


def vllm_multimodal_limits(condition: str, max_images: int = 1) -> dict[str, int]:
    if condition not in CONDITIONS:
        raise ValueError(f"unsupported blind-solvability condition: {condition}")
    if max_images < 0:
        raise ValueError("max_images cannot be negative")
    return (
        {"image": max_images, "video": 0}
        if condition in {"real", "gray", "noise"}
        else {"image": 0, "video": 0}
    )


def load_geometry_rows(manifest: str | Path, splits: Iterable[str] = ("train", "test")) -> list[dict[str, Any]]:
    split_order = {name: index for index, name in enumerate(splits)}
    selected = set(split_order)
    rows = []
    with Path(manifest).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["split"] in selected:
                rows.append(row)
    return sorted(rows, key=lambda row: (split_order[str(row["split"])], int(row["row_index"])))


def load_caption_map(shards: Iterable[str | Path]) -> dict[str, str]:
    rows, _ = merge_caption_rows(shards)
    return {str(row["image_sha256"]): str(row["caption"]).strip() for row in rows}


def build_conditioned_messages(
    row: dict[str, Any],
    format_prompt: str,
    condition: str,
    cache_dir: str | Path,
    captions: dict[str, str] | None = None,
    noise_seed: int = 0,
) -> tuple[list[dict[str, Any]], list[str]]:
    if condition not in CONDITIONS:
        raise ValueError(f"unsupported blind-solvability condition: {condition}")
    rendered = Template(format_prompt.strip()).render(content=str(row["problem"]))
    images = list(row.get("images", []))
    parts = rendered.split("<image>")
    if len(parts) - 1 != len(images):
        raise ValueError(
            f"row {row['row_index']} has {len(parts) - 1} image markers but {len(images)} images"
        )

    content: list[dict[str, Any]] = []
    conditioned_paths: list[str] = []
    cache_dir = Path(cache_dir)
    for index, part in enumerate(parts):
        if index:
            image = images[index - 1]
            if condition in {"real", "gray", "noise"}:
                path = materialize_image(
                    str(image["path"]),
                    condition,
                    cache_dir,
                    noise_seed=noise_seed,
                )
                content.append({"type": "image", "image": path})
                conditioned_paths.append(path)
            elif condition == "caption":
                if captions is None or str(image["sha256"]) not in captions:
                    raise KeyError(f"missing fixed caption for image {image['sha256']}")
                caption = captions[str(image["sha256"])]
                content.append(
                    {
                        "type": "text",
                        "text": f"\n[Question-blind image description {index}: {caption}]\n",
                    }
                )
        if part:
            content.append({"type": "text", "text": part})

    if condition == "none":
        text = "".join(str(item["text"]) for item in content if item["type"] == "text")
        text = re.sub(r"[ \t]+", " ", text)
        content = [{"type": "text", "text": text}]
    return [{"role": "user", "content": content}], conditioned_paths


def pass_at_k(n: int, c: int, k: int) -> float:
    if not 0 <= c <= n or not 1 <= k <= n:
        raise ValueError("pass@k requires 0 <= c <= n and 1 <= k <= n")
    if n - c < k:
        return 1.0
    return 1.0 - math.prod((n - c - index) / (n - index) for index in range(k))


def score_item(
    gold: str,
    greedy_response: str,
    sampled_responses: list[str],
    group_size: int,
) -> dict[str, Any]:
    if not sampled_responses:
        raise ValueError("sampled responses cannot be empty")
    greedy = bool(answer_reward(greedy_response, gold))
    sampled_correct = [bool(answer_reward(response, gold)) for response in sampled_responses]
    n = len(sampled_correct)
    c = sum(sampled_correct)
    p = c / n
    greedy_extracted = extract_answer_span(greedy_response)
    return {
        "p_greedy": float(greedy),
        "greedy_correct": greedy,
        "greedy_extracted_answer": greedy_extracted.span,
        "greedy_format_valid": greedy_extracted.format_valid,
        "sample_count": n,
        "sample_correct_count": c,
        "sample_correct": sampled_correct,
        "p_sample": p,
        "pass_at_g": pass_at_k(n, c, group_size),
        "pass_at_k16": pass_at_k(n, c, n),
        "variance_proxy": p * (1.0 - p),
    }
