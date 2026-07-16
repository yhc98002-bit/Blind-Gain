#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import torch
from qwen_vl_utils import process_vision_info
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.captioning.store import (
    CAPTION_PROMPT,
    SCHEMA_VERSION,
    discover_images,
    load_validated_caption_prefix,
    select_shard,
)


def generate_caption(model, processor, image_path: str, max_new_tokens: int) -> str:
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image_path},
                {"type": "text", "text": CAPTION_PROMPT},
            ],
        }
    ]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(text=[text], images=image_inputs, videos=video_inputs, padding=True, return_tensors="pt").to(model.device)
    with torch.inference_mode():
        generated = model.generate(**inputs, do_sample=False, max_new_tokens=max_new_tokens)
    generated = generated[:, inputs["input_ids"].shape[1] :]
    return processor.batch_decode(generated, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0].strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--caption-model-id")
    parser.add_argument("--caption-model-revision")
    parser.add_argument("--tensor-parallel-width", type=int, choices=(1,), default=1)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--num-shards", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--max-new-tokens", type=int, default=384)
    parser.add_argument("--resume-from", type=Path)
    args = parser.parse_args()
    caption_model_id = args.caption_model_id or args.model_path
    caption_model_revision = args.caption_model_revision or args.model_path
    output = Path(args.output)
    if output.exists() and output.stat().st_size:
        raise FileExistsError(f"refusing to overwrite caption-store shard: {output}")
    items = select_shard(discover_images(args.input_dir), args.num_shards, args.shard_index)
    if not items:
        raise ValueError("selected caption-store shard is empty")
    resume_lines = (
        load_validated_caption_prefix(
            args.resume_from,
            items,
            model_path=args.model_path,
            max_new_tokens=args.max_new_tokens,
            model_revision=caption_model_revision,
            tensor_parallel_width=args.tensor_parallel_width,
        )
        if args.resume_from
        else []
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for line in resume_lines:
            handle.write(line + "\n")
        handle.flush()
    if len(resume_lines) == len(items):
        print(
            json.dumps(
                {
                    "n_images": len(items),
                    "resumed": len(resume_lines),
                    "num_shards": args.num_shards,
                    "shard_index": args.shard_index,
                }
            )
        )
        return

    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        args.model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    processor = AutoProcessor.from_pretrained(args.model_path, trust_remote_code=True)
    prompt_hash = hashlib.sha256(CAPTION_PROMPT.encode("utf-8")).hexdigest()
    with output.open("a", encoding="utf-8") as handle:
        for item in items[len(resume_lines) :]:
            row = {
                "schema_version": SCHEMA_VERSION,
                **item,
                "caption": generate_caption(model, processor, item["image_path"], args.max_new_tokens),
                "caption_model_path": args.model_path,
                "caption_model_id": caption_model_id,
                "caption_model_revision": caption_model_revision,
                "caption_prompt": CAPTION_PROMPT,
                "caption_prompt_sha256": prompt_hash,
                "max_new_tokens": args.max_new_tokens,
                "decoding": {"temperature": 0.0, "top_p": 1.0, "n": 1},
                "tensor_parallel_width": args.tensor_parallel_width,
            }
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
            handle.flush()
    print(
        json.dumps(
            {
                "n_images": len(items),
                "resumed": len(resume_lines),
                "num_shards": args.num_shards,
                "shard_index": args.shard_index,
            }
        )
    )


if __name__ == "__main__":
    main()
