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


_RESUME_SCORE_FIELDS = {
    "greedy_response",
    "sampled_responses",
    "p_greedy",
    "greedy_correct",
    "greedy_extracted_answer",
    "greedy_format_valid",
    "sample_count",
    "sample_correct_count",
    "sample_correct",
    "p_sample",
    "pass_at_g",
    "pass_at_k16",
    "variance_proxy",
}


def load_validated_resume_prefix(
    resume_from: Path,
    rows: list[dict[str, Any]],
    *,
    condition: str,
    batch_size: int,
    max_tokens: int,
    sample_count: int,
    sample_temperature: float,
    seed: int,
) -> list[str]:
    """Return raw JSONL rows after proving they are this run's canonical prefix."""
    raw_lines = resume_from.read_text(encoding="utf-8").splitlines()
    if not raw_lines:
        raise ValueError(f"resume source is empty: {resume_from}")
    if any(not line.strip() for line in raw_lines):
        raise ValueError(f"resume source contains a blank JSONL row: {resume_from}")
    if len(raw_lines) > len(rows):
        raise ValueError(
            f"resume source has {len(raw_lines)} rows but current selection has only {len(rows)}"
        )
    if len(raw_lines) != len(rows) and len(raw_lines) % batch_size:
        raise ValueError(
            f"resume prefix length {len(raw_lines)} is not aligned to batch size {batch_size}"
        )

    expected_decoding = {
        "greedy": {"temperature": 0.0, "top_p": 1.0, "n": 1},
        "sampled": {
            "temperature": sample_temperature,
            "top_p": 1.0,
            "n": sample_count,
        },
        "max_tokens": max_tokens,
        "seed": seed,
    }
    seen: set[tuple[Any, Any, Any]] = set()
    for index, (raw_line, source_row) in enumerate(zip(raw_lines, rows), start=1):
        try:
            resumed = json.loads(raw_line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid JSON in resume source at line {index}: {error}") from error
        if not isinstance(resumed, dict):
            raise ValueError(f"resume source line {index} is not a JSON object")

        identity = (resumed.get("split"), resumed.get("row_index"), resumed.get("qid"))
        if identity in seen:
            raise ValueError(f"duplicate row identity in resume source at line {index}: {identity}")
        seen.add(identity)

        expected = {
            "schema_version": "blind-gains.blind-solvability.v1",
            "split": source_row["split"],
            "row_index": source_row["row_index"],
            "qid": source_row.get("qid"),
            "problem": source_row["problem"],
            "ground_truth": source_row["answer"],
            "image_sha256": [image["sha256"] for image in source_row.get("images", [])],
            "condition": condition,
            "source_metadata": source_row.get("metadata"),
            "sample_count": sample_count,
            "decoding": expected_decoding,
        }
        for key, expected_value in expected.items():
            if resumed.get(key) != expected_value:
                raise ValueError(
                    f"resume source mismatch at line {index} for {key}: "
                    f"expected {expected_value!r}, found {resumed.get(key)!r}"
                )
        missing = sorted(_RESUME_SCORE_FIELDS - resumed.keys())
        if missing:
            raise ValueError(f"resume source line {index} is missing score fields: {missing}")
        if len(resumed["sampled_responses"]) != sample_count:
            raise ValueError(f"resume source line {index} has the wrong sampled response count")
        if len(resumed["sample_correct"]) != sample_count:
            raise ValueError(f"resume source line {index} has the wrong sampled score count")
        correct_count = sum(bool(value) for value in resumed["sample_correct"])
        if resumed["sample_correct_count"] != correct_count:
            raise ValueError(f"resume source line {index} has inconsistent sampled scores")
    return raw_lines


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
    parser.add_argument("--resume-from", type=Path)
    parser.add_argument("--caption-shards", type=Path, nargs="*")
    parser.add_argument("--splits", nargs="+", default=["train", "test"])
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--group-size", type=int, default=5)
    parser.add_argument("--sample-count", type=int, default=16)
    parser.add_argument("--sample-temperature", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=20260710)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.72)
    parser.add_argument("--max-model-len", type=int, default=4096)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite blind-solvability output: {args.output}")
    if args.sample_count < args.group_size:
        raise ValueError("sample count must be at least the registered group size")

    format_prompt = args.format_prompt.read_text(encoding="utf-8")
    captions = load_caption_map(args.caption_shards or []) if args.condition == "caption" else None
    rows = load_geometry_rows(args.manifest, args.splits)
    if not rows:
        raise ValueError(f"manifest selection is empty for splits: {args.splits}")
    resume_lines = (
        load_validated_resume_prefix(
            args.resume_from,
            rows,
            condition=args.condition,
            batch_size=args.batch_size,
            max_tokens=args.max_tokens,
            sample_count=args.sample_count,
            sample_temperature=args.sample_temperature,
            seed=args.seed,
        )
        if args.resume_from
        else []
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for line in resume_lines:
            handle.write(line + "\n")
        handle.flush()
    if len(resume_lines) == len(rows):
        print(
            json.dumps(
                {
                    "condition": args.condition,
                    "processed": len(rows),
                    "resumed": len(resume_lines),
                    "total": len(rows),
                }
            ),
            flush=True,
        )
        return

    from transformers import AutoProcessor
    from vllm import LLM, SamplingParams

    max_images = max((len(row.get("images", [])) for row in rows), default=0)
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
        max_model_len=args.max_model_len,
        gpu_memory_utilization=args.gpu_memory_utilization,
        limit_mm_per_prompt=vllm_multimodal_limits(args.condition, max_images=max_images),
    )
    greedy_params = SamplingParams(temperature=0.0, top_p=1.0, n=1, max_tokens=args.max_tokens, seed=args.seed)
    sample_params = SamplingParams(
        temperature=args.sample_temperature,
        top_p=1.0,
        n=args.sample_count,
        max_tokens=args.max_tokens,
        seed=args.seed,
    )

    with args.output.open("a", encoding="utf-8") as handle:
        for start in range(len(resume_lines), len(rows), args.batch_size):
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
                    "qid": row.get("qid"),
                    "problem": row["problem"],
                    "ground_truth": row["answer"],
                    "image_sha256": [image["sha256"] for image in row.get("images", [])],
                    "condition": args.condition,
                    "source_metadata": row.get("metadata"),
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
            print(
                json.dumps(
                    {
                        "condition": args.condition,
                        "processed": min(start + len(batch), len(rows)),
                        "resumed": len(resume_lines),
                        "total": len(rows),
                    }
                ),
                flush=True,
            )


if __name__ == "__main__":
    main()
