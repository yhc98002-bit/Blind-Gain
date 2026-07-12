from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.audit_grpo_chat_template_v2 import audit_rendered_rows, build_messages


class _Shape:
    shape = (1, 17)


class FakeProcessor:
    def apply_chat_template(self, messages, add_generation_prompt=True, tokenize=False):
        assert add_generation_prompt and not tokenize
        content = messages[0]["content"]
        rendered = "<|im_start|>user\n"
        for item in content:
            rendered += (
                "<|vision_start|><|image_pad|><|vision_end|>"
                if item["type"] == "image"
                else item["text"]
            )
        return rendered + "<|im_end|>\n<|im_start|>assistant"

    def __call__(self, **kwargs):
        assert kwargs["add_special_tokens"] is False
        return {"input_ids": _Shape()}


def _row(split: str, index: int) -> dict[str, object]:
    return {
        "split": split,
        "row_index": index,
        "problem": "<image>Find x.",
        "answer": "3",
        "images": [f"image-{split}-{index}.png"],
    }


def test_chat_template_audit_checks_exact_contract_without_loading_images() -> None:
    rows = [_row("train", index) for index in range(8)] + [
        _row("test", index) for index in range(8)
    ]
    template = "{{ content }} <think>reasoning</think><answer>answer</answer>"

    records, checks = audit_rendered_rows(
        processor=FakeProcessor(),
        rows=rows,
        format_prompt=template,
        min_pixels=None,
        max_pixels=None,
        max_prompt_length=2048,
        load_images=False,
    )

    assert len(records) == 16
    assert all(checks.values())
    assert all(row["rendered_vision_marker_count"] == 1 for row in records)


def test_message_builder_rejects_silent_image_marker_mismatch() -> None:
    row = _row("train", 0)
    row["images"] = []

    with pytest.raises(ValueError, match="image markers"):
        build_messages(row, "{{ content }}")


def test_chat_template_audit_launcher_is_cpu_only_and_versioned() -> None:
    root = Path(__file__).resolve().parents[1]
    launcher = root / "scripts" / "launch_grpo_chat_template_audit_v2.sh"
    subprocess.run(["bash", "-n", str(launcher)], check=True)
    source = launcher.read_text(encoding="utf-8")

    assert "CUDA_VISIBLE_DEVICES=''" in source
    assert 'gpu_ids: []' in source
    assert "grpo_chat_template_audit_v2.json" in source
    assert "refusing to overwrite" in source
