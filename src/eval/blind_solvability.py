from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Any, Iterable

from jinja2 import Template

from src.captioning.store import merge_caption_rows
from src.eval.image_conditions import materialize_image
from src.eval.prompt_contract import (
    DEFAULT_PROMPT_CONTRACT,
    PromptContractLike,
    prompt_contract_metadata,
    response_satisfies_contract,
)
from src.rewards.answer_reward import PARSER_VERSION, answer_reward, extract_answer_span
from src.rewards.pilot_reward import (
    DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
    PILOT_REWARD_VERSION,
    REASON_CODES,
    SYMBOLIC_GRADER_GUARD_VERSION,
    compute_score as pilot_compute_score,
)


CONDITIONS = ("real", "gray", "noise", "none", "caption")
PILOT_SCORING_MODE = "pilot-reward-v1+canonical-v2"
PILOT_ROW_SCHEMA_VERSION = "blind-gains.blind-solvability-pilot.v1"
GUARDED_RESCORE_VERSION = "l7-guarded-rescore-v1"


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


def load_geometry_rows(
    manifest: str | Path,
    splits: Iterable[str] = ("train", "test"),
    *,
    train_filter_ids: set[int] | None = None,
) -> list[dict[str, Any]]:
    split_order = {name: index for index, name in enumerate(splits)}
    selected = set(split_order)
    rows = []
    matched_train_ids: set[int] = set()
    with Path(manifest).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            split = str(row["split"])
            if split not in selected:
                continue
            row_index = int(row["row_index"])
            if split == "train" and train_filter_ids is not None:
                if row_index not in train_filter_ids:
                    continue
                matched_train_ids.add(row_index)
            rows.append(row)
    if train_filter_ids is not None and "train" in selected:
        missing = sorted(train_filter_ids - matched_train_ids)
        if missing:
            preview = ", ".join(str(value) for value in missing[:10])
            raise ValueError(
                f"train filter contains {len(missing)} IDs absent from the selected manifest: {preview}"
            )
    return sorted(rows, key=lambda row: (split_order[str(row["split"])], int(row["row_index"])))


def load_train_filter_ids(path: str | Path) -> set[int]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError("train filter must be a non-empty JSON list")
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in payload):
        raise ValueError("train filter IDs must be non-negative integers")
    values = set(payload)
    if len(values) != len(payload):
        raise ValueError("train filter contains duplicate IDs")
    return values


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


def jeffreys_smoothed_probability(n: int, c: int) -> float:
    if n <= 0 or not 0 <= c <= n:
        raise ValueError("Jeffreys smoothing requires n > 0 and 0 <= c <= n")
    return (c + 0.5) / (n + 1.0)


def mixed_group_probability(probability: float, group_size: int) -> float:
    if not 0.0 <= probability <= 1.0 or group_size <= 0:
        raise ValueError("mixed-group probability requires p in [0, 1] and group_size > 0")
    return 1.0 - probability**group_size - (1.0 - probability) ** group_size


def score_item_pilot(
    gold: str,
    greedy_response: str,
    sampled_responses: list[str],
    group_size: int,
    prompt_contract: PromptContractLike = None,
    *,
    format_weight: float = 0.5,
    symbolic_grader_timeout_seconds: float = DEFAULT_SYMBOLIC_GRADER_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Score L7 with the exact pilot reward and canonical-v2 in parallel."""

    if not sampled_responses:
        raise ValueError("sampled responses cannot be empty")
    contract_metadata = prompt_contract_metadata(prompt_contract)
    if contract_metadata["prompt_contract_sha256"] != DEFAULT_PROMPT_CONTRACT.sha256:
        raise ValueError("pilot scoring requires the registered pilot prompt contract")

    responses = [greedy_response, *sampled_responses]
    inherited_shadow_path = os.environ.pop("BLIND_GAINS_REWARD_SHADOW_LOG", None)
    try:
        pilot_scores = [
            pilot_compute_score(
                {"response": response, "ground_truth": gold},
                format_weight=format_weight,
                require_shadow_log=False,
                symbolic_grader_timeout_seconds=symbolic_grader_timeout_seconds,
            )
            for response in responses
        ]
    finally:
        if inherited_shadow_path is not None:
            os.environ["BLIND_GAINS_REWARD_SHADOW_LOG"] = inherited_shadow_path
    inverse_reasons = {value: key for key, value in REASON_CODES.items()}
    reason_names = [
        inverse_reasons[float(score["reward_disagreement_reason_code"])] for score in pilot_scores
    ]
    canonical_correct = [bool(answer_reward(response, gold)) for response in responses]
    extracted = [extract_answer_span(response) for response in responses]
    contract_valid = [
        response_satisfies_contract(response, prompt_contract) for response in responses
    ]

    greedy_score = pilot_scores[0]
    sampled_scores = pilot_scores[1:]
    sampled_correct = [bool(score["accuracy"]) for score in sampled_scores]
    n = len(sampled_correct)
    c = sum(sampled_correct)
    p_raw = c / n
    p_i = jeffreys_smoothed_probability(n, c)
    sampled_training_rewards = [float(score["training_reward"]) for score in sampled_scores]
    sampled_format_rewards = [float(score["format"]) for score in sampled_scores]
    sampled_native_rewards = [
        float(score["native_r1v_shadow_reward"]) for score in sampled_scores
    ]
    sampled_native_valid = [
        bool(score["native_r1v_shadow_valid"]) for score in sampled_scores
    ]
    sampled_canonical_rewards = [
        float(score["canonical_eval_reward"]) for score in sampled_scores
    ]
    canonical_sample_count = sum(canonical_correct[1:])

    return {
        "scoring_mode": PILOT_SCORING_MODE,
        "pilot_reward_version": PILOT_REWARD_VERSION,
        "symbolic_grader_guard_version": SYMBOLIC_GRADER_GUARD_VERSION,
        "symbolic_grader_timeout_seconds": symbolic_grader_timeout_seconds,
        "format_weight": format_weight,
        "p_greedy": float(greedy_score["accuracy"]),
        "greedy_correct": bool(greedy_score["accuracy"]),
        "greedy_training_reward": float(greedy_score["training_reward"]),
        "greedy_format_reward": float(greedy_score["format"]),
        "greedy_native_r1v_shadow_reward": float(greedy_score["native_r1v_shadow_reward"]),
        "greedy_native_r1v_shadow_valid": bool(greedy_score["native_r1v_shadow_valid"]),
        "greedy_canonical_correct": canonical_correct[0],
        "greedy_reward_disagreement_reason": reason_names[0],
        "greedy_extracted_answer": extracted[0].span,
        "greedy_extractor_valid": extracted[0].extractor_valid,
        "greedy_contract_valid": contract_valid[0],
        "greedy_format_valid": contract_valid[0],
        "greedy_acc_strict": contract_valid[0] and bool(greedy_score["accuracy"]),
        "sampled_extractor_valid": [value.extractor_valid for value in extracted[1:]],
        "sampled_contract_valid": contract_valid[1:],
        "sampled_training_rewards": sampled_training_rewards,
        "sampled_format_rewards": sampled_format_rewards,
        "sampled_native_r1v_shadow_rewards": sampled_native_rewards,
        "sampled_native_r1v_shadow_valid": sampled_native_valid,
        "sampled_canonical_rewards": sampled_canonical_rewards,
        "sampled_reward_disagreement_reasons": reason_names[1:],
        "parser_version": PARSER_VERSION,
        **contract_metadata,
        "sample_count": n,
        "sample_correct_count": c,
        "sample_correct": sampled_correct,
        "p_sample": p_raw,
        "p_i_jeffreys": p_i,
        "q_i": mixed_group_probability(p_i, group_size),
        "pass_at_g": pass_at_k(n, c, group_size),
        "pass_at_k16": pass_at_k(n, c, n),
        "variance_proxy": p_i * (1.0 - p_i),
        "mean_sampled_training_reward": sum(sampled_training_rewards) / n,
        "mean_sampled_format_reward": sum(sampled_format_rewards) / n,
        "canonical_sample_correct_count": canonical_sample_count,
        "canonical_p_sample": canonical_sample_count / n,
        "sampled_canonical_correct": canonical_correct[1:],
    }


def score_item(
    gold: str,
    greedy_response: str,
    sampled_responses: list[str],
    group_size: int,
    prompt_contract: PromptContractLike = None,
) -> dict[str, Any]:
    if not sampled_responses:
        raise ValueError("sampled responses cannot be empty")
    greedy = bool(answer_reward(greedy_response, gold))
    sampled_correct = [bool(answer_reward(response, gold)) for response in sampled_responses]
    n = len(sampled_correct)
    c = sum(sampled_correct)
    p = c / n
    greedy_extracted = extract_answer_span(greedy_response)
    greedy_contract_valid = response_satisfies_contract(greedy_response, prompt_contract)
    sampled_extractor_valid = [extract_answer_span(response).extractor_valid for response in sampled_responses]
    sampled_contract_valid = [
        response_satisfies_contract(response, prompt_contract) for response in sampled_responses
    ]
    return {
        "p_greedy": float(greedy),
        "greedy_correct": greedy,
        "greedy_extracted_answer": greedy_extracted.span,
        "greedy_extractor_valid": greedy_extracted.extractor_valid,
        "greedy_contract_valid": greedy_contract_valid,
        "greedy_format_valid": greedy_contract_valid,
        "greedy_acc_strict": greedy_contract_valid and greedy,
        "sampled_extractor_valid": sampled_extractor_valid,
        "sampled_contract_valid": sampled_contract_valid,
        "parser_version": PARSER_VERSION,
        **prompt_contract_metadata(prompt_contract),
        "sample_count": n,
        "sample_correct_count": c,
        "sample_correct": sampled_correct,
        "p_sample": p,
        "pass_at_g": pass_at_k(n, c, group_size),
        "pass_at_k16": pass_at_k(n, c, n),
        "variance_proxy": p * (1.0 - p),
    }
