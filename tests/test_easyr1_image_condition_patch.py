from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
EASYR1 = ROOT / "artifacts" / "repos" / "EasyR1"
sys.path.insert(0, str(EASYR1))

from verl.utils.dataset import RLHFDataset, condition_image  # noqa: E402


class FakeTokenizer:
    pad_token_id = 0

    def __init__(self) -> None:
        self.last_prompt = ""

    def apply_chat_template(self, messages, add_generation_prompt=True, tokenize=False):
        del add_generation_prompt, tokenize
        content = messages[0]["content"]
        self.last_prompt = content if isinstance(content, str) else str(content)
        return self.last_prompt

    def __call__(self, texts, add_special_tokens=False, return_tensors="pt"):
        del texts, add_special_tokens, return_tensors
        return {"input_ids": torch.tensor([[11, 12, 13]]), "attention_mask": torch.ones((1, 3), dtype=torch.long)}

    def encode(self, prompt, add_special_tokens=False):
        del prompt, add_special_tokens
        return [11, 12, 13]


class FakeImageProcessor:
    pass


class FakeProcessor:
    def __init__(self) -> None:
        self.image_processor = FakeImageProcessor()
        self.last_images = None

    def apply_chat_template(self, messages, add_generation_prompt=True, tokenize=False):
        del add_generation_prompt, tokenize
        chunks = []
        for item in messages[0]["content"]:
            chunks.append("<image>" if item["type"] == "image" else item["text"])
        return "".join(chunks)

    def __call__(self, images, texts, add_special_tokens=False, return_tensors="pt"):
        del texts, add_special_tokens, return_tensors
        self.last_images = images
        return {"input_ids": torch.tensor([[21, 22, 23]]), "attention_mask": torch.ones((1, 3), dtype=torch.long)}


def _dataset(tmp_path: Path, condition: str) -> tuple[RLHFDataset, FakeTokenizer, FakeProcessor]:
    image_dir = tmp_path / "images"
    image_dir.mkdir(exist_ok=True)
    Image.new("RGB", (10, 6), (255, 0, 0)).save(image_dir / "sample.png")
    source = tmp_path / f"{condition}.jsonl"
    source.write_text(
        json.dumps({"problem": "<image>Read the diagram.", "answer": "7", "images": ["sample.png"]}) + "\n",
        encoding="utf-8",
    )
    tokenizer = FakeTokenizer()
    processor = FakeProcessor()
    dataset = RLHFDataset(
        data_path=str(source),
        tokenizer=tokenizer,
        processor=processor,
        prompt_key="problem",
        answer_key="answer",
        image_key="images",
        image_dir=str(image_dir),
        max_prompt_length=16,
        truncation="right",
        min_pixels=None,
        max_pixels=None,
        filter_overlong_prompts=False,
        image_condition=condition,
        image_condition_seed=19,
    )
    return dataset, tokenizer, processor


def test_gray_condition_reaches_processor_and_rollout_payload(tmp_path: Path) -> None:
    dataset, _, processor = _dataset(tmp_path, "gray")
    row = dataset[0]
    rollout_image = row["multi_modal_data"]["images"][0]
    assert np.all(np.asarray(rollout_image) == 128)
    assert np.all(np.asarray(processor.last_images[0]) == 128)


def test_none_condition_removes_image_token_and_multimodal_payload(tmp_path: Path) -> None:
    dataset, tokenizer, processor = _dataset(tmp_path, "none")
    row = dataset[0]
    assert "multi_modal_data" not in row
    assert "<image>" not in tokenizer.last_prompt
    assert tokenizer.last_prompt == "Read the diagram."
    assert processor.last_images is None


def test_noise_condition_is_deterministic_and_content_keyed() -> None:
    red = Image.new("RGB", (12, 8), "red")
    blue = Image.new("RGB", (12, 8), "blue")
    first = np.asarray(condition_image(red, "noise", 5))
    second = np.asarray(condition_image(red, "noise", 5))
    different = np.asarray(condition_image(blue, "noise", 5))
    assert np.array_equal(first, second)
    assert not np.array_equal(first, different)


def test_unknown_condition_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unsupported image_condition"):
        _dataset(tmp_path, "invisible")
