#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from PIL import Image
from vllm import LLM, SamplingParams


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--image-path", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--max-model-len", type=int, default=4096)
    parser.add_argument("--max-tokens", type=int, default=32)
    args = parser.parse_args()

    prompt = (
        "<|im_start|>user\n"
        "<|vision_start|><|image_pad|><|vision_end|>"
        f"{args.question}<|im_end|>\n"
        "<|im_start|>assistant\n"
    )
    llm = LLM(
        model=args.model_path,
        trust_remote_code=True,
        max_model_len=args.max_model_len,
        limit_mm_per_prompt={"image": 1},
        gpu_memory_utilization=0.6,
    )
    image = Image.open(args.image_path).convert("RGB")
    outputs = llm.generate(
        {"prompt": prompt, "multi_modal_data": {"image": image}},
        SamplingParams(temperature=0.0, max_tokens=args.max_tokens),
    )
    text = outputs[0].outputs[0].text.strip()
    print(json.dumps({"image_path": args.image_path, "question": args.question, "response": text}, ensure_ascii=True))


if __name__ == "__main__":
    main()

