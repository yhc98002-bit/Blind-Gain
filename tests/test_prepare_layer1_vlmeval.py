from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import pytest
from PIL import Image

from scripts.prepare_layer1_vlmeval import prepare_blink_frames, prepare_mathvista_frame


def _image_record(color: str) -> dict[str, bytes]:
    buffer = io.BytesIO()
    Image.new("RGB", (12, 8), color).save(buffer, format="PNG")
    return {"bytes": buffer.getvalue()}


def test_mathvista_adapter_preserves_typed_metadata_and_derives_option(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        [
            {
                "pid": "7",
                "question": "Which value?",
                "query": "Hint: inspect the plot.\nQuestion: Which value?",
                "decoded_image": _image_record("red"),
                "answer": "two",
                "question_type": "multi_choice",
                "answer_type": "text",
                "choices": ["one", "two", "three"],
                "metadata": {"task": "chart", "skills": ["reading"]},
            }
        ]
    )
    rows = prepare_mathvista_frame(frame, tmp_path / "images")
    assert rows[0]["answer_option"] == "B"
    assert rows[0]["question"].startswith("Hint:")
    assert rows[0]["skills"] == "['reading']"
    assert Path(rows[0]["image_path"]).is_file()


def test_mathvista_adapter_rejects_ambiguous_choice_mapping(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        [
            {
                "pid": "8",
                "question": "Which?",
                "decoded_image": _image_record("red"),
                "answer": "same",
                "question_type": "multi_choice",
                "answer_type": "text",
                "choices": ["same", "same"],
                "metadata": {},
            }
        ]
    )
    with pytest.raises(ValueError, match="exactly one choice"):
        prepare_mathvista_frame(frame, tmp_path / "images")

    dropped: list[str] = []
    assert prepare_mathvista_frame(
        frame,
        tmp_path / "images",
        drop_ambiguous_choices=True,
        dropped_ids=dropped,
    ) == []
    assert dropped == ["8"]


def test_blink_adapter_keeps_image_order_and_removes_duplicate_choice_block(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        [
            {
                "idx": "val_demo_1",
                "question": "Which image matches?",
                "sub_task": "Demo",
                "image_1": _image_record("red"),
                "image_2": _image_record("blue"),
                "image_3": None,
                "image_4": None,
                "choices": ["first", "second"],
                "answer": "(B)",
                "prompt": "Compare the images.\nSelect from the following choices.\n(A) first\n(B) second",
            }
        ]
    )
    rows = prepare_blink_frames([frame], tmp_path / "images")
    assert rows[0]["answer"] == "B"
    assert rows[0]["question"] == "Compare the images."
    assert rows[0]["A"] == "first" and rows[0]["B"] == "second"
    assert rows[0]["image_path"].startswith("[")
