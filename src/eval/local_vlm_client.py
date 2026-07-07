from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class VLMRequest:
    image_path: str
    prompt: str
    request_id: str | None = None


class LocalVLMClient:
    """Small deterministic wrapper for local Qwen-VL-style inference.

    The implementation lazy-loads transformers so parser tests and data generation
    can run before the heavy VLM environment is installed.
    """

    def __init__(self, model_path: str, device: str = "cuda", max_new_tokens: int = 64):
        self.model_path = model_path
        self.device = device
        self.max_new_tokens = max_new_tokens
        self._model = None
        self._processor = None

    def load(self) -> None:
        if self._model is not None:
            return
        import torch
        from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

        self._processor = AutoProcessor.from_pretrained(self.model_path, trust_remote_code=True)
        self._model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            self.model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto" if self.device == "cuda" else None,
            trust_remote_code=True,
        )
        self._model.eval()

    def generate(self, request: VLMRequest) -> str:
        self.load()
        import torch
        from qwen_vl_utils import process_vision_info

        assert self._model is not None
        assert self._processor is not None
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": request.image_path},
                    {"type": "text", "text": request.prompt},
                ],
            }
        ]
        text = self._processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self._processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        ).to(self._model.device)
        with torch.inference_mode():
            output_ids = self._model.generate(
                **inputs,
                do_sample=False,
                temperature=None,
                max_new_tokens=self.max_new_tokens,
            )
        generated = output_ids[:, inputs["input_ids"].shape[1] :]
        return self._processor.batch_decode(generated, skip_special_tokens=True)[0].strip()


def run_jsonl(model_path: str, input_jsonl: str | Path, output_jsonl: str | Path) -> None:
    client = LocalVLMClient(model_path)
    output_jsonl = Path(output_jsonl)
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with Path(input_jsonl).open("r", encoding="utf-8") as src, output_jsonl.open("w", encoding="utf-8") as dst:
        for line in src:
            row = json.loads(line)
            request = VLMRequest(
                image_path=row["image_path"],
                prompt=row["prompt"],
                request_id=row.get("request_id"),
            )
            row["prediction"] = client.generate(request)
            dst.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--input-jsonl", required=True)
    parser.add_argument("--output-jsonl", required=True)
    args = parser.parse_args(argv)
    run_jsonl(args.model_path, args.input_jsonl, args.output_jsonl)


if __name__ == "__main__":
    main()
