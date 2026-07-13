from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from PIL import Image

from src.eval.prompt_contract import ANSWER_FORMAT_CONTRACT, format_question


NONQWEN_BACKENDS = ("internvl3", "gemma3")
FLIPTRACK_CONDITIONS = ("real", "none", "caption")


def validate_content(content: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for index, item in enumerate(content):
        item_type = str(item.get("type", ""))
        if item_type == "image":
            value = str(item.get("image", ""))
            if not value:
                raise ValueError(f"empty image path at content index {index}")
            normalized.append({"type": "image", "image": value})
        elif item_type == "text":
            value = str(item.get("text", ""))
            if not value:
                raise ValueError(f"empty text at content index {index}")
            normalized.append({"type": "text", "text": value})
        else:
            raise ValueError(f"unsupported content type at index {index}: {item_type!r}")
    if not normalized or not any(item["type"] == "text" for item in normalized):
        raise ValueError("VLM content requires at least one text part")
    return normalized


def internvl_question(content: Iterable[dict[str, Any]]) -> tuple[str, list[str]]:
    normalized = validate_content(content)
    image_count = sum(item["type"] == "image" for item in normalized)
    image_paths: list[str] = []
    parts: list[str] = []
    for item in normalized:
        if item["type"] == "image":
            image_paths.append(item["image"])
            marker = (
                "<image>\n"
                if image_count == 1
                else f"Image-{len(image_paths)}: <image>\n"
            )
            parts.append(marker)
        else:
            parts.append(item["text"])
    return "".join(parts), image_paths


def gemma_messages(content: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"role": "user", "content": validate_content(content)}]


def caption_qa_prompt(caption: str, question: str) -> str:
    caption = caption.strip()
    if not caption:
        raise ValueError("fixed question-blind caption cannot be empty")
    return (
        "Answer the question using only the image caption. "
        "If the caption does not contain enough information, make the best possible "
        "answer from the caption.\n"
        f"Caption: {caption}\n"
        f"Question: {question.strip()}\n"
        f"{ANSWER_FORMAT_CONTRACT}"
    )


def fliptrack_content(
    row: dict[str, Any],
    side: str,
    condition: str,
    caption_row: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    if side not in {"a", "b"}:
        raise ValueError(f"invalid FlipTrack side: {side}")
    if condition not in FLIPTRACK_CONDITIONS:
        raise ValueError(f"invalid non-Qwen FlipTrack condition: {condition}")
    question = str(row["question"])
    if condition == "real":
        return [
            {"type": "image", "image": str(row[f"image_{side}_path"])},
            {"type": "text", "text": format_question(question)},
        ]
    if condition == "none":
        return [{"type": "text", "text": format_question(question)}]
    if caption_row is None:
        raise ValueError(f"caption condition lacks pair {row['pair_id']}")
    if str(caption_row.get("pair_id")) != str(row["pair_id"]):
        raise ValueError("caption row pair identity mismatch")
    caption = str(caption_row.get(f"caption_{side}", ""))
    return [{"type": "text", "text": caption_qa_prompt(caption, question)}]


def _dynamic_preprocess(
    image: Image.Image,
    *,
    min_num: int = 1,
    max_num: int = 12,
    image_size: int = 448,
    use_thumbnail: bool = True,
) -> list[Image.Image]:
    width, height = image.size
    if width <= 0 or height <= 0:
        raise ValueError("image dimensions must be positive")
    aspect_ratio = width / height
    target_ratios = sorted(
        {
            (i, j)
            for n in range(min_num, max_num + 1)
            for i in range(1, n + 1)
            for j in range(1, n + 1)
            if min_num <= i * j <= max_num
        },
        key=lambda ratio: ratio[0] * ratio[1],
    )
    best_ratio = (1, 1)
    best_difference = float("inf")
    area = width * height
    for ratio in target_ratios:
        difference = abs(aspect_ratio - ratio[0] / ratio[1])
        if difference < best_difference or (
            difference == best_difference
            and area > 0.5 * image_size * image_size * ratio[0] * ratio[1]
        ):
            best_difference = difference
            best_ratio = ratio
    target_width = image_size * best_ratio[0]
    target_height = image_size * best_ratio[1]
    resized = image.resize((target_width, target_height), Image.Resampling.BICUBIC)
    tiles = []
    columns = target_width // image_size
    for index in range(best_ratio[0] * best_ratio[1]):
        left = (index % columns) * image_size
        top = (index // columns) * image_size
        tiles.append(resized.crop((left, top, left + image_size, top + image_size)))
    if use_thumbnail and len(tiles) != 1:
        tiles.append(image.resize((image_size, image_size), Image.Resampling.BICUBIC))
    return tiles


@dataclass
class InternVL3Adapter:
    model_path: str
    device: str = "cuda"
    max_new_tokens: int = 384
    max_dynamic_patches: int = 12
    _model: Any = None
    _tokenizer: Any = None
    _transform: Any = None

    def load(self) -> None:
        if self._model is not None:
            return
        import torch
        import torchvision.transforms as transforms
        from transformers import AutoModel, AutoTokenizer

        self._model = AutoModel.from_pretrained(
            self.model_path,
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
            use_flash_attn=False,
            trust_remote_code=True,
            local_files_only=True,
        ).eval()
        self._model.to(self.device)
        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            trust_remote_code=True,
            use_fast=False,
            local_files_only=True,
        )
        self._transform = transforms.Compose(
            [
                transforms.Lambda(
                    lambda image: image.convert("RGB") if image.mode != "RGB" else image
                ),
                transforms.Resize(
                    (448, 448), interpolation=transforms.InterpolationMode.BICUBIC
                ),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)
                ),
            ]
        )

    def generate(self, content: Iterable[dict[str, Any]]) -> str:
        self.load()
        import torch

        question, image_paths = internvl_question(content)
        pixel_values = None
        patch_counts: list[int] = []
        if image_paths:
            tensors = []
            for image_path in image_paths:
                with Image.open(Path(image_path)) as image:
                    tiles = _dynamic_preprocess(
                        image.convert("RGB"), max_num=self.max_dynamic_patches
                    )
                image_tensor = torch.stack([self._transform(tile) for tile in tiles])
                tensors.append(image_tensor)
                patch_counts.append(int(image_tensor.shape[0]))
            pixel_values = torch.cat(tensors).to(device=self.device, dtype=torch.bfloat16)
        generation_config = {
            "max_new_tokens": self.max_new_tokens,
            "do_sample": False,
        }
        kwargs: dict[str, Any] = {}
        if len(image_paths) > 1:
            kwargs["num_patches_list"] = patch_counts
        with torch.inference_mode():
            response = self._model.chat(
                self._tokenizer,
                pixel_values,
                question,
                generation_config,
                **kwargs,
            )
        return str(response).strip()


@dataclass
class Gemma3Adapter:
    model_path: str
    device: str = "cuda"
    max_new_tokens: int = 384
    _model: Any = None
    _processor: Any = None

    def load(self) -> None:
        if self._model is not None:
            return
        import torch
        from transformers import AutoProcessor, Gemma3ForConditionalGeneration

        self._model = Gemma3ForConditionalGeneration.from_pretrained(
            self.model_path,
            torch_dtype=torch.bfloat16,
            device_map={"": self.device},
            local_files_only=True,
        ).eval()
        self._processor = AutoProcessor.from_pretrained(
            self.model_path,
            local_files_only=True,
            use_fast=False,
        )

    def generate(self, content: Iterable[dict[str, Any]]) -> str:
        self.load()
        import torch

        messages = gemma_messages(content)
        inputs = self._processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self._model.device, dtype=torch.bfloat16)
        input_length = inputs["input_ids"].shape[-1]
        with torch.inference_mode():
            output = self._model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
            )
        generated = output[0][input_length:]
        return self._processor.decode(generated, skip_special_tokens=True).strip()


def create_nonqwen_adapter(
    backend: str,
    model_path: str,
    *,
    device: str = "cuda",
    max_new_tokens: int = 384,
) -> InternVL3Adapter | Gemma3Adapter:
    if backend == "internvl3":
        return InternVL3Adapter(model_path, device, max_new_tokens)
    if backend == "gemma3":
        return Gemma3Adapter(model_path, device, max_new_tokens)
    raise ValueError(f"unsupported non-Qwen backend: {backend}")
