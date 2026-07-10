from __future__ import annotations

import io
import json
from pathlib import Path

import pandas as pd
import pytest
from PIL import Image

from scripts.prepare_layer1_vlmeval import (
    prepare_blink_frames,
    prepare_hallusion_json,
    prepare_mathvista_frame,
    prepare_mmvp_csv,
)


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


def test_mmvp_adapter_preserves_adjacent_pairs_and_labels(tmp_path: Path) -> None:
    source = tmp_path / "Questions.csv"
    source.write_text(
        "Index,Question,Options,Correct Answer\n"
        "1,Open or closed?,(a) Open (b) Closed,(a)\n"
        "2,Open or closed?,(a) Open (b) Closed,(b)\n",
        encoding="utf-8",
    )
    images = tmp_path / "MMVP Images"
    images.mkdir()
    Image.new("RGB", (8, 8), "red").save(images / "1.jpg")
    Image.new("RGB", (8, 8), "blue").save(images / "2.jpg")

    rows = prepare_mmvp_csv(source, images)

    assert [row["index"] for row in rows] == [1, 2]
    assert [row["pair_id"] for row in rows] == [0, 0]
    assert [row["pair_member"] for row in rows] == ["A", "B"]
    assert rows[0]["A"] == "Open" and rows[0]["B"] == "Closed"
    assert [row["answer"] for row in rows] == ["A", "B"]


def test_hallusion_adapter_keeps_text_controls_and_resolves_png_case(tmp_path: Path) -> None:
    source = tmp_path / "hallusion"
    visual_dir = source / "data" / "VS" / "chart"
    visual_dir.mkdir(parents=True)
    Image.new("RGB", (8, 8), "red").save(visual_dir / "0_1.PNG")
    rows = [
        {
            "category": "VS",
            "subcategory": "chart",
            "visual_input": "0",
            "set_id": "0",
            "figure_id": "0",
            "sample_note": "demo",
            "question_id": "0",
            "question": "Is red primary?",
            "gt_answer_details": "Yes.",
            "gt_answer": "1",
            "filename": None,
        },
        {
            "category": "VS",
            "subcategory": "chart",
            "visual_input": "1",
            "set_id": "0",
            "figure_id": "1",
            "sample_note": "demo",
            "question_id": "0",
            "question": "Is the plot red?",
            "gt_answer_details": "No.",
            "gt_answer": "0",
            "filename": "./VS/chart/0_1.png",
        },
    ]
    (source / "HallusionBench.json").write_text(json.dumps(rows), encoding="utf-8")

    adapted = prepare_hallusion_json(source, tmp_path / "adapter-images")

    assert len(adapted) == 2
    assert adapted[0]["answer"] == "Yes" and adapted[0]["image_is_placeholder"] is True
    assert adapted[1]["answer"] == "No" and adapted[1]["image_is_placeholder"] is False
    assert Path(adapted[0]["image_path"]).is_file()
    assert Path(adapted[1]["image_path"]).name == "0_1.PNG"
    assert adapted[1]["index"].split("_")[3:] == ["0", "1", "0"]
