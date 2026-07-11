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
    prepare_mathverse_frame,
    prepare_mmmu_frames,
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


def test_mathverse_adapter_keeps_mixed_scoring_contracts(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        [
            {
                "sample_index": "1",
                "problem_index": "9",
                "problem_version": "Vision Only",
                "question": "Which value?\nChoice:\nA.5 cm\nB.5 m",
                "image": _image_record("red"),
                "answer": "5 cm",
                "question_type": "multi-choice",
                "metadata": {"subject": "Geometry", "subfield": "Length", "source": "fixture"},
                "query_wo": "Return the correct option.\nWhich value?\nChoices:\nA:5 cm\nB:5 m",
                "question_for_eval": "Which value?\nChoice:\nA.5 cm\nB.5 m",
            },
            {
                "sample_index": "2",
                "problem_index": "10",
                "problem_version": "Text Dominant",
                "question": "What is 2 + 3?",
                "image": _image_record("blue"),
                "answer": "5",
                "question_type": "free-form",
                "metadata": {"subject": "Arithmetic"},
                "query_wo": "Directly answer.\nWhat is 2 + 3?",
                "question_for_eval": "What is 2 + 3?",
            },
        ]
    )

    rows = prepare_mathverse_frame(frame, tmp_path / "images")

    assert rows[0]["A"] == "5 cm" and rows[0]["B"] == "5 m"
    assert rows[0]["answer_option"] == "A"
    assert rows[0]["answer_options"] == "['A']"
    assert rows[0]["question_type"] == "multi_choice"
    assert "A" not in rows[1] and rows[1]["answer_option"] == ""
    assert rows[1]["question_type"] == "free_form"
    assert rows[1]["question"] == "Directly answer.\nWhat is 2 + 3?"


def test_mathverse_adapter_rejects_declared_free_form_choice_block(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        [
            {
                "sample_index": "1",
                "problem_index": "1",
                "problem_version": "Vision Only",
                "question": "Value?\nChoices:\nA:1\nB:2",
                "image": _image_record("red"),
                "answer": "1",
                "question_type": "free-form",
                "metadata": {},
                "query_wo": "Value?",
                "question_for_eval": "Value?\nChoices:\nA:1\nB:2",
            }
        ]
    )
    with pytest.raises(ValueError, match="free-form but contains a choice block"):
        prepare_mathverse_frame(frame, tmp_path / "images")


def test_mmmu_adapter_preserves_multi_image_order_and_open_contract(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        [
            {
                "id": "validation_Physics_1",
                "question": "Compare <image 2> with <image 1>.",
                "options": "['left', 'right']",
                "answer": "B",
                "question_type": "multiple-choice",
                "subfield": "Mechanics",
                "topic_difficulty": "Hard",
                "img_type": "['Plots', 'Diagrams']",
                "image_1": _image_record("red"),
                "image_2": _image_record("blue"),
            },
            {
                "id": "validation_Physics_2",
                "question": "Read <image 1>.",
                "options": "[]",
                "answer": "42",
                "question_type": "open",
                "subfield": "Mechanics",
                "topic_difficulty": "Easy",
                "img_type": "['Plots']",
                "image_1": _image_record("green"),
                "image_2": None,
            },
        ]
    )

    rows = prepare_mmmu_frames([("Physics", "validation", frame)], tmp_path / "images")

    assert rows[0]["image_count"] == 2
    assert rows[0]["image_references"] == "[2, 1]"
    assert rows[0]["A"] == "left" and rows[0]["answer_option"] == "B"
    assert rows[1]["question_type"] == "free_form" and "A" not in rows[1]
    assert rows[1]["split"] == "validation" and rows[1]["category"] == "Physics"


def test_mmmu_adapter_rejects_noncontiguous_or_missing_image_reference(tmp_path: Path) -> None:
    base = {
        "id": "dev_Art_1",
        "question": "Inspect <image 2>.",
        "options": "['yes', 'no']",
        "answer": "A",
        "question_type": "multiple-choice",
        "subfield": "Art",
        "topic_difficulty": "Easy",
        "image_1": _image_record("red"),
        "image_2": None,
    }
    with pytest.raises(ValueError, match="references image 2"):
        prepare_mmmu_frames([("Art", "dev", pd.DataFrame([base]))], tmp_path / "images-a")

    noncontiguous = {**base, "question": "Inspect <image 2>.", "image_1": None, "image_2": _image_record("blue")}
    with pytest.raises(ValueError, match="noncontiguous image fields"):
        prepare_mmmu_frames(
            [("Art", "dev", pd.DataFrame([noncontiguous]))],
            tmp_path / "images-b",
        )


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
