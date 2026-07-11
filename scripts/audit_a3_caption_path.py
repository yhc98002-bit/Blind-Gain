#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import torch


ROOT = Path(__file__).resolve().parents[1]
EASYR1 = ROOT / "artifacts" / "repos" / "EasyR1"
sys.path.insert(0, str(EASYR1))

from verl.utils.dataset import (  # noqa: E402
    CAPTION_INSERT_TEMPLATE,
    RLHFDataset,
    load_caption_store,
)


class AuditTokenizer:
    pad_token_id = 0

    def __init__(self) -> None:
        self.last_prompt: Any = None

    def apply_chat_template(self, messages, add_generation_prompt=True, tokenize=False):
        del add_generation_prompt, tokenize
        self.last_prompt = messages[0]["content"]
        return self.last_prompt if isinstance(self.last_prompt, str) else str(self.last_prompt)

    def __call__(self, texts, add_special_tokens=False, return_tensors="pt"):
        del texts, add_special_tokens, return_tensors
        return {
            "input_ids": torch.tensor([[11, 12, 13]]),
            "attention_mask": torch.ones((1, 3), dtype=torch.long),
        }

    def encode(self, prompt, add_special_tokens=False):
        del prompt, add_special_tokens
        return [11, 12, 13]


class AuditImageProcessor:
    pass


class AuditProcessor:
    def __init__(self) -> None:
        self.image_processor = AuditImageProcessor()
        self.last_images = None

    def apply_chat_template(self, messages, add_generation_prompt=True, tokenize=False):
        del add_generation_prompt, tokenize
        return "".join(
            "<image>" if item["type"] == "image" else item["text"]
            for item in messages[0]["content"]
        )

    def __call__(self, images, texts, add_special_tokens=False, return_tensors="pt"):
        del texts, add_special_tokens, return_tensors
        self.last_images = images
        return {
            "input_ids": torch.tensor([[21, 22, 23]]),
            "attention_mask": torch.ones((1, 3), dtype=torch.long),
        }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dataset(
    source: Path, condition: str, caption_stores: list[Path]
) -> tuple[RLHFDataset, AuditTokenizer, AuditProcessor]:
    tokenizer = AuditTokenizer()
    processor = AuditProcessor()
    dataset = RLHFDataset(
        data_path=str(source),
        tokenizer=tokenizer,
        processor=processor,
        prompt_key="problem",
        answer_key="answer",
        image_key="images",
        image_dir=None,
        max_prompt_length=2048,
        truncation="right",
        min_pixels=262144,
        max_pixels=4194304,
        filter_overlong_prompts=False,
        image_condition=condition,
        image_condition_seed=20260710,
        caption_store_paths=[str(path) for path in caption_stores],
    )
    return dataset, tokenizer, processor


def build_audit(source: Path, caption_stores: list[Path]) -> dict[str, Any]:
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line]
    if not rows:
        raise ValueError("caption-path audit requires a nonempty training dataset")
    image_paths = [Path(image) for row in rows for image in row["images"]]
    if any(not path.is_file() for path in image_paths):
        raise FileNotFoundError("one or more filtered Geometry3K images are absent")
    image_hashes = {_sha256(path) for path in image_paths}
    captions, metadata = load_caption_store([str(path) for path in caption_stores])
    missing = sorted(image_hashes - captions.keys())
    if missing:
        raise KeyError(f"caption store misses {len(missing)} filtered image hashes")

    sample_indices = sorted({0, len(rows) // 2, len(rows) - 1})
    samples: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="blindgain_a3_audit_", dir="/tmp") as temporary:
        sample_source = Path(temporary) / "sample.jsonl"
        sample_rows = [rows[index] for index in sample_indices]
        sample_source.write_text(
            "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in sample_rows),
            encoding="utf-8",
        )
        real, _, real_processor = _dataset(sample_source, "real", caption_stores)
        caption, caption_tokenizer, caption_processor = _dataset(
            sample_source, "caption", caption_stores
        )
        if len(real) != len(sample_rows) or len(caption) != len(sample_rows):
            raise ValueError("EasyR1 loader changed sampled dataset row count")
        for index, source_row in enumerate(sample_rows):
            real_row = real[index]
            if "multi_modal_data" not in real_row or real_processor.last_images is None:
                raise AssertionError(f"real sample {index} did not reach the image processor")
            caption_row = caption[index]
            prompt = str(caption_tokenizer.last_prompt)
            if "multi_modal_data" in caption_row or caption_processor.last_images is not None:
                raise AssertionError(f"caption sample {index} leaked an image tensor")
            if "[Question-blind image description 1:" not in prompt or "<image>" in prompt:
                raise AssertionError(f"caption sample {index} does not use the fixed text insertion")
            samples.append(
                {
                    "row_index": int(source_row["row_index"]),
                    "real_has_multimodal_data": True,
                    "caption_has_multimodal_data": False,
                    "caption_prompt_has_fixed_block": True,
                    "caption_prompt_has_image_token": False,
                }
            )

    return {
        "schema_version": "blind-gains.a3-caption-path-audit.v1",
        "status": "pass",
        "source": str(source),
        "source_sha256": _sha256(source),
        "n_rows": len(rows),
        "n_image_references": len(image_paths),
        "n_unique_image_hashes": len(image_hashes),
        "caption_store_paths": [str(path) for path in caption_stores],
        "caption_store_file_sha256": {str(path): _sha256(path) for path in caption_stores},
        "caption_store_metadata": metadata,
        "caption_store_total_hashes": len(captions),
        "caption_store_missing_filtered_hashes": missing,
        "caption_store_coverage": 1.0,
        "caption_insert_template": CAPTION_INSERT_TEMPLATE,
        "sample_checks": samples,
        "question_blind_contract": (
            "caption store rows may not contain question, problem, answer, answer_a, or answer_b"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--caption-stores", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite caption-path audit: {args.output}")
    payload = build_audit(args.source, args.caption_stores)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(f".{args.output.name}.partial.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, args.output)
    print(json.dumps({key: payload[key] for key in ("status", "n_rows", "n_unique_image_hashes", "caption_store_coverage")}, sort_keys=True))


if __name__ == "__main__":
    main()
