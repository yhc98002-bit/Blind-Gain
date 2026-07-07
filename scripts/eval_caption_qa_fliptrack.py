#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.eval.fliptrack_metrics import aggregate_pair_metrics


def answer_from_caption(model, processor, caption: str, question: str, max_new_tokens: int) -> str:
    prompt = (
        "Answer the question using only the image caption. "
        "If the caption does not contain enough information, make the best possible answer from the caption.\n"
        f"Caption: {caption}\n"
        f"Question: {question}\n"
        "Answer with only the answer."
    )
    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text], padding=True, return_tensors="pt").to(model.device)
    with torch.inference_mode():
        out = model.generate(**inputs, do_sample=False, max_new_tokens=max_new_tokens)
    out = out[:, inputs["input_ids"].shape[1] :]
    return processor.batch_decode(out, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0].strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--metrics-output", default=None)
    parser.add_argument("--max-new-tokens", type=int, default=32)
    args = parser.parse_args()

    rows = []
    with Path(args.input).open("r", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]

    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        args.model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    processor = AutoProcessor.from_pretrained(args.model_path, trust_remote_code=True)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    scored = []
    with out_path.open("w", encoding="utf-8") as out:
        for row in rows:
            row = dict(row)
            row["prediction_a"] = answer_from_caption(model, processor, row["caption_a"], row["question"], args.max_new_tokens)
            row["prediction_b"] = answer_from_caption(model, processor, row["caption_b"], row["question"], args.max_new_tokens)
            scored.append(row)
            out.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
            out.flush()

    metrics = aggregate_pair_metrics(scored)
    if args.metrics_output:
        metrics_path = Path(args.metrics_output)
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(metrics, sort_keys=True))


if __name__ == "__main__":
    main()
