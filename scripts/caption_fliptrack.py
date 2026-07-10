#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
from qwen_vl_utils import process_vision_info
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.captioning.store import CAPTION_PROMPT


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
        out = model.generate(**inputs, do_sample=False, max_new_tokens=max_new_tokens)
    out = out[:, inputs["input_ids"].shape[1] :]
    return processor.batch_decode(out, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0].strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--num-shards", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--max-new-tokens", type=int, default=384)
    args = parser.parse_args()
    if args.num_shards < 1:
        raise ValueError("--num-shards must be >= 1")
    if not 0 <= args.shard_index < args.num_shards:
        raise ValueError("--shard-index must be in [0, --num-shards)")

    rows = []
    with Path(args.manifest).open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle):
            if idx % args.num_shards != args.shard_index:
                continue
            rows.append(json.loads(line))
            if args.limit is not None and len(rows) >= args.limit:
                break

    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        args.model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    processor = AutoProcessor.from_pretrained(args.model_path, trust_remote_code=True)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as out:
        for row in rows:
            row = dict(row)
            row["caption_model_path"] = args.model_path
            row["caption_prompt"] = CAPTION_PROMPT
            row["caption_a"] = generate_caption(model, processor, row["image_a_path"], args.max_new_tokens)
            row["caption_b"] = generate_caption(model, processor, row["image_b_path"], args.max_new_tokens)
            out.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
            out.flush()
    print(json.dumps({"n_pairs": len(rows), "num_shards": args.num_shards, "shard_index": args.shard_index}, sort_keys=True))


if __name__ == "__main__":
    main()
