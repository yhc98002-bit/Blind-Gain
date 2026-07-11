from __future__ import annotations

import math

from transformers.models.qwen2_vl.image_processing_qwen2_vl import smart_resize


def easyr1_resize_dimensions(
    width: int,
    height: int,
    *,
    min_pixels: int | None,
    max_pixels: int | None,
) -> tuple[int, int]:
    if width <= 0 or height <= 0:
        raise ValueError("image dimensions must be positive")
    resized_width, resized_height = width, height
    if max_pixels is not None and resized_width * resized_height > max_pixels:
        factor = math.sqrt(max_pixels / (resized_width * resized_height))
        resized_width = int(resized_width * factor)
        resized_height = int(resized_height * factor)
    if min_pixels is not None and resized_width * resized_height < min_pixels:
        factor = math.sqrt(min_pixels / (resized_width * resized_height))
        resized_width = int(resized_width * factor)
        resized_height = int(resized_height * factor)
    return resized_width, resized_height


def qwen25vl_visual_token_count(
    width: int,
    height: int,
    *,
    patch_size: int = 14,
    merge_size: int = 2,
    min_pixels: int = 3136,
    max_pixels: int = 12845056,
) -> int:
    factor = patch_size * merge_size
    resized_height, resized_width = smart_resize(
        height,
        width,
        factor=factor,
        min_pixels=min_pixels,
        max_pixels=max_pixels,
    )
    return (resized_height // patch_size) * (resized_width // patch_size) // (merge_size**2)


def image_grid_contract(
    width: int,
    height: int,
    *,
    min_pixels: int = 262144,
    max_pixels: int = 4194304,
) -> dict[str, object]:
    first = easyr1_resize_dimensions(
        width,
        height,
        min_pixels=min_pixels,
        max_pixels=max_pixels,
    )
    second = easyr1_resize_dimensions(
        *first,
        min_pixels=min_pixels,
        max_pixels=max_pixels,
    )
    old_prompt_tokens = qwen25vl_visual_token_count(*first)
    old_worker_features = qwen25vl_visual_token_count(*second)
    fixed_prompt_tokens = qwen25vl_visual_token_count(*first)
    fixed_worker_features = qwen25vl_visual_token_count(*first)
    return {
        "source_size": [width, height],
        "first_resize": list(first),
        "second_resize": list(second),
        "old_prompt_tokens": old_prompt_tokens,
        "old_worker_features": old_worker_features,
        "old_grid_mismatch": old_prompt_tokens != old_worker_features,
        "old_feature_delta": old_worker_features - old_prompt_tokens,
        "fixed_prompt_tokens": fixed_prompt_tokens,
        "fixed_worker_features": fixed_worker_features,
        "fixed_grid_mismatch": fixed_prompt_tokens != fixed_worker_features,
    }
