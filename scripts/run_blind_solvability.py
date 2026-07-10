#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image

from src.eval.blind_solvability import (
    CONDITIONS,
    build_conditioned_messages,
    load_caption_map,
    load_geometry_rows,
    score_item,
    vllm_multimodal_limits,
)


def _vllm_request(processor: Any, messages: list[dict[str, Any]], image_paths: list[str]) -> tuple[dict[str, Any], list[Image.Image]]:
    prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    opened = []
    for path in image_paths:
        with Image.open(path) as source:
            opened.append(source.convert("RGB"))
    request: dict[str, Any] = {"prompt": prompt}
    if opened:
        request["multi_modal_data"] = {"image": opened[0] if len(opened) == 1 else opened}
    return request, opened


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--format-prompt", type=Path, required=True)
    parser.add_argument("--condition", choices=CONDITIONS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--caption-shards", type=Path, nargs="*")
    parser.add_argument("--splits", nargs="+", default=["train", "test"])
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--group-size", type=int, default=5)
    parser.add_argument("--sample-count", type=int, default=16)
    parser.add_argument("--sample-temperature", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=20260710)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.72)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite blind-solvability output: {args.output}")
    if args.sample_count < args.group_size:
        raise ValueError("sample count must be at least the registered group size")

    from transformers import AutoProcessor
    from vllm import LLM, SamplingParams

    format_prompt = args.format_prompt.read_text(encoding="utf-8")
    captions = load_caption_map(args.caption_shards or []) if args.condition == "caption" else None
    rows = load_geometry_rows(args.manifest, args.splits)
    processor = AutoProcessor.from_pretrained(
        args.model_path,
        trust_remote_code=True,
        local_files_only=True,
    )
    llm = LLM(
        model=args.model_path,
        trust_remote_code=True,
        tensor_parallel_size=1,
        dtype="bfloat16",
        max_model_len=4096,
        gpu_memory_utilization=args.gpu_memory_utilization,
        limit_mm_per_prompt=vllm_multimodal_limits(args.condition),
    )
    greedy_params = SamplingParams(temperature=0.0, top_p=1.0, n=1, max_tokens=args.max_tokens, seed=args.seed)
    sample_params = SamplingParams(
        temperature=args.sample_temperature,
        top_p=1.0,
        n=args.sample_count,
        max_tokens=args.max_tokens,
        seed=args.seed,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for start in range(0, len(rows), args.batch_size):
            batch = rows[start : start + args.batch_size]
            requests = []
            opened_images: list[Image.Image] = []
            for row in batch:
                messages, image_paths = build_conditioned_messages(
                    row,
                    format_prompt,
                    args.condition,
                    args.cache_dir,
                    captions=captions,
                    noise_seed=args.seed,
                )
                request, opened = _vllm_request(processor, messages, image_paths)
                requests.append(request)
                opened_images.extend(opened)
            try:
                greedy_outputs = llm.generate(requests, greedy_params, use_tqdm=False)
                sampled_outputs = llm.generate(requests, sample_params, use_tqdm=False)
            finally:
                for image in opened_images:
                    image.close()
            for row, greedy_output, sampled_output in zip(batch, greedy_outputs, sampled_outputs):
                greedy_response = greedy_output.outputs[0].text.strip()
                sampled_responses = [output.text.strip() for output in sampled_output.outputs]
                scored = score_item(str(row["answer"]), greedy_response, sampled_responses, args.group_size)
                output = {
                    "schema_version": "blind-gains.blind-solvability.v1",
                    "split": row["split"],
                    "row_index": row["row_index"],
                    "problem": row["problem"],
                    "ground_truth": row["answer"],
                    "image_sha256": [image["sha256"] for image in row.get("images", [])],
                    "condition": args.condition,
                    "greedy_response": greedy_response,
                    "sampled_responses": sampled_responses,
                    **scored,
                    "decoding": {
                        "greedy": {"temperature": 0.0, "top_p": 1.0, "n": 1},
                        "sampled": {
                            "temperature": args.sample_temperature,
                            "top_p": 1.0,
                            "n": args.sample_count,
                        },
                        "max_tokens": args.max_tokens,
                        "seed": args.seed,
                    },
                }
                handle.write(json.dumps(output, sort_keys=True, ensure_ascii=True) + "\n")
                handle.flush()
            print(json.dumps({"condition": args.condition, "processed": min(start + len(batch), len(rows)), "total": len(rows)}), flush=True)


if __name__ == "__main__":
    main()
