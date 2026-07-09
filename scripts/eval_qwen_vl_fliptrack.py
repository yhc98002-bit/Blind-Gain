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

from src.eval.fliptrack_metrics import aggregate_pair_metrics, pair_score
from src.eval.image_conditions import IMAGE_MODES, materialize_image
from src.eval.prompt_contract import format_question


def generate(model, processor, image_path: str, question: str, max_new_tokens: int) -> str:
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image_path},
                {"type": "text", "text": format_question(question)},
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
    parser.add_argument("--metrics-output", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--num-shards", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--image-mode", choices=IMAGE_MODES, default="real")
    parser.add_argument("--image-cache-dir", default=None)
    parser.add_argument("--noise-seed", type=int, default=0)
    parser.add_argument("--max-new-tokens", type=int, default=32)
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
    cache_dir = Path(args.image_cache_dir) if args.image_cache_dir else out_path.parent.parent / f"{args.image_mode}_image_cache"
    scored = []
    with out_path.open("w", encoding="utf-8") as out:
        for row in rows:
            row = dict(row)
            row["eval_image_mode"] = args.image_mode
            image_a = materialize_image(row["image_a_path"], args.image_mode, cache_dir, args.noise_seed)
            image_b = materialize_image(row["image_b_path"], args.image_mode, cache_dir, args.noise_seed)
            row["eval_image_a_path"] = image_a
            row["eval_image_b_path"] = image_b
            row["prediction_a"] = generate(model, processor, image_a, row["question"], args.max_new_tokens)
            row["prediction_b"] = generate(model, processor, image_b, row["question"], args.max_new_tokens)
            row.update(pair_score(row))
            scored.append(row)
            out.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
            out.flush()
    metrics = aggregate_pair_metrics(scored)
    metrics.update(
        {
            "image_mode": args.image_mode,
            "num_shards": float(args.num_shards),
            "shard_index": float(args.shard_index),
        }
    )
    if args.metrics_output:
        metrics_path = Path(args.metrics_output)
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(metrics, sort_keys=True))


if __name__ == "__main__":
    main()
