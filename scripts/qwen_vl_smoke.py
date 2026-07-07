#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

import torch
from qwen_vl_utils import process_vision_info
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--image-path", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    args = parser.parse_args()

    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        args.model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    processor = AutoProcessor.from_pretrained(args.model_path, trust_remote_code=True)
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": args.image_path},
                {"type": "text", "text": args.question},
            ],
        }
    ]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to(model.device)
    with torch.inference_mode():
        generated_ids = model.generate(**inputs, do_sample=False, max_new_tokens=args.max_new_tokens)
    generated_ids = generated_ids[:, inputs["input_ids"].shape[1] :]
    response = processor.batch_decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
    print(json.dumps({"image_path": args.image_path, "question": args.question, "response": response.strip()}, ensure_ascii=True))


if __name__ == "__main__":
    main()

