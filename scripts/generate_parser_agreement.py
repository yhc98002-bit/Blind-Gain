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

from src.eval.parser_agreement import build_r1v_messages, format_prompt_sha256, load_geometry_examples


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--format-prompt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--split", default="test")
    parser.add_argument("--limit", type=int, default=320)
    parser.add_argument("--num-shards", type=int, required=True)
    parser.add_argument("--shard-index", type=int, required=True)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite parser-agreement shard: {args.output}")
    if not 0 <= args.shard_index < args.num_shards:
        raise ValueError("invalid shard index")

    all_rows = load_geometry_examples(args.manifest, args.split, args.limit)
    rows = [row for index, row in enumerate(all_rows) if index % args.num_shards == args.shard_index]
    format_prompt = args.format_prompt.read_text(encoding="utf-8")
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        args.model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
        local_files_only=True,
    ).eval()
    processor = AutoProcessor.from_pretrained(args.model_path, trust_remote_code=True, local_files_only=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in rows:
            messages = build_r1v_messages(row, format_prompt)
            prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            image_inputs, video_inputs = process_vision_info(messages)
            inputs = processor(
                text=[prompt],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            ).to(model.device)
            with torch.inference_mode():
                generated = model.generate(**inputs, do_sample=False, max_new_tokens=args.max_new_tokens)
            generated = generated[:, inputs["input_ids"].shape[1] :]
            response = processor.batch_decode(
                generated, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )[0].strip()
            output = {
                "schema_version": "blind-gains.parser-agreement-generation.v1",
                "source_row_index": row["row_index"],
                "split": row["split"],
                "image_paths": [image["path"] for image in row["images"]],
                "problem": row["problem"],
                "ground_truth": row["answer"],
                "response": response,
                "model_path": args.model_path,
                "format_prompt_sha256": format_prompt_sha256(format_prompt),
                "decoding": {"temperature": 0.0, "top_p": 1.0, "n": 1, "max_new_tokens": args.max_new_tokens},
                "num_shards": args.num_shards,
                "shard_index": args.shard_index,
            }
            handle.write(json.dumps(output, sort_keys=True, ensure_ascii=True) + "\n")
            handle.flush()
    print(json.dumps({"rows": len(rows), "shard_index": args.shard_index}, sort_keys=True))


if __name__ == "__main__":
    main()
