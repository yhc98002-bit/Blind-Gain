from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from src.eval.nonqwen_adapters import (
    Gemma3Adapter,
    caption_qa_prompt,
    fliptrack_content,
    gemma_messages,
    internvl_question,
)
from scripts.eval_nonqwen_fliptrack import load_caption_pairs


ROW = {
    "pair_id": "pair-1",
    "question": "Which value is shown?",
    "image_a_path": "/images/a.png",
    "image_b_path": "/images/b.png",
}


def test_internvl_preserves_single_image_then_registered_question() -> None:
    content = fliptrack_content(ROW, "a", "real")

    question, images = internvl_question(content)

    assert images == ["/images/a.png"]
    assert question.startswith("<image>\nWhich value is shown?")
    assert question.count("<image>") == 1
    assert "<answer>" in question and "</answer>" in question


def test_internvl_numbers_multiple_images_without_answer_pointing_cues() -> None:
    question, images = internvl_question(
        [
            {"type": "text", "text": "Compare: "},
            {"type": "image", "image": "a.png"},
            {"type": "text", "text": " and "},
            {"type": "image", "image": "b.png"},
            {"type": "text", "text": " now."},
        ]
    )

    assert images == ["a.png", "b.png"]
    assert "Image-1: <image>" in question
    assert "Image-2: <image>" in question
    assert "circle" not in question.lower()
    assert "highlight" not in question.lower()


def test_no_image_and_caption_conditions_never_send_an_image_part() -> None:
    caption_row = {
        "pair_id": "pair-1",
        "caption_a": "A document with code 7Q.",
        "caption_b": "A document with code 7O.",
    }

    none_content = fliptrack_content(ROW, "a", "none")
    caption_content = fliptrack_content(ROW, "b", "caption", caption_row)

    assert all(item["type"] == "text" for item in none_content + caption_content)
    assert "7O" in caption_content[0]["text"]
    assert "Which value is shown?" in caption_content[0]["text"]
    assert "<answer>" in caption_content[0]["text"]


def test_caption_identity_and_missing_caption_fail_closed() -> None:
    with pytest.raises(ValueError, match="lacks pair"):
        fliptrack_content(ROW, "a", "caption")
    with pytest.raises(ValueError, match="identity mismatch"):
        fliptrack_content(
            ROW,
            "a",
            "caption",
            {"pair_id": "other", "caption_a": "caption", "caption_b": "caption"},
        )
    with pytest.raises(ValueError, match="cannot be empty"):
        caption_qa_prompt(" ", ROW["question"])


def test_gemma_messages_preserve_validated_content() -> None:
    content = fliptrack_content(ROW, "b", "real")

    messages = gemma_messages(content)

    assert messages == [{"role": "user", "content": content}]


def test_backend_content_rejects_unknown_payload_type() -> None:
    with pytest.raises(ValueError, match="unsupported content type"):
        gemma_messages([{"type": "video", "video": "clip.mp4"}])


def test_caption_pair_loader_rejects_duplicate_identity(tmp_path) -> None:
    source = tmp_path / "captions.jsonl"
    row = '{"pair_id":"same","caption_a":"A","caption_b":"B"}\n'
    source.write_text(row + row, encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate caption pair_id"):
        load_caption_pairs(source)


def test_nonqwen_launcher_pins_single_node_tp1_and_greedy_contract() -> None:
    root = Path(__file__).resolve().parents[1]
    launcher = (root / "scripts/launch_nonqwen_fliptrack_eval.sh").read_text(
        encoding="utf-8"
    )

    assert 'tensor_parallel_width: 1' in launcher
    assert 'replica_count: 1' in launcher
    assert 'decoding: {temperature: 0.0, top_p: 1.0, n: 1}' in launcher
    assert 'CUDA_VISIBLE_DEVICES=${GPU}' in launcher
    assert 'model must be an ephemeral node-local checkout' in launcher
    assert 'caption condition requires a nonempty fixed caption input' in launcher
    assert 'refusing to overwrite immutable non-Qwen run' in launcher
    assert 'LIMIT_ARGS="--limit ${LIMIT}"' in launcher
    assert '--dataset-id' in launcher


def test_gemma_adapter_explicitly_pins_slow_processor(monkeypatch) -> None:
    processor_kwargs = {}

    class FakeModel:
        device = "cpu"

        @classmethod
        def from_pretrained(cls, *args, **kwargs):
            return cls()

        def eval(self):
            return self

    class FakeProcessor:
        @classmethod
        def from_pretrained(cls, *args, **kwargs):
            processor_kwargs.update(kwargs)
            return cls()

    fake_torch = types.ModuleType("torch")
    fake_torch.bfloat16 = object()
    fake_transformers = types.ModuleType("transformers")
    fake_transformers.Gemma3ForConditionalGeneration = FakeModel
    fake_transformers.AutoProcessor = FakeProcessor
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(sys.modules, "transformers", fake_transformers)

    adapter = Gemma3Adapter("/models/gemma", device="cpu")
    adapter.load()

    assert processor_kwargs["local_files_only"] is True
    assert processor_kwargs["use_fast"] is False
